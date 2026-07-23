"""
Format-agnostic report content.

Decides *what* a report should say — which tests belong in each section —
independent of how it is drawn. Renderers (text, markdown) consume these results
and are responsible only for presentation, so the selection logic lives in
exactly one place.
"""

from typing import Any, Dict, List


def group_failures_by_type(analysis: Dict[str, Any]) -> Dict[str, list]:
    """Group failed tests by their failure_type (RESULT_MISMATCH, INFRA_ERROR, ...)."""
    failed_tests = [t for t in analysis["tests"] if t["outcome"] == "FAIL"]
    grouped: Dict[str, list] = {}
    for test in failed_tests:
        ft = test.get("failure_type", "UNKNOWN")
        grouped.setdefault(ft, []).append(test)
    return grouped


def tag_rows(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return per-tag rows sorted worst-pass-rate-first, ready for tabulation."""
    rows = []
    by_tag = analysis.get("by_tag", {})
    for tag, stats in sorted(by_tag.items(), key=lambda x: x[1]["pass_rate"]):
        rows.append(
            {
                "tag": tag,
                "passed": stats["passed"],
                "total": stats["total"],
                "failed": stats["failed"],
                "skipped": stats["skipped"],
                "pass_rate": stats["pass_rate"],
            }
        )
    return rows


def tests_with_outcome(analysis: Dict[str, Any], outcome: str) -> List[Dict[str, Any]]:
    """Return the tests whose categorized outcome matches (e.g. SKIPPED, XPASS)."""
    return [t for t in analysis["tests"] if t["outcome"] == outcome]
