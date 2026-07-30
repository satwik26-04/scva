"""sources package"""
from .base import MetadataSource, SourceRecord
from .crossref import CrossrefSource
from .dblp import DBLPSource
from .openalex import OpenAlexSource
from .semantic_scholar import SemanticScholarSource
from .arxiv_source import ArXivSource
from .consensus import ConsensusEngine

__all__ = [
    "MetadataSource", "SourceRecord",
    "CrossrefSource", "DBLPSource", "OpenAlexSource",
    "SemanticScholarSource", "ArXivSource", "ConsensusEngine",
]
