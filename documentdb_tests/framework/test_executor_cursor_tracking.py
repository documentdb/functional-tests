"""Unit tests for server cursor tracking in the executor (no database needed)."""

import pytest
from bson import Int64

from documentdb_tests.framework import executor


class _FakeDatabase:
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def command(self, command, **kwargs):
        self.client.commands.append((self.name, command))
        if self.client.fail_with is not None:
            raise self.client.fail_with
        return self.client.results.pop(0) if self.client.results else {"ok": 1.0}


class _FakeClient:
    """Client whose databases record every command and return queued results."""

    def __init__(self, results=None, fail_with=None):
        self.results = list(results or [])
        self.fail_with = fail_with
        self.commands = []
        self.admin = _FakeDatabase(self, "admin")

    def __getitem__(self, name):
        return _FakeDatabase(self, name)


class _FakeCollection:
    def __init__(self, client, db_name="db", name="coll"):
        self.database = _FakeDatabase(client, db_name)
        self.name = name


@pytest.fixture(autouse=True)
def empty_registry():
    executor._tracked_cursors.clear()
    yield
    executor._tracked_cursors.clear()


def _cursor_result(cursor_id, ns="db.coll"):
    return {"cursor": {"id": Int64(cursor_id), "ns": ns, "firstBatch": []}, "ok": 1.0}


def _kills(client):
    return [(db, cmd) for db, cmd in client.commands if "killCursors" in cmd]


@pytest.mark.unit
def test_open_cursor_is_killed_on_close():
    client = _FakeClient(results=[_cursor_result(42)])
    result = executor.execute_command(_FakeCollection(client), {"find": "coll", "batchSize": 1})
    assert result["cursor"]["id"] == 42

    executor.close_tracked_cursors()

    assert _kills(client) == [("db", {"killCursors": "coll", "cursors": [Int64(42)]})]


@pytest.mark.unit
def test_exhausted_cursor_is_not_tracked():
    client = _FakeClient(results=[_cursor_result(0)])
    executor.execute_command(_FakeCollection(client), {"find": "coll"})

    executor.close_tracked_cursors()

    assert _kills(client) == []


@pytest.mark.unit
def test_failed_command_is_not_tracked():
    client = _FakeClient(fail_with=RuntimeError("boom"))
    result = executor.execute_command(_FakeCollection(client), {"find": "coll"})
    assert isinstance(result, RuntimeError)

    assert executor._tracked_cursors == []


@pytest.mark.unit
def test_cursors_are_grouped_by_namespace():
    client = _FakeClient(
        results=[
            _cursor_result(1),
            _cursor_result(2),
            _cursor_result(3, ns="db.$cmd.aggregate"),
        ]
    )
    coll = _FakeCollection(client)
    for _ in range(3):
        executor.execute_command(coll, {"aggregate": "coll", "pipeline": [], "cursor": {}})

    executor.close_tracked_cursors()

    assert sorted(_kills(client), key=lambda k: k[1]["killCursors"]) == [
        ("db", {"killCursors": "$cmd.aggregate", "cursors": [Int64(3)]}),
        ("db", {"killCursors": "coll", "cursors": [Int64(1), Int64(2)]}),
    ]


@pytest.mark.unit
def test_admin_command_cursor_is_killed_on_its_namespace():
    client = _FakeClient(results=[_cursor_result(7, ns="admin.$cmd.aggregate")])
    executor.execute_admin_command(
        _FakeCollection(client), {"aggregate": 1, "pipeline": [], "cursor": {}}
    )

    executor.close_tracked_cursors()

    assert _kills(client) == [("admin", {"killCursors": "$cmd.aggregate", "cursors": [Int64(7)]})]


@pytest.mark.unit
def test_close_clears_registry_and_is_idempotent():
    client = _FakeClient(results=[_cursor_result(5)])
    executor.execute_command(_FakeCollection(client), {"find": "coll", "batchSize": 1})

    executor.close_tracked_cursors()
    executor.close_tracked_cursors()

    assert len(_kills(client)) == 1


@pytest.mark.unit
def test_kill_failure_is_ignored():
    client = _FakeClient(results=[_cursor_result(9)])
    executor.execute_command(_FakeCollection(client), {"find": "coll", "batchSize": 1})
    client.fail_with = RuntimeError("namespace dropped")

    executor.close_tracked_cursors()

    assert executor._tracked_cursors == []
