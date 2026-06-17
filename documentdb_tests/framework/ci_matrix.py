"""Emit the CI test matrix from the compose file.

The CI workflow runs the suite once per test target. Rather than duplicating the
target list (ports, profiles, connection strings) in the workflow YAML, this
module derives the matrix from ``dev/compose.yaml`` — the same single source of
truth the test harness reads via :mod:`documentdb_tests.framework.engine_registry`.

Run as ``python -m documentdb_tests.framework.ci_matrix`` to print a JSON array
of target objects, one per target::

    [{"name": ..., "profile": ..., "connection_string": ..., "engine": ...}, ...]

Run with the ``engines`` argument to print one entry per distinct engine instead
(used by the crash-test job, which is engine-keyed rather than per-target)::

    [{"engine": ..., "profile": ..., "connection_string": ...}, ...]

Each target's compose profile is the service's first declared profile, which by
convention equals the service (target) name.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from documentdb_tests.framework.engine_registry import COMPOSE_PATH, load_targets


def _profile_for(service_name: str, compose_path: Path) -> str:
    """Return the target-specific compose profile for a service.

    A target service declares ``profiles: [<target>, "all"]``; the first entry
    is the profile that brings up just that target. It equals the service name
    by convention, but is read from the file so the convention lives in one
    place (the compose file) rather than being assumed here.
    """
    document = yaml.safe_load(compose_path.read_text())
    profiles = document["services"][service_name].get("profiles") or [service_name]
    return str(profiles[0])


def build_matrix(compose_path: Path = COMPOSE_PATH) -> list[dict[str, str]]:
    """Return the CI matrix entries for every declared test target."""
    return [
        {
            "name": t.name,
            "profile": _profile_for(t.name, compose_path),
            "connection_string": t.connection_string,
            "engine": t.engine,
        }
        for t in load_targets(compose_path)
    ]


def build_engine_matrix(compose_path: Path = COMPOSE_PATH) -> list[dict[str, str]]:
    """Return one CI matrix entry per distinct engine.

    Crash tests (``engine_xcrash(engine=...)``) are keyed on the engine, not the
    deployment topology, so the crash probe runs once per distinct engine rather
    than once per target. For each engine the first declared target supplies a
    profile and connection string to reach a server of that engine.
    """
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for t in load_targets(compose_path):
        if t.engine in seen:
            continue
        seen.add(t.engine)
        entries.append(
            {
                "engine": t.engine,
                "profile": _profile_for(t.name, compose_path),
                "connection_string": t.connection_string,
            }
        )
    return entries


if __name__ == "__main__":
    import sys

    which = sys.argv[1] if len(sys.argv) > 1 else "targets"
    matrix = build_engine_matrix() if which == "engines" else build_matrix()
    if not matrix:
        # The compose file declares no test targets. The suite has nothing to
        # run against, which is a misconfiguration; exit non-zero so CI fails
        # loudly instead of producing an empty matrix that silently skips jobs.
        print(f"no test targets found in the compose file ({which})", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(matrix))
