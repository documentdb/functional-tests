"""
Error case tests for $inc update field operator.

Tests invalid increment types, invalid field types, conflict detection,
and dollar-prefixed field restrictions.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONFLICTING_UPDATE_OPERATORS_ERROR,
    DOLLAR_PREFIXED_FIELD_NAME_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_NON_NUMERIC_TYPES: list[tuple[str, object]] = [
    ("string", "hello"),
    ("bool_true", True),
    ("bool_false", False),
    ("null", None),
    ("object", {"a": 1}),
    ("empty_object", {}),
    ("array", [1, 2]),
    ("empty_array", []),
    ("binary", Binary(b"\x00")),
    ("objectid", ObjectId()),
    ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ("regex", Regex("abc")),
    ("timestamp", Timestamp(1, 1)),
    ("code", Code("function(){}")),
    ("minkey", MinKey()),
    ("maxkey", MaxKey()),
]

# Property [Invalid Increment Types]: $inc rejects non-numeric increment values.
INVALID_INCREMENT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        f"{name}_increment",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": value}},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$inc should reject {name} as increment value",
    )
    for name, value in _NON_NUMERIC_TYPES
]

# Property [Invalid Field Types]: $inc rejects incrementing non-numeric existing field values.
INVALID_FIELD_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        f"{name}_field",
        setup_docs=[{"_id": 1, "val": value}],
        query={"_id": 1},
        update={"$inc": {"val": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$inc should reject incrementing a {name} field",
    )
    for name, value in _NON_NUMERIC_TYPES
]

# Property [Conflict Detection]: $inc conflicts with other operators on same field or path.
CONFLICT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "inc_and_set_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": 1}, "$set": {"val": 10}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$inc should reject conflict with $set on same field",
    ),
    UpdateTestCase(
        "inc_and_mul_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": 1}, "$mul": {"val": 2}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$inc should reject conflict with $mul on same field",
    ),
    UpdateTestCase(
        "inc_path_prefix_conflict",
        setup_docs=[{"_id": 1, "x": {"y": 5}}],
        query={"_id": 1},
        update={"$inc": {"x.y": 1}, "$set": {"x": {}}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$inc should reject path prefix conflict with $set on parent",
    ),
]

# Property [Dollar-Prefixed Fields]: $inc rejects dollar-prefixed field names.
DOLLAR_PREFIX_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "dollar_prefixed_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"$field": 5}},
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="$inc should reject dollar-prefixed field name",
    ),
    UpdateTestCase(
        "bare_dollar_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"$": 5}},
        error_code=BAD_VALUE_ERROR,
        msg="$inc should reject bare '$' as field name",
    ),
]

ALL_ERROR_TESTS = (
    INVALID_INCREMENT_TESTS + INVALID_FIELD_TYPE_TESTS + CONFLICT_TESTS + DOLLAR_PREFIX_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_inc_errors(collection, test: UpdateTestCase):
    """Test $inc error cases produce expected error codes."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assert test.error_code is not None
    assertFailureCode(result, test.error_code, msg=test.msg)
