from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_INFINITY,
    DOUBLE_MAX,
    DOUBLE_MIN,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Infinity Behavior]: positive infinity is greater than all finite
# numeric values, and negative infinity is less than all finite numeric values.
MIN_INFINITY_TESTS: list[ExpressionTestCase] = [
    # Positive infinity loses to all finite values.
    ExpressionTestCase(
        "inf_float_vs_large_int32",
        expression={"$min": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": INT32_MAX},
        expected=INT32_MAX,
        msg="$min should pick int32 max over float Infinity",
    ),
    ExpressionTestCase(
        "inf_float_vs_large_int64",
        expression={"$min": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": INT64_MAX},
        expected=INT64_MAX,
        msg="$min should pick int64 max over float Infinity",
    ),
    ExpressionTestCase(
        "inf_float_vs_large_double",
        expression={"$min": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": DOUBLE_MAX},
        expected=DOUBLE_MAX,
        msg="$min should pick DBL_MAX over float Infinity",
    ),
    ExpressionTestCase(
        "inf_float_vs_decimal128_max",
        expression={"$min": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": DECIMAL128_MAX},
        expected=DECIMAL128_MAX,
        msg="$min should pick Decimal128 MAX over float Infinity",
    ),
    ExpressionTestCase(
        "inf_decimal128_vs_large_int32",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": INT32_MAX},
        expected=INT32_MAX,
        msg="$min should pick int32 max over Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "inf_decimal128_vs_large_int64",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": INT64_MAX},
        expected=INT64_MAX,
        msg="$min should pick int64 max over Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "inf_decimal128_vs_large_double",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": DOUBLE_MAX},
        expected=DOUBLE_MAX,
        msg="$min should pick DBL_MAX over Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "inf_decimal128_vs_decimal128_max",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": DECIMAL128_MAX},
        expected=DECIMAL128_MAX,
        msg="$min should pick Decimal128 MAX over Decimal128 Infinity",
    ),
    # Negative infinity beats all finite values.
    ExpressionTestCase(
        "inf_neg_float_vs_small_int32",
        expression={"$min": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": INT32_MIN},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$min should pick float -Infinity over int32 min",
    ),
    ExpressionTestCase(
        "inf_neg_float_vs_small_int64",
        expression={"$min": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": INT64_MIN},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$min should pick float -Infinity over int64 min",
    ),
    ExpressionTestCase(
        "inf_neg_float_vs_negative_double",
        expression={"$min": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": DOUBLE_MIN},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$min should pick float -Infinity over -DBL_MAX",
    ),
    ExpressionTestCase(
        "inf_neg_float_vs_decimal128_min",
        expression={"$min": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": DECIMAL128_MIN},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$min should pick float -Infinity over Decimal128 MIN",
    ),
    ExpressionTestCase(
        "inf_neg_decimal128_vs_small_int32",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": INT32_MIN},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$min should pick Decimal128 -Infinity over int32 min",
    ),
    ExpressionTestCase(
        "inf_neg_decimal128_vs_negative_int64",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": INT64_MIN},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$min should pick Decimal128 -Infinity over int64 min",
    ),
    ExpressionTestCase(
        "inf_neg_decimal128_vs_negative_double",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": DOUBLE_MIN},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$min should pick Decimal128 -Infinity over -DBL_MAX",
    ),
    ExpressionTestCase(
        "inf_neg_decimal128_vs_decimal128_min",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": DECIMAL128_MIN},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$min should pick Decimal128 -Infinity over Decimal128 MIN",
    ),
    # Infinity is numeric type, so it is less than string per BSON order.
    ExpressionTestCase(
        "inf_float_vs_string",
        expression={"$min": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": "a"},
        expected=FLOAT_INFINITY,
        msg="$min should pick float Infinity over string per BSON type order",
    ),
    ExpressionTestCase(
        "inf_decimal128_vs_string",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": "a"},
        expected=DECIMAL128_INFINITY,
        msg="$min should pick Decimal128 Infinity over string per BSON type order",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MIN_INFINITY_TESTS))
def test_min_infinity_cases(collection, test_case: ExpressionTestCase):
    """Test $min infinity behavior cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
