"""
Markdown rendering for the GitHub step summary.

Consumes the format-agnostic report content and draws it as GitHub-flavored
markdown (headings, tables, and — in later sections — collapsible details).
Presentation only; no selection logic lives here.
"""

from typing import Any, Dict, List

from .report_content import VERDICT_PASS, determine_verdict


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


def render(analysis: Dict[str, Any]) -> str:
    """Render the full markdown report body."""
    lines = [_verdict_heading(analysis), ""]
    lines.extend(_breakdown_lines(analysis.get("reconciliation", {})))
    return "\n".join(lines) + "\n"
