"""
Secure Configuration & API Key Manager for SCVA.
Stores keys and provider settings securely in ~/.scva/config.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


CONFIG_DIR = Path.home() / ".scva"
CONFIG_FILE = CONFIG_DIR / "config.json"


DEFAULT_CONFIG: dict[str, Any] = {
    "default_oracle": "antigravity",
    "default_models": {
        "gemini": "gemini-2.0-flash",
        "openai": "gpt-4o-mini",
        "claude": "claude-3-5-haiku-20241022",
        "deepseek": "deepseek-chat",
        "moonshot": "kimi-latest",
        "ollama": "llama3.2",
        "openrouter": "meta-llama/llama-3.3-70b-instruct",
        "nanogpt": "gpt-4o-mini",
        "glm": "glm-4-flash",
        "custom": "default",
    },
    "api_keys": {
        "gemini": "",
        "openai": "",
        "claude": "",
        "deepseek": "",
        "moonshot": "",
        "openrouter": "",
        "nanogpt": "",
        "glm": "",
        "custom": "",
        # Citation Services
        "semantic_scholar": "",
        "crossref_mailto": "scva-polite@research-community.org",
        "openalex": "",
    },
    "custom_endpoints": {
        "ollama_base_url": "http://localhost:11434",
        "deepseek_base_url": "https://api.deepseek.com",
        "moonshot_base_url": "https://api.moonshot.ai/v1",
        "custom_openai_base_url": "https://api.openai.com/v1",
    },
}


class ConfigManager:
    """Manages persistent config and API keys securely."""

    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._config = self._load()

    def _load(self) -> dict[str, Any]:
        if not CONFIG_FILE.exists():
            self._save_file(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            for k in ("default_models", "api_keys", "custom_endpoints"):
                if k in data:
                    merged[k] = {**DEFAULT_CONFIG[k], **data[k]}
            return merged
        except Exception:
            return DEFAULT_CONFIG.copy()

    def _save_file(self, data: dict[str, Any]) -> None:
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except Exception:
            pass

    def save(self) -> None:
        self._save_file(self._config)

    def set_key(self, provider: str, key: str) -> None:
        provider = provider.lower()
        self._config["api_keys"][provider] = key.strip()
        self.save()

    def get_key(self, provider: str) -> str:
        provider = provider.lower()
        env_map = {
            "gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "moonshot": "MOONSHOT_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "semantic_scholar": "SEMANTIC_SCHOLAR_API_KEY",
            "glm": "ZHIPU_API_KEY",
        }
        env_var = env_map.get(provider)
        if env_var and os.environ.get(env_var):
            return os.environ[env_var]
        return self._config["api_keys"].get(provider, "")

    def set_default_oracle(self, oracle: str) -> None:
        self._config["default_oracle"] = oracle.lower()
        self.save()

    def get_default_oracle(self) -> str:
        return self._config.get("default_oracle", "antigravity")

    def set_model(self, provider: str, model: str) -> None:
        self._config["default_models"][provider.lower()] = model.strip()
        self.save()

    def get_model(self, provider: str) -> str:
        provider = provider.lower()
        return self._config["default_models"].get(provider, "")

    def get_endpoint(self, key: str) -> str:
        return self._config["custom_endpoints"].get(key, "")

    def set_endpoint(self, key: str, value: str) -> None:
        self._config["custom_endpoints"][key] = value.strip()
        self.save()

    def show(self) -> dict[str, Any]:
        safe = json.loads(json.dumps(self._config))
        for k, v in safe["api_keys"].items():
            if v:
                safe["api_keys"][k] = v[:4] + "••••••••" + v[-2:] if len(v) > 8 else "••••••••"
        return safe
