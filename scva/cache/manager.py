"""
SQLite-backed cache manager with TTL support.
Tables: metadata_cache, pdf_cache, audit_runs
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional


_DDL = """
CREATE TABLE IF NOT EXISTS metadata_cache (
    cache_key   TEXT PRIMARY KEY,
    source      TEXT,
    data        TEXT,          -- JSON blob
    fetched_at  REAL,
    ttl_seconds REAL
);

CREATE TABLE IF NOT EXISTS pdf_cache (
    doi_or_url  TEXT PRIMARY KEY,
    text        TEXT,
    fetched_at  REAL
);

CREATE TABLE IF NOT EXISTS audit_runs (
    run_id      TEXT PRIMARY KEY,
    bib_path    TEXT,
    tex_path    TEXT,
    started_at  REAL,
    stage       TEXT,
    state       TEXT           -- JSON blob
);
"""


class CacheManager:
    """Thread-safe SQLite cache. Call close() when done."""

    DEFAULT_TTL = 60 * 60 * 24 * 30   # 30 days

    def __init__(self, db_path: Path) -> None:
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.executescript(_DDL)
        self._conn.commit()


    # Metadata cache


    def get_metadata(self, source: str, identifier: str) -> Optional[dict]:
        key = _make_key(source, identifier)
        row = self._conn.execute(
            "SELECT data, fetched_at, ttl_seconds FROM metadata_cache WHERE cache_key=?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        data_json, fetched_at, ttl = row
        if time.time() - fetched_at > ttl:
            self._conn.execute(
                "DELETE FROM metadata_cache WHERE cache_key=?", (key,)
            )
            self._conn.commit()
            return None
        return json.loads(data_json)

    def set_metadata(
        self,
        source: str,
        identifier: str,
        data: dict,
        ttl: float = DEFAULT_TTL,
    ) -> None:
        key = _make_key(source, identifier)
        self._conn.execute(
            """
            INSERT OR REPLACE INTO metadata_cache
            (cache_key, source, data, fetched_at, ttl_seconds)
            VALUES (?, ?, ?, ?, ?)
            """,
            (key, source, json.dumps(data, ensure_ascii=False), time.time(), ttl),
        )
        self._conn.commit()


    # PDF text cache


    def get_pdf_text(self, doi_or_url: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT text FROM pdf_cache WHERE doi_or_url=?", (doi_or_url,)
        ).fetchone()
        return row[0] if row else None

    def set_pdf_text(self, doi_or_url: str, text: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO pdf_cache (doi_or_url, text, fetched_at) VALUES (?,?,?)",
            (doi_or_url, text, time.time()),
        )
        self._conn.commit()


    # Run state (for resume)


    def save_run_state(self, run_id: str, stage: str, state: Any) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO audit_runs
            (run_id, stage, state, started_at)
            VALUES (?, ?, ?, COALESCE(
                (SELECT started_at FROM audit_runs WHERE run_id=?),
                ?
            ))
            """,
            (run_id, stage, json.dumps(state, default=str), run_id, time.time()),
        )
        self._conn.commit()

    def load_run_state(self, run_id: str) -> Optional[tuple[str, Any]]:
        row = self._conn.execute(
            "SELECT stage, state FROM audit_runs WHERE run_id=?", (run_id,)
        ).fetchone()
        if row is None:
            return None
        return row[0], json.loads(row[1])

    def close(self) -> None:
        self._conn.close()


def _make_key(source: str, identifier: str) -> str:
    raw = f"{source}::{identifier}"
    return hashlib.sha256(raw.encode()).hexdigest()
