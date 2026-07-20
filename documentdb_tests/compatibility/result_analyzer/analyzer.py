"""
Result analyzer for parsing and categorizing test results.

This module provides functions to analyze pytest JSON output and categorize
test results by tags and failure types.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

# Module-level constants
from documentdb_tests.framework.infra_exceptions import INFRA_EXCEPTION_NAMES as INFRA_EXCEPTIONS

# Mapping from TestOutcome to counter key names
OUTCOME_TO_KEY = {
    "PASS": "passed",
    "FAIL": "failed",
    "SKIPPED": "skipped",
    "XFAIL": "xfailed",
    "XPASS": "xpassed",
}


class TestOutcome:
    """Enumeration of test outcomes."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    XFAIL = "XFAIL"
    XPASS = "XPASS"


def categorize_outcome(test_result: Dict[str, Any]) -> str:
    """
    Categorize a test outcome based on test result information.

    Maps pytest outcomes to simple categories:
    - PASS: Test passed
    - FAIL: Test failed (for any reason)
    - SKIPPED: Test skipped
    - XFAIL: Test expected to fail and did fail
    - XPASS: Test expected to fail but passed

    Args:
        test_result: Test result dictionary from pytest JSON report

    Returns:
        One of: PASS, FAIL, SKIPPED, XFAIL, XPASS
    """
    outcome = test_result.get("outcome", "")

    if outcome == "passed":
        return TestOutcome.PASS
    elif outcome == "skipped":
        return TestOutcome.SKIPPED
    elif outcome == "xfailed":
        return TestOutcome.XFAIL
    elif outcome == "xpassed":
        return TestOutcome.XPASS
    else:
        return TestOutcome.FAIL


def extract_exception_type(crash_message: str) -> str:
    """
    Extract exception type from pytest crash message.

    Args:
        crash_message: Message like "module.Exception: error details"

    Returns:
        Full exception type (e.g., "pymongo.errors.OperationFailure")
        or empty string if not found
    """
    # Match pattern: "module.exception.Type: message"
    # Capture everything before the first colon
    match = re.match(r"^([a-zA-Z0-9_.]+):\s", crash_message)
    if match:
        return match.group(1)

    return ""


# Phases pytest reports for a test, in execution order. A test can fail in any of
# them: a fixture crash surfaces in ``setup``, an assertion in ``call``, a
# fixture-teardown error in ``teardown``.
_PHASES = ("call", "setup", "teardown")


