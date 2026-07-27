"""
Markdown rendering for the GitHub step summary.

Consumes the format-agnostic report content and renders it as GitHub-flavored
markdown (headings, tables, and - in later sections - collapsible details).
Presentation only; no selection logic lives here.
"""

from typing import Any, Dict, List

from .report_content import (
    NEEDS_ATTENTION_CAP,
    VERDICT_PASS,
    cap_items,
    determine_verdict,
    group_needs_attention,
    known_gaps,
    pass_rate,
    skipped_tests,
)


def _verdict_heading(analysis: Dict[str, Any]) -> str:
    verdict, reason = determine_verdict(analysis.get("reconciliation", {}))
    icon = "✅" if verdict == VERDICT_PASS else "❌"
    heading = f"## {icon} {verdict}"
    if reason:
        heading += f" - {reason}"
    return heading


def _breakdown_lines(reconciliation: Dict[str, Any]) -> List[str]:
    """
    The run breakdown table.

    Shows how the run decomposes - collected into deselected vs executed, and
    executed into each outcome - so the pass rate is never read without the
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
    lines.append(f"| \u2003Unsupported (deselected) | {r.get('deselected', 0)} |")
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
        f"**Pass rate: {pass_rate(r)}** - {passed} of {counted} passed "
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
            lines.append(f"_... and {omitted} more not shown (cap {NEEDS_ATTENTION_CAP})._")
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


def _known_gaps_lines(analysis: Dict[str, Any]) -> List[str]:
    """
    Documented incompatibilities (xfailed), collapsed by default.

    These are expected gaps, not regressions, so the detail sits behind a
    ``<details>`` - out of the way for the common reader, but available as a
    plain-English catalogue of what doesn't work and why. The section carries its
    own heading so it reads as a peer of needs-attention rather than blending
    into that section's per-failure-type dropdowns.
    """
    gaps = known_gaps(analysis)
    if not gaps:
        return []

    lines = [
        "",
        f"### Known gaps ({len(gaps)})",
        "",
        "<details>",
        "<summary>Show all</summary>",
        "",
    ]
    lines.append("| Test | Reason |")
    lines.append("|---|---|")
    for gap in gaps:
        reason = gap["reason"] or "-"
        lines.append(f"| `{gap['name']}` | {reason} |")
    lines.append("")
    lines.append("</details>")
    return lines


def _skipped_lines(analysis: Dict[str, Any]) -> List[str]:
    """
    Skipped tests with reasons, collapsed by default.

    Explains why tests didn't run (e.g. not applicable to this target), mirroring
    known gaps: its own heading, with the detail behind a ``<details>``.
    """
    skipped = skipped_tests(analysis)
    if not skipped:
        return []

    lines = [
        "",
        f"### Skipped ({len(skipped)})",
        "",
        "<details>",
        "<summary>Show all</summary>",
        "",
    ]
    lines.append("| Test | Reason |")
    lines.append("|---|---|")
    for test in skipped:
        reason = test["reason"] or "-"
        lines.append(f"| `{test['name']}` | {reason} |")
    lines.append("")
    lines.append("</details>")
    return lines


def _feature_status(counts: Dict[str, int]) -> str:
    """
    Status icon for a feature node.

    - red if anything failed or errored
    - blank circle if nothing ran at all (all deselected / not applicable)
    - blank circle if nothing actually *passed* either (only skipped/xfailed) —
      a green check would wrongly imply success where nothing was verified
    - green only when something passed and nothing failed
    """
    if counts.get("failed", 0) or counts.get("error", 0):
        return "❌"
    if counts.get("passed", 0) == 0:
        return "⚪"
    return "✅"


def _feature_summary(counts: Dict[str, int]) -> str:
    """Concise one-line breakdown for a collapsed node: only non-zero buckets."""
    labels = [
        ("passed", "passed"),
        ("failed", "failed"),
        ("error", "errored"),
        ("xfailed", "known gaps"),
        ("skipped", "skipped"),
        ("deselected", "unsupported"),
    ]
    parts = [f"{counts.get(key, 0)} {label}" for key, label in labels if counts.get(key, 0)]
    return ", ".join(parts) if parts else "no tests"


def _unsupported_cell(child: Dict[str, Any], status: str) -> str:
    """
    The Unsupported-count cell, with a ``needs: <caps>`` note only on a not-run (⚪) row.

    A test is unsupported when the target lacks a capability it requires, so it
    was deselected at collection. The note explains which capability was missing.
    On a passing or failing parent that merely contains some unsupported tests the
    note would be noise — the row's real story is its passes/failures — so there
    the cell is just the count.
    """
    count = child["counts"].get("deselected", 0)
    if status != "⚪" or not count:
        return str(count)
    requires = sorted(child.get("requires", []))
    return f"{count} <sub>needs: {', '.join(requires)}</sub>" if requires else str(count)


def _children_table(node: Dict[str, Any]) -> List[str]:
    """
    An aligned table of every direct child of ``node`` — folders and files — with
    each one's totals, so a reader can scan a level's rollups at a glance.

    Folders are marked with a trailing ``/`` (and are also expandable below via
    ``<details>``); files have no slash. This keeps the parent totals visible in
    the table while still distinguishing the two, and folders sort before files
    so they aren't interleaved.

    Every test lands in exactly one column — Passed, Failed, Errored, Known gaps
    (xfailed), Skipped, or Unsupported (deselected because the target lacks a
    required capability) — so each row reconciles with no hidden "missing" tests.
    """
    children = node.get("children", {})
    # Folders first, then files; each group alphabetical.
    folders = [n for n in sorted(children) if children[n].get("children")]
    files = [n for n in sorted(children) if not children[n].get("children")]
    ordered = folders + files
    if not ordered:
        return []

    lines = [
        "| | Feature | Passed | Failed | Errored | Known gaps | Skipped | Unsupported |",
        "|--|--|--:|--:|--:|--:|--:|--:|",
    ]
    for name in ordered:
        child = children[name]
        c = child["counts"]
        status = _feature_status(c)
        # Trailing slash marks a folder (also expandable below); files have none.
        label = f"{name}/" if child.get("children") else name
        lines.append(
            f"| {status} | {label} | "
            f"{c.get('passed', 0)} | {c.get('failed', 0)} | {c.get('error', 0)} | "
            f"{c.get('xfailed', 0)} | {c.get('skipped', 0)} | "
            f"{_unsupported_cell(child, status)} |"
        )
    return lines


def _feature_nodes(node: Dict[str, Any]) -> List[str]:
    """
    Render a node's children table (folders + files with totals), then a
    collapsible ``<details>`` per subfolder to drill in.

    The table shows every child's rollup at this level; folders (marked with a
    trailing ``/``) additionally expand below. The full tree is emitted — passing
    branches included — because it all lives behind collapsed ``<details>``, so
    showing everything costs the reader nothing. Nesting uses ``<ul><li>`` for a
    clear, unshaded indentation boundary.
    """
    children = node.get("children", {})
    lines = _children_table(node)
    if lines:
        lines.append("")

    for name in sorted(children):
        child = children[name]
        if child.get("children"):
            c = child["counts"]
            lines.append("<details>")
            lines.append(
                f"<summary>{_feature_status(c)} <b>{name}/</b> — "
                f"{_feature_summary(c)}</summary>"
            )
            lines.append("<ul><li>")
            lines.append("")
            lines.extend(_feature_nodes(child))
            lines.append("")
            lines.append("</li></ul>")
            lines.append("</details>")
            lines.append("")
    return lines


def _feature_breakdown_lines(analysis: Dict[str, Any]) -> List[str]:
    """
    Per-feature results as a collapsible tree of aligned tables.

    Each level is a table (aligned, scannable); every branch expands into its
    children via ``<details>``, so the whole hierarchy is browsable down to the
    operator level. It's all collapsed by default, and the summary lines carry
    each branch's status so a reader can spot and open the failing paths without
    expanding the green ones.
    """
    tree = analysis.get("by_feature", {})
    if not tree.get("children"):
        return []

    lines = [
        "",
        "### Feature breakdown",
        "",
        "<details>",
        "<summary>Show all</summary>",
        "",
    ]
    lines.extend(_feature_nodes(tree))
    lines.append("</details>")
    return lines


def render(analysis: Dict[str, Any]) -> str:
    """Render the full markdown report body."""
    lines = [_verdict_heading(analysis), ""]
    lines.extend(_breakdown_lines(analysis.get("reconciliation", {})))
    lines.extend(_needs_attention_lines(analysis))
    lines.extend(_known_gaps_lines(analysis))
    lines.extend(_skipped_lines(analysis))
    lines.extend(_feature_breakdown_lines(analysis))
    return "\n".join(lines) + "\n"
