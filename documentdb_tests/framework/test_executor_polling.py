"""Unit tests for execute_command_until in the executor (no database needed)."""

import pytest
from pymongo.errors import OperationFailure

from documentdb_tests.framework import executor


class _FakeDatabase:
    def __init__(self, results):
        self.results = list(results)
        self.calls = 0
        self.client = None

    def command(self, command, **kwargs):
        self.calls += 1
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        if isinstance(result, Exception):
            raise result
        return result


class _FakeCollection:
    def __init__(self, results):
        self.database = _FakeDatabase(results)
        self.name = "coll"


def _ready(result):
    return result.get("ready") is True


@pytest.mark.unit
def test_first_accepted_result_runs_command_once():
    collection = _FakeCollection([{"ready": True, "ok": 1.0}])
    result = executor.execute_command_until(collection, {"ping": 1}, _ready, interval=0)
    assert result == {"ready": True, "ok": 1.0}
    assert collection.database.calls == 1


@pytest.mark.unit
def test_polls_until_result_is_accepted():
    collection = _FakeCollection([{"ready": False}, {"ready": False}, {"ready": True}])
    result = executor.execute_command_until(collection, {"ping": 1}, _ready, interval=0)
    assert result == {"ready": True}
    assert collection.database.calls == 3


@pytest.mark.unit
def test_error_is_returned_without_polling():
    error = OperationFailure("boom", code=2)
    collection = _FakeCollection([error])
    calls = []
    result = executor.execute_command_until(
        collection, {"ping": 1}, lambda r: calls.append(r) or False, interval=0
    )
    assert result is error
    assert collection.database.calls == 1
    assert calls == []


@pytest.mark.unit
def test_timeout_returns_last_result():
    collection = _FakeCollection([{"ready": False}])
    result = executor.execute_command_until(
        collection, {"ping": 1}, _ready, timeout=0.05, interval=0.01
    )
    assert result == {"ready": False}
    assert collection.database.calls >= 2
