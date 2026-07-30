"""
SCVA Master Pipeline Orchestrator.
Coordinates all 18 stages from parsing to final exports.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Optional

from .cache.manager import CacheManager
from .models.report import FinalReport
from .oracle import AIOracle, make_oracle, FileBasedOracle
from .stages import (
    run_stage_01,
    run_stage_02_03,
    run_stage_04_05,
    run_stage_06,
    run_stage_07,
    run_stage_08,
    run_stage_09,
    run_stage_10,
    run_stage_11,
    run_stage_12,
    run_stage_13,
    run_stage_14,
    run_stage_15,
    run_stage_16,
    run_stage_17,
    run_stage_18,
)
from .reports import (
    generate_markdown_report,
    generate_html_report,
    generate_json_export,
    generate_csv_export,
)


class VerificationPipeline:
    """Master pipeline executor for SCVA."""

    def __init__(
        self,
        bib_path: str | Path,
        tex_path: str | Path,
        output_dir: str | Path = "./scva_output",
        oracle_mode: str = "file",
        db_path: Optional[str | Path] = None,
    ) -> None:
        self.bib_path = Path(bib_path)
        self.tex_path = Path(tex_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        db_file = Path(db_path) if db_path else self.output_dir / "scva.db"
        self.cache = CacheManager(db_file)

        self.oracle = make_oracle(oracle_mode, output_dir=self.output_dir)
        self.run_id = f"RUN-{str(uuid.uuid4())[:8]}"

    async def run(self) -> FinalReport:
        """Run all 18 stages of verification."""
        # STAGE 1: Parse Inputs & build CitationGraph
        graph = run_stage_01(self.bib_path, self.tex_path)

        entries_list = list(graph.entries.values())

        # STAGE 2 & 3: Metadata Verification & Multi-Source Validation
        verifications, corrected_map = await run_stage_02_03(
            entries_list, self.cache
        )

        # STAGE 4 & 5: Paper Retrieval & Semantic Understanding
        knowledge_map = await run_stage_04_05(entries_list, self.cache)

        # STAGE 6: Claim Extraction
        claims = run_stage_06(graph)

        # STAGE 7: Claim-to-Citation Verification
        claim_supports = run_stage_07(claims, knowledge_map, self.oracle)

        # STAGE 8: Citation Completeness
        tex_content = self.tex_path.read_text(encoding="utf-8", errors="replace")
        missing_citations = run_stage_08(tex_content)

        # STAGE 9: Overcitation / Density
        density_alerts = run_stage_09(graph)

        # STAGE 10: Primary Source Detection
        primary_alerts = run_stage_10(entries_list)

        # STAGE 11: Version Checking
        version_map = run_stage_11(entries_list, verifications)

        # STAGE 12: Duplicate Detection
        duplicates_map = run_stage_12(entries_list)

        # STAGE 13: Consistency Audit
        consistency = run_stage_13(graph)

        # STAGE 14: PDF Deep Verification
        deep_supports = run_stage_14(claim_supports, knowledge_map)

        # Organize claim supports per entry
        supports_by_key: dict[str, list] = {}
        for cs in deep_supports:
            supports_by_key.setdefault(cs.citation_key, []).append(cs)

        # STAGES 15 & 16: Per-Entry Confidence & Report Compilation
        entry_reports = []
        for entry in entries_list:
            key = entry.key
            meta = verifications[key]
            corr = corrected_map[key]
            pk = knowledge_map.get(key)
            sups = supports_by_key.get(key, [])

            conf = run_stage_15(meta, pk, sups)
            dup = duplicates_map.get(key)
            ver = version_map.get(key)
            is_uncited = key in consistency.get("uncited_entries", [])

            e_report = run_stage_16(
                entry, corr, meta, pk, sups, conf, dup, ver, is_uncited
            )
            entry_reports.append(e_report)

        # STAGE 17: Automatic BibTeX Fix
        corrected_bib_str = run_stage_17(entry_reports)
        bib_out_path = self.output_dir / "references_corrected.bib"
        bib_out_path.write_text(corrected_bib_str, encoding="utf-8")

        # STAGE 18: Integrity Summary Scores
        integrity = run_stage_18(entry_reports, missing_citations, consistency)

        # Flush pending AI queries if FileBasedOracle is used
        pending_queries = 0
        if isinstance(self.oracle, FileBasedOracle):
            self.oracle.flush_queries()
            pending_queries = self.oracle.pending_count()

        final_report = FinalReport(
            entries=entry_reports,
            integrity=integrity,
            ai_queries_pending=pending_queries,
            run_id=self.run_id,
            input_tex=str(self.tex_path),
            input_bib=str(self.bib_path),
        )

        # Export report artifacts
        generate_markdown_report(final_report, self.output_dir / "report.md")
        generate_html_report(final_report, self.output_dir / "report.html")
        generate_json_export(final_report, self.output_dir / "report.json")
        generate_csv_export(final_report, self.output_dir / "report.csv")

        self.cache.close()
        return final_report
