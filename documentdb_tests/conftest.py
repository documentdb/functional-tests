"""
Global pytest fixtures for functional testing framework.

This module provides fixtures for:
- Engine parametrization
- Database connection management
- Test isolation
"""

from __future__ import annotations

import pytest

# Enable assertion rewriting BEFORE importing framework modules
pytest.register_assert_rewrite("documentdb_tests.framework.assertions")

from pathlib import Path  # noqa: E402

from documentdb_tests.framework import fixtures  # noqa: E402
from documentdb_tests.framework.engine_registry import (  # noqa: E402
    Target,
    ensure_initiated,
    live_targets,
)
from documentdb_tests.framework.error_codes_validator import (  # noqa: E402
    validate_error_codes_sorted,
)
from documentdb_tests.framework.preconditions import (  # noqa: E402
    REQUIRES_MARKER,
    detect_capabilities,
    known_engines,
    marker_spec,
    unmet_requirements,
)
from documentdb_tests.framework.test_format_validator import validate_test_format  # noqa: E402
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
    parser.addoption(
        "--run-crash-tests",
        action="store_true",
        default=False,
        help="Run tests marked engine_xcrash against the engine they crash. They "
        "are skipped by default because they kill the server; enable this only "
        "in an isolated job that can tolerate (and expects) a server crash.",
    )


def pytest_configure(config):
    """Configure pytest with custom settings.

    Resolves the set of test targets the session will run against and stores it
    on the config as ``test_targets``:

    - If ``--connection-string`` is given, it pins a single ad-hoc target using
      that string and ``--engine-name`` (used by CI and for pointing at an
      arbitrary instance not in the registry). Discovery is bypassed.
    - Otherwise the live targets from the dev compose registry are discovered
      and the session runs against each (the zero-config local workflow).

    Tests are parametrized over these targets in ``pytest_generate_tests``.
    """
    connection_string = config.getoption("--connection-string")
    engine_name = config.getoption("--engine-name")

    if connection_string:
        # Explicit override: a single pinned target, discovery bypassed. The
        # engine must be a known one so its preconditions can be resolved the
        # same way as for an auto-discovered target.
        if engine_name not in known_engines():
            raise pytest.UsageError(
                f"--engine-name must be one of {sorted(known_engines())} when "
                f"--connection-string is given, got {engine_name!r}"
            )
        config.test_targets = [
            Target(
                name=engine_name,
                engine=engine_name,
                connection_string=connection_string,
            )
        ]
    else:
        # Zero-config: run against whichever registered targets are live.
        config.test_targets = live_targets()

    # A target started as a replica set member accepts connections (so it is
    # discovered as live) but is not usable until the set is initiated. Initiate
    # it here, once, before tests run: idempotent, and a no-op for an
    # already-initiated set or a standalone server. Under xdist this runs on the
    # controller before workers fork, so there is no cross-worker race.
    #
    # Collection must work without a live server, so skip initiation when only
    # collecting. An unreachable target at run time surfaces as a per-test
    # connection error via the engine_client fixture.
    if not hasattr(config, "workerinput") and not config.option.collectonly:
        for target in config.test_targets:
            ensure_initiated(target.connection_string)

    # Register the requires marker from its single source of truth so it need
    # not be duplicated in the pytest configuration file.
    config.addinivalue_line("markers", marker_spec())


def pytest_generate_tests(metafunc):
    """Parametrize tests over the resolved test targets.

    Every test that reaches a live engine does so through the ``engine_client``
    fixture, so parametrizing that fixture (indirectly) fans each test out into
    one instance per target. The target name is the parametrization id, so a
    failure is reported against the specific target it occurred on.
    """
    if "engine_client" not in metafunc.fixturenames:
        return
    targets = getattr(metafunc.config, "test_targets", [])
    metafunc.parametrize(
        "engine_client",
        targets,
        ids=[t.name for t in targets],
        indirect=True,
    )


def _item_target(item) -> Target | None:
    """Return the Target a parametrized item is bound to, or None.

    Each test is parametrized over the session's targets via the indirect
    ``engine_client`` param, so the bound Target is the ``engine_client`` value
    in the item's callspec.
    """
    callspec = getattr(item, "callspec", None)
    if callspec is None:
        return None
    target = callspec.params.get("engine_client")
    # Only a real Target counts; other param types (or pytest's NOTSET sentinel
    # for tests not parametrized over engine_client) are not targets.
    return target if isinstance(target, Target) else None