def _failing_phase_info(test_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return the phase dict that carries the failure, preferring ``call``.

    A normal test failure lives in ``call``, but an errored test has no ``call``
    phase at all — its crash/longrepr is under ``setup`` (or ``teardown``).
    Reading only ``call`` would miss those entirely, so fall back across phases.
    """
    # Prefer an explicitly failed phase; otherwise the first phase present.
    for phase in _PHASES:
        info = test_result.get(phase)
        if isinstance(info, dict) and info.get("outcome") == "failed":
            return info
    for phase in _PHASES:
        info = test_result.get(phase)
        if isinstance(info, dict):
            return info
    return {}


def extract_failure_tag(test_result: Dict[str, Any]) -> str:
    """
    Extract a failure tag (e.g. RESULT_MISMATCH) from an assertion message.

    Framework assertions prefix errors with a bracketed tag; this returns the
    first one found, whatever it is, so new tags need no change here.

    Args:
        test_result: Full test result dict from pytest JSON

    Returns:
        Tag string without brackets, or empty string if not found
    """
    phase_info = _failing_phase_info(test_result)
    crash_info = phase_info.get("crash", {})
    crash_message = crash_info.get("message", "")

    # Detect strict XPASS from longrepr
    longrepr = phase_info.get("longrepr", "")
    if isinstance(longrepr, str) and longrepr.startswith("[XPASS(strict)]"):
        return "XPASS_STRICT"

    match = re.search(r"\[([A-Z_]+)\]", crash_message)
    if match:
        return match.group(1)
    return ""


def is_infrastructure_error(test_result: Dict[str, Any]) -> bool:
    """
    Check if error is infrastructure-related based on exception type.

    This checks the actual exception type rather than keywords in error messages,
    preventing false positives from error messages that happen to contain
    infrastructure-related words (e.g., "host" in an assertion message).

    Args:
        test_result: Full test result dict from pytest JSON

    Returns:
        True if error is infrastructure-related, False otherwise
    """
    # Get the crash info from the failing phase (setup for errored tests)
    phase_info = _failing_phase_info(test_result)
    crash_info = phase_info.get("crash", {})
    crash_message = crash_info.get("message", "")

    if not crash_message:
        return False

    # Extract exception type from "module.ExceptionClass: message" format
    exception_type = extract_exception_type(crash_message)

    if not exception_type:
        return False

    # Check against module-level constant
    return exception_type in INFRA_EXCEPTIONS


# Every outcome count we report. pytest-json-report includes a key only when its
# count is non-zero (an all-pass run has no "failed"/"error"/"skipped" key), so
# we list the full set here and fill any the run omitted with zero.
_OUTCOME_COUNT_KEYS = (
    "collected",
    "deselected",
    "total",
    "passed",
    "failed",
    "error",
    "skipped",
    "xfailed",
    "xpassed",
)


def _counts_with_missing_as_zero(native_summary: Dict[str, Any]) -> Dict[str, int]:
    """
    Return every outcome count, treating a key the run omitted as zero.

    pytest reports only the outcomes that occurred, so a missing count genuinely
    means zero. Filling them in lets the rest of the code read each count
    directly instead of guarding every access.
    """
    return {key: native_summary.get(key, 0) for key in _OUTCOME_COUNT_KEYS}


def build_reconciliation(native_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build reconciliation figures from pytest-json-report's native summary.

    The native summary already decomposes a run honestly:
    ``collected = deselected + total`` and
    ``total = passed + failed + skipped + xfailed + error`` (there is no
    ``xpassed`` key under ``xfail_strict`` — an unexpected pass is a ``failed``).
    We surface those counts plus a pass rate whose denominator is only the tests
    that reached a verdict and could have passed: ``passed + failed + error``.
    Skipped and xfailed are excluded — a skip never ran and an xfail is a known,
    expected gap — so neither should move the rate.

    Args:
        native_summary: The ``summary`` block from the pytest JSON report.

    Returns:
        Dict of reconciliation counts plus ``pass_rate`` (percent, rounded).
    """
    counts = _counts_with_missing_as_zero(native_summary)

    # Only verdict-bearing outcomes count toward the rate; a run with any error
    # therefore cannot read 100%.
    denominator = counts["passed"] + counts["failed"] + counts["error"]
    pass_rate = (counts["passed"] / denominator * 100) if denominator > 0 else 0.0
    return {**counts, "pass_rate": round(pass_rate, 2)}


def load_registered_markers(pytest_ini_path: str = "pytest.ini") -> set:
    """
    Load registered markers from pytest.ini.

    Parses the markers section to extract marker names, ensuring we only
    use markers that are explicitly registered in pytest configuration.

    Args:
        pytest_ini_path: Path to pytest.ini file (defaults to "pytest.ini")

    Returns:
        Set of registered marker names
    """
    # Check if pytest.ini exists
    if not Path(pytest_ini_path).exists():
        return set()

    registered_markers = set()

    try:
        with open(pytest_ini_path, "r") as f:
            in_markers_section = False

            for line in f:
                # Check if we're entering the markers section
                if line.strip() == "markers =":
                    in_markers_section = True
                    continue

                if in_markers_section:
                    # Marker lines are indented, config keys are not
                    if line and not line[0].isspace():
                        # Non-indented line means we left the markers section
                        break

                    # Parse indented marker lines like "    find: Find operation tests"
                    match = re.match(r"^\s+([a-zA-Z0-9_]+):", line)
                    if match:
                        registered_markers.add(match.group(1))

    except Exception:
        # If parsing fails, return empty set
        pass

    return registered_markers


class ResultAnalyzer:
    """
    Analyzer for pytest JSON test results.

    This class provides stateful analysis with configurable pytest.ini path,
    making it easier to test and use in multiple contexts.

    Args:
        pytest_ini_path: Path to pytest.ini file for marker configuration

    Example:
        analyzer = ResultAnalyzer("pytest.ini")
        results = analyzer.analyze_results("report.json")
    """

    _DEFAULT_PYTEST_INI = str(Path(__file__).resolve().parent.parent.parent / "pytest.ini")

    def __init__(self, pytest_ini_path: str = _DEFAULT_PYTEST_INI):
        """
        Initialize the result analyzer.

        Args:
            pytest_ini_path: Path to pytest.ini file (default: documentdb_tests/pytest.ini)
        """
        self.pytest_ini_path = pytest_ini_path
        self._markers_cache: Optional[set] = None

    def _get_registered_markers(self) -> set:
        """
        Get registered markers (cached per instance).

        Returns:
            Set of registered marker names
        """
        if self._markers_cache is None:
            self._markers_cache = load_registered_markers(self.pytest_ini_path)
        return self._markers_cache

    def extract_markers(self, test_result: Dict[str, Any]) -> List[str]:
        """
        Extract pytest markers (tags) from a test result.

        Uses registered markers from pytest.ini as an allow list.
        This ensures only intentional test categorization markers are included,
        avoiding brittle heuristics that could break with future pytest versions.

        Args:
            test_result: Test result dictionary from pytest JSON report

        Returns:
            List of marker names that match registered markers from pytest.ini
        """
        registered_markers = self._get_registered_markers()

        markers = []

        # Extract from keywords
        keywords = test_result.get("keywords", [])
        if isinstance(keywords, list):
            markers.extend(keywords)

        # Extract from markers field if present
        test_markers = test_result.get("markers", [])
        if isinstance(test_markers, list):
            for marker in test_markers:
                if isinstance(marker, dict):
                    markers.append(marker.get("name", ""))
                else:
                    markers.append(str(marker))

        # Filter to only registered markers
        return [m for m in markers if m in registered_markers]

    def analyze_results(self, json_report_path: str) -> Dict[str, Any]:
        """
        Analyze pytest JSON report and generate categorized results.

        Args:
            json_report_path: Path to pytest JSON report file

        Returns:
            Dictionary containing analysis results with structure:
            {
                "summary": {
                    "total": int,
                    "passed": int,
                    "failed": int,
                    "skipped": int,
                    "pass_rate": float
                },
                "by_tag": {
                    "tag_name": {
                        "passed": int,
                        "failed": int,
                        "skipped": int,
                        "total": int,
                        "pass_rate": float
                    }
                },
                "tests": [
                    {
                        "name": str,
                        "outcome": str,
                        "duration": float,
                        "tags": List[str],
                        "error": str (optional, present for failed tests),
                        "is_infra_error": bool (optional, present for failed tests)
                    }
                ]
            }
        """
        # Load JSON report
        with open(json_report_path, "r") as f:
            report = json.load(f)

        # Reconciliation is derived from pytest's own summary, which counts
        # deselected/errored tests that the per-test loop below never sees.
        reconciliation = build_reconciliation(report.get("summary", {}))

        # Initialize counters
        summary: Dict[str, Any] = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "xfailed": 0,
            "xpassed": 0,
        }

        by_tag: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"passed": 0, "failed": 0, "skipped": 0, "xfailed": 0, "xpassed": 0}
        )

        tests_details = []

        # Process each test
        tests = report.get("tests", [])
        for test in tests:
            summary["total"] += 1

            # Categorize the outcome
            test_outcome = categorize_outcome(test)

            # Extract tags using instance method
            tags = self.extract_markers(test)

            # Update summary counters using mapping
            counter_key = OUTCOME_TO_KEY.get(test_outcome)
            if counter_key:
                summary[counter_key] += 1

            # Update tag-specific counters
            if counter_key:
                for tag in tags:
                    by_tag[tag][counter_key] += 1

            # Store test details
            test_detail = {
                "name": test.get("nodeid", ""),
                "outcome": test_outcome,
                "duration": test.get("duration", 0),
                "tags": tags,
            }

            # Add error information for failed tests
            if test_outcome == TestOutcome.FAIL:
                phase_info = _failing_phase_info(test)
                test_detail["error"] = phase_info.get("longrepr", "")
                if is_infrastructure_error(test):
                    test_detail["failure_type"] = "INFRA_ERROR"
                else:
                    test_detail["failure_type"] = extract_failure_tag(test) or "UNKNOWN"

            tests_details.append(test_detail)

        # Calculate pass rates for each tag
        # Note: 'total' includes all tests (passed + failed + skipped)
        # Pass rate is calculated as: passed / total
        # This means skipped tests lower the pass rate, which is intentional
        by_tag_with_rates = {}
        for tag, counts in by_tag.items():
            total = counts["passed"] + counts["failed"] + counts["skipped"]
            pass_rate = (counts["passed"] / total * 100) if total > 0 else 0

            by_tag_with_rates[tag] = {**counts, "total": total, "pass_rate": round(pass_rate, 2)}

        # Calculate overall pass rate
        summary["pass_rate"] = round(
            (summary["passed"] / summary["total"] * 100) if summary["total"] > 0 else 0, 2
        )

        return {
            "summary": summary,
            "by_tag": by_tag_with_rates,
            "tests": tests_details,
            "reconciliation": reconciliation,
        }
