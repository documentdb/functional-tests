"""
Comparison tests for $max update field operator.

Tests core behavior, null handling, date comparisons, string comparisons,
and type preservation.
"""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_EARLY = datetime(2023, 1, 1, tzinfo=timezone.utc)
_MID = datetime(2023, 6, 15, tzinfo=timezone.utc)
_LATE = datetime(2025, 12, 31, tzinfo=timezone.utc)
_FAR_FUTURE = datetime(9999, 12, 31, tzinfo=timezone.utc)

TESTS: list[UpdateTestCase] = [
    # Core behavior
    UpdateTestCase(
        "updates_when_specified_greater",
        setup_docs=[{"_id": 1, "score": 800}],
        query={"_id": 1},
        update={"$max": {"score": 950}},
        expected={"_id": 1, "score": 950},
        msg="$max should update field when specified (950) > current (800)",
    ),
    UpdateTestCase(
        "no_update_when_specified_less",
        setup_docs=[{"_id": 1, "score": 950}],
        query={"_id": 1},
        update={"$max": {"score": 870}},
        expected={"_id": 1, "score": 950},
        msg="$max should leave field unchanged when specified (870) < current (950)",
    ),
    UpdateTestCase(
        "no_update_when_equal",
        setup_docs=[{"_id": 1, "score": 800}],
        query={"_id": 1},
        update={"$max": {"score": 800}},
        expected={"_id": 1, "score": 800},
        msg="$max should not update when specified equals current (equal is NOT greater)",
    ),
    UpdateTestCase(
        "empty_operand_no_op",
        setup_docs=[{"_id": 1, "score": 100}],
        query={"_id": 1},
        update={"$max": {}},
        expected={"_id": 1, "score": 100},
        msg="$max with empty operand {} should leave document unchanged",
    ),
    # Null handling
    UpdateTestCase(
        "null_specified_numeric_current_unchanged",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"val": None}},
        expected={"_id": 1, "val": 10},
        msg="$max with specified null, current numeric should not update (null < numbers)",
    ),
    UpdateTestCase(
        "null_specified_null_current_unchanged",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": None}},
        expected={"_id": 1, "val": None},
        msg="$max with specified null, current null should not update (equal)",
    ),
    UpdateTestCase(
        "number_specified_null_current_updates",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": 5}},
        expected={"_id": 1, "val": 5},
        msg="$max with current null, specified number should update (Number > null)",
    ),
    UpdateTestCase(
        "string_specified_null_current_updates",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": "hello"}},
        expected={"_id": 1, "val": "hello"},
        msg="$max with current null, specified string should update (String > null)",
    ),
    # Date comparisons
    UpdateTestCase(
        "date_later_updates",
        setup_docs=[{"_id": 1, "val": _EARLY}],
        query={"_id": 1},
        update={"$max": {"val": _LATE}},
        expected={"_id": 1, "val": _LATE},
        msg="$max with later date > current date should update",
    ),
    UpdateTestCase(
        "date_earlier_unchanged",
        setup_docs=[{"_id": 1, "val": _LATE}],
        query={"_id": 1},
        update={"$max": {"val": _EARLY}},
        expected={"_id": 1, "val": _LATE},
        msg="$max with earlier date < current date should not update",
    ),
    UpdateTestCase(
        "date_equal_unchanged",
        setup_docs=[{"_id": 1, "val": _MID}],
        query={"_id": 1},
        update={"$max": {"val": _MID}},
        expected={"_id": 1, "val": _MID},
        msg="$max with identical dates should not update",
    ),
    UpdateTestCase(
        "epoch_to_later_updates",
        setup_docs=[{"_id": 1, "val": _EPOCH}],
        query={"_id": 1},
        update={"$max": {"val": _EARLY}},
        expected={"_id": 1, "val": _EARLY},
        msg="$max should update from epoch to later date",
    ),
    UpdateTestCase(
        "far_future_date",
        setup_docs=[{"_id": 1, "val": _EARLY}],
        query={"_id": 1},
        update={"$max": {"val": _FAR_FUTURE}},
        expected={"_id": 1, "val": _FAR_FUTURE},
        msg="$max should update to far future date (year 9999)",
    ),
    # String comparisons
    UpdateTestCase(
        "string_greater_updates",
        setup_docs=[{"_id": 1, "val": "a"}],
        query={"_id": 1},
        update={"$max": {"val": "b"}},
        expected={"_id": 1, "val": "b"},
        msg="$max comparing 'a' with 'b' should update to 'b'",
    ),
    # Type preservation
    UpdateTestCase(
        "int32_to_int64_type_change",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"val": Int64(20)}},
        expected={"_id": 1, "val": Int64(20)},
        msg="$max updating Int32 to Int64 should store as Int64",
    ),
    UpdateTestCase(
        "int32_to_double_type_change",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"val": 20.5}},
        expected={"_id": 1, "val": 20.5},
        msg="$max updating Int32 to Double should store as Double",
    ),
    UpdateTestCase(
        "double_to_decimal128_type_change",
        setup_docs=[{"_id": 1, "val": 10.5}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("20.5")}},
        expected={"_id": 1, "val": Decimal128("20.5")},
        msg="$max updating Double to Decimal128 should store as Decimal128",
    ),
    UpdateTestCase(
        "no_update_type_unchanged",
        setup_docs=[{"_id": 1, "val": 100}],
        query={"_id": 1},
        update={"$max": {"val": Int64(5)}},
        expected={"_id": 1, "val": 100},
        msg="$max where no update occurs should leave type unchanged",
    ),
    UpdateTestCase(
        "creates_field_with_decimal128",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("42.5")}},
        expected={"_id": 1, "val": Decimal128("42.5")},
        msg="$max creating non-existent field with Decimal128 should store as Decimal128",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_max_comparisons(collection, test: UpdateTestCase):
    """Test $max comparison behavior produces expected document."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
