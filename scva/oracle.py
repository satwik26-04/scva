"""
Unified AI Oracle Provider Framework for SCVA.
Supports:
  - Antigravity (IDE agent integration via ai_queries.json / ai_responses.json)
  - Google Gemini API
  - OpenAI API (GPT-4o, GPT-4o-mini, etc.)
  - Anthropic Claude API (Claude 3.5 Sonnet / Haiku)
  - Local LLMs via Ollama (localhost:11434)
  - OpenRouter (Meta Llama 3.3, DeepSeek, etc.)
  - NanoGPT API
  - Zhipu GLM / Z.ai
  - Custom OpenAI-Compatible Endpoints
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import aiohttp

from .config import ConfigManager



# Query / Response schemas


@dataclass
class AIQuery:
    query_id: str = ""
    query_type: str = ""
    instruction: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    expected_format: dict[str, Any] = field(default_factory=dict)
    citation_key: str = ""
    claim_text: str = ""

    def __post_init__(self):
        if not self.query_id:
            raw = f"{self.citation_key}::{self.query_type}::{self.claim_text}"
            self.query_id = hashlib.sha256(raw.encode()).hexdigest()[:12]


@dataclass
class AIResponse:
    query_id: str
    result: Any
    confidence: float = 1.0
    explanation: str = ""
    verified_by: str = "ai_oracle"



# Abstract Base Oracle


class AIOracle(ABC):
    @abstractmethod
    def query(self, q: AIQuery) -> Optional[AIResponse]:
        """Submit query synchronously or return cached answer."""
        ...

    async def query_async(self, q: AIQuery, session: aiohttp.ClientSession) -> Optional[AIResponse]:
        """Async implementation for online API providers."""
        return self.query(q)



# Null Oracle (Rule-based fallback)


class NullOracle(AIOracle):
    def query(self, q: AIQuery) -> Optional[AIResponse]:
        return None



# FileBasedOracle — Default for Antigravity IDE Integration


class FileBasedOracle(AIOracle):
    """
    Primary integration point for Antigravity AI assistant.
    Writes queries to ai_queries.json; ingests responses from ai_responses.json.
    """

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._pending: list[AIQuery] = []
        self._responses: dict[str, AIResponse] = {}

        resp_path = self.output_dir / "ai_responses.json"
        if resp_path.exists():
            self._load_responses(resp_path)

    def query(self, q: AIQuery) -> Optional[AIResponse]:
        if q.query_id in self._responses:
            return self._responses[q.query_id]
        self._pending.append(q)
        return None

    def flush_queries(self) -> Path:
        path = self.output_dir / "ai_queries.json"
        payload = {
            "scva_version": "1.0.0",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pending_count": len(self._pending),
            "instructions": (
                "For each query below, fill in 'result', 'confidence' (0-1), "
                "and 'explanation', then save as ai_responses.json. "
                "Run `scva ingest-response` to complete."
            ),
            "queries": [_query_to_dict(q) for q in self._pending],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        return path

    def ingest(self, response_path: Path) -> int:
        self._load_responses(response_path)
        return len(self._responses)

    def pending_count(self) -> int:
        return len(self._pending)

    def _load_responses(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(text)
        responses = data if isinstance(data, list) else data.get("responses", [])
        for r in responses:
            resp = AIResponse(
                query_id=r["query_id"],
                result=r.get("result"),
                confidence=float(r.get("confidence", 1.0)),
                explanation=r.get("explanation", ""),
                verified_by=r.get("verified_by", "ai_oracle_antigravity"),
            )
            self._responses[resp.query_id] = resp



# OpenAI-Compatible Generic Oracle (OpenAI, OpenRouter, NanoGPT, GLM, Custom)


class OpenAICompatibleOracle(AIOracle):
    """Generic Oracle supporting any OpenAI-compatible chat completions API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        provider_name: str = "openai",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider_name = provider_name

    async def query_async(self, q: AIQuery, session: aiohttp.ClientSession) -> Optional[AIResponse]:
        prompt = _build_prompt(q)
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a scientific citation verification assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }

        try:
            async with session.post(url, json=payload, headers=headers, timeout=25) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = _extract_json(content)
                    return AIResponse(
                        query_id=q.query_id,
                        result=parsed.get("result"),
                        confidence=float(parsed.get("confidence", 0.9)),
                        explanation=parsed.get("explanation", content),
                        verified_by=f"{self.provider_name}:{self.model}",
                    )
        except Exception as e:
            return AIResponse(
                query_id=q.query_id,
                result=None,
                confidence=0.0,
                explanation=f"{self.provider_name} API Error: {e}",
                verified_by=f"{self.provider_name}_error",
            )
        return None

    def query(self, q: AIQuery) -> Optional[AIResponse]:
        return None  # Called via query_async in pipeline



# Ollama Local LLM Oracle


