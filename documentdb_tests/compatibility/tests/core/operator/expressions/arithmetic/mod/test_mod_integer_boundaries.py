"""
Integer boundary tests for $mod expression.

Covers INT32/INT64 max/min (and adjacent) values as the dividend, the
INT_MIN mod -1 no-overflow case, and large dividend/divisor combinations.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

MOD_INTEGER_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT32_MAX, "divisor": 10},
        expected=7,
        msg="Should handle INT32_MAX as dividend",
    ),
    ExpressionTestCase(
        "int32_max_minus_1",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT32_MAX_MINUS_1, "divisor": 10},
        expected=6,
        msg="Should handle INT32_MAX-1 as dividend",
    ),
    ExpressionTestCase(
        "int32_min",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT32_MIN, "divisor": 10},
        expected=-8,
        msg="Should handle INT32_MIN as dividend",
    ),
    ExpressionTestCase(
        "int32_min_plus_1",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT32_MIN_PLUS_1, "divisor": 10},
        expected=-7,
        msg="Should handle INT32_MIN+1 as dividend",
    ),
    ExpressionTestCase(
        "int64_max",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT64_MAX, "divisor": Int64(10)},
        expected=Int64(7),
        msg="Should handle INT64_MAX as dividend",
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT64_MAX_MINUS_1, "divisor": Int64(10)},
        expected=Int64(6),
        msg="Should handle INT64_MAX-1 as dividend",
    ),
    ExpressionTestCase(
        "int64_min",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT64_MIN, "divisor": Int64(10)},
        expected=Int64(-8),
        msg="Should handle INT64_MIN as dividend",
    ),
    ExpressionTestCase(
        "int64_min_plus_1",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT64_MIN_PLUS_1, "divisor": Int64(10)},
        expected=Int64(-7),
        msg="Should handle INT64_MIN+1 as dividend",
    ),
    ExpressionTestCase(
        "int32_min_mod_negative_one",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT32_MIN, "divisor": -1},
        expected=0,
        msg="Should handle INT32_MIN mod -1 without overflow",
    ),
    ExpressionTestCase(
        "int32_min_plus_1_mod_negative_one",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT32_MIN_PLUS_1, "divisor": -1},
        expected=0,
        msg="Should handle INT32_MIN+1 mod -1",
    ),
    ExpressionTestCase(
        "int64_min_mod_negative_one",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT64_MIN, "divisor": Int64(-1)},
        expected=Int64(0),
        msg="Should handle INT64_MIN mod -1 without overflow",
    ),
    ExpressionTestCase(
        "int64_min_plus_1_mod_negative_one",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT64_MIN_PLUS_1, "divisor": Int64(-1)},
        expected=Int64(0),
        msg="Should handle INT64_MIN+1 mod -1",
    ),
    ExpressionTestCase(
        "million_mod_seven",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 1000000, "divisor": 7},
        expected=1,
        msg="Should handle large dividend",
    ),
    ExpressionTestCase(
        "int64_max_modulo",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": INT64_MAX, "divisor": 1000000},
        expected=Int64(775807),
        msg="Should handle INT64_MAX mod large divisor",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_INTEGER_BOUNDARY_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.doc["dividend"], test.doc["divisor"]]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_INTEGER_BOUNDARY_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
