"""
Global pytest fixtures for functional testing framework.

This module provides fixtures for:
- Engine parametrization
- Database connection management
- Test isolation
"""

import pytest

# Enable assertion rewriting BEFORE importing framework modules
pytest.register_assert_rewrite("documentdb_tests.framework.assertions")

from pathlib import Path  # noqa: E402

from documentdb_tests.framework import fixtures  # noqa: E402
from documentdb_tests.framework.error_codes_validator import (  # noqa: E402
    validate_error_codes_sorted,
)
from documentdb_tests.framework.test_format_validator import (  # noqa: E402
    validate_test_format,
)
from documentdb_tests.framework.test_structure_validator import (  # noqa: E402
    validate_python_files_in_tests,
)


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--connection-string",
        action="store",
        default=None,
        help="Database connection string. "
        "Example: --connection-string mongodb://localhost:27017",
    )
    parser.addoption(
        "--engine-name",
        action="store",
        default="default",
        help="Optional engine identifier for metadata. " "Example: --engine-name documentdb",
    )


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Get connection string and engine name
    connection_string = config.getoption("--connection-string")
    engine_name = config.getoption("--engine-name")

    # Store in config for access by fixtures
    config.connection_string = connection_string
    config.engine_name = engine_name

    # If no connection string specified, default to localhost
    if not connection_string:
        config.connection_string = "mongodb://localhost:27017"


def pytest_runtest_setup(item):
    """Apply engine-specific xfail markers."""
    for marker in item.iter_markers("engine_xfail"):
        if getattr(item.config, "engine_name", None) == marker.kwargs.get("engine"):
            item.add_marker(
                pytest.mark.xfail(
                    reason=marker.kwargs.get("reason", ""),
                    raises=marker.kwargs.get("raises", AssertionError),
                )
            )


@pytest.fixture(scope="session")
def engine_client(request):
    """
    Create a MongoDB client for the configured engine.

    Session-scoped for performance - MongoClient is thread-safe and maintains
    an internal connection pool. This significantly improves test execution speed
    by eliminating redundant connection overhead.

    Per-test isolation is maintained through database_client and collection fixtures
    which create unique databases/collections for each test.

    Args:
        request: pytest request object

    Yields:
        MongoClient: Connected MongoDB client (shared across session)

    Raises:
        ConnectionError: If unable to connect to the database
    """
    connection_string = request.config.connection_string
    engine_name = request.config.engine_name

    client = fixtures.create_engine_client(connection_string, engine_name)

    yield client

    # Cleanup: close connection
    client.close()


@pytest.fixture(scope="session")
def worker_id(request):
    """
    Provide worker_id for test isolation, with fallback when xdist is not active.

    Returns xdist's worker_id if available, otherwise 'master'.
    """
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


@pytest.fixture(scope="function")
def database_client(engine_client, request, worker_id):
    """
    Provide a database client with automatic cleanup.

    Creates a test database with a collision-free name for parallel execution.
    The name includes worker ID, hash, and abbreviated test name.
    Automatically drops the database after the test completes.

    Args:
        engine_client: MongoDB client from engine_client fixture
        request: pytest request object
        worker_id: Worker ID from pytest-xdist (e.g., 'gw0', 'gw1', or 'master')

    Yields:
        Database: MongoDB database object
    """
    # Generate unique database name using framework utility
    full_test_id = request.node.nodeid
    db_name = fixtures.generate_database_name(full_test_id, worker_id)

    db = engine_client[db_name]

    yield db

    # Cleanup: drop test database
    fixtures.cleanup_database(engine_client, db_name)


@pytest.fixture(scope="function")
def collection(database_client, request, worker_id):
    """
    Provide an empty collection with automatic cleanup.

    Creates a collection with a collision-free name for parallel execution.
    Tests should directly insert any required test data.

    Args:
        database_client: Database from database_client fixture
        request: pytest request object
        worker_id: Worker ID from pytest-xdist (e.g., 'gw0', 'gw1', or 'master')

    Yields:
        Collection: Empty MongoDB collection object
    """
    # Generate unique collection name using framework utility
    full_test_id = request.node.nodeid
    collection_name = fixtures.generate_collection_name(full_test_id, worker_id)

    coll = database_client[collection_name]

    yield coll

    # Cleanup: drop collection
    fixtures.cleanup_collection(database_client, collection_name)


