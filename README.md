# Scientific Citation Verification Agent (SCVA)

[![PyPI Version](https://img.shields.io/pypi/v/scva.svg)](https://pypi.org/project/scva/)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**SCVA** is an 18-stage citation verification agent for pre-submission academic paper auditing. It functions like an independent scientific editor, catching bibliographic errors, missing DOIs, incorrect author order, venue mismatches, and semantic claim-to-citation discrepancies before submitting to top venues (AAAI, NeurIPS, ICML, ICLR, CVPR, Nature, Science, etc.).

---

## 🌟 Key Features

- **🔍 Multi-Source Metadata Consensus:** Cross-verifies references against Crossref, DBLP, OpenAlex, Semantic Scholar, and arXiv.
- **🧠 Multi-Provider AI Oracle:** Supports DeepSeek, Moonshot AI (Kimi), Google Gemini, OpenAI, Anthropic Claude, OpenRouter, NanoGPT, Zhipu GLM, and Local LLMs (Ollama).
- **🤖 IDE Agent Integration:** Works seamlessly with IDE AI assistants (e.g. Antigravity) via zero-config `ai_queries.json` / `ai_responses.json` file protocol.
- **📊 Claim-to-Citation Audit:** Verifies if cited papers genuinely support manuscript assertions (`FULLY_SUPPORTED`, `CONTRADICTS`, etc.).
- **✍️ Automatic BibTeX Repair:** Generates clean, corrected, publication-ready `.bib` files.
- **📈 Multi-Format Exports:** Produces Markdown reports, interactive HTML dashboards, JSON, CSV, and corrected BibTeX.

---

## 🤖 Equipping Antigravity AI Agent with SCVA Skill

To give your **Antigravity AI Agent** (or any compatible LLM pair-programming agent) the ability to automatically run SCVA citation audits:

1. **Install SCVA:**
   ```bash
   pip install scva
   ```

2. **Add `SKILL.md` to your Project or Agent Configuration:**
   Copy the [`SKILL.md`](SKILL.md) file included in this repository to:
   - **Workspace Level:** `.agents/skills/scva-citation-audit/SKILL.md`
   - **Global Level:** `~/.gemini/config/skills/scva-citation-audit/SKILL.md`

3. **Ask your agent:**
   > *"Audit my paper's bibliography `references.bib` and manuscript `paper.tex`."*

   Your agent will automatically execute SCVA, perform in-IDE semantic claim evaluations via the AI Oracle protocol, and deliver publication-ready corrected `.bib` files and visual dashboards.

---

## 🏗️ 18-Stage Verification Architecture

```
                  ┌──────────────────────────────────────────────────┐
                  │              INPUTS (.tex, .bib)                 │
                  └────────────────────────┬─────────────────────────┘
                                           │
 ┌─────────────────────────────────────────▼────────────────────────────────────────┐
 │                              18-STAGE PIPELINE                                   │
 ├──────────────────────────────────────────────────────────────────────────────────┤
 │ S01: Parse Inputs & Citation Graph       S10: Primary Source Detection           │
 │ S02: Metadata Verification               S11: Version Checking (arXiv vs Published)│
 │ S03: Multi-Source Validation             S12: Duplicate Detection                │
 │ S04: Paper Retrieval (PDF / Abstract)    S13: Consistency Audit                  │
 │ S05: Semantic Understanding              S14: PDF Deep Evidence Search           │
 │ S06: Claim Extraction                    S15: Confidence Scoring                 │
 │ S07: Claim-to-Citation Verification      S16: Per-Entry Report Generation        │
 │ S08: Citation Completeness               S17: Automatic BibTeX Fixer             │
 │ S09: Over/Under-Citation Density         S18: Scientific Integrity Quality Score │
 └────────────────────────┬────────────────────────────────┬────────────────────────┘
                          │                                │
        ┌─────────────────▼─────────────────┐   ┌──────────▼──────────┐
        │       MULTI-SOURCE APIS           │   │  MULTI-PROVIDER LLM │
        │ Crossref | DBLP | OpenAlex        │   │ DeepSeek | Moonshot │
        │ Semantic Scholar | arXiv          │   │ Gemini | OpenAI ... │
        └───────────────────────────────────┘   └─────────────────────┘
                                           │
 ┌─────────────────────────────────────────▼────────────────────────────────────────┐
 │                               OUTPUT ARTIFACTS                                   │
 │ report.md (Markdown) | report.html (Dashboard) | report.json | report.csv       │
 │ references_corrected.bib (Auto-fixed BibTeX) | scva.db (SQLite Cache)            │
 └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation

Install SCVA directly from PyPI via `pip`:

```bash
pip install scva
```

Or install from GitHub source:

```bash
git clone https://github.com/satwik26-04/scva.git
cd scva
pip install -e .
```

---

## 🚀 Quick Start CLI

### 1. Run Full Audit

```bash
scva audit references.bib manuscript.tex --output-dir ./scva_output
```

### 2. Configure API Keys & Preferred Providers

SCVA includes a secure config manager storing encrypted/masked keys in `~/.scva/config.json`:

```bash
# Set API keys securely
scva config set-key deepseek YOUR_DEEPSEEK_API_KEY
scva config set-key moonshot YOUR_MOONSHOT_API_KEY
scva config set-key gemini YOUR_GEMINI_API_KEY
scva config set-key openai YOUR_OPENAI_API_KEY
scva config set-key claude YOUR_CLAUDE_API_KEY

# Set default oracle provider & models
scva config set-default-oracle deepseek
scva config set-model deepseek deepseek-reasoner
scva config set-model ollama llama3.2

# Show configuration (keys are automatically masked)
scva config show
```

### 3. Run Standalone Audit with Specific LLM Backend

```bash
# Run with DeepSeek
scva audit references.bib manuscript.tex -m deepseek

# Run with Moonshot AI (Kimi)
scva audit references.bib manuscript.tex -m moonshot --model kimi-latest

# Run with Local Ollama
scva audit references.bib manuscript.tex -m ollama --model llama3.2
```

---

## 💻 Python API Usage

```python
from scva.api import audit

report = audit(
    bib_path="references.bib",
    tex_path="manuscript.tex",
    output_dir="./scva_output",
    oracle_mode="antigravity",
)

print(f"Publication Readiness Score: {report.integrity.publication_readiness_score * 100:.1f}%")
print(f"Bibliography Quality Score: {report.integrity.bibliography_quality_score * 100:.1f}%")
```

---

## 🤖 Supported LLM Oracle Providers

| Provider | Oracle Flag (`-m`) | Base Endpoint / API | Default Model |
|---|---|---|---|
| **Antigravity (IDE Agent)** | `-m antigravity` | In-IDE `ai_queries.json` / `ai_responses.json` | N/A |
| **DeepSeek** | `-m deepseek` | `https://api.deepseek.com` | `deepseek-chat` / `deepseek-reasoner` |
| **Moonshot AI (Kimi)** | `-m moonshot` | `https://api.moonshot.ai/v1` | `kimi-latest` |
| **Google Gemini API** | `-m gemini` | REST `generativelanguage.googleapis.com` | `gemini-2.0-flash` |
| **OpenAI API** | `-m openai` | REST `api.openai.com/v1` | `gpt-4o-mini` |
| **Anthropic Claude API** | `-m claude` | REST `api.anthropic.com/v1` | `claude-3-5-haiku-20241022` |
| **Local LLMs (Ollama)** | `-m ollama` | `http://localhost:11434` | `llama3.2` |
| **OpenRouter** | `-m openrouter` | REST `openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct` |
| **NanoGPT** | `-m nanogpt` | REST `nano-gpt.com/api/v1` | `gpt-4o-mini` |
| **Zhipu GLM / Z.ai** | `-m glm` | REST `open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |

---

## 📄 Output Reports

When an audit completes, SCVA outputs:

1. **`report.md`**: Detailed Markdown report per citation with metadata comparisons and claim support quotes.
2. **`report.html`**: Interactive dark-themed web dashboard.
3. **`references_corrected.bib`**: Auto-repaired, publication-ready BibTeX file.
4. **`report.json` & `report.csv`**: Machine-readable structured exports.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
