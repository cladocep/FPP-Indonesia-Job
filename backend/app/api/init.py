"""
api/__init__.py

API routes initialization
"""

from . import routes_chat
from . import routes_consultation
from . import routes_cv
from . import routes_recommendation

__all__ = [
    "routes_chat",
    "routes_consultation",
    "routes_cv",
    "routes_recommendation"
]