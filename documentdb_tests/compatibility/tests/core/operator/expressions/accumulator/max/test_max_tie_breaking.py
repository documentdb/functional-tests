from __future__ import annotations

import pytest
from bson import Decimal128, Int64

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
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Tie-Breaking]: when two values are equal but have different
# types, the first value in argument order wins, preserving its type.
MAX_TIE_BREAKING_TESTS: list[ExpressionTestCase] = [
    # All numeric type pairs: first wins on equal value.
    ExpressionTestCase(
        "tie_int32_int64_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": 5, "b": Int64(5)},
        expected=["int", 5],
        msg="$max should preserve int32 type when int32 and int64 are equal and int32 is first",
    ),
    ExpressionTestCase(
        "tie_int64_int32_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": Int64(5), "b": 5},
        expected=["long", Int64(5)],
        msg="$max should preserve int64 type when int64 and int32 are equal and int64 is first",
    ),
    ExpressionTestCase(
        "tie_int32_double_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": 5, "b": 5.0},
        expected=["int", 5],
        msg="$max should preserve int32 type when int32 and double are equal and int32 is first",
    ),
    ExpressionTestCase(
        "tie_double_int32_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": 5.0, "b": 5},
        expected=["double", 5.0],
        msg="$max should preserve double type when double and int32 are equal and double is first",
    ),
    ExpressionTestCase(
        "tie_int32_decimal128_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": 5, "b": Decimal128("5")},
        expected=["int", 5],
        msg="$max should preserve int32 when int32 and Decimal128 are equal",
    ),
    ExpressionTestCase(
        "tie_decimal128_int32_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": Decimal128("5"), "b": 5},
        expected=["decimal", Decimal128("5")],
        msg="$max should preserve Decimal128 when Decimal128 and int32 are equal",
    ),
    ExpressionTestCase(
        "tie_int64_double_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": Int64(5), "b": 5.0},
        expected=["long", Int64(5)],
        msg="$max should preserve int64 type when int64 and double are equal and int64 is first",
    ),
    ExpressionTestCase(
        "tie_double_int64_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": 5.0, "b": Int64(5)},
        expected=["double", 5.0],
        msg="$max should preserve double type when double and int64 are equal and double is first",
    ),
    ExpressionTestCase(
        "tie_int64_decimal128_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": Int64(5), "b": Decimal128("5")},
        expected=["long", Int64(5)],
        msg="$max should preserve int64 when int64 and Decimal128 are equal",
    ),
    ExpressionTestCase(
        "tie_decimal128_int64_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": Decimal128("5"), "b": Int64(5)},
        expected=["decimal", Decimal128("5")],
        msg="$max should preserve Decimal128 when Decimal128 and int64 are equal",
    ),
    # double vs Decimal128: exactly representable equal values.
    ExpressionTestCase(
        "tie_double_decimal128_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": 3.5, "b": Decimal128("3.5")},
        expected=["double", 3.5],
        msg=(
            "$max should preserve double when double and Decimal128"
            " are exactly equal and double is first"
        ),
    ),
    ExpressionTestCase(
        "tie_decimal128_double_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": Decimal128("3.5"), "b": 3.5},
        expected=["decimal", Decimal128("3.5")],
        msg=(
            "$max should preserve Decimal128 when Decimal128 and double"
            " are exactly equal and Decimal128 is first"
        ),
    ),
    # Double negative zero vs positive zero.
    ExpressionTestCase(
        "tie_double_negzero_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": DOUBLE_NEGATIVE_ZERO, "b": DOUBLE_ZERO},
        expected=["double", DOUBLE_NEGATIVE_ZERO],
        msg="$max should return double -0 when it appears first and +0 is second",
    ),
    ExpressionTestCase(
        "tie_double_poszero_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": DOUBLE_ZERO, "b": DOUBLE_NEGATIVE_ZERO},
        expected=["double", DOUBLE_ZERO],
        msg="$max should return double 0 when it appears first and -0 is second",
    ),
    # Decimal128 negative zero vs positive zero: the driver distinguishes these.
    ExpressionTestCase(
        "tie_decimal128_negzero_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": DECIMAL128_NEGATIVE_ZERO, "b": DECIMAL128_ZERO},
        expected=["decimal", DECIMAL128_NEGATIVE_ZERO],
        msg="$max should return Decimal128 -0 when it appears first and +0 is second",
    ),
    ExpressionTestCase(
        "tie_decimal128_poszero_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": DECIMAL128_ZERO, "b": DECIMAL128_NEGATIVE_ZERO},
        expected=["decimal", DECIMAL128_ZERO],
        msg="$max should return Decimal128 0 when it appears first and -0 is second",
    ),
    # Cross-type equal infinities: first argument's type is preserved.
    ExpressionTestCase(
        "tie_double_inf_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": FLOAT_INFINITY, "b": DECIMAL128_INFINITY},
        expected=["double", FLOAT_INFINITY],
        msg="$max should preserve double Infinity when it appears first",
    ),
    ExpressionTestCase(
        "tie_decimal128_inf_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": DECIMAL128_INFINITY, "b": FLOAT_INFINITY},
        expected=["decimal", DECIMAL128_INFINITY],
        msg="$max should preserve Decimal128 Infinity when it appears first",
    ),
    ExpressionTestCase(
        "tie_double_neginf_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=["double", FLOAT_NEGATIVE_INFINITY],
        msg="$max should preserve double -Infinity when it appears first",
    ),
    ExpressionTestCase(
        "tie_decimal128_neginf_first",
        expression={
            "$let": {"vars": {"m": {"$max": ["$a", "$b"]}}, "in": [{"$type": "$$m"}, "$$m"]}
        },
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": FLOAT_NEGATIVE_INFINITY},
        expected=["decimal", DECIMAL128_NEGATIVE_INFINITY],
        msg="$max should preserve Decimal128 -Infinity when it appears first",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MAX_TIE_BREAKING_TESTS))
def test_max_tie_breaking_cases(collection, test_case: ExpressionTestCase):
    """Test $max tie-breaking cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
