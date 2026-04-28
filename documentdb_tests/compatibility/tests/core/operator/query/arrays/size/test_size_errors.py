"""
Tests for $size error cases.

Covers invalid argument types, negative values, fractional values,
no range support, and boundary errors.
"""

from datetime import datetime

import pytest
from bson import Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex
from bson.binary import Binary
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DOUBLE_PRECISION_LOSS,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
    INT64_MIN,
    TS_EPOCH,
)

DOCS = [
    {"_id": 1, "a": []},
    {"_id": 2, "a": [1]},
    {"_id": 3, "a": [1, 2]},
    {"_id": 4, "a": [1, 2, 3]},
]

INVALID_ARGUMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="negative_int",
        filter={"a": {"$size": -1}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with -1 errors",
    ),
    QueryTestCase(
        id="negative_decimal128",
        filter={"a": {"$size": Decimal128("-1")}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with Decimal128('-1') errors",
    ),
    QueryTestCase(
        id="fractional_double",
        filter={"a": {"$size": 1.5}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with 1.5 errors",
    ),
    QueryTestCase(
        id="fractional_decimal128",
        filter={"a": {"$size": Decimal128("3.5")}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with Decimal128('3.5') errors",
    ),
    QueryTestCase(
        id="nan_double",
        filter={"a": {"$size": FLOAT_NAN}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with NaN errors",
    ),
    QueryTestCase(
        id="infinity",
        filter={"a": {"$size": FLOAT_INFINITY}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with Infinity errors",
    ),
    QueryTestCase(
        id="negative_infinity",
        filter={"a": {"$size": FLOAT_NEGATIVE_INFINITY}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with -Infinity errors",
    ),
    QueryTestCase(
        id="string",
        filter={"a": {"$size": "1"}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with string errors",
    ),
    QueryTestCase(
        id="bool_true",
        filter={"a": {"$size": True}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with true errors",
    ),
    QueryTestCase(
        id="null",
        filter={"a": {"$size": None}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with null errors",
    ),
    QueryTestCase(
        id="object",
        filter={"a": {"$size": {}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with object errors",
    ),
    QueryTestCase(
        id="array",
        filter={"a": {"$size": [1]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with array errors",
    ),
    QueryTestCase(
        id="objectid",
        filter={"a": {"$size": ObjectId()}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with ObjectId errors",
    ),
    QueryTestCase(
        id="bindata",
        filter={"a": {"$size": Binary(b"\x00")}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with BinData errors",
    ),
    QueryTestCase(
        id="date",
        filter={"a": {"$size": datetime(2020, 1, 1)}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with date errors",
    ),
    QueryTestCase(
        id="timestamp",
        filter={"a": {"$size": TS_EPOCH}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with Timestamp errors",
    ),
    QueryTestCase(
        id="regex",
        filter={"a": {"$size": Regex(".*")}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with regex errors",
    ),
    QueryTestCase(
        id="negative_int64",
        filter={"a": {"$size": Int64(-1)}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with NumberLong(-1) errors",
    ),
    QueryTestCase(
        id="negative_double",
        filter={"a": {"$size": -1.0}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with -1.0 errors",
    ),
    QueryTestCase(
        id="decimal128_nan",
        filter={"a": {"$size": DECIMAL128_NAN}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with Decimal128('NaN') errors",
    ),
    QueryTestCase(
        id="decimal128_infinity",
        filter={"a": {"$size": DECIMAL128_INFINITY}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with Decimal128('Infinity') errors",
    ),
    QueryTestCase(
        id="decimal128_huge",
        filter={"a": {"$size": Decimal128("9999999999999999999999")}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with Decimal128 exceeding int64 range errors",
    ),
    QueryTestCase(
        id="int64_min",
        filter={"a": {"$size": INT64_MIN}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with INT64_MIN errors",
    ),
    QueryTestCase(
        id="bool_false",
        filter={"a": {"$size": False}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with false errors",
    ),
    QueryTestCase(
        id="empty_string",
        filter={"a": {"$size": ""}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with empty string errors",
    ),
    QueryTestCase(
        id="minkey",
        filter={"a": {"$size": MinKey()}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with MinKey errors",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"a": {"$size": MaxKey()}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with MaxKey errors",
    ),
    QueryTestCase(
        id="double_precision_loss",
        filter={"a": {"$size": DOUBLE_PRECISION_LOSS}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with double 2^53+1 (precision loss) errors",
    ),
]

NO_RANGE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="range_gt",
        filter={"a": {"$size": {"$gt": 2}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size does not accept $gt range",
    ),
    QueryTestCase(
        id="range_gte",
        filter={"a": {"$size": {"$gte": 1}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size does not accept $gte range",
    ),
    QueryTestCase(
        id="range_lt",
        filter={"a": {"$size": {"$lt": 5}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size does not accept $lt range",
    ),
    QueryTestCase(
        id="range_lte",
        filter={"a": {"$size": {"$lte": 3}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size does not accept $lte range",
    ),
    QueryTestCase(
        id="range_ne",
        filter={"a": {"$size": {"$ne": 2}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size does not accept $ne",
    ),
    QueryTestCase(
        id="range_eq",
        filter={"a": {"$size": {"$eq": 2}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size does not accept $eq",
    ),
    QueryTestCase(
        id="range_in",
        filter={"a": {"$size": {"$in": [1, 2]}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size does not accept $in",
    ),
    QueryTestCase(
        id="range_nin",
        filter={"a": {"$size": {"$nin": [0]}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size does not accept $nin",
    ),
    QueryTestCase(
        id="range_add_expression",
        filter={"a": {"$size": {"$add": [1, 1]}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size does not accept $add expression",
    ),
]

BOUNDARY_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int64_max",
        filter={"a": {"$size": INT64_MAX}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with INT64_MAX errors (cannot represent in int)",
    ),
    QueryTestCase(
        id="javascript_code",
        filter={"a": {"$size": Code("return 1")}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with JavaScript Code BSON type errors",
    ),
    QueryTestCase(
        id="deeply_nested_array",
        filter={"a": {"$size": [[1]]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$size with nested array [[1]] errors",
    ),
]

ERROR_TESTS = INVALID_ARGUMENT_TESTS + NO_RANGE_TESTS + BOUNDARY_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_size_error(collection, test):
    """Parametrized test for $size invalid argument types and range rejection."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code)
