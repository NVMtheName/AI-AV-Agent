"""
AI AV Agent - Enterprise AV/IT Root Cause Analysis System

Expert system for analyzing operational logs from enterprise AV, network,
and IT systems to identify root causes and provide actionable recommendations.
"""

__version__ = "1.0.0"
__author__ = "Enterprise AV Operations Team"

from .agent import AVAgent
from .models import (
    StructuredEvent,
    RootCause,
    RecommendedAction,
    IncidentAnalysis
)

__all__ = [
    "AVAgent",
    "StructuredEvent",
    "RootCause",
    "RecommendedAction",
    "IncidentAnalysis"
]