def pytest_runtest_setup(item):
    """Apply engine-specific xfail and xcrash markers for the item's target."""
    target = _item_target(item)
    engine = target.engine if target is not None else None
    for marker in item.iter_markers("engine_xfail"):
        if engine == marker.kwargs.get("engine"):
            item.add_marker(
                pytest.mark.xfail(
                    reason=marker.kwargs.get("reason", ""),
                    raises=marker.kwargs.get("raises", AssertionError),
                )
            )
    # A crash test kills the server, so it is skipped against the engine it
    # crashes unless the run-crash-tests option opts in. The dedicated crash job
    # sets it and runs each such test in isolation against a server it can lose.
    run_crash_tests = item.config.getoption("--run-crash-tests")
    for marker in item.iter_markers("engine_xcrash"):
        if engine == marker.kwargs.get("engine") and not run_crash_tests:
            pytest.skip(marker.kwargs.get("reason", "crashes the server"))


@pytest.fixture(scope="session")
def engine_client(request):
    """
    Create a database client for the test's target engine.

    The target is supplied indirectly by ``pytest_generate_tests``, which
    parametrizes this fixture over the session's resolved targets. Session-scoped
    for performance: pytest creates one client per distinct target and shares it
    across the session. The client is thread-safe and pools connections, so this
    avoids redundant connection overhead.

    Per-test isolation is maintained through the database_client and collection
    fixtures, which create unique databases/collections for each test.

    Args:
        request: pytest request object; ``request.param`` is the Target.

    Yields:
        MongoClient: Connected client for the target (shared across session).

    Raises:
        ConnectionError: If unable to connect to the database
    """
    target: Target = request.param

    client = fixtures.create_engine_client(target.connection_string, target.engine)

    yield client

    # Cleanup: close connection
    client.close()


@pytest.fixture
def engine_name(request) -> str:
    """Return the engine name of the target the current test runs against.

    Tests are parametrized over targets via the indirect ``engine_client``
    fixture, so the engine is per-target. Tests that gate on the engine (e.g.
    skip unless a specific engine) read this fixture.
    """
    target = _item_target(request.node)
    assert target is not None, "engine_name requires a test parametrized over a target"
    return target.engine


@pytest.fixture
def connection_string(request) -> str:
    """Return the connection string of the target the current test runs against.

    Tests are parametrized over targets via the indirect ``engine_client``
    fixture, so the connection string is per-target. Tests that open an
    additional connection to the same target read this fixture.
    """
    target = _item_target(request.node)
    assert target is not None, "connection_string requires a test parametrized over a target"
    return target.connection_string


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


@pytest.fixture(scope="function")
def register_db_cleanup(engine_client):
    """Provide a callback to register extra databases or namespaces for post-test cleanup.

    Accepts either a bare database name (drops the entire database) or a
    dot-separated namespace like "db.collection" (drops only that collection).
    """
    names: list[str] = []

    def register(db_or_namespace: str) -> None:
        names.append(db_or_namespace)

    yield register

    for name in names:
        if "." in name:
            db, coll = name.split(".", 1)
            try:
                engine_client[db].drop_collection(coll)
            except Exception:
                pass
        else:
            fixtures.cleanup_database(engine_client, name)


def pytest_collection_modifyitems(session, config, items):
    """
    Combined pytest hook to validate test structure, format, and framework invariants.

    When running with xdist (-n), automatically deselects tests marked with
    'no_parallel' to prevent interference. Run these separately with:
        pytest -m no_parallel -p no:xdist
    Or run them manually with: pytest -m no_parallel -p no:xdist

    Tests carrying a ``requires`` marker are skipped when their target's
    capabilities do not match what the test requires. A target's capabilities
    are determined by its engine and topology, resolved per target at runtime
    (see ``framework.preconditions``).
    """
    # Skip a capability-gated test when its target's capabilities do not match
    # its requires(...) marker. Each item is parametrized over a target; probe
    # each distinct target once.
    capabilities_by_target: dict[str, frozenset[str]] = {}
    for item in items:
        marker = item.get_closest_marker(REQUIRES_MARKER)
        if marker is None or not marker.kwargs:
            continue
        target = _item_target(item)
        if target is None:
            continue
        capabilities = capabilities_by_target.get(target.connection_string)
        if capabilities is None:
            capabilities = detect_capabilities(target.engine, target.connection_string)
            capabilities_by_target[target.connection_string] = capabilities
        unmet = unmet_requirements(marker.kwargs, capabilities)
        if unmet:
            needs = ", ".join(f"{name}={expected}" for name, expected in sorted(unmet.items()))
            item.add_marker(
                pytest.mark.skip(reason=f"target '{target.name}' does not meet requires({needs})")
            )

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
    # Pass through the engine selection so Phase 2 targets the same engines as
    # Phase 1. If an explicit connection string was given (override / CI), pass
    # it through; otherwise Phase 2 re-discovers live targets the same way.
    override_conn = config.getoption("--connection-string")
    if override_conn:
        cmd.extend(["--connection-string", override_conn])
        cmd.extend(["--engine-name", config.getoption("--engine-name")])

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