def pytest_collection_modifyitems(session, config, items):
    """
    Combined pytest hook to validate test structure, format, and framework invariants.

    When running with xdist (-n), automatically deselects tests marked with
    'no_parallel' to prevent interference. Run these separately with:
        pytest -m no_parallel -p no:xdist
    Or run them manually with: pytest -m no_parallel -p no:xdist
    """
    # Deselect no_parallel tests when running under xdist
    is_xdist = bool(getattr(config.option, "numprocesses", None)) or hasattr(config, "workerinput")
    if is_xdist:
        parallel_items = []
        deselected = []
        for item in items:
            if item.get_closest_marker("no_parallel"):
                deselected.append(item)
            else:
                parallel_items.append(item)
        if deselected:
            config.hook.pytest_deselected(items=deselected)
            items[:] = parallel_items

    structure_errors = []
    format_errors = {}

    # Validate file structure for all files under "tests" folder
    if items:
        first_item_path = Path(items[0].fspath)
        if "tests" in first_item_path.parts:
            tests_idx = first_item_path.parts.index("tests")
            tests_dir = Path(*first_item_path.parts[: tests_idx + 1])
            structure_errors.extend(validate_python_files_in_tests(tests_dir))

    # Validate test format for collected test files (only compatibility tests under tests/)
    seen_files = set()
    for item in items:
        file_path = str(item.fspath)
        if file_path in seen_files:
            continue
        seen_files.add(file_path)
        if "tests" not in Path(file_path).parts:
            continue
        file_errors = validate_test_format(file_path)
        if file_errors:
            format_errors[file_path] = file_errors

    # Validate framework error code invariants
    structure_errors.extend(validate_error_codes_sorted())

    if structure_errors or format_errors:
        import sys

        if structure_errors:
            print("\n\n❌ Folder Structure Violations:", file=sys.stderr)
            print("".join(structure_errors), file=sys.stderr)
            print("\nSee docs/testing/FOLDER_STRUCTURE.md for rules.\n", file=sys.stderr)

        if format_errors:
            print("\n❌ Test Format Violations:", file=sys.stderr)
            for file_path, file_errors in format_errors.items():
                print(f"\n{file_path}:", file=sys.stderr)
                print("\n".join(file_errors), file=sys.stderr)
            print("\nSee docs/testing/TEST_FORMAT.md for rules.\n", file=sys.stderr)

        pytest.exit("Test validation failed", returncode=1)


def _merge_json_reports(phase1_path, phase2_path):
    """Merge Phase 2 JSON report into Phase 1 report."""
    import json

    with open(phase1_path) as f:
        p1 = json.load(f)
    with open(phase2_path) as f:
        p2 = json.load(f)

    p1.setdefault("tests", []).extend(p2.get("tests", []))
    p1["duration"] = p1.get("duration", 0) + p2.get("duration", 0)
    p1_summary = p1.setdefault("summary", {})
    p2_summary = p2.get("summary", {})
    for key in ("passed", "failed", "error", "skipped", "total"):
        if key in p2_summary:
            p1_summary[key] = p1_summary.get(key, 0) + p2_summary[key]
    # Phase 2 runs without xdist, so its collected reflects the true count
    # before any deselection. Phase 1 under xdist may have a reduced count
    # due to no_parallel deselection in pytest_collection_modifyitems.
    p2_collected = p2_summary.get("collected", 0)
    if p2_collected > 0:
        p1_summary["collected"] = p2_collected
    p1_summary.pop("deselected", None)

    with open(phase1_path, "w") as f:
        json.dump(p1, f, indent=2)


