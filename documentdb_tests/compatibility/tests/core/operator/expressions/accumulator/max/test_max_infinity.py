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
MAX_INFINITY_TESTS: list[ExpressionTestCase] = [
    # Positive infinity beats large finite values.
    ExpressionTestCase(
        "inf_float_vs_large_int32",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": INT32_MAX},
        expected=FLOAT_INFINITY,
        msg="$max should pick float Infinity over int32 max",
    ),
    ExpressionTestCase(
        "inf_float_vs_large_int64",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": INT64_MAX},
        expected=FLOAT_INFINITY,
        msg="$max should pick float Infinity over int64 max",
    ),
    ExpressionTestCase(
        "inf_float_vs_large_double",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": DOUBLE_MAX},
        expected=FLOAT_INFINITY,
        msg="$max should pick float Infinity over DBL_MAX",
    ),
    ExpressionTestCase(
        "inf_float_vs_decimal128_max",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": DECIMAL128_MAX},
        expected=FLOAT_INFINITY,
        msg="$max should pick float Infinity over Decimal128 MAX",
    ),
    ExpressionTestCase(
        "inf_decimal128_vs_large_int32",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": INT32_MAX},
        expected=DECIMAL128_INFINITY,
        msg="$max should pick Decimal128 Infinity over int32 max",
    ),
    ExpressionTestCase(
        "inf_decimal128_vs_large_int64",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": INT64_MAX},
        expected=DECIMAL128_INFINITY,
        msg="$max should pick Decimal128 Infinity over int64 max",
    ),
    ExpressionTestCase(
        "inf_decimal128_vs_large_double",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": DOUBLE_MAX},
        expected=DECIMAL128_INFINITY,
        msg="$max should pick Decimal128 Infinity over DBL_MAX",
    ),
    ExpressionTestCase(
        "inf_decimal128_vs_decimal128_max",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": DECIMAL128_MAX},
        expected=DECIMAL128_INFINITY,
        msg="$max should pick Decimal128 Infinity over Decimal128 MAX",
    ),
    # Negative infinity loses to all finite values.
    ExpressionTestCase(
        "inf_neg_float_vs_small_int32",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": INT32_MIN},
        expected=INT32_MIN,
        msg="$max should pick int32 min over float -Infinity",
    ),
    ExpressionTestCase(
        "inf_neg_float_vs_small_int64",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": INT64_MIN},
        expected=INT64_MIN,
        msg="$max should pick int64 min over float -Infinity",
    ),
    ExpressionTestCase(
        "inf_neg_float_vs_negative_double",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": DOUBLE_MIN},
        expected=DOUBLE_MIN,
        msg="$max should pick -DBL_MAX over float -Infinity",
    ),
    ExpressionTestCase(
        "inf_neg_float_vs_decimal128_min",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": DECIMAL128_MIN},
        expected=DECIMAL128_MIN,
        msg="$max should pick Decimal128 MIN over float -Infinity",
    ),
    ExpressionTestCase(
        "inf_neg_decimal128_vs_small_int32",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": INT32_MIN},
        expected=INT32_MIN,
        msg="$max should pick int32 min over Decimal128 -Infinity",
    ),
    ExpressionTestCase(
        "inf_neg_decimal128_vs_negative_int64",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": INT64_MIN},
        expected=INT64_MIN,
        msg="$max should pick int64 min over Decimal128 -Infinity",
    ),
    ExpressionTestCase(
        "inf_neg_decimal128_vs_negative_double",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": DOUBLE_MIN},
        expected=DOUBLE_MIN,
        msg="$max should pick -DBL_MAX over Decimal128 -Infinity",
    ),
    ExpressionTestCase(
        "inf_neg_decimal128_vs_decimal128_min",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": DECIMAL128_MIN},
        expected=DECIMAL128_MIN,
        msg="$max should pick Decimal128 MIN over Decimal128 -Infinity",
    ),
    # Infinity is numeric type, so it is less than string per BSON order.
    ExpressionTestCase(
        "inf_float_vs_string",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": "a"},
        expected="a",
        msg="$max should pick string over float Infinity per BSON type order",
    ),
    ExpressionTestCase(
        "inf_decimal128_vs_string",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": "a"},
        expected="a",
        msg="$max should pick string over Decimal128 Infinity per BSON type order",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MAX_INFINITY_TESTS))
def test_max_infinity_cases(collection, test_case: ExpressionTestCase):
    """Test $max infinity behavior cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
