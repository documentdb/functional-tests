"""Tests for $addToSet accumulator numeric type preservation during deduplication.

When numerically equivalent values of different BSON types are deduplicated,
verify which type survives in the result via $type projection.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property lists
# ---------------------------------------------------------------------------

# Property [Numeric Equivalence — Type Preservation]: when numerically equal values
# are deduplicated, verify which type survives via $type.
ADDTOSET_TYPE_PRESERVATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_pres_int32_then_int64",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$unwind": "$result"},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 5, "type": "int"}],
        msg="$addToSet should keep int type when int32 is inserted before int64",
    ),
    AccumulatorTestCase(
        "type_pres_int64_then_int32",
        docs=[{"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$unwind": "$result"},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Int64(5), "type": "long"}],
        msg="$addToSet should keep long type when int64 is inserted before int32",
    ),
    AccumulatorTestCase(
        "type_pres_double_then_int32",
        docs=[{"v": 3.0}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$unwind": "$result"},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 3.0, "type": "double"}],
        msg="$addToSet should keep double type when double is inserted before int32",
    ),
    AccumulatorTestCase(
        "type_pres_int32_then_double",
        docs=[{"v": 3}, {"v": 3.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$unwind": "$result"},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 3, "type": "int"}],
        msg="$addToSet should keep int type when int32 is inserted before double",
    ),
    AccumulatorTestCase(
        "type_pres_all_four_types",
        docs=[
            {"v": 1},
            {"v": Int64(1)},
            {"v": 1.0},
            {"v": Decimal128("1")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$unwind": "$result"},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 1, "type": "int"}],
        msg="$addToSet should keep int type when int32 is inserted first "
        "among all four numeric types",
    ),
    AccumulatorTestCase(
        "type_pres_decimal128_first",
        docs=[
            {"v": Decimal128("1")},
            {"v": 1},
            {"v": Int64(1)},
            {"v": 1.0},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$unwind": "$result"},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Decimal128("1"), "type": "decimal"}],
        msg="$addToSet should keep decimal type when Decimal128 is inserted "
        "first among all four numeric types",
    ),
]

# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_TYPE_PRESERVATION_TESTS))
def test_accumulator_addToSet_type_preservation(collection, test_case: AccumulatorTestCase):
    """Test $addToSet numeric type preservation during deduplication."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
