"""Tests for $millisecond null propagation and non-date type rejection."""

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_DATE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    MISSING,
)

# Property [Null Propagation]: a null or missing date resolves to null rather than an error.
MILLISECOND_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_date",
        doc={"date": None},
        expression={"$millisecond": "$date"},
        expected=None,
        msg="$millisecond should return null for a null date",
    ),
    ExpressionTestCase(
        "missing_date",
        expression={"$millisecond": MISSING},
        expected=None,
        msg="$millisecond should return null when the date references a missing field",
    ),
]

# Property [Type Rejection]: any non-date input type is rejected with a type-mismatch error.
MILLISECOND_TYPE_REJECTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_date",
        doc={"date": "not-a-date"},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a string as the date input",
    ),
    ExpressionTestCase(
        "empty_string_date",
        doc={"date": ""},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject an empty string as the date input",
    ),
    ExpressionTestCase(
        "integer_date",
        doc={"date": 42},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject an int as the date input",
    ),
    ExpressionTestCase(
        "int64_date",
        doc={"date": Int64(42)},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject an int64 as the date input",
    ),
    ExpressionTestCase(
        "double_date",
        doc={"date": 3.14},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a double as the date input",
    ),
    ExpressionTestCase(
        "decimal128_date",
        doc={"date": Decimal128("42")},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a decimal128 as the date input",
    ),
    ExpressionTestCase(
        "boolean_date",
        doc={"date": True},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a boolean as the date input",
    ),
    ExpressionTestCase(
        "array_date",
        doc={"date": [1, 2, 3]},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject an array as the date input",
    ),
    ExpressionTestCase(
        "empty_array_date",
        doc={"date": []},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject an empty array as the date input",
    ),
    ExpressionTestCase(
        "object_date",
        doc={"date": {"a": 1}},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject an object as the date input",
    ),
    ExpressionTestCase(
        "empty_object_date",
        doc={"date": {}},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject an empty object as the date input",
    ),
    ExpressionTestCase(
        "float_nan_date",
        doc={"date": FLOAT_NAN},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a float NaN as the date input",
    ),
    ExpressionTestCase(
        "decimal128_nan_date",
        doc={"date": DECIMAL128_NAN},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a decimal128 NaN as the date input",
    ),
    ExpressionTestCase(
        "float_inf_date",
        doc={"date": FLOAT_INFINITY},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a float infinity as the date input",
    ),
    ExpressionTestCase(
        "float_neg_inf_date",
        doc={"date": FLOAT_NEGATIVE_INFINITY},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a float negative infinity as the date input",
    ),
    ExpressionTestCase(
        "decimal128_inf_date",
        doc={"date": DECIMAL128_INFINITY},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a decimal128 infinity as the date input",
    ),
    ExpressionTestCase(
        "decimal128_neg_inf_date",
        doc={"date": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a decimal128 negative infinity as the date input",
    ),
    ExpressionTestCase(
        "regex_date",
        doc={"date": Regex(".*")},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject a regex as the date input",
    ),
    ExpressionTestCase(
        "minkey_date",
        doc={"date": MinKey()},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject MinKey as the date input",
    ),
    ExpressionTestCase(
        "maxkey_date",
        doc={"date": MaxKey()},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject MaxKey as the date input",
    ),
    ExpressionTestCase(
        "bindata_date",
        doc={"date": Binary(b"")},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject binary data as the date input",
    ),
    ExpressionTestCase(
        "javascript_date",
        doc={"date": Code("function(){}")},
        expression={"$millisecond": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should reject JavaScript code as the date input",
    ),
]

MILLISECOND_NULL_AND_TYPE_ERROR_TESTS: list[ExpressionTestCase] = (
    MILLISECOND_NULL_TESTS + MILLISECOND_TYPE_REJECTION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MILLISECOND_NULL_AND_TYPE_ERROR_TESTS))
def test_millisecond_null_and_type_errors(collection, test_case: ExpressionTestCase):
    """Test $millisecond null propagation and non-date type rejection."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
