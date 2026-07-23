"""
Format-agnostic report content.

Decides *what* a report should say — the verdict, and which tests belong in each
section — independent of how it is drawn. Renderers (text, markdown) consume
these results and are responsible only for presentation, so the selection logic
lives in exactly one place.
"""

from typing import Any, Dict, List, Tuple

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"


def determine_verdict(reconciliation: Dict[str, Any]) -> Tuple[str, str]:
    """
    Decide the binary run verdict and a one-line reason.

    Anything that isn't a clean, meaningful, all-passing run is a FAIL; the
    breakdown section carries the detail. The checks run in priority order so
    the most serious explanation wins:

    1. A raw ``xpassed`` means ``xfail_strict`` wasn't applied, so the run's
       results can't be trusted — flag it as invalid.
    2. No test reached a verdict (all deselected/skipped) — a run with nothing to
       show for it is treated as a failure, not a silent pass.
    3. Any failure or error.
    Otherwise PASS.

    Args:
        reconciliation: The reconciliation counts from the analysis.

    Returns:
        A ``(verdict, reason)`` pair; ``reason`` is empty on PASS.
    """
    executed = (
        reconciliation.get("passed", 0)
        + reconciliation.get("failed", 0)
        + reconciliation.get("error", 0)
    )

    if reconciliation.get("xpassed", 0) > 0:
        return VERDICT_FAIL, "results may be invalid — strict xfail not applied"
    if executed == 0:
        return VERDICT_FAIL, "no tests ran"
    if reconciliation.get("failed", 0) or reconciliation.get("error", 0):
        return VERDICT_FAIL, "tests failed"
    return VERDICT_PASS, ""


def group_failures_by_type(analysis: Dict[str, Any]) -> Dict[str, list]:
    """Group failed tests by their failure_type (RESULT_MISMATCH, INFRA_ERROR, ...)."""
    failed_tests = [t for t in analysis["tests"] if t["outcome"] == "FAIL"]
    grouped: Dict[str, list] = {}
    for test in failed_tests:
        ft = test.get("failure_type", "UNKNOWN")
        grouped.setdefault(ft, []).append(test)
    return grouped


# Above this many needs-attention items, the report lists a capped sample rather
# than every traceback. A mass failure would otherwise bury the summary and blow
# past the step-summary size limit.
NEEDS_ATTENTION_CAP = 25


def needs_attention(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return the tests a human must act on: failures and errors.

    A FAIL reached a verdict and was wrong; an ERROR never reached one (a crash,
    usually in a fixture). Both need attention, so they're surfaced together —
    each still tagged with its outcome so a renderer can distinguish them.
    """
    return [t for t in analysis["tests"] if t["outcome"] in ("FAIL", "ERROR")]


def group_needs_attention(analysis: Dict[str, Any]) -> Dict[str, list]:
    """Group needs-attention tests by failure_type, for sectioned display."""
    grouped: Dict[str, list] = {}
    for test in needs_attention(analysis):
        ft = test.get("failure_type", "UNKNOWN")
        grouped.setdefault(ft, []).append(test)
    return grouped


def cap_items(items: List[Any], cap: int = NEEDS_ATTENTION_CAP) -> Tuple[List[Any], int]:
    """
    Trim a list to at most ``cap`` items.

    Returns the kept items and the number omitted, so a renderer can show
    "N more not shown" instead of an overwhelming wall of tracebacks.
    """
    if len(items) <= cap:
        return items, 0
    return items[:cap], len(items) - cap


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
