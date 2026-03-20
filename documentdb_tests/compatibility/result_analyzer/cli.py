#!/usr/bin/env python3
"""
DocumentDB Functional Test Results Analyzer - CLI

Command-line interface for analyzing pytest JSON reports and generating
categorized results by feature tags.
"""

import argparse
import sys
from pathlib import Path

from .analyzer import ResultAnalyzer
from .report_generator import generate_report, print_summary


def main():
    parser = argparse.ArgumentParser(
        description="Analyze DocumentDB functional test results and generate reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze default report location
  %(prog)s

  # Analyze specific report
  %(prog)s --input my-results.json

  # Generate text report
  %(prog)s --output report.txt --format text

  # Generate JSON analysis
  %(prog)s --output analysis.json --format json

  # Quiet mode (no console output)
  %(prog)s --output report.txt --quiet
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        default=".test-results/report.json",
        help="Path to pytest JSON report file (default: .test-results/report.json)",
    )

    parser.add_argument(
        "-o", "--output", help="Path to output report file (if not specified, prints to console)"
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: text or json (default: text)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress console output (only write to output file)",
    )

    parser.add_argument(
        "--no-summary", action="store_true", help="Skip printing summary to console"
    )

    args = parser.parse_args()

    # Check if input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        print("\nMake sure to run pytest with --json-report first:", file=sys.stderr)
        print(f"  pytest --json-report --json-report-file={args.input}", file=sys.stderr)
        return 1

    try:
        # Analyze the results
        if not args.quiet:
            print(f"Analyzing test results from: {args.input}")

        analyzer = ResultAnalyzer()
        analysis = analyzer.analyze_results(args.input)

        # Print summary to console (unless quiet or no-summary)
        if not args.quiet and not args.no_summary:
            print_summary(analysis)

        # Generate output file if specified
        if args.output:
            generate_report(analysis, args.output, format=args.format)
            if not args.quiet:
                print(f"\nReport saved to: {args.output}")

        # If no output file and quiet mode, print to stdout
        elif not args.quiet:
            print("\nResults by Tag:")
            print("-" * 60)
            for tag, stats in sorted(
                analysis["by_tag"].items(), key=lambda x: x[1]["pass_rate"], reverse=True
            ):
                passed = stats["passed"]
                total = stats["total"]
                rate = stats["pass_rate"]
                print(f"{tag:30s} | {passed:3d}/{total:3d} passed ({rate:5.1f}%)")

        # Return exit code based on test results
        if analysis["summary"]["failed"] > 0:
            return 1
        return 0

    except Exception as e:
        print(f"Error analyzing results: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
