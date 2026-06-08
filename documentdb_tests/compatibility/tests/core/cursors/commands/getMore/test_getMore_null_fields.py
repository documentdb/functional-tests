"""Tests for getMore field presence and recognition behavior."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    CursorCommandContext,
    CursorCommandTestCase,
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    MISSING_FIELD_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Unrecognized Fields]: any field not in the getMore command (whether
# a find-only field or an arbitrary unknown field) produces
# UNRECOGNIZED_COMMAND_FIELD_ERROR.
GETMORE_UNRECOGNIZED_FIELD_ERROR_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "unrecognized_find_only_field",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "filter": {"x": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="getMore should reject a find-only field",
    ),
    CursorCommandTestCase(
        "unrecognized_arbitrary_field",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "unknownField": 123,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="getMore should reject an arbitrary unknown field",
    ),
]

# Property [Null Required Fields Error]: getMore and collection fields set to
# null are treated as missing required fields and produce MISSING_FIELD_ERROR.
GETMORE_NULL_REQUIRED_FIELD_ERROR_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "null_getmore_field",
        cursor_count=0,
        command=lambda ctx: {"getMore": None, "collection": ctx.collection},
        error_code=MISSING_FIELD_ERROR,
        msg="getMore should reject null getMore field as missing required field",
    ),
    CursorCommandTestCase(
        "null_collection_field",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {"getMore": ctx.cursors[0], "collection": None},
        error_code=MISSING_FIELD_ERROR,
        msg="getMore should reject null collection field as missing required field",
    ),
    CursorCommandTestCase(
        "missing_collection_field",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {"getMore": ctx.cursors[0]},
        error_code=MISSING_FIELD_ERROR,
        msg="getMore should reject omitted collection field as missing required field",
    ),
]

GETMORE_NULL_TESTS: list[CursorCommandTestCase] = (
    GETMORE_UNRECOGNIZED_FIELD_ERROR_TESTS + GETMORE_NULL_REQUIRED_FIELD_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(GETMORE_NULL_TESTS))
def test_getMore_field_presence(collection, test_case: CursorCommandTestCase):
    """Test getMore field presence and recognition behavior."""
    collection.insert_many([{"_id": i, "v": i} for i in range(5)])
    cursors = open_find_cursors(
        collection, test_case.cursor_count, batch_size=test_case.find_batch_size
    )
    ctx = CursorCommandContext.from_collection(collection, cursors=cursors)
    result = execute_command(collection, test_case.build_command(ctx))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
