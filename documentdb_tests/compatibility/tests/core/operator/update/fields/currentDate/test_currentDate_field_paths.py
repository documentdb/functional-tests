"""
Field path tests for $currentDate update field operator.

Tests field creation on non-existent fields, overwrite of existing fields,
dot notation traversal, array index targeting, and _id field behavior.
"""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Timestamp

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Exists, IsType, Len

# ---------------------------------------------------------------------------
# Property [Field Creation]: $currentDate creates non-existent fields
# ---------------------------------------------------------------------------

FIELD_CREATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "creates_missing_field_as_timestamp",
        setup_docs=[{"_id": 1, "name": "test"}],
        query={"_id": 1},
        update={"$currentDate": {"lastModified": {"$type": "timestamp"}}},
        expected={"lastModified": IsType("timestamp")},
        msg="$currentDate should create non-existent field as Timestamp",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_CREATION_TESTS))
def test_currentDate_field_creation(collection, test: UpdateTestCase):
    """Test $currentDate creates non-existent fields with the expected type."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertProperties(result, test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [Overwrite]: $currentDate overwrites existing fields regardless of current type
# ---------------------------------------------------------------------------

OVERWRITE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "overwrite_int32",
        setup_docs=[{"_id": 1, "field": 42}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"field": IsType("date")},
        msg="$currentDate should overwrite int32 field with Date",
    ),
    UpdateTestCase(
        "overwrite_string",
        setup_docs=[{"_id": 1, "field": "hello"}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"field": IsType("date")},
        msg="$currentDate should overwrite string field with Date",
    ),
    UpdateTestCase(
        "overwrite_object",
        setup_docs=[{"_id": 1, "field": {"nested": 1}}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"field": IsType("date")},
        msg="$currentDate should overwrite object field with Date",
    ),
    UpdateTestCase(
        "overwrite_array",
        setup_docs=[{"_id": 1, "field": [1, 2, 3]}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"field": IsType("date")},
        msg="$currentDate should overwrite array field with Date",
    ),
    UpdateTestCase(
        "overwrite_null",
        setup_docs=[{"_id": 1, "field": None}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"field": IsType("date")},
        msg="$currentDate should overwrite null field with Date",
    ),
    UpdateTestCase(
        "overwrite_bool",
        setup_docs=[{"_id": 1, "field": True}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "date"}}},
        expected={"field": IsType("date")},
        msg="$currentDate should overwrite boolean field with Date",
    ),
    UpdateTestCase(
        "overwrite_existing_date",
        setup_docs=[{"_id": 1, "field": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"field": IsType("date")},
        msg="$currentDate should overwrite existing Date field with Date",
    ),
    UpdateTestCase(
        "overwrite_existing_timestamp",
        setup_docs=[{"_id": 1, "field": Timestamp(1000, 1)}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "timestamp"}}},
        expected={"field": IsType("timestamp")},
        msg="$currentDate should overwrite existing Timestamp field with Timestamp",
    ),
    UpdateTestCase(
        "overwrite_decimal128",
        setup_docs=[{"_id": 1, "field": Decimal128("3.14")}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"field": IsType("date")},
        msg="$currentDate should overwrite Decimal128 field with Date",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OVERWRITE_TESTS))
def test_currentDate_overwrite(collection, test: UpdateTestCase):
    """Test $currentDate overwrites existing fields of any BSON type with the expected type."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertProperties(result, test.expected, msg=test.msg)


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


def test_currentDate_dotted_into_array_element_by_index_sets_field(collection):
    """Test $currentDate on a field within an array element via `tags.0.ts`."""
    collection.insert_one({"_id": 1, "tags": [{"a": 1}]})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"tags.0.ts": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"tags.0.ts": IsType("date")},
        msg="Dotted path through an array index should add a Date to that element",
    )


def test_currentDate_dotted_past_array_end_pads_with_nulls(collection):
    """`tags.10` on a 2-element array pads with nulls and sets a Date at index 10."""
    collection.insert_one({"_id": 1, "tags": [10, 20]})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"tags.10": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"tags": Len(11), "tags.0": Exists(), "tags.1": Exists(), "tags.10": IsType("date")},
        msg="Dotted path past the end of an array should pad with nulls and set the Date",
    )
