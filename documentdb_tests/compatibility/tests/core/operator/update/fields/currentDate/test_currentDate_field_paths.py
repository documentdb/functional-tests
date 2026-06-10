"""
Field path tests for $currentDate update field operator.

Tests field creation on non-existent fields, overwrite of existing fields,
dot notation traversal, array index targeting, and _id field behavior.
"""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Timestamp

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import IMMUTABLE_FIELD_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import IsType

# ---------------------------------------------------------------------------
# Property [Field Creation]: $currentDate creates non-existent fields
# ---------------------------------------------------------------------------

FIELD_CREATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "creates_missing_field_as_date",
        setup_docs=[{"_id": 1, "name": "test"}],
        query={"_id": 1},
        update={"$currentDate": {"lastModified": True}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should create non-existent field with Date",
    ),
    UpdateTestCase(
        "creates_missing_field_as_timestamp",
        setup_docs=[{"_id": 1, "name": "test"}],
        query={"_id": 1},
        update={"$currentDate": {"lastModified": {"$type": "timestamp"}}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should create non-existent field with Timestamp",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_CREATION_TESTS))
def test_currentDate_field_creation(collection, test: UpdateTestCase):
    """Test $currentDate creates non-existent fields."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


def test_currentDate_creates_field_with_date_type(collection):
    """Test $currentDate on non-existent field produces Date type."""
    collection.insert_one({"_id": 1})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"created": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(result, {"created": IsType("date")}, msg="Created field should be Date type")


def test_currentDate_creates_field_with_timestamp_type(collection):
    """Test $currentDate on non-existent field with $type:'timestamp' produces Timestamp type."""
    collection.insert_one({"_id": 1})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"created": {"$type": "timestamp"}}}}
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result, {"created": IsType("timestamp")}, msg="Created field should be Timestamp type"
    )


# ---------------------------------------------------------------------------
# Property [Overwrite]: $currentDate overwrites existing fields regardless of current type
# ---------------------------------------------------------------------------

OVERWRITE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "overwrite_int32",
        setup_docs=[{"_id": 1, "field": 42}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should overwrite int32 field",
    ),
    UpdateTestCase(
        "overwrite_string",
        setup_docs=[{"_id": 1, "field": "hello"}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should overwrite string field",
    ),
    UpdateTestCase(
        "overwrite_object",
        setup_docs=[{"_id": 1, "field": {"nested": 1}}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should overwrite object field",
    ),
    UpdateTestCase(
        "overwrite_array",
        setup_docs=[{"_id": 1, "field": [1, 2, 3]}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should overwrite array field",
    ),
    UpdateTestCase(
        "overwrite_null",
        setup_docs=[{"_id": 1, "field": None}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should overwrite null field",
    ),
    UpdateTestCase(
        "overwrite_bool",
        setup_docs=[{"_id": 1, "field": True}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "date"}}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should overwrite boolean field",
    ),
    UpdateTestCase(
        "overwrite_existing_date",
        setup_docs=[{"_id": 1, "field": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should overwrite existing Date field",
    ),
    UpdateTestCase(
        "overwrite_existing_timestamp",
        setup_docs=[{"_id": 1, "field": Timestamp(1000, 1)}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "timestamp"}}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should overwrite existing Timestamp field",
    ),
    UpdateTestCase(
        "overwrite_decimal128",
        setup_docs=[{"_id": 1, "field": Decimal128("3.14")}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate should overwrite Decimal128 field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OVERWRITE_TESTS))
def test_currentDate_overwrite(collection, test: UpdateTestCase):
    """Test $currentDate overwrites existing fields of any BSON type."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


def test_currentDate_overwrite_int32_produces_date(collection):
    """Test $currentDate overwriting int32 field produces Date type."""
    collection.insert_one({"_id": 1, "field": 42})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"field": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(result, {"field": IsType("date")}, msg="Overwritten int32 should become Date")


def test_currentDate_overwrite_string_produces_timestamp(collection):
    """Test $currentDate overwriting string field with $type:'timestamp' produces Timestamp."""
    collection.insert_one({"_id": 1, "field": "hello"})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"field": {"$type": "timestamp"}}}}
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result, {"field": IsType("timestamp")}, msg="Overwritten string should become Timestamp"
    )


# ---------------------------------------------------------------------------
# Property [Dot Notation]: $currentDate supports dot notation for embedded fields
# ---------------------------------------------------------------------------


def test_currentDate_dot_notation_embedded_field(collection):
    """Test $currentDate on embedded field via dot notation."""
    collection.insert_one({"_id": 1, "a": {"b": 5}})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"a.b": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result, {"a": {"b": IsType("date")}}, msg="Dot notation should set embedded field to Date"
    )


def test_currentDate_dot_notation_deeply_nested(collection):
    """Test $currentDate on deeply nested field via dot notation."""
    collection.insert_one({"_id": 1, "a": {"b": {"c": "old"}}})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"a.b.c": {"$type": "timestamp"}}}}
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"a": {"b": {"c": IsType("timestamp")}}},
        msg="Deep dot notation should produce Timestamp",
    )


def test_currentDate_dot_notation_creates_nested_path(collection):
    """Test $currentDate creates nested path when parent exists but child doesn't."""
    collection.insert_one({"_id": 1, "a": {}})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"a.b": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result, {"a": {"b": IsType("date")}}, msg="Should create nested field when parent exists"
    )


def test_currentDate_dot_notation_creates_full_path(collection):
    """Test $currentDate creates full nested path when no parent exists."""
    collection.insert_one({"_id": 1, "other": "data"})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"a.b": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(result, {"a": {"b": IsType("date")}}, msg="Should create full nested path")


def test_currentDate_array_index(collection):
    """Test $currentDate on array element by index via dot notation."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"arr.0": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(result, {"arr": {"0": IsType("date")}}, msg="Array index 0 should become Date")


# ---------------------------------------------------------------------------
# Property [_id Field]: $currentDate on _id field should error (immutable)
# ---------------------------------------------------------------------------


def test_currentDate_on_id_field_errors(collection):
    """Test $currentDate on _id field produces immutable field error."""
    collection.insert_one({"_id": 1, "name": "test"})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"_id": True}}}],
        },
    )
    assertFailureCode(
        result,
        IMMUTABLE_FIELD_ERROR,
        msg="$currentDate on _id should produce immutable field error",
    )
