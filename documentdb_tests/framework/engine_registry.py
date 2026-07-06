"""Test-target registry derived from the dev compose file.

``dev/compose.yaml`` is the single source of truth for the local database
targets. Each runnable service carries an ``x-test-target`` block describing how
the test harness should reach it:

    x-test-target:
      engine: <engine name for engine_xfail / engine_xcrash markers>
      query: <optional connection-string query string, without leading '?'>

The host port comes from the service's ``ports:`` mapping, so it is not
duplicated here. This module reads that file and exposes the targets so the test
session can discover which are live and run against each, without any port or
connection-string information living in two places.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import yaml
from pymongo import MongoClient
from pymongo.errors import OperationFailure

# dev/compose.yaml relative to the repository root (two levels up from this
# module's package: documentdb_tests/framework/ -> repo root).
COMPOSE_PATH = Path(__file__).resolve().parents[2] / "dev" / "compose.yaml"


@dataclass(frozen=True)
class Target:
    """A test target read from the compose file.

    Attributes:
        name: The compose service name, used as the target / parametrization id.
        engine: Engine name reported to the harness, matched by engine_xfail and
            engine_xcrash markers.
        connection_string: Full connection string built from the host port and
            optional query suffix.
    """

    name: str
    engine: str
    connection_string: str


def _host_port(service: dict) -> str | None:
    """Return the published host port from a service's first ``ports`` entry."""
    ports = service.get("ports") or []
    if not ports:
        return None
    # Entries look like "27017:27017"; the host port is the left side.
    return str(ports[0]).split(":")[0]


def load_targets(compose_path: Path = COMPOSE_PATH) -> list[Target]:
    """Parse the compose file and return every declared test target.

    A service is a target only if it carries an ``x-test-target`` block and
    publishes a host port. Services without that block (e.g. one-shot init
    containers) are ignored.
    """
    document = yaml.safe_load(compose_path.read_text())
    targets: list[Target] = []
    for name, service in (document.get("services") or {}).items():
        spec = service.get("x-test-target")
        if not spec:
            continue
        port = _host_port(service)
        if port is None:
            continue
        query = spec.get("query")
        connection_string = f"mongodb://localhost:{port}"
        if query:
            connection_string += f"/?{query}"
        targets.append(
            Target(name=name, engine=spec["engine"], connection_string=connection_string)
        )
    return targets


def _is_reachable(connection_string: str) -> bool:
    """Return whether a server accepts a connection within a short timeout."""
    try:
        client: MongoClient = MongoClient(connection_string, serverSelectionTimeoutMS=2000)
    except Exception:
        return False
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
    finally:
        client.close()


# replSetGetStatus error code when the server is a replica set member that has
# not been initiated yet; the only case in which the harness initiates.
_NOT_YET_INITIALIZED = 94
# replSetInitiate error code when the set is already initiated (e.g. a race
# between concurrent callers); treated as success.
_ALREADY_INITIALIZED = 23


def ensure_initiated(connection_string: str, timeout_s: float = 30.0) -> None:
    """Idempotently initiate a single-node replica set, if the target is one.

    A server started with ``--replSet`` accepts connections before the set is
    initiated, but is not usable until it is. This brings such a server up to a
    writable primary. It is safe to call against any target:

    - An already-initiated replica set: ``replSetGetStatus`` succeeds, so nothing
      is done.
    - A standalone server: ``replSetGetStatus`` fails with a code other than
      NotYetInitialized (replication is not enabled), so nothing is done.
    - An uninitiated ``--replSet`` server: ``replSetGetStatus`` fails with
      NotYetInitialized, so ``replSetInitiate`` is issued; a concurrent caller
      that already initiated it (AlreadyInitialized) is tolerated.

    After initiating, it waits up to ``timeout_s`` for a primary to be elected
    so callers can write immediately.
    """
    client: MongoClient = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
    try:
        try:
            client.admin.command("replSetGetStatus")
            return  # Already initiated.
        except OperationFailure as exc:
            if exc.code != _NOT_YET_INITIALIZED:
                return  # Not an uninitiated replica set (e.g. a standalone).

        try:
            client.admin.command("replSetInitiate")
        except OperationFailure as exc:
            if exc.code != _ALREADY_INITIALIZED:
                raise

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if client.admin.command("hello").get("isWritablePrimary"):
                return
            time.sleep(0.5)
        raise TimeoutError(
            f"replica set at {connection_string} did not elect a primary within {timeout_s}s"
        )
    finally:
        client.close()


def live_targets(compose_path: Path = COMPOSE_PATH) -> list[Target]:
    """Return the declared targets that are currently reachable."""
    return [t for t in load_targets(compose_path) if _is_reachable(t.connection_string)]


if __name__ == "__main__":
    # Initiate every reachable target's replica set, if any. Useful before a
    # collection-only run (which does not initiate on its own) so that topology
    # detection sees a usable server. A no-op for standalone targets.
    for _target in live_targets():
        ensure_initiated(_target.connection_string)
