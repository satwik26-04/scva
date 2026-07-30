"""
SCVA — Scientific Citation Verification Agent
"""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("scva")
except PackageNotFoundError:
    __version__ = "1.0.0-dev"

__all__ = ["__version__"]
