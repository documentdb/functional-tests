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
"""

from __future__ import annotations

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
    "unforced_compact": "compact succeeds without force",
    "reindex": "reIndex is permitted",
    "local_rename": "renaming into the unreplicated local database is permitted",
    "search": "search and vector search surfaces are available",
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
        }
    ),
    ("mongodb", "standalone"): frozenset(
        {
            "unforced_compact",
            "reindex",
            "local_rename",
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
        }
    ),
}

# The single marker tests use to declare capability requirements.
REQUIRES_MARKER = "requires"

# Every known capability name, for validation of requires(...) kwargs.
CAPABILITIES = frozenset(_CAPABILITY_DESCRIPTIONS)


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
    raise ValueError(f"unknown engine {engine!r}; cannot classify topology")


def marker_spec() -> str:
    """Return the pytest marker definition line for the ``requires`` marker."""
    return (
        "requires(**capabilities): gate a test on capabilities the target must have "
        "(name=True) or lack (name=False); known names: " + ", ".join(sorted(CAPABILITIES))
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
    return _CAPABILITIES_BY_PROFILE[profile]


def unmet_requirements(required: dict[str, bool], capabilities: frozenset[str]) -> dict[str, bool]:
    """Return the subset of ``required`` the target's capabilities do not meet.

    ``required`` maps a capability name to whether the test needs it present
    (True) or absent (False). A requirement is unmet when the capability's
    presence does not match. Unknown capability names raise, so a typo in a
    ``requires(...)`` marker fails loudly rather than silently never gating.
    """
    unknown = set(required) - CAPABILITIES
    if unknown:
        raise RuntimeError(f"requires(...) names unknown capabilities: {sorted(unknown)}")
    return {
        name: expected for name, expected in required.items() if (name in capabilities) != expected
    }
