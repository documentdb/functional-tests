"""
Result analyzer for parsing and categorizing test results.

This module provides functions to analyze pytest JSON output and categorize
test results by feature (from the test path) and failure type.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Module-level constants
from documentdb_tests.framework.infra_exceptions import INFRA_EXCEPTION_NAMES as INFRA_EXCEPTIONS

# Mapping from TestOutcome to counter key names
OUTCOME_TO_KEY = {
    "PASS": "passed",
    "FAIL": "failed",
    "ERROR": "error",
    "SKIPPED": "skipped",
    "XFAIL": "xfailed",
    "XPASS": "xpassed",
}


class TestOutcome:
    """Enumeration of test outcomes."""

    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"
    XFAIL = "XFAIL"
    XPASS = "XPASS"


def categorize_outcome(test_result: Dict[str, Any]) -> str:
    """
    Categorize a test outcome based on test result information.

    Maps pytest outcomes to simple categories:
    - PASS: Test passed
    - FAIL: Test failed a verdict (assertion/comparison in the call phase)
    - ERROR: Test never reached a verdict (a crash in setup or teardown)
    - SKIPPED: Test skipped
    - XFAIL: Test expected to fail and did fail
    - XPASS: Test expected to fail but passed

    Args:
        test_result: Test result dictionary from pytest JSON report

    Returns:
        One of: PASS, FAIL, ERROR, SKIPPED, XFAIL, XPASS
    """
    outcome = test_result.get("outcome", "")

    if outcome == "passed":
        return TestOutcome.PASS
    elif outcome == "error":
        return TestOutcome.ERROR
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


def extract_skip_reason(test_result: Dict[str, Any]) -> str:
    """
    Extract the reason a test was skipped, from its setup-phase longrepr.

    pytest records a skip as ``('<path>', <lineno>, 'Skipped: <reason>')`` in the
    setup phase's longrepr. Pull out the reason text.

    Args:
        test_result: Full test result dict from pytest JSON

    Returns:
        The reason, or empty string if none is recorded.
    """
    longrepr = (test_result.get("setup") or {}).get("longrepr", "")
    if not isinstance(longrepr, str):
        return ""
    match = re.search(r"Skipped:\s*(.*?)'\)\s*$", longrepr)
    return match.group(1) if match else ""


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

# Per-test outcome buckets (the subset of the above that a single test can land
# in). Used when aggregating tests, where run-level totals like "collected" or
# "deselected" have no meaning.
_PER_TEST_OUTCOME_KEYS = (
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

    # Deselected tests are those collected but not run. pytest doesn't always
    # record a ``deselected`` count, so derive it from collected - total to keep
    # the decomposition honest: collected = deselected + total, always.
    collected = counts["collected"]
    total = counts["total"]
    if collected >= total:
        counts["deselected"] = collected - total

    # Only verdict-bearing outcomes count toward the rate; a run with any error
    # therefore cannot read 100%.
    denominator = counts["passed"] + counts["failed"] + counts["error"]
    pass_rate = (counts["passed"] / denominator * 100) if denominator > 0 else 0.0
    return {**counts, "pass_rate": round(pass_rate, 2)}


# The test root under which the feature taxonomy begins. A nodeid looks like
# "documentdb_tests/compatibility/tests/core/operator/.../test_x.py::test_y";
# everything after this prefix is the feature path (core, operator, ...).
_TESTS_ROOT = "tests/"


def feature_path(nodeid: str) -> List[str]:
    """
    Return the feature path components for a test, from its nodeid.

    The directory tree under ``tests/`` *is* the feature taxonomy
    (e.g. ``core/operator/expressions/arithmetic/add``), so the path components
    are the grouping tiers — area first, then successively narrower categories,
    down to the test file itself as the deepest tier (files group related cases,
    e.g. ``subtract/test_subtract_errors.py``). The tree is ragged, so callers
    must not assume a fixed depth. The ``::test`` selector is dropped — individual
    test cases are the leaves shown elsewhere, not tree tiers.

    Args:
        nodeid: A pytest node id.

    Returns:
        Ordered path components (directories then the file), or an empty list if
        the root isn't found.
    """
    path = nodeid.split("::", 1)[0]
    marker = path.rfind(_TESTS_ROOT)
    if marker == -1:
        return []
    relative = path[marker + len(_TESTS_ROOT) :]
    return relative.split("/")


def group_by_feature(
    tests: List[Dict[str, Any]], deselected: Optional[Dict[str, Dict[str, bool]]] = None
) -> Dict[str, Any]:
    """
    Aggregate per-test outcomes into a nested tree keyed by feature path.

    Each node holds its own aggregated outcome counts (summed over every test
    beneath it) and a ``children`` map of the next path component to a child
    node. A node is a leaf when tests live directly at its path; because the
    tree is ragged, leaves occur at varying depths.

    Args:
        tests: The per-test detail dicts (each with ``name`` and ``outcome``).
        deselected: Optional mapping of deselected nodeid -> the requirements the
            target didn't meet. Deselected tests have no outcome, so they're
            counted under a separate ``deselected`` tally and their required
            capability names are collected into each node's ``requires`` set,
            letting the tree show — and explain — areas not applicable here.

    Returns:
        The root node:
        ``{"counts": {...}, "requires": set(), "children": {component: node}}``.
    """

    def _new_node() -> Dict[str, Any]:
        counts = dict.fromkeys(_PER_TEST_OUTCOME_KEYS, 0)
        counts["deselected"] = 0
        return {"counts": counts, "requires": set(), "children": {}}

    def _credit(nodeid: str, counter_key: str, requires: Optional[List[str]] = None) -> None:
        components = feature_path(nodeid)
        node = root
        node["counts"][counter_key] += 1
        node["requires"].update(requires or [])
        for component in components:
            node = node["children"].setdefault(component, _new_node())
            node["counts"][counter_key] += 1
            node["requires"].update(requires or [])

    root = _new_node()
    for test in tests:
        counter_key = OUTCOME_TO_KEY.get(test.get("outcome", ""))
        if counter_key is None:
            continue
        # Credit the count to the root and every node along the path, so each
        # node's counts include all tests beneath it.
        _credit(test.get("name", ""), counter_key)
    for nodeid, unmet in (deselected or {}).items():
        _credit(nodeid, "deselected", requires=list(unmet.keys()))
    return root


class ResultAnalyzer:
    """
    Analyzer for pytest JSON test results.

    Example:
        analyzer = ResultAnalyzer()
        results = analyzer.analyze_results("report.json")
    """

    @staticmethod
    def _load_deselected(json_report_path: str) -> Dict[str, Dict[str, bool]]:
        """
        Return the report's deselected sidecar: nodeid -> unmet requirements.

        The sidecar (``<report>.deselected.json``) is written at collection time
        (see conftest); it maps each deselected nodeid to the requirements the
        target didn't meet. Absent sidecar (older runs, or no deselection) yields
        an empty mapping.
        """
        sidecar = f"{json_report_path}.deselected.json"
        if not Path(sidecar).exists():
            return {}
        try:
            with open(sidecar) as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def analyze_results(self, json_report_path: str) -> Dict[str, Any]:
        """
        Analyze pytest JSON report and generate categorized results.

        Args:
            json_report_path: Path to pytest JSON report file

        Returns:
            Dictionary containing analysis results with structure:
            {
                "reconciliation": { ... }, # counts + pass_rate (see build_reconciliation)
                "by_feature": { ... },     # nested feature tree (see group_by_feature)
                "tests": [
                    {
                        "name": str,
                        "outcome": str,
                        "duration": float,
                        "error": str (optional, present for failed/errored tests),
                        "failure_type": str (optional, present for failed/errored tests),
                        "xfail_reason": str (optional, present for xfailed tests),
                        "skip_reason": str (optional, present for skipped tests)
                    }
                ]
            }
        """
        # Load JSON report
        with open(json_report_path, "r") as f:
            report = json.load(f)

        # Deselected tests are dropped before the run, so they aren't in the
        # report. A sidecar written at collection time (if present) records which
        # ones and why, letting the feature tree show areas not applicable here.
        deselected_nodeids = self._load_deselected(json_report_path)

        # Reconciliation is derived from pytest's own summary, which counts
        # deselected/errored tests that the per-test loop below never sees. It
        # is the single source of run totals and pass rate.
        reconciliation = build_reconciliation(report.get("summary", {}))

        tests_details = []

        # Process each test
        tests = report.get("tests", [])
        for test in tests:
            # Categorize the outcome
            test_outcome = categorize_outcome(test)

            # Store test details
            test_detail = {
                "name": test.get("nodeid", ""),
                "outcome": test_outcome,
                "duration": test.get("duration", 0),
            }

            # Add error information for tests that failed or errored. A FAIL
            # reached a verdict and was wrong; an ERROR crashed before a verdict
            # (usually in a fixture) - both carry a traceback worth surfacing.
            if test_outcome in (TestOutcome.FAIL, TestOutcome.ERROR):
                phase_info = _failing_phase_info(test)
                test_detail["error"] = phase_info.get("longrepr", "")
                if is_infrastructure_error(test):
                    test_detail["failure_type"] = "INFRA_ERROR"
                else:
                    test_detail["failure_type"] = extract_failure_tag(test) or "UNKNOWN"

            # An xfailed test is a documented incompatibility; carry its reason
            # (recorded into the report metadata by a conftest hook) so it can be
            # listed as a known gap.
            if test_outcome == TestOutcome.XFAIL:
                metadata = test.get("metadata") or {}
                test_detail["xfail_reason"] = metadata.get("xfail_reason", "")

            # A skipped test was deliberately not run; carry its reason so the
            # report can explain why, rather than showing a bare count.
            if test_outcome == TestOutcome.SKIPPED:
                test_detail["skip_reason"] = extract_skip_reason(test)

            tests_details.append(test_detail)

        return {
            "reconciliation": reconciliation,
            "tests": tests_details,
            "by_feature": group_by_feature(tests_details, deselected_nodeids),
        }
