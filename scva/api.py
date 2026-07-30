"""
Public Python API for SCVA.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from .pipeline import VerificationPipeline
from .models.report import FinalReport


def audit(
    bib_path: str | Path,
    tex_path: str | Path,
    output_dir: str | Path = "./scva_output",
    oracle_mode: str = "file",
) -> FinalReport:
    """Synchronous Python entry point to audit a manuscript and bibliography."""
    pipeline = VerificationPipeline(
        bib_path=bib_path,
        tex_path=tex_path,
        output_dir=output_dir,
        oracle_mode=oracle_mode,
    )
    return asyncio.run(pipeline.run())


async def audit_async(
    bib_path: str | Path,
    tex_path: str | Path,
    output_dir: str | Path = "./scva_output",
    oracle_mode: str = "file",
) -> FinalReport:
    """Async Python entry point to audit a manuscript and bibliography."""
    pipeline = VerificationPipeline(
        bib_path=bib_path,
        tex_path=tex_path,
        output_dir=output_dir,
        oracle_mode=oracle_mode,
    )
    return await pipeline.run()
