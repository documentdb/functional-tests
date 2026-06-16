"""Tests for compact command boolean parameter type strictness."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [dryRun Type Strictness]: all non-bool BSON types for dryRun
# produce a type mismatch error; null is accepted and treated as omitted.
COMPACT_DRYRUN_TYPE_STRICTNESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "dryrun_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="int32 dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Int64 dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="double dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": Decimal128("1")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Decimal128 dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": "true"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="string dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": [True]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="array dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": {"x": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="object dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "dryRun": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="datetime dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": Timestamp(1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": Binary(b"\x01")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Binary subtype 0 dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": Code("x")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "dryRun": Code("x", {"a": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code with scope dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey dryRun should be rejected as wrong type",
    ),
    CommandTestCase(
        "dryrun_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey dryRun should be rejected as wrong type",
    ),
]

# Property [force Type Strictness]: all non-bool BSON types for force
# produce a type mismatch error; null is accepted and treated as omitted.
COMPACT_FORCE_TYPE_STRICTNESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "force_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="int32 force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Int64 force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="double force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": Decimal128("1")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Decimal128 force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": "true"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="string force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": [True]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="array force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": {"x": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="object force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "force": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="datetime force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": Timestamp(1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": Binary(b"\x01")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Binary subtype 0 force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": Code("x")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "force": Code("x", {"a": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code with scope force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey force should be rejected as wrong type",
    ),
    CommandTestCase(
        "force_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey force should be rejected as wrong type",
    ),
]

COMPACT_BOOL_TYPE_ERROR_TESTS: list[CommandTestCase] = (
    COMPACT_DRYRUN_TYPE_STRICTNESS_TESTS + COMPACT_FORCE_TYPE_STRICTNESS_TESTS
)


@pytest.mark.requires(unforced_compact=True)
@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_BOOL_TYPE_ERROR_TESTS))
def test_compact_bool_type_errors(database_client, collection, test):
    """Test compact command rejects non-bool types for dryRun and force."""
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
