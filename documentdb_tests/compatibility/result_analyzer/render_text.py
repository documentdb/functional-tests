"""
Plain-text rendering for local/terminal use.

Consumes the format-agnostic report content and draws it as aligned monospace
text, which reads better in a terminal than raw markdown. Presentation only.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from .report_content import group_failures_by_type, tag_rows, tests_with_outcome


def _xpass_warning_lines(xpassed_tests: List[Dict[str, Any]], indent: str) -> List[str]:
    """Shared strict-xpass alarm text (a raw XPASS means pytest.ini wasn't applied)."""
    lines = [
        f"⚠ ERROR: {len(xpassed_tests)} test(s) unexpectedly passed (XPASS).",
        "  With xfail_strict=true, these should appear as failures instead.",
        "  If you see this, the test run may not have used pytest.ini.",
    ]
    return lines + [f"{indent}{t['name']}" for t in xpassed_tests]


def render(analysis: Dict[str, Any]) -> str:
    """Render the full plain-text report body."""
    lines: List[str] = []

    lines.append("=" * 80)
    lines.append("DocumentDB Functional Test Results")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    summary = analysis["summary"]
    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Total Tests:  {summary['total']}")
    lines.append(f"Passed:       {summary['passed']} ({summary['pass_rate']}%)")
    lines.append(f"Failed:       {summary['failed']}")
    lines.append(f"Skipped:      {summary['skipped']}")
    lines.append(f"XFailed:      {summary['xfailed']}")
    lines.append(f"XPassed:      {summary['xpassed']}")
    lines.append("")

    lines.append("RESULTS BY TAG")
    lines.append("-" * 80)
    rows = tag_rows(analysis)
    if rows:
        for t in rows:
            lines.append(f"\n{t['tag']}:")
            lines.append(f"  Total:   {t['total']}")
            lines.append(f"  Passed:  {t['passed']} ({t['pass_rate']}%)")
            lines.append(f"  Failed:  {t['failed']}")
            lines.append(f"  Skipped: {t['skipped']}")
    else:
        lines.append("No tags found in test results.")
    lines.append("")

    grouped = group_failures_by_type(analysis)
    if grouped:
        lines.append("FAILED TESTS")
        lines.append("-" * 80)
        for ft in sorted(grouped):
            lines.append(f"\n  {ft} ({len(grouped[ft])}):")
            for test in grouped[ft]:
                lines.append(f"\n    {test['name']}")
                lines.append(f"      Tags: {', '.join(test['tags'])}")
                lines.append(f"      Duration: {test['duration']:.2f}s")
                if "error" in test:
                    lines.append(f"      Error: {test['error'][:200]}...")

    skipped_tests = tests_with_outcome(analysis, "SKIPPED")
    if skipped_tests:
        lines.append("")
        lines.append("SKIPPED TESTS")
        lines.append("-" * 80)
        for test in skipped_tests:
            lines.append(f"  {test['name']}")

    xpassed_tests = tests_with_outcome(analysis, "XPASS")
    if xpassed_tests:
        lines.append("")
        lines.extend(_xpass_warning_lines(xpassed_tests, "    "))

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines) + "\n"


def print_summary(analysis: Dict[str, Any]):
    """Print a brief summary to the console."""
    summary = analysis["summary"]
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Total:   {summary['total']}")
    print(f"Passed:  {summary['passed']} ({summary['pass_rate']}%)")
    print(f"Failed:  {summary['failed']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"XFailed: {summary['xfailed']}")
    print(f"XPassed: {summary['xpassed']}")
    print("=" * 60)

    grouped = group_failures_by_type(analysis)
    if grouped:
        total = sum(len(v) for v in grouped.values())
        print(f"\nFailed Tests ({total}):")
        print("-" * 60)
        for ft in sorted(grouped):
            print(f"  {ft}: {len(grouped[ft])}")

    if summary["xpassed"] > 0:
        xpassed_tests = tests_with_outcome(analysis, "XPASS")
        print()
        for line in _xpass_warning_lines(xpassed_tests, "    "):
            print(line)

    print("=" * 60 + "\n")
