"""
Core behavior tests for $currentDate update field operator.

Tests argument handling (empty, single, multiple fields) and
temporal consistency.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gte, IsType

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

MULTI_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "mixed_type_specifications",
        setup_docs=[{"_id": 1, "name": "test"}],
        query={"_id": 1},
        update={
            "$currentDate": {
                "a": True,
                "b": {"$type": "timestamp"},
                "c": {"$type": "date"},
            }
        },
        expected={"a": IsType("date"), "b": IsType("timestamp"), "c": IsType("date")},
        msg="Multiple fields should each get their specified type",
    ),
    UpdateTestCase(
        "all_boolean_true",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"x": True, "y": True, "z": True}},
        expected={"x": IsType("date"), "y": IsType("date"), "z": IsType("date")},
        msg="All fields with true should be Date type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MULTI_FIELD_TESTS))
def test_currentDate_multiple_fields(collection, test: UpdateTestCase):
    """Test $currentDate with multiple fields applies the correct type to each."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertProperties(result, test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [Temporal Consistency]: sequential $currentDate updates are monotonic
# ---------------------------------------------------------------------------


def test_currentDate_sequential_updates_monotonic(collection):
    """Test sequential $currentDate updates on the same field are monotonically non-decreasing."""
    collection.insert_one({"_id": 1})

    # First update sets the field to the current date.
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"ts": True}}}],
        },
    )
    first = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    first_ts = first.get("cursor", {}).get("firstBatch", [])[0].get("ts")

    # Second update on the same field should produce a date at or after the first.
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"ts": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"ts": [IsType("date"), Gte(first_ts)]},
        msg="A later $currentDate update should produce a date >= the earlier one",
    )