def _merge_junit_xml(phase1_path, phase2_path):
    """Merge Phase 2 JUnit XML into Phase 1 XML."""
    import xml.etree.ElementTree as ET

    p1_tree = ET.parse(phase1_path)
    p2_tree = ET.parse(phase2_path)
    p1_suite = p1_tree.find(".//testsuite")
    p2_suite = p2_tree.find(".//testsuite")
    if p1_suite is None or p2_suite is None:
        return

    for testcase in p2_suite.findall("testcase"):
        p1_suite.append(testcase)

    for attr in ("tests", "errors", "failures", "skipped"):
        v1 = int(p1_suite.get(attr, 0))
        v2 = int(p2_suite.get(attr, 0))
        p1_suite.set(attr, str(v1 + v2))

    t1 = float(p1_suite.get("time", 0))
    t2 = float(p2_suite.get("time", 0))
    p1_suite.set("time", f"{t1 + t2:.3f}")

    p1_tree.write(phase1_path, xml_declaration=True, encoding="utf-8")


def pytest_sessionfinish(session, exitstatus):
    """
    After parallel phase completes, automatically run no_parallel tests sequentially.

    Only triggers on the xdist controller node (not workers, not non-xdist runs).
    Phase 2 results are merged into Phase 1 report files (JSON and JUnit XML).
    """
    config = session.config
    is_xdist_controller = bool(getattr(config.option, "numprocesses", None)) and not hasattr(
        config, "workerinput"
    )
    if not is_xdist_controller:
        return

    import os
    import subprocess
    import sys
    import tempfile

    print(
        f"\n{'='*60}\n" f"Phase 2: Running no_parallel tests sequentially\n" f"{'='*60}\n",
        flush=True,
    )

    cmd = [sys.executable, "-m", "pytest", "-p", "no:xdist", "-v"]

    # Combine user's marker expression with no_parallel
    user_marker = getattr(config.option, "markexpr", "")
    if user_marker:
        cmd.extend(["-m", f"no_parallel and ({user_marker})"])
    else:
        cmd.extend(["-m", "no_parallel"])
    cmd.extend(["--connection-string", config.connection_string])
    cmd.extend(["--engine-name", config.engine_name])

    # Detect Phase 1 report paths and set up Phase 2 temp report files
    phase1_json = getattr(config.option, "json_report_file", None)
    phase1_junit = getattr(config.option, "xmlpath", None)
    phase2_json = None
    phase2_junit = None

    if phase1_json and os.path.exists(phase1_json):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".json", prefix="phase2_")
        phase2_json = f.name
        f.close()
        cmd.extend(["--json-report", f"--json-report-file={phase2_json}"])
    if phase1_junit and os.path.exists(phase1_junit):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".xml", prefix="phase2_")
        phase2_junit = f.name
        f.close()
        cmd.extend([f"--junitxml={phase2_junit}"])

    if config.args:
        cmd.extend(config.args)

    result = subprocess.call(cmd)

    if result == 5:
        print("\nℹ️  No no_parallel tests found — Phase 2 skipped")
    elif result != 0:
        print(f"\n❌ Phase 2 failed (exit code {result})")
        session.exitstatus = 1
    else:
        print("\n✅ Phase 2 complete — all no_parallel tests passed")

    # Merge Phase 2 reports into Phase 1 reports
    if phase2_json and os.path.exists(phase2_json):
        try:
            _merge_json_reports(phase1_json, phase2_json)
            print(f"📊 Merged Phase 2 results into {phase1_json}")
        except Exception as e:
            print(f"⚠️  Failed to merge JSON reports: {e}", file=sys.stderr)
        finally:
            os.unlink(phase2_json)

    if phase2_junit and os.path.exists(phase2_junit):
        try:
            _merge_junit_xml(phase1_junit, phase2_junit)
            print(f"📊 Merged Phase 2 results into {phase1_junit}")
        except Exception as e:
            print(f"⚠️  Failed to merge JUnit XML reports: {e}", file=sys.stderr)
        finally:
            os.unlink(phase2_junit)

    # Pytest prints its own Phase 1 summary after this hook returns;
    # add a note so it's not confused with Phase 2 results.
    print(
        '\nℹ️  The summary line below ("=== N passed in Xs ===") is Phase 1 (parallel) only. '
        "See merged report files for combined results.",
        flush=True,
    )

    if exitstatus != 0:
        session.exitstatus = exitstatus
