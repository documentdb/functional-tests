"""Capability resolution for environment-gated tests.

A test case may apply only to targets that have (or lack) a particular
capability. It declares this with the ``requires`` marker, naming capabilities
and whether each must be present::

    @pytest.mark.requires(change_streams=True)     # only where change streams exist
    @pytest.mark.requires(change_streams=False)    # only where they do not
    @pytest.mark.requires(transactions=True, cluster_admin=True)

A capability is any named fact about a target -- a feature it provides (change
streams, transactions) or a behavior it exhibits (compact succeeding without
``force``). The test is skipped against a target whose capabilities do not match
what it requires.

For a given engine, which capabilities a target has is fully determined by its
topology (e.g. a standalone server vs a replica set). The engine is always known
(it is declared per target) and the topology is detected once from a live
connection. The pair ``(engine, topology)`` then selects the present
capabilities from a static table, so there is a single declarative source of
truth for every engine and topology and the manual-connection path resolves
identically to auto-discovered targets.

The expected behavior of a case is the reference engine's behavior, applied
uniformly to all engines (a compatible engine is measured against it, never
defining its own). Adding an engine or a new topology (e.g. a search-backed
deployment) is a new row in ``_CAPABILITIES_BY_PROFILE`` plus teaching
``_detect_topology`` to recognize it.

The same marker also scopes a test to versions of the reference spec. A run
picks one spec version (``--spec-version``), which decides which tests are in
scope; it is independent of the target, so any target can be measured against
any spec version::

    @pytest.mark.requires(spec_since="8.3")   # behavior added in spec 8.3
    @pytest.mark.requires(spec_until="8.2")   # behavior a later spec changed

A test with no spec gate belongs to the oldest spec and runs under every spec
version. A whole folder is gated from its ``conftest.py`` with
``spec_gate_folder``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

import pytest
from pymongo import MongoClient

# The capabilities the harness knows about, each mapped to a human-readable
# description. A capability is satisfied on the profiles listed for it in
# ``_CAPABILITIES_BY_PROFILE``. Every capability named there must appear here and
# vice versa (enforced by _check_consistency at import time).
_CAPABILITY_DESCRIPTIONS: dict[str, str] = {
    "change_streams": "change streams are available",
    "transactions": "multi-document transactions are available",
    "queryable_encryption": "encryptedFields / queryable encryption is available",
    "cluster_admin": (
        "cluster-wide admin features are available (query settings, default RW concern, "
        "user write-block mode, query sampling)"
    ),
    "cluster_time": "$$CLUSTER_TIME resolves rather than being unavailable",
    "cluster_read_concern": (
        "replication-dependent read concern (afterClusterTime, linearizable, snapshot) "
        "is accepted rather than rejected"
    ),
    "quorum_write_concern": (
        "a quorum write concern is accepted (reported as a writeConcernError) rather than "
        "rejected up front"
    ),
    "oplog": "a replicated oplog (local.oplog.rs) exists",
    "unforced_compact": "compact succeeds without force",
    "reindex": "reIndex is permitted",
    "local_rename": "renaming into the unreplicated local database is permitted",
    "search": "search and vector search surfaces are available",
    "replication": "replication commands are available (applyOps, oplog access)",
    "remote_target": "the server sees the connection as originating from a non-localhost address",
    "validate_repair": (
        "validate with repair/fixMultikey is permitted and background validation "
        "is rejected (standalone-only behavior)"
    ),
}

# The capabilities each (engine, topology) target has. To add an engine or
# topology, add an entry here; every test then gates correctly.
_CAPABILITIES_BY_PROFILE: dict[tuple[str, str], frozenset[str]] = {
    # A replica set, wired to a mongot search sidecar so it also serves the
    # search surfaces (see dev/compose.yaml). mongot is transparent to all other
    # behavior, so this is a replica set that additionally has the search
    # capability, not a distinct topology.
    ("mongodb", "replica_set"): frozenset(
        {
            "change_streams",
            "transactions",
            "queryable_encryption",
            "cluster_admin",
            "cluster_time",
            "cluster_read_concern",
            "quorum_write_concern",
            "search",
            "oplog",
            "replication",
            "remote_target",
        }
    ),
    ("mongodb", "standalone"): frozenset(
        {
            "unforced_compact",
            "reindex",
            "local_rename",
            "remote_target",
            "validate_repair",
        }
    ),
    ("documentdb", "standalone"): frozenset(
        {
            "change_streams",
            "transactions",
            "queryable_encryption",
            "cluster_admin",
            "cluster_time",
            "cluster_read_concern",
            "quorum_write_concern",
            "unforced_compact",
            "reindex",
            "replication",
            "remote_target",
            "validate_repair",
        }
    ),
    # Amazon DocumentDB. A managed, replicated deployment: it presents the
    # DocumentDB capability surface and, being backed by a replica set,
    # additionally has the replication-dependent capabilities the reference
    # server gates behind one (oplog access). Exposed as a single deployment
    # form, so its one topology is named ``replica_set``.
    ("amazon-documentdb", "replica_set"): frozenset(
        {
            "change_streams",
            "transactions",
            "queryable_encryption",
            "cluster_admin",
            "cluster_time",
            "cluster_read_concern",
            "quorum_write_concern",
            "oplog",
            "unforced_compact",
            "reindex",
            "replication",
            "validate_repair",
        }
    ),
}

# The single marker tests use to declare capability requirements.
REQUIRES_MARKER = "requires"

# Every known capability name, for validation of requires(...) kwargs.
CAPABILITIES = frozenset(_CAPABILITY_DESCRIPTIONS)

# The reference spec versions a run can be scoped to, oldest first. A test with
# no spec gate belongs to the oldest one.
SPEC_VERSIONS: tuple[str, ...] = ("8.2", "8.3")
DEFAULT_SPEC_VERSION = "8.2"

# requires(...) keys that gate on the run's spec version rather than on a
# target capability. spec_since: in scope from this version on. spec_until: in
# scope up to and including this version.
SPEC_KEYS = frozenset({"spec_since", "spec_until"})


def _check_consistency() -> None:
    """Fail at import if the descriptions and the profile table diverge.

    Every capability named in the profile table must have a description, and
    every described capability must be present on at least one profile, so a
    capability cannot be referenced without being described or described without
    ever being satisfiable.
    """
    described = set(_CAPABILITY_DESCRIPTIONS)
    mapped: set[str] = set()
    for capabilities in _CAPABILITIES_BY_PROFILE.values():
        mapped |= capabilities
    unknown = mapped - described
    if unknown:
        raise RuntimeError(f"profile table references undescribed capabilities: {sorted(unknown)}")
    unsatisfiable = described - mapped
    if unsatisfiable:
        raise RuntimeError(
            f"described capabilities never present on any profile: {sorted(unsatisfiable)}"
        )


_check_consistency()


def _detect_topology(engine: str, client: MongoClient) -> str:
    """Classify a live target's topology. The only runtime-observed step.

    Engine-specific: each engine names and recognizes its own topologies.
    """
    if engine == "mongodb":
        # A replica set member reports its set name in ``hello``; a standalone
        # server does not.
        if client.admin.command("hello").get("setName"):
            return "replica_set"
        return "standalone"
    if engine == "documentdb":
        # One deployment form. Issue hello so an unreachable target raises here
        # and resolves to no capabilities rather than the full set.
        client.admin.command("hello")
        return "standalone"
    if engine == "amazon-documentdb":
        # Amazon DocumentDB is exposed as a single, replicated deployment form.
        # Issue hello so an unreachable target raises here and resolves to no
        # capabilities rather than the full set.
        client.admin.command("hello")
        return "replica_set"
    raise ValueError(f"unknown engine {engine!r}; cannot classify topology")


_LOCALHOST_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})


def _is_remote_target(client: MongoClient) -> bool:
    """Return whether the server sees this connection as non-localhost."""
    result = client.admin.command("whatsmyuri")
    server_sees_host = result["you"].rsplit(":", 1)[0]
    return server_sees_host not in _LOCALHOST_HOSTS


def marker_spec() -> str:
    """Return the pytest marker definition line for the ``requires`` marker."""
    return (
        "requires(**capabilities): gate a test on capabilities the target must have "
        "(name=True) or lack (name=False), or on the run's spec version "
        "(spec_since=/spec_until=<version>); known names: " + ", ".join(sorted(CAPABILITIES))
    )


def known_engines() -> frozenset[str]:
    """Return the engine names the capability table knows how to resolve."""
    return frozenset(engine for engine, _topology in _CAPABILITIES_BY_PROFILE)


def detect_capabilities(engine: str, connection_string: str) -> frozenset[str]:
    """Return the capabilities the target has.

    Detects the target's topology from a live connection, then looks up the
    capabilities that ``(engine, topology)`` has. On a connection failure the
    set is empty, so capability-gated tests skip rather than error.
    """
    try:
        client: MongoClient = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
    except Exception:
        return frozenset()

    try:
        topology = _detect_topology(engine, client)
        is_remote = _is_remote_target(client)
    except Exception:
        return frozenset()
    finally:
        client.close()

    profile = (engine, topology)
    if profile not in _CAPABILITIES_BY_PROFILE:
        raise RuntimeError(
            f"no capability mapping for target profile {profile}; "
            "add it to _CAPABILITIES_BY_PROFILE"
        )
    capabilities = set(_CAPABILITIES_BY_PROFILE[profile])
    if not is_remote:
        capabilities.discard("remote_target")
    return frozenset(capabilities)


def unmet_requirements(required: dict[str, bool], capabilities: frozenset[str]) -> dict[str, bool]:
    """Return the subset of ``required`` the target's capabilities do not meet.

    ``required`` maps a capability name to whether the test needs it present
    (True) or absent (False). A requirement is unmet when the capability's
    presence does not match. Unknown capability names raise, so a typo in a
    ``requires(...)`` marker fails loudly rather than silently never gating.
    Spec-version keys are not capabilities and are ignored here (see
    ``unmet_spec``).
    """
    unknown = set(required) - CAPABILITIES - SPEC_KEYS
    if unknown:
        raise RuntimeError(f"requires(...) names unknown capabilities: {sorted(unknown)}")
    return {
        name: expected
        for name, expected in required.items()
        if name not in SPEC_KEYS and (name in capabilities) != expected
    }


def _check_spec_gate(gate: dict[str, Any]) -> None:
    """Raise if a spec gate names an unknown key or version."""
    unknown = set(gate) - SPEC_KEYS
    if unknown:
        raise RuntimeError(f"unknown spec gate keys: {sorted(unknown)}")
    for key, version in gate.items():
        if version not in SPEC_VERSIONS:
            raise RuntimeError(
                f"requires({key}={version!r}) names an unknown spec version; "
                f"known versions: {', '.join(SPEC_VERSIONS)}"
            )


def unmet_spec(required: dict[str, Any], spec_version: str) -> dict[str, str]:
    """Return the spec gates in ``required`` that put a test out of scope.

    A test is out of scope when the run's spec version is older than its
    ``spec_since`` or newer than its ``spec_until``. An unknown version raises,
    so a typo fails loudly rather than silently never running the test.
    """
    gate = {key: value for key, value in required.items() if key in SPEC_KEYS}
    _check_spec_gate(gate)
    run = SPEC_VERSIONS.index(spec_version)
    unmet = {}
    since = gate.get("spec_since")
    if since is not None and run < SPEC_VERSIONS.index(since):
        unmet["spec_since"] = since
    until = gate.get("spec_until")
    if until is not None and run > SPEC_VERSIONS.index(until):
        unmet["spec_until"] = until
    return unmet


def merged_requirements(markers: Iterable[Any]) -> dict[str, Any]:
    """Combine every ``requires`` marker on a test into one mapping.

    Markers are given closest first (as ``item.iter_markers`` yields them), so
    a folder or module gate and a test's own capability gate both apply, and on
    a key set at two levels the closest one wins.
    """
    merged: dict[str, Any] = {}
    for marker in markers:
        for key, value in marker.kwargs.items():
            merged.setdefault(key, value)
    return merged


def spec_gate_folder(conftest_file: str, **gate: str) -> Callable[..., None]:
    """Return a collection hook that spec-gates every test under a folder.

    Use it from the folder's ``conftest.py``::

        pytest_collection_modifyitems = spec_gate_folder(__file__, spec_since="8.3")

    The gate is added to each test module under the folder, after the module's
    own marks, so a file or test gate still wins on the same key and capability
    gates combine with it.
    """
    _check_spec_gate(gate)
    folder = Path(conftest_file).resolve().parent
    mark = getattr(pytest.mark, REQUIRES_MARKER)(**gate)

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection_modifyitems(items: list) -> None:
        checked: set[int] = set()
        for item in items:
            module = item.getparent(pytest.Module)
            if module is None or id(module) in checked:
                continue
            checked.add(id(module))
            if folder in Path(module.path).resolve().parents:
                module.add_marker(mark)

    return pytest_collection_modifyitems
