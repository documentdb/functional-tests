import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [writeConcern Acceptance]: drop accepts valid writeConcern options.
DROP_WRITE_CONCERN_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w1",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "writeConcern": {"w": 1}},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with w:1",
    ),
    CommandTestCase(
        "majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "writeConcern": {"w": "majority"}},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with w:majority",
    ),
    CommandTestCase(
        "w0",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "writeConcern": {"w": 0}},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with w:0",
    ),
    CommandTestCase(
        "wtimeout",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "writeConcern": {"w": 1, "wtimeout": 1000}},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with wtimeout",
    ),
    CommandTestCase(
        "journal",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "writeConcern": {"w": 1, "j": True}},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with j:true",
    ),
    CommandTestCase(
        "empty_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "writeConcern": {}},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with empty writeConcern",
    ),
]

# Property [writeConcern Rejection]: drop rejects invalid writeConcern values.
DROP_WRITE_CONCERN_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "non_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "writeConcern": "invalid"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Non-object writeConcern should fail with 14",
    ),
    CommandTestCase(
        "negative_w",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "writeConcern": {"w": -1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:-1 should fail with error code 9",
    ),
]

# Property [comment Acceptance]: drop accepts comment of any BSON type.
DROP_COMMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "comment": "dropping collection"},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with string comment",
    ),
    CommandTestCase(
        "integer",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "comment": 42},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with integer comment",
    ),
    CommandTestCase(
        "object",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "comment": {"reason": "cleanup"}},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with object comment",
    ),
    CommandTestCase(
        "array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "comment": [1, 2, 3]},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with array comment",
    ),
    CommandTestCase(
        "boolean",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "comment": True},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with boolean comment",
    ),
]

# Property [Unrecognized Field Rejection]: drop rejects unrecognized fields.
DROP_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection, "unknownField": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field should fail with 40415",
    ),
]

DROP_OPTIONS_TESTS: list[CommandTestCase] = (
    DROP_WRITE_CONCERN_SUCCESS_TESTS
    + DROP_WRITE_CONCERN_ERROR_TESTS
    + DROP_COMMENT_TESTS
    + DROP_UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DROP_OPTIONS_TESTS))
def test_drop_options(database_client, collection, test):
    """Test drop command option acceptance and rejection."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
