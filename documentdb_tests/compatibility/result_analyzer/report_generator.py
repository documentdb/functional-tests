"""
Report generation entry point.

Thin dispatch layer: picks a renderer by format name and writes its output.
Selection logic lives in ``report_content``; drawing lives in the ``render_*``
modules, each exposing ``render(analysis) -> str``. ``print_summary`` is
re-exported here for backward compatibility with existing imports.
"""

from typing import Any, Callable, Dict

from . import render_json, render_text
from .render_text import print_summary

__all__ = ["generate_report", "print_summary"]

# Format name -> renderer. Each renderer takes the analysis and returns the
# report body as a string.
_RENDERERS: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "json": render_json.render,
    "text": render_text.render,
}


def generate_report(analysis: Dict[str, Any], output_path: str, format: str = "json"):
    """
    Generate a report from analysis results.

    Args:
        analysis: Analysis results from analyze_results()
        output_path: Path to write the report
        format: Report format (one of ``_RENDERERS``)
    """
    try:
        renderer = _RENDERERS[format]
    except KeyError:
        raise ValueError(f"Unsupported report format: {format}")
    with open(output_path, "w") as f:
        f.write(renderer(analysis))
