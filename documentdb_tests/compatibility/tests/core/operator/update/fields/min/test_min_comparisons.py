"""
Comparison tests for $min update field operator.

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

_EARLY = datetime(2023, 1, 1, tzinfo=timezone.utc)
_LATE = datetime(2025, 12, 31, tzinfo=timezone.utc)

# Property [Core Comparison]: $min updates only when specified value is strictly less than current.
TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "updates_when_specified_less",
        setup_docs=[{"_id": 1, "score": 950}],
        query={"_id": 1},
        update={"$min": {"score": 800}},
        expected={"_id": 1, "score": 800},
        msg="$min should update field when specified (800) < current (950)",
    ),
    UpdateTestCase(
        "no_update_when_specified_greater",
        setup_docs=[{"_id": 1, "score": 800}],
        query={"_id": 1},
        update={"$min": {"score": 950}},
        expected={"_id": 1, "score": 800},
        msg="$min should leave field unchanged when specified (950) > current (800)",
    ),
    UpdateTestCase(
        "no_update_when_equal",
        setup_docs=[{"_id": 1, "score": 800}],
        query={"_id": 1},
        update={"$min": {"score": 800}},
        expected={"_id": 1, "score": 800},
        msg="$min should not update when specified equals current (equal is NOT less)",
    ),
    UpdateTestCase(
        "empty_operand_no_op",
        setup_docs=[{"_id": 1, "score": 100}],
        query={"_id": 1},
        update={"$min": {}},
        expected={"_id": 1, "score": 100},
        msg="$min with empty operand {} should leave document unchanged",
    ),
    UpdateTestCase(
        "null_specified_numeric_current_updates",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$min": {"val": None}},
        expected={"_id": 1, "val": None},
        msg="$min with specified null, current numeric should update (null < numbers)",
    ),
    UpdateTestCase(
        "null_specified_null_current_unchanged",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$min": {"val": None}},
        expected={"_id": 1, "val": None},
        msg="$min with specified null, current null should not update (equal)",
    ),
    UpdateTestCase(
        "number_specified_null_current_unchanged",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$min": {"val": 5}},
        expected={"_id": 1, "val": None},
        msg="$min with current null, specified number should not update (null < Number)",
    ),
    UpdateTestCase(
        "string_specified_null_current_unchanged",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$min": {"val": "hello"}},
        expected={"_id": 1, "val": None},
        msg="$min with current null, specified string should not update (null < String)",
    ),
    # Date wiring (1 representative case per §19).
    UpdateTestCase(
        "date_earlier_updates",
        setup_docs=[{"_id": 1, "val": _LATE}],
        query={"_id": 1},
        update={"$min": {"val": _EARLY}},
        expected={"_id": 1, "val": _EARLY},
        msg="$min with earlier date < current date should update",
    ),
    # String wiring (1 representative case per §19).
    UpdateTestCase(
        "string_less_updates",
        setup_docs=[{"_id": 1, "val": "b"}],
        query={"_id": 1},
        update={"$min": {"val": "a"}},
        expected={"_id": 1, "val": "a"},
        msg="$min comparing 'b' with 'a' should update to 'a'",
    ),
    UpdateTestCase(
        "int32_to_int64_type_change",
        setup_docs=[{"_id": 1, "val": Int64(20)}],
        query={"_id": 1},
        update={"$min": {"val": 10}},
        expected={"_id": 1, "val": 10},
        msg="$min updating Int64 to Int32 should store as Int32",
    ),
    UpdateTestCase(
        "int32_to_double_type_change",
        setup_docs=[{"_id": 1, "val": 20}],
        query={"_id": 1},
        update={"$min": {"val": 10.5}},
        expected={"_id": 1, "val": 10.5},
        msg="$min updating Int32 to Double should store as Double",
    ),
    UpdateTestCase(
        "double_to_decimal128_type_change",
        setup_docs=[{"_id": 1, "val": 20.5}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("10.5")}},
        expected={"_id": 1, "val": Decimal128("10.5")},
        msg="$min updating Double to Decimal128 should store as Decimal128",
    ),
    UpdateTestCase(
        "no_update_type_unchanged",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$min": {"val": Int64(100)}},
        expected={"_id": 1, "val": 5},
        msg="$min where no update occurs should leave type unchanged",
    ),
    UpdateTestCase(
        "creates_field_with_decimal128",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("42.5")}},
        expected={"_id": 1, "val": Decimal128("42.5")},
        msg="$min creating non-existent field with Decimal128 should store as Decimal128",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_min_comparisons(collection, test: UpdateTestCase):
    """Test $min comparison behavior produces expected document."""
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
