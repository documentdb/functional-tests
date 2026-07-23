"""
Markdown rendering for the GitHub step summary.

Consumes the format-agnostic report content and draws it as GitHub-flavored
markdown (headings, tables, and — in later sections — collapsible details).
Presentation only; no selection logic lives here.
"""

from typing import Any, Dict, List

from .report_content import (
    NEEDS_ATTENTION_CAP,
    VERDICT_PASS,
    cap_items,
    determine_verdict,
    group_needs_attention,
)


def _verdict_heading(analysis: Dict[str, Any]) -> str:
    verdict, reason = determine_verdict(analysis.get("reconciliation", {}))
    icon = "✅" if verdict == VERDICT_PASS else "❌"
    heading = f"## {icon} {verdict}"
    if reason:
        heading += f" — {reason}"
    return heading


def _breakdown_lines(reconciliation: Dict[str, Any]) -> List[str]:
    """
    The run breakdown table.

    Shows how the run decomposes — collected into deselected vs executed, and
    executed into each outcome — so the pass rate is never read without the
    context that explains it (e.g. an all-error run reads 0 passed, not "0% of a
    real suite").
    """
    r = reconciliation
    passed = r.get("passed", 0)
    failed = r.get("failed", 0)
    errored = r.get("error", 0)
    counted = passed + failed + errored

    lines = ["### Breakdown", ""]
    lines.append("| Outcome | Count |")
    lines.append("|---|--:|")
    lines.append(f"| Collected | {r.get('collected', 0)} |")
    lines.append(f"| \u2003Not applicable (deselected) | {r.get('deselected', 0)} |")
    lines.append(f"| \u2003Executed | {r.get('total', 0)} |")
    lines.append(f"| \u2003\u2003Passed | {passed} |")
    lines.append(f"| \u2003\u2003Failed | {failed} |")
    lines.append(f"| \u2003\u2003Errored | {errored} |")
    lines.append(f"| \u2003\u2003Skipped | {r.get('skipped', 0)} |")
    lines.append(f"| \u2003\u2003Known gaps (xfailed) | {r.get('xfailed', 0)} |")
    if r.get("xpassed", 0):
        lines.append(f"| \u2003\u2003Unexpected passes (xpassed) | {r.get('xpassed', 0)} |")
    lines.append("")
    lines.append(
        f"**Pass rate: {r.get('pass_rate', 0)}%** — {passed} of {counted} passed "
        "(skipped and known gaps excluded)"
    )
    return lines


def _needs_attention_lines(analysis: Dict[str, Any]) -> List[str]:
    """
    The failures and errors a human must act on, grouped by failure type.

    Each test is a collapsible ``<details>`` whose summary is the one-line
    identity and whose body is the real traceback, so the section stays scannable
    while the full detail is one click away. A mass failure is capped so it can't
    bury the report or exceed the step-summary size limit.
    """
    grouped = group_needs_attention(analysis)
    if not grouped:
        return []

    total = sum(len(v) for v in grouped.values())
    lines = ["", f"### Needs attention ({total})", ""]

    for failure_type in sorted(grouped):
        tests = grouped[failure_type]
        lines.append(f"#### {failure_type} ({len(tests)})")
        lines.append("")
        shown, omitted = cap_items(tests)
        for test in shown:
            lines.extend(_failure_details(test))
        if omitted:
            lines.append(f"_… and {omitted} more not shown (cap {NEEDS_ATTENTION_CAP})._")
            lines.append("")
    return lines


def _failure_details(test: Dict[str, Any]) -> List[str]:
    """One collapsible entry: summary line + traceback in a code block."""
    name = test.get("name", "")
    outcome = test.get("outcome", "")
    traceback = test.get("error") or "(no traceback captured)"
    return [
        "<details>",
        f"<summary>{outcome}: <code>{name}</code></summary>",
        "",
        "```",
        traceback.rstrip(),
        "```",
        "</details>",
        "",
    ]


def render(analysis: Dict[str, Any]) -> str:
    """Render the full markdown report body."""
    lines = [_verdict_heading(analysis), ""]
    lines.extend(_breakdown_lines(analysis.get("reconciliation", {})))
    lines.extend(_needs_attention_lines(analysis))
    return "\n".join(lines) + "\n"
