"""
Result Analyzer for DocumentDB Functional Tests.

This module provides tools for analyzing pytest test results and generating
reports categorized by feature tags.
"""

from .analyzer import ResultAnalyzer, categorize_outcome
from .report_generator import generate_report, print_summary

__all__ = [
    "ResultAnalyzer",
    "categorize_outcome",
    "generate_report",
    "print_summary",
]
