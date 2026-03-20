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


def generate_text_report(analysis: Dict[str, Any], output_path: str):
    """
    Generate a human-readable text report.

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

    if analysis["by_tag"]:
        # Sort tags by pass rate (ascending) to highlight problematic areas
        sorted_tags = sorted(analysis["by_tag"].items(), key=lambda x: x[1]["pass_rate"])

        for tag, stats in sorted_tags:
            lines.append(f"\n{tag}:")
            lines.append(f"  Total:   {stats['total']}")
            lines.append(f"  Passed:  {stats['passed']} ({stats['pass_rate']}%)")
            lines.append(f"  Failed:  {stats['failed']}")
            lines.append(f"  Skipped: {stats['skipped']}")
    else:
        lines.append("No tags found in test results.")

    lines.append("")

    # Failed tests details
    failed_tests = [t for t in analysis["tests"] if t["outcome"] == "FAIL"]
    if failed_tests:
        lines.append("FAILED TESTS")
        lines.append("-" * 80)
        for test in failed_tests:
            lines.append(f"\n{test['name']}")
            lines.append(f"  Tags: {', '.join(test['tags'])}")
            lines.append(f"  Duration: {test['duration']:.2f}s")
            if "error" in test:
                error_preview = test["error"][:200]
                lines.append(f"  Error: {error_preview}...")

    lines.append("")
    lines.append("=" * 80)

    # Write report
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
    print("=" * 60 + "\n")
