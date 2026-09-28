"""
Format-agnostic report content.

Decides *what* a report should say — the verdict, and which tests belong in each
section — independent of how it is drawn. Renderers (text, markdown) consume
these results and are responsible only for presentation, so the selection logic
lives in exactly one place.
"""

import math
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


def known_gaps(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return the xfailed tests — documented incompatibilities — with their reasons.

    These are expected, not regressions, so they're reported separately from
    needs-attention. Each entry carries the test name and its recorded reason.
    """
    gaps = []
    for test in analysis["tests"]:
        if test["outcome"] == "XFAIL":
            gaps.append({"name": test["name"], "reason": test.get("xfail_reason", "")})
    return gaps


def skipped_tests(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return the skipped tests with their reasons.

    A skip is a deliberate "not run here" (e.g. not applicable to this target),
    so — like known gaps — it's worth explaining rather than showing as a bare
    count. Each entry carries the test name and its recorded reason.
    """
    skipped = []
    for test in analysis["tests"]:
        if test["outcome"] == "SKIPPED":
            skipped.append({"name": test["name"], "reason": test.get("skip_reason", "")})
    return skipped


def pass_rate(counts: Dict[str, Any]) -> str:
    """
    Format a node's pass rate over verdict-bearing outcomes.

    Only a genuinely clean node (no failures or errors) may read 100%. When
    something failed, the rate is truncated rather than rounded, so a handful of
    failures diluted by tens of thousands of passes can't round up to a
    misleading 100%.

    Returns a percent string, or "—" when nothing ran.
    """
    passed = counts.get("passed", 0)
    bad = counts.get("failed", 0) + counts.get("error", 0)
    counted = passed + bad
    if counted == 0:
        return "—"
    if bad == 0:
        return "100%"
    # Truncate to 1dp so a near-perfect-but-not-clean node never shows 100%.
    return f"{math.floor(passed / counted * 1000) / 10}%"
