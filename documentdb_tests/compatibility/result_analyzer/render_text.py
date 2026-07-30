"""
Plain-text rendering for local/terminal use.

Consumes the format-agnostic report content and shows the same information as the
markdown report - verdict, run breakdown, and what needs attention - as concise
aligned text. Presentation only; the selection logic lives in ``report_content``.
"""

from typing import Any, Dict, List

from .report_content import (
    NEEDS_ATTENTION_CAP,
    VERDICT_PASS,
    cap_items,
    determine_verdict,
    group_needs_attention,
    pass_rate,
)


def _verdict_line(analysis: Dict[str, Any]) -> str:
    verdict, reason = determine_verdict(analysis.get("reconciliation", {}))
    mark = "PASS" if verdict == VERDICT_PASS else "FAIL"
    return f"{mark}{f' - {reason}' if reason else ''}"


def _breakdown_lines(reconciliation: Dict[str, Any]) -> List[str]:
    """The run breakdown: collected decomposed into deselected vs each outcome."""
    r = reconciliation
    rows = [
        ("Collected", r.get("collected", 0)),
        ("  Unsupported", r.get("deselected", 0)),
        ("  Executed", r.get("total", 0)),
        ("    Passed", r.get("passed", 0)),
        ("    Failed", r.get("failed", 0)),
        ("    Errored", r.get("error", 0)),
        ("    Skipped", r.get("skipped", 0)),
        ("    Known gaps", r.get("xfailed", 0)),
    ]
    if r.get("xpassed", 0):
        rows.append(("    Unexpected passes", r.get("xpassed", 0)))
    width = max(len(label) for label, _ in rows)
    lines = [f"{label.ljust(width)}  {count}" for label, count in rows]
    lines.append("")
    lines.append(f"Pass rate: {pass_rate(r)}")
    return lines


def _needs_attention_lines(analysis: Dict[str, Any]) -> List[str]:
    """Failures and errors, grouped by failure type, as a plain list (capped)."""
    grouped = group_needs_attention(analysis)
    if not grouped:
        return []
    total = sum(len(v) for v in grouped.values())
    lines = ["", f"Needs attention ({total}):"]
    for failure_type in sorted(grouped):
        tests = grouped[failure_type]
        lines.append(f"  {failure_type} ({len(tests)}):")
        shown, omitted = cap_items(tests)
        for test in shown:
            lines.append(f"    {test['outcome']}: {test['name']}")
        if omitted:
            lines.append(f"    ... and {omitted} more (cap {NEEDS_ATTENTION_CAP})")
    return lines


def render(analysis: Dict[str, Any]) -> str:
    """Render the plain-text report body."""
    lines = [f"Verdict: {_verdict_line(analysis)}", ""]
    lines.extend(_breakdown_lines(analysis.get("reconciliation", {})))
    lines.extend(_needs_attention_lines(analysis))
    return "\n".join(lines) + "\n"


def print_summary(analysis: Dict[str, Any]):
    """Print the plain-text report to the console."""
    print(render(analysis))
