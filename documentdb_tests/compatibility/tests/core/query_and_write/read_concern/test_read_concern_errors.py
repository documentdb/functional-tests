"""readConcern rejection cases with find: bad levels, unknown fields, topology, afterClusterTime."""

from typing import Any, Dict, cast

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    NOT_A_REPLICA_SET_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_REQUIRES_STANDALONE = (pytest.mark.requires(cluster_read_concern=False),)
_REQUIRES_REPLICA_SET = (pytest.mark.requires(cluster_read_concern=True),)

INVALID_LEVEL_STRING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_rejects_empty_string_level",
        command={"filter": {}, "readConcern": {"level": ""}},
        error_code=BAD_VALUE_ERROR,
        msg="find should reject empty readConcern level string.",
    ),
    CommandTestCase(
        "find_rejects_unknown_level_string",
        command={"filter": {}, "readConcern": {"level": "invalid"}},
        error_code=BAD_VALUE_ERROR,
        msg="find should reject unrecognized readConcern level string 'invalid'.",
    ),
    CommandTestCase(
        "find_rejects_uppercase_level",
        command={"filter": {}, "readConcern": {"level": "LOCAL"}},
        error_code=BAD_VALUE_ERROR,
        msg="find should reject uppercase readConcern level 'LOCAL'.",
    ),
    CommandTestCase(
        "find_rejects_mixed_case_level",
        command={"filter": {}, "readConcern": {"level": "Majority"}},
        error_code=BAD_VALUE_ERROR,
        msg="find should reject mixed-case readConcern level 'Majority'.",
    ),
    CommandTestCase(
        "find_rejects_nonexistent_level",
        command={"filter": {}, "readConcern": {"level": "strong"}},
        error_code=BAD_VALUE_ERROR,
        msg="find should reject nonexistent readConcern level 'strong'.",
    ),
    CommandTestCase(
        "find_rejects_null_byte_in_level",
        command={"filter": {}, "readConcern": {"level": "local\x00extra"}},
        error_code=BAD_VALUE_ERROR,
        msg="find should reject null byte in readConcern level string.",
    ),
]

UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_rejects_unknown_field_no_level",
        command={"filter": {}, "readConcern": {"unknownField": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="find should reject readConcern with unknown field and no level.",
    ),
    CommandTestCase(
        "find_rejects_extra_field_with_valid_level",
        command={"filter": {}, "readConcern": {"level": "local", "unknownField": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="find should reject readConcern with extra unknown field.",
    ),
]


AFTER_CLUSTER_TIME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_rejects_afterClusterTime_string",
        command={"filter": {}, "readConcern": {"level": "local", "afterClusterTime": "invalid"}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject non-Timestamp afterClusterTime (string).",
        marks=_REQUIRES_REPLICA_SET,
    ),
    CommandTestCase(
        "find_rejects_afterClusterTime_integer",
        command={"filter": {}, "readConcern": {"level": "local", "afterClusterTime": 12345}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject non-Timestamp afterClusterTime (integer).",
        marks=_REQUIRES_REPLICA_SET,
    ),
    CommandTestCase(
        "find_rejects_afterClusterTime_null",
        command={"filter": {}, "readConcern": {"level": "local", "afterClusterTime": None}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject non-Timestamp afterClusterTime (null).",
        marks=_REQUIRES_REPLICA_SET,
    ),
]

# 'snapshot' and 'linearizable' both require a replicated topology and are rejected on standalone.
REPLICA_SET_ONLY_LEVEL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_rejects_snapshot_on_standalone",
        docs=[{"_id": 1}],
        command={"filter": {}, "readConcern": {"level": "snapshot"}},
        error_code=NOT_A_REPLICA_SET_ERROR,
        msg="readConcern 'snapshot' should be rejected on a standalone (not a replica set).",
        marks=_REQUIRES_STANDALONE,
    ),
    CommandTestCase(
        "find_rejects_linearizable_on_standalone",
        docs=[{"_id": 1}],
        command={"filter": {}, "readConcern": {"level": "linearizable"}},
        error_code=NOT_A_REPLICA_SET_ERROR,
        msg="readConcern 'linearizable' should be rejected on a standalone (not a replica set).",
        marks=_REQUIRES_STANDALONE,
    ),
]

ERROR_TESTS: list[CommandTestCase] = (
    INVALID_LEVEL_STRING_TESTS
    + UNKNOWN_FIELD_TESTS
    + REPLICA_SET_ONLY_LEVEL_TESTS
    + AFTER_CLUSTER_TIME_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_read_concern_rejected(collection, test: CommandTestCase):
    """Test readConcern rejection cases return the expected error code."""
    collection = test.prepare(collection.database, collection)
    find_body = cast(Dict[str, Any], test.command)
    result = execute_command(collection, {"find": collection.name, **find_body})
    assertResult(result, error_code=test.error_code, msg=test.msg)
