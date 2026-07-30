---
name: scva-citation-audit
description: Run comprehensive 18-stage Scientific Citation Verification Agent (SCVA) audit on BibTeX (.bib) and LaTeX (.tex) files to detect bibliographic metadata errors, claim-to-citation mismatches, secondary citations, duplicate entries, and version updates before conference submission.
---

# Scientific Citation Verification Agent (SCVA) Agent Skill

This skill enables AI assistants (such as Antigravity) to perform automated, multi-source, production-grade citation and bibliography auditing using the `scva` CLI and Python package.

---

## Installation & Setup

1. **Install SCVA:**
   ```bash
   pip install scva
   ```

2. **Add Skill to your Agent Configuration:**
   Copy this `SKILL.md` file into your local agent skills root:
   - **Workspace Scope:** `<your-project-root>/.agents/skills/scva-citation-audit/SKILL.md`
   - **Global Scope:** `~/.gemini/config/skills/scva-citation-audit/SKILL.md`

---

## Protocol for AI Assistant Execution

When the user asks you to audit a bibliography (`.bib`), check citations in a manuscript (`.tex`), or prepare references for paper submission (AAAI, NeurIPS, ICML, ICLR, CVPR, Nature, Science, etc.):

### Step 1: Run the SCVA Audit
Execute the `scva audit` command:

```bash
scva audit "<path/to/references.bib>" "<path/to/manuscript.tex>" --output-dir "<path/to/output_dir>"
```

### Step 2: AI Oracle Loop (In-IDE Intelligence Delegation)
If pending queries are reported (`ai_queries.json` exists in `<output_dir>`):

1. **Read `ai_queries.json`:**
   Inspect `<output_dir>/ai_queries.json`.

2. **Evaluate Queries:**
   - **`CLAIM_SUPPORT` queries:** Evaluate if the paper's title/abstract supports the claim text.
   - **`PRIMARY_SOURCE` queries:** Determine if a survey/review paper is cited in place of the primary work.
   - **`METADATA_CONFLICT` queries:** Determine authoritative values when metadata APIs disagree.

3. **Write `ai_responses.json`:**
   Create `<output_dir>/ai_responses.json` matching this schema:
   ```json
   {
     "responses": [
       {
         "query_id": "<query_id>",
         "result": {
           "label": "FULLY_SUPPORTED",
           "evidence_quote": "<verbatim quote from abstract>",
           "explanation": "<reasoning>"
         },
         "confidence": 0.95,
         "explanation": "Evaluated by AI Oracle",
         "verified_by": "ai_oracle_antigravity"
       }
     ]
   }
   ```

4. **Ingest Responses:**
   Run response ingestion:
   ```bash
   scva ingest-response "<output_dir>/ai_responses.json" --output-dir "<output_dir>"
   ```

5. **Finalize Audit Reports:**
   Re-run `scva audit` to update all final reports with 100% verified intelligence entries.

---

## Generated Output Artifacts

- `report.md` — Comprehensive Markdown verification report
- `report.html` — Interactive HTML dashboard
- `references_corrected.bib` — Publication-ready auto-fixed BibTeX file
- `report.json` & `report.csv` — Machine-readable & spreadsheet exports
