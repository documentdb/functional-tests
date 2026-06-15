"""
Type conversion tests for $mul update field operator.

Tests that numeric type promotion follows numeric type-promotion rules
for all 16 combinations of field type × multiplier type.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int32_x_int32",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$mul": {"val": 3}},
        expected={"_id": 1, "val": 15},
        msg="int32 × int32 should produce int32",
    ),
    UpdateTestCase(
        "int32_x_int64",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(3)}},
        expected={"_id": 1, "val": Int64(15)},
        msg="int32 × int64 should produce int64",
    ),
    UpdateTestCase(
        "int32_x_double",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$mul": {"val": 2.5}},
        expected={"_id": 1, "val": 12.5},
        msg="int32 × double should produce double",
    ),
    UpdateTestCase(
        "int32_x_double_zero",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$mul": {"val": 0.0}},
        expected={"_id": 1, "val": 0.0},
        msg="int32 × double(0.0) should produce double(0.0) via type promotion",
    ),
    UpdateTestCase(
        "int32_x_decimal128",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("3")}},
        expected={"_id": 1, "val": Decimal128("15")},
        msg="int32 × decimal128 should produce decimal128",
    ),
    UpdateTestCase(
        "int64_x_int32",
        setup_docs=[{"_id": 1, "val": Int64(5)}],
        query={"_id": 1},
        update={"$mul": {"val": 3}},
        expected={"_id": 1, "val": Int64(15)},
        msg="int64 × int32 should produce int64",
    ),
    UpdateTestCase(
        "int64_x_int64",
        setup_docs=[{"_id": 1, "val": Int64(5)}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(3)}},
        expected={"_id": 1, "val": Int64(15)},
        msg="int64 × int64 should produce int64",
    ),
    UpdateTestCase(
        "int64_x_double",
        setup_docs=[{"_id": 1, "val": Int64(5)}],
        query={"_id": 1},
        update={"$mul": {"val": 2.5}},
        expected={"_id": 1, "val": 12.5},
        msg="int64 × double should produce double",
    ),
    UpdateTestCase(
        "int64_x_decimal128",
        setup_docs=[{"_id": 1, "val": Int64(5)}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("3")}},
        expected={"_id": 1, "val": Decimal128("15")},
        msg="int64 × decimal128 should produce decimal128",
    ),
    UpdateTestCase(
        "double_x_int32",
        setup_docs=[{"_id": 1, "val": 2.5}],
        query={"_id": 1},
        update={"$mul": {"val": 2}},
        expected={"_id": 1, "val": 5.0},
        msg="double × int32 should produce double",
    ),
    UpdateTestCase(
        "double_x_int64",
        setup_docs=[{"_id": 1, "val": 2.5}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(2)}},
        expected={"_id": 1, "val": 5.0},
        msg="double × int64 should produce double",
    ),
    UpdateTestCase(
        "double_x_double",
        setup_docs=[{"_id": 1, "val": 2.5}],
        query={"_id": 1},
        update={"$mul": {"val": 3.0}},
        expected={"_id": 1, "val": 7.5},
        msg="double × double should produce double",
    ),
    UpdateTestCase(
        "double_x_decimal128",
        setup_docs=[{"_id": 1, "val": 2.5}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("2")}},
        expected={"_id": 1, "val": Decimal128("5.00000000000000")},
        msg="double × decimal128 should produce decimal128",
    ),
    UpdateTestCase(
        "decimal128_x_int32",
        setup_docs=[{"_id": 1, "val": Decimal128("5")}],
        query={"_id": 1},
        update={"$mul": {"val": 3}},
        expected={"_id": 1, "val": Decimal128("15")},
        msg="decimal128 × int32 should produce decimal128",
    ),
    UpdateTestCase(
        "decimal128_x_int64",
        setup_docs=[{"_id": 1, "val": Decimal128("5")}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(3)}},
        expected={"_id": 1, "val": Decimal128("15")},
        msg="decimal128 × int64 should produce decimal128",
    ),
    UpdateTestCase(
        "decimal128_x_double",
        setup_docs=[{"_id": 1, "val": Decimal128("5")}],
        query={"_id": 1},
        update={"$mul": {"val": 2.0}},
        expected={"_id": 1, "val": Decimal128("10.00000000000000")},
        msg="decimal128 × double should produce decimal128",
    ),
    UpdateTestCase(
        "decimal128_x_decimal128",
        setup_docs=[{"_id": 1, "val": Decimal128("5")}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("3")}},
        expected={"_id": 1, "val": Decimal128("15")},
        msg="decimal128 × decimal128 should produce decimal128",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_mul_type_conversion(collection, test: UpdateTestCase):
    """Test $mul numeric type conversion produces correct result type."""
    collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
