"""
Report generator for creating human-readable reports from analysis results.

This module provides functions to generate various report formats from
analyzed test results.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict


def generate_report(analysis: Dict[str, Any], output_path: str, format: str = "json"):
    """
    Generate a report from analysis results.

    Args:
        analysis: Analysis results from analyze_results()
        output_path: Path to write the report
        format: Report format ("json" or "text")
    """
    if format == "json":
        generate_json_report(analysis, output_path)
    elif format == "text":
        generate_text_report(analysis, output_path)
    else:
        raise ValueError(f"Unsupported report format: {format}")


def generate_json_report(analysis: Dict[str, Any], output_path: str):
    """
    Generate a JSON report.

    Args:
        analysis: Analysis results from analyze_results()
        output_path: Path to write the JSON report
    """
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": analysis["summary"],
        "by_tag": analysis["by_tag"],
        "tests": analysis["tests"],
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)


def _format_by_tag(analysis: Dict[str, Any]) -> list:
    """Format by-tag results as lines. Shared by both report functions."""
    lines = []
    by_tag = analysis.get("by_tag", {})
    if by_tag:
        sorted_tags = sorted(by_tag.items(), key=lambda x: x[1]["pass_rate"])
        for tag, stats in sorted_tags:
            lines.append(
                {
                    "tag": tag,
                    "passed": stats["passed"],
                    "total": stats["total"],
                    "failed": stats["failed"],
                    "skipped": stats["skipped"],
                    "pass_rate": stats["pass_rate"],
                }
            )
    return lines


def _categorize_failures(analysis: Dict[str, Any]) -> Dict[str, list]:
    """Group failed tests by failure_type. Shared by both report functions."""
    failed_tests = [t for t in analysis["tests"] if t["outcome"] == "FAIL"]
    grouped: Dict[str, list] = {}
    for test in failed_tests:
        ft = test.get("failure_type", "UNKNOWN")
        grouped.setdefault(ft, []).append(test)
    return grouped


def generate_text_report(analysis: Dict[str, Any], output_path: str):
    """
    Generate a detailed human-readable text report to file.

    Args:
        analysis: Analysis results from analyze_results()
        output_path: Path to write the text report
    """
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append("DocumentDB Functional Test Results")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    # Summary
    summary = analysis["summary"]
    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Total Tests:  {summary['total']}")
    lines.append(f"Passed:       {summary['passed']} ({summary['pass_rate']}%)")
    lines.append(f"Failed:       {summary['failed']}")
    lines.append(f"Skipped:      {summary['skipped']}")
    lines.append("")

    # Results by tag
    lines.append("RESULTS BY TAG")
    lines.append("-" * 80)
    tag_data = _format_by_tag(analysis)
    if tag_data:
        for t in tag_data:
            lines.append(f"\n{t['tag']}:")
            lines.append(f"  Total:   {t['total']}")
            lines.append(f"  Passed:  {t['passed']} ({t['pass_rate']}%)")
            lines.append(f"  Failed:  {t['failed']}")
            lines.append(f"  Skipped: {t['skipped']}")
    else:
        lines.append("No tags found in test results.")
    lines.append("")

    # Failed tests details
    grouped = _categorize_failures(analysis)
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

    # Skipped tests
    skipped_tests = [t for t in analysis["tests"] if t["outcome"] == "SKIPPED"]
    if skipped_tests:
        lines.append("")
        lines.append("SKIPPED TESTS")
        lines.append("-" * 80)
        for test in skipped_tests:
            lines.append(f"  {test['name']}")

    lines.append("")
    lines.append("=" * 80)

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def print_summary(analysis: Dict[str, Any]):
    """
    Print a brief summary to console.

    Args:
        analysis: Analysis results from analyze_results()
    """
    summary = analysis["summary"]
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Total:   {summary['total']}")
    print(f"Passed:  {summary['passed']} ({summary['pass_rate']}%)")
    print(f"Failed:  {summary['failed']}")
    print(f"Skipped: {summary['skipped']}")
    print("=" * 60)

    # Failed test counts by type
    grouped = _categorize_failures(analysis)
    if grouped:
        total = sum(len(v) for v in grouped.values())
        print(f"\nFailed Tests ({total}):")
        print("-" * 60)
        for ft in sorted(grouped):
            print(f"  {ft}: {len(grouped[ft])}")

    print("=" * 60 + "\n")
