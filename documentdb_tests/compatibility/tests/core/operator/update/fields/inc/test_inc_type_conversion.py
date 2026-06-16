"""
Numeric type conversion tests for $inc update field operator.

Tests all numeric type combinations (existing field type x increment type),
verifies correct output type promotion rules, and covers fractional-increment
promotion (e.g. int32 + 0.5 -> double).
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Conversion]: $inc produces output type following promotion rules:
# int32+int32->int32, int32+int64->int64, int32+double->double, int32+decimal128->decimal128,
# int64+int32->int64, int64+int64->int64, int64+double->double, int64+decimal128->decimal128,
# double+int32->double, double+int64->double, double+double->double, double+decimal128->decimal128,
# decimal128+int32->decimal128, decimal128+int64->decimal128, decimal128+double->decimal128,
# decimal128+decimal128->decimal128.
TYPE_CONVERSION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int32_plus_int32",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": 5}},
        expected={"_id": 1, "val": 15},
        msg="$inc should produce int32 from int32 + int32",
    ),
    UpdateTestCase(
        "int32_plus_int64",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": Int64(5)}},
        expected={"_id": 1, "val": Int64(15)},
        msg="$inc should produce int64 from int32 + int64",
    ),
    UpdateTestCase(
        "int32_plus_double",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": 2.5}},
        expected={"_id": 1, "val": 12.5},
        msg="$inc should produce double from int32 + double",
    ),
    UpdateTestCase(
        "int32_plus_decimal128",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("5")}},
        expected={"_id": 1, "val": Decimal128("15")},
        msg="$inc should produce decimal128 from int32 + decimal128",
    ),
    UpdateTestCase(
        "int64_plus_int32",
        setup_docs=[{"_id": 1, "val": Int64(10)}],
        query={"_id": 1},
        update={"$inc": {"val": 5}},
        expected={"_id": 1, "val": Int64(15)},
        msg="$inc should produce int64 from int64 + int32",
    ),
    UpdateTestCase(
        "int64_plus_int64",
        setup_docs=[{"_id": 1, "val": Int64(10)}],
        query={"_id": 1},
        update={"$inc": {"val": Int64(5)}},
        expected={"_id": 1, "val": Int64(15)},
        msg="$inc should produce int64 from int64 + int64",
    ),
    UpdateTestCase(
        "int64_plus_double",
        setup_docs=[{"_id": 1, "val": Int64(10)}],
        query={"_id": 1},
        update={"$inc": {"val": 2.5}},
        expected={"_id": 1, "val": 12.5},
        msg="$inc should produce double from int64 + double",
    ),
    UpdateTestCase(
        "int64_plus_decimal128",
        setup_docs=[{"_id": 1, "val": Int64(10)}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("5")}},
        expected={"_id": 1, "val": Decimal128("15")},
        msg="$inc should produce decimal128 from int64 + decimal128",
    ),
    UpdateTestCase(
        "double_plus_int32",
        setup_docs=[{"_id": 1, "val": 10.5}],
        query={"_id": 1},
        update={"$inc": {"val": 5}},
        expected={"_id": 1, "val": 15.5},
        msg="$inc should produce double from double + int32",
    ),
    UpdateTestCase(
        "double_plus_int64",
        setup_docs=[{"_id": 1, "val": 10.5}],
        query={"_id": 1},
        update={"$inc": {"val": Int64(5)}},
        expected={"_id": 1, "val": 15.5},
        msg="$inc should produce double from double + int64",
    ),
    UpdateTestCase(
        "double_plus_double",
        setup_docs=[{"_id": 1, "val": 10.5}],
        query={"_id": 1},
        update={"$inc": {"val": 2.5}},
        expected={"_id": 1, "val": 13.0},
        msg="$inc should produce double from double + double",
    ),
    UpdateTestCase(
        "double_plus_decimal128",
        setup_docs=[{"_id": 1, "val": 10.5}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("2.5")}},
        expected={"_id": 1, "val": Decimal128("13.0000000000000")},
        msg="$inc should produce decimal128 with trailing precision from double + decimal128",
    ),
    UpdateTestCase(
        "decimal128_plus_int32",
        setup_docs=[{"_id": 1, "val": Decimal128("10.5")}],
        query={"_id": 1},
        update={"$inc": {"val": 5}},
        expected={"_id": 1, "val": Decimal128("15.5")},
        msg="$inc should produce decimal128 from decimal128 + int32",
    ),
    UpdateTestCase(
        "decimal128_plus_int64",
        setup_docs=[{"_id": 1, "val": Decimal128("10.5")}],
        query={"_id": 1},
        update={"$inc": {"val": Int64(5)}},
        expected={"_id": 1, "val": Decimal128("15.5")},
        msg="$inc should produce decimal128 from decimal128 + int64",
    ),
    UpdateTestCase(
        "decimal128_plus_double",
        setup_docs=[{"_id": 1, "val": Decimal128("10.5")}],
        query={"_id": 1},
        update={"$inc": {"val": 2.5}},
        expected={"_id": 1, "val": Decimal128("13.00000000000000")},
        msg="$inc should produce decimal128 with trailing precision from decimal128 + double",
    ),
    UpdateTestCase(
        "decimal128_plus_decimal128",
        setup_docs=[{"_id": 1, "val": Decimal128("10.5")}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("2.5")}},
        expected={"_id": 1, "val": Decimal128("13.0")},
        msg="$inc should produce decimal128 from decimal128 + decimal128",
    ),
    UpdateTestCase(
        "int32_plus_fractional_double",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": 0.5}},
        expected={"_id": 1, "val": 10.5},
        msg="$inc should promote int32 to double when incrementing by fractional double",
    ),
    UpdateTestCase(
        "int64_plus_fractional_double",
        setup_docs=[{"_id": 1, "val": Int64(10)}],
        query={"_id": 1},
        update={"$inc": {"val": 0.5}},
        expected={"_id": 1, "val": 10.5},
        msg="$inc should promote int64 to double when incrementing by fractional double",
    ),
    UpdateTestCase(
        "int32_plus_fractional_decimal128",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("0.5")}},
        expected={"_id": 1, "val": Decimal128("10.5")},
        msg="$inc should promote int32 to decimal128 when incrementing by fractional decimal128",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TYPE_CONVERSION_TESTS))
def test_inc_type_conversion(collection, test: UpdateTestCase):
    """Test $inc numeric type promotion rules."""
    collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
