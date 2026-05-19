"""Tests for cloneCollectionAsCapped writeConcern j and fsync validation."""

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ZERO

# Property [WriteConcern j Acceptance]: j accepts bool, numeric, and
# null values.
WRITECONCERN_J_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"j_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"j": v},
        },
        expected={"ok": 1.0},
        msg=f"j={id} should succeed",
    )
    for id, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("int32", 0),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", DECIMAL128_ZERO),
        ("null", None),
    ]
]

# Property [WriteConcern j Type Rejection]: j rejects non-coercible
# types with TYPE_MISMATCH_ERROR.
WRITECONCERN_J_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"j_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"j": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"j={id} should fail with type mismatch",
    )
    for id, val in [
        ("string", "true"),
        ("array", [1]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01")),
        ("regex", Regex("abc", "i")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [WriteConcern fsync Acceptance]: fsync accepts bool,
# numeric, and null values.
WRITECONCERN_FSYNC_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"fsync_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"fsync": v},
        },
        expected={"ok": 1.0},
        msg=f"fsync={id} should succeed",
    )
    for id, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("int32", 0),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", DECIMAL128_ZERO),
        ("null", None),
    ]
]

# Property [WriteConcern fsync Type Rejection]: fsync rejects
# non-coercible types with TYPE_MISMATCH_ERROR.
WRITECONCERN_FSYNC_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"fsync_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"fsync": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"fsync={id} should fail with type mismatch",
    )
    for id, val in [
        ("string", "true"),
        ("array", [1]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01")),
        ("regex", Regex("abc", "i")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [WriteConcern fsync+j Conflict]: specifying both fsync:true
# and j:true together produces FAILED_TO_PARSE_ERROR.
WRITECONCERN_FSYNC_J_CONFLICT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "fsync_true_j_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"fsync": True, "j": True},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="fsync:true and j:true together should fail with failed to parse",
    ),
]

WC_DURABILITY_TESTS: list[CommandTestCase] = (
    WRITECONCERN_J_ACCEPTANCE_TESTS
    + WRITECONCERN_J_TYPE_REJECTION_TESTS
    + WRITECONCERN_FSYNC_ACCEPTANCE_TESTS
    + WRITECONCERN_FSYNC_TYPE_REJECTION_TESTS
    + WRITECONCERN_FSYNC_J_CONFLICT_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WC_DURABILITY_TESTS))
def test_clone_collection_as_capped_wc_durability(database_client, collection, test):
    """Test cloneCollectionAsCapped writeConcern j and fsync validation."""
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
