"""readConcern acceptance with find: valid levels, default shapes, and valid afterClusterTime."""

from typing import Any, Dict, cast

import pytest
from bson import Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_TWO_DOCS = [{"_id": 1, "x": 1}, {"_id": 2, "x": 2}]

ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_accepts_local",
        docs=_TWO_DOCS,
        command={"filter": {}, "sort": {"_id": 1}, "readConcern": {"level": "local"}},
        expected=_TWO_DOCS,
        msg="find should accept readConcern level 'local'.",
    ),
    CommandTestCase(
        "find_accepts_available",
        docs=_TWO_DOCS,
        command={"filter": {}, "sort": {"_id": 1}, "readConcern": {"level": "available"}},
        expected=_TWO_DOCS,
        msg="find should accept readConcern level 'available'.",
    ),
    CommandTestCase(
        "find_accepts_majority",
        docs=_TWO_DOCS,
        command={"filter": {}, "sort": {"_id": 1}, "readConcern": {"level": "majority"}},
        expected=_TWO_DOCS,
        msg="find should accept readConcern level 'majority'.",
    ),
    CommandTestCase(
        "find_accepts_linearizable",
        docs=[{"_id": 1, "x": 1}],
        command={"filter": {"_id": 1}, "readConcern": {"level": "linearizable"}},
        expected=[{"_id": 1, "x": 1}],
        msg="find should accept readConcern level 'linearizable'.",
        marks=(pytest.mark.requires(cluster_read_concern=True),),
    ),
    CommandTestCase(
        "find_accepts_snapshot",
        docs=[{"_id": 1, "x": 1}],
        command={"filter": {"_id": 1}, "readConcern": {"level": "snapshot"}},
        expected=[{"_id": 1, "x": 1}],
        msg="find should accept readConcern level 'snapshot' on a replica set.",
        marks=(pytest.mark.requires(cluster_read_concern=True),),
    ),
    CommandTestCase(
        "find_accepts_empty_document",
        docs=[{"_id": 1, "x": 1}],
        command={"filter": {}, "readConcern": {}},
        expected=[{"_id": 1, "x": 1}],
        msg="find should accept empty readConcern document.",
    ),
    CommandTestCase(
        "find_accepts_null_read_concern",
        docs=[{"_id": 1, "x": 1}],
        command={"filter": {}, "readConcern": None},
        expected=[{"_id": 1, "x": 1}],
        msg="find should treat null readConcern as omitted.",
    ),
    CommandTestCase(
        "find_accepts_null_level",
        docs=[{"_id": 1, "x": 1}],
        command={"filter": {}, "readConcern": {"level": None}},
        expected=[{"_id": 1, "x": 1}],
        msg="find should treat readConcern {level: null} as implicit default.",
    ),
    CommandTestCase(
        "find_accepts_valid_after_cluster_time",
        docs=[{"_id": 1, "x": 1}],
        command={
            "filter": {"_id": 1},
            "readConcern": {"level": "local", "afterClusterTime": Timestamp(1, 1)},
        },
        expected=[{"_id": 1, "x": 1}],
        msg="find should accept a valid Timestamp afterClusterTime on a replica set.",
        marks=(pytest.mark.requires(cluster_read_concern=True),),
    ),
]


@pytest.mark.parametrize("test", pytest_params(ACCEPTANCE_TESTS))
def test_read_concern_level_acceptance(collection, test: CommandTestCase):
    """Test readConcern level (and default-equivalent shapes) is accepted by find."""
    collection = test.prepare(collection.database, collection)
    find_body = cast(Dict[str, Any], test.command)
    result = execute_command(collection, {"find": collection.name, **find_body})
    assertResult(result, expected=test.expected, msg=test.msg)