class OllamaOracle(AIOracle):
    """Local LLM Oracle connecting to Ollama (http://localhost:11434)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def query_async(self, q: AIQuery, session: aiohttp.ClientSession) -> Optional[AIResponse]:
        prompt = _build_prompt(q)
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1},
        }

        try:
            async with session.post(url, json=payload, timeout=45) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data.get("response", "")
                    parsed = _extract_json(content)
                    return AIResponse(
                        query_id=q.query_id,
                        result=parsed.get("result"),
                        confidence=float(parsed.get("confidence", 0.85)),
                        explanation=parsed.get("explanation", content),
                        verified_by=f"ollama:{self.model}",
                    )
        except Exception as e:
            return AIResponse(
                query_id=q.query_id,
                result=None,
                confidence=0.0,
                explanation=f"Ollama Error: {e}",
                verified_by="ollama_error",
            )
        return None

    def query(self, q: AIQuery) -> Optional[AIResponse]:
        return None



# Anthropic Claude Oracle


class ClaudeOracle(AIOracle):
    """Anthropic Claude API integration."""

    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022") -> None:
        self.api_key = api_key
        self.model = model
        self.url = "https://api.anthropic.com/v1/messages"

    async def query_async(self, q: AIQuery, session: aiohttp.ClientSession) -> Optional[AIResponse]:
        prompt = _build_prompt(q)
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            async with session.post(self.url, json=payload, headers=headers, timeout=25) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["content"][0]["text"]
                    parsed = _extract_json(content)
                    return AIResponse(
                        query_id=q.query_id,
                        result=parsed.get("result"),
                        confidence=float(parsed.get("confidence", 0.95)),
                        explanation=parsed.get("explanation", content),
                        verified_by=f"claude:{self.model}",
                    )
        except Exception as e:
            return AIResponse(
                query_id=q.query_id,
                result=None,
                confidence=0.0,
                explanation=f"Claude API Error: {e}",
                verified_by="claude_error",
            )
        return None

    def query(self, q: AIQuery) -> Optional[AIResponse]:
        return None



# Google Gemini Oracle


class GeminiOracle(AIOracle):
    """Google Gemini API integration via REST endpoint."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self.api_key = api_key
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    async def query_async(self, q: AIQuery, session: aiohttp.ClientSession) -> Optional[AIResponse]:
        prompt = _build_prompt(q)
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            async with session.post(self.url, json=payload, timeout=25) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = _extract_json(content)
                    return AIResponse(
                        query_id=q.query_id,
                        result=parsed.get("result"),
                        confidence=float(parsed.get("confidence", 0.95)),
                        explanation=parsed.get("explanation", content),
                        verified_by=f"gemini:{self.model}",
                    )
        except Exception as e:
            return AIResponse(
                query_id=q.query_id,
                result=None,
                confidence=0.0,
                explanation=f"Gemini API Error: {e}",
                verified_by="gemini_error",
            )
        return None

    def query(self, q: AIQuery) -> Optional[AIResponse]:
        return None



# Multi-Provider Factory


def make_oracle(
    mode: str = "antigravity",
    output_dir: Optional[Path] = None,
    model_override: Optional[str] = None,
) -> AIOracle:
    """
    Factory creating an AIOracle instance for any requested provider.
    Supported modes:
      - 'antigravity' or 'file'
      - 'gemini'
      - 'openai'
      - 'claude'
      - 'ollama'
      - 'openrouter'
      - 'nanogpt'
      - 'glm' / 'z.ai'
      - 'null'
    """
    config = ConfigManager()
    mode = mode.lower()

    if mode in ("antigravity", "file"):
        if output_dir is None:
            raise ValueError("output_dir required for Antigravity file oracle")
        return FileBasedOracle(Path(output_dir))

    if mode == "null":
        return NullOracle()

    if mode == "ollama":
        endpoint = config.get_endpoint("ollama_base_url") or "http://localhost:11434"
        model = model_override or config.get_model("ollama") or "llama3.2"
        return OllamaOracle(base_url=endpoint, model=model)

    if mode == "gemini":
        key = config.get_key("gemini")
        model = model_override or config.get_model("gemini") or "gemini-2.0-flash"
        return GeminiOracle(api_key=key, model=model)

    if mode == "claude":
        key = config.get_key("claude")
        model = model_override or config.get_model("claude") or "claude-3-5-haiku-20241022"
        return ClaudeOracle(api_key=key, model=model)

    if mode == "openai":
        key = config.get_key("openai")
        model = model_override or config.get_model("openai") or "gpt-4o-mini"
        return OpenAICompatibleOracle(api_key=key, base_url="https://api.openai.com/v1", model=model, provider_name="openai")

    if mode == "deepseek":
        key = config.get_key("deepseek")
        endpoint = config.get_endpoint("deepseek_base_url") or "https://api.deepseek.com"
        model = model_override or config.get_model("deepseek") or "deepseek-chat"
        return OpenAICompatibleOracle(api_key=key, base_url=endpoint, model=model, provider_name="deepseek")

    if mode == "moonshot":
        key = config.get_key("moonshot")
        endpoint = config.get_endpoint("moonshot_base_url") or "https://api.moonshot.ai/v1"
        model = model_override or config.get_model("moonshot") or "kimi-latest"
        return OpenAICompatibleOracle(api_key=key, base_url=endpoint, model=model, provider_name="moonshot")

    if mode == "openrouter":
        key = config.get_key("openrouter")
        model = model_override or config.get_model("openrouter") or "meta-llama/llama-3.3-70b-instruct"
        return OpenAICompatibleOracle(api_key=key, base_url="https://openrouter.ai/api/v1", model=model, provider_name="openrouter")

    if mode == "nanogpt":
        key = config.get_key("nanogpt")
        model = model_override or config.get_model("nanogpt") or "gpt-4o-mini"
        return OpenAICompatibleOracle(api_key=key, base_url="https://nano-gpt.com/api/v1", model=model, provider_name="nanogpt")

    if mode in ("glm", "z.ai", "zhipu"):
        key = config.get_key("glm")
        model = model_override or config.get_model("glm") or "glm-4-flash"
        return OpenAICompatibleOracle(api_key=key, base_url="https://open.bigmodel.cn/api/paas/v4", model=model, provider_name="glm")

    raise ValueError(f"Unknown oracle mode '{mode}'. Choose from: antigravity, gemini, openai, claude, ollama, openrouter, nanogpt, glm")



