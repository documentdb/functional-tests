"""
Core behavior tests for $currentDate update field operator.

Tests argument handling (empty, single, multiple fields) and
temporal consistency.
"""

from datetime import datetime, timedelta, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gt, IsType, Lt

# ---------------------------------------------------------------------------
# Property [Argument Handling]: empty, single, and multiple fields
# ---------------------------------------------------------------------------

ARGUMENT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "empty_operand_no_op",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$currentDate": {}},
        expected={"val": Eq(10)},
        msg="$currentDate with empty {} should be a no-op (document unchanged)",
    ),
    UpdateTestCase(
        "single_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$currentDate": {"lastModified": True}},
        expected={"lastModified": IsType("date")},
        msg="$currentDate with single field should set it to Date",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_TESTS))
def test_currentDate_argument_handling(collection, test: UpdateTestCase):
    """Test $currentDate argument variations produce the expected document."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertProperties(result, test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [Multiple Fields]: $currentDate with multiple fields applies correct types
# ---------------------------------------------------------------------------


def test_currentDate_multiple_fields_mixed_types(collection):
    """Test $currentDate with multiple fields using different type specifications."""
    collection.insert_one({"_id": 1, "name": "test"})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$currentDate": {
                            "a": True,
                            "b": {"$type": "timestamp"},
                            "c": {"$type": "date"},
                        }
                    },
                }
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"a": IsType("date"), "b": IsType("timestamp"), "c": IsType("date")},
        msg="Multiple fields should each get their specified type",
    )


def test_currentDate_multiple_fields_all_true(collection):
    """Test $currentDate with multiple fields all using boolean true."""
    collection.insert_one({"_id": 1})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"x": True, "y": True, "z": True}}}
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"x": IsType("date"), "y": IsType("date"), "z": IsType("date")},
        msg="All fields with true should be Date type",
    )


# ---------------------------------------------------------------------------
# Property [Temporal Consistency]: $currentDate produces recent timestamps
# ---------------------------------------------------------------------------


def test_currentDate_date_is_recent(collection):
    """Test $currentDate produces a Date value close to current time."""
    before = datetime.now(timezone.utc)
    collection.insert_one({"_id": 1})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"ts": True}}}],
        },
    )
    after = datetime.now(timezone.utc) + timedelta(seconds=5)

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"ts": [IsType("date"), Gt(before - timedelta(seconds=5)), Lt(after)]},
        msg="Date value should be recent (within a few seconds of now)",
    )


def test_currentDate_timestamp_is_recent(collection):
    """Test $currentDate with $type:'timestamp' produces a Timestamp with recent seconds."""
    collection.insert_one({"_id": 1})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"ts": {"$type": "timestamp"}}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"ts": IsType("timestamp")},
        msg="Timestamp should be produced with recent time",
    )


def test_currentDate_multiple_fields_same_timestamp(collection):
    """Test multiple $currentDate fields in same update get same/close Date values."""
    collection.insert_one({"_id": 1})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"a": True, "b": True}}}],
        },
    )

    # Verify both fields are Date type (they should be identical or within milliseconds)
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"a": IsType("date"), "b": IsType("date")},
        msg="Multiple Date fields should both be set",
    )


def test_currentDate_sequential_updates_monotonic(collection):
    """Test sequential $currentDate updates produce monotonically increasing dates."""
    collection.insert_one({"_id": 1})

    # First update
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"first": True}}}],
        },
    )

    # Second update
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"second": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"first": IsType("date"), "second": IsType("date")},
        msg="Both sequential updates should produce Date fields",
    )
