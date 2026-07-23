"""Tests for $isoDayOfWeek null propagation and non-date type rejection."""

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
ISODAYOFWEEK_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_date",
        doc={"date": None},
        expression={"$isoDayOfWeek": "$date"},
        expected=None,
        msg="$isoDayOfWeek should return null for a null date",
    ),
    ExpressionTestCase(
        "missing_date",
        expression={"$isoDayOfWeek": MISSING},
        expected=None,
        msg="$isoDayOfWeek should return null when the date references a missing field",
    ),
]

# Property [Type Rejection]: any non-date input type is rejected with a type-mismatch error.
ISODAYOFWEEK_TYPE_REJECTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_date",
        doc={"date": "not-a-date"},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a string as the date input",
    ),
    ExpressionTestCase(
        "integer_date",
        doc={"date": 123},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject an int as the date input",
    ),
    ExpressionTestCase(
        "int64_date",
        doc={"date": Int64(123)},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject an int64 as the date input",
    ),
    ExpressionTestCase(
        "double_date",
        doc={"date": 1.0},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a double as the date input",
    ),
    ExpressionTestCase(
        "decimal128_date",
        doc={"date": Decimal128("1")},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a decimal128 as the date input",
    ),
    ExpressionTestCase(
        "boolean_true_date",
        doc={"date": True},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a true boolean as the date input",
    ),
    ExpressionTestCase(
        "boolean_false_date",
        doc={"date": False},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a false boolean as the date input",
    ),
    ExpressionTestCase(
        "array_date",
        doc={"date": [1, 2, 3]},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject an array as the date input",
    ),
    ExpressionTestCase(
        "object_date",
        doc={"date": {"a": 1}},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject an object as the date input",
    ),
    ExpressionTestCase(
        "regex_date",
        doc={"date": Regex(".*")},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a regex as the date input",
    ),
    ExpressionTestCase(
        "minkey_date",
        doc={"date": MinKey()},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject MinKey as the date input",
    ),
    ExpressionTestCase(
        "maxkey_date",
        doc={"date": MaxKey()},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject MaxKey as the date input",
    ),
    ExpressionTestCase(
        "bindata_date",
        doc={"date": Binary(b"")},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject binary data as the date input",
    ),
    ExpressionTestCase(
        "javascript_date",
        doc={"date": Code("function(){}")},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject JavaScript code as the date input",
    ),
    ExpressionTestCase(
        "float_nan_date",
        doc={"date": FLOAT_NAN},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a float NaN as the date input",
    ),
    ExpressionTestCase(
        "decimal128_nan_date",
        doc={"date": DECIMAL128_NAN},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a decimal128 NaN as the date input",
    ),
    ExpressionTestCase(
        "float_inf_date",
        doc={"date": FLOAT_INFINITY},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a float infinity as the date input",
    ),
    ExpressionTestCase(
        "float_neg_inf_date",
        doc={"date": FLOAT_NEGATIVE_INFINITY},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a float negative infinity as the date input",
    ),
    ExpressionTestCase(
        "decimal128_inf_date",
        doc={"date": DECIMAL128_INFINITY},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a decimal128 infinity as the date input",
    ),
    ExpressionTestCase(
        "decimal128_neg_inf_date",
        doc={"date": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$isoDayOfWeek": "$date"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a decimal128 negative infinity as the date input",
    ),
]

ISODAYOFWEEK_NULL_AND_TYPE_ERROR_TESTS: list[ExpressionTestCase] = (
    ISODAYOFWEEK_NULL_TESTS + ISODAYOFWEEK_TYPE_REJECTION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISODAYOFWEEK_NULL_AND_TYPE_ERROR_TESTS))
def test_isoDayOfWeek_null_and_type_errors(collection, test_case: ExpressionTestCase):
    """Test $isoDayOfWeek null propagation and non-date type rejection."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