# Helpers


def make_claim_support_query(
    claim_text: str,
    citation_key: str,
    paper_abstract: str,
    paper_title: str,
) -> AIQuery:
    return AIQuery(
        query_type="CLAIM_SUPPORT",
        citation_key=citation_key,
        claim_text=claim_text,
        instruction=(
            f"Does the paper '{paper_title}' (abstract below) genuinely support "
            f"the following claim from a manuscript?\n\n"
            f"CLAIM: {claim_text}\n\n"
            f"PAPER ABSTRACT:\n{paper_abstract}\n\n"
            f"Classify the support and explain."
        ),
        context={
            "claim": claim_text,
            "paper_title": paper_title,
            "paper_abstract": paper_abstract,
            "citation_key": citation_key,
        },
        expected_format={
            "result": {
                "label": "one of: FULLY_SUPPORTED | PARTIALLY_SUPPORTED | INDIRECT_SUPPORT | BACKGROUND_ONLY | DOES_NOT_SUPPORT | CONTRADICTS",
                "evidence_quote": "short verbatim quote from the abstract",
                "explanation": "your reasoning",
            },
            "confidence": "float 0-1",
            "explanation": "brief rationale",
        },
    )


def make_metadata_conflict_query(
    citation_key: str,
    field_name: str,
    bib_value: str,
    source_values: dict[str, str],
) -> AIQuery:
    return AIQuery(
        query_type="METADATA_CONFLICT",
        citation_key=citation_key,
        instruction=(
            f"Multiple metadata sources disagree on the '{field_name}' field for '{citation_key}'.\n"
            f"BibTeX value: {bib_value}\n"
            f"Source values: {json.dumps(source_values)}\n"
            f"Which is correct? Provide the authoritative value."
        ),
        context={
            "citation_key": citation_key,
            "field": field_name,
            "bib_value": bib_value,
            "source_values": source_values,
        },
        expected_format={
            "result": {
                "correct_value": "authoritative value",
                "winning_source": "most reliable source",
                "explanation": "reasoning",
            },
            "confidence": "float 0-1",
        },
    )


def make_primary_source_query(
    citation_key: str,
    paper_title: str,
    paper_abstract: str,
    claim_context: str,
) -> AIQuery:
    return AIQuery(
        query_type="PRIMARY_SOURCE",
        citation_key=citation_key,
        instruction=(
            f"The citation '{citation_key}' ({paper_title}) appears to be a review/survey paper.\n"
            f"Is the original primary source omitted?\n"
            f"CLAIM CONTEXT: {claim_context}\n"
            f"PAPER ABSTRACT: {paper_abstract}\n"
        ),
        context={
            "citation_key": citation_key,
            "paper_title": paper_title,
            "paper_abstract": paper_abstract,
            "claim_context": claim_context,
        },
        expected_format={
            "result": {
                "is_secondary_citation": "true | false",
                "primary_source_suggestion": "title or description",
                "explanation": "reasoning",
            },
            "confidence": "float 0-1",
        },
    )


def _query_to_dict(q: AIQuery) -> dict:
    return {
        "query_id": q.query_id,
        "query_type": q.query_type,
        "citation_key": q.citation_key,
        "claim_text": q.claim_text,
        "instruction": q.instruction,
        "context": q.context,
        "expected_format": q.expected_format,
        "result": None,
        "confidence": None,
        "explanation": "",
        "verified_by": "ai_oracle_antigravity",
    }


def _build_prompt(q: AIQuery) -> str:
    return (
        f"You are a scientific citation verification assistant.\n\n"
        f"TASK TYPE: {q.query_type}\n\n"
        f"{q.instruction}\n\n"
        f"Respond ONLY with valid JSON matching this schema:\n"
        f"{json.dumps(q.expected_format, indent=2)}\n\n"
        f"Wrap your JSON in ```json ... ``` fences."
    )


def _extract_json(text: str) -> dict:
    import re
    m = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"result": None, "explanation": text}
