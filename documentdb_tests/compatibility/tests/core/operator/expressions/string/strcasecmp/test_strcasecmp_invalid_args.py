from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import EXPRESSION_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.strcasecmp.utils.strcasecmp_common import (
    StrcasecmpTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Arity]: wrong number of arguments or non-array syntax produces an error.
STRCASECMP_ARITY_ERROR_TESTS: list[StrcasecmpTest] = [
    StrcasecmpTest(
        "arity_zero_args",
        expr={"$strcasecmp": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject zero arguments",
    ),
    StrcasecmpTest(
        "arity_one_arg",
        expr={"$strcasecmp": ["hello"]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject one argument",
    ),
    StrcasecmpTest(
        "arity_three_args",
        expr={"$strcasecmp": ["a", "b", "c"]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject three arguments",
    ),
    # Non-array argument shapes are treated as 1 argument.
    StrcasecmpTest(
        "arity_string",
        expr={"$strcasecmp": "hello"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare string as non-array argument",
    ),
    StrcasecmpTest(
        "arity_int",
        expr={"$strcasecmp": 42},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare int as non-array argument",
    ),
    StrcasecmpTest(
        "arity_float",
        expr={"$strcasecmp": 3.14},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare float as non-array argument",
    ),
    StrcasecmpTest(
        "arity_long",
        expr={"$strcasecmp": Int64(1)},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare Int64 as non-array argument",
    ),
    StrcasecmpTest(
        "arity_decimal",
        expr={"$strcasecmp": Decimal128("1")},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare Decimal128 as non-array argument",
    ),
    StrcasecmpTest(
        "arity_bool",
        expr={"$strcasecmp": True},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare boolean as non-array argument",
    ),
    StrcasecmpTest(
        "arity_null",
        expr={"$strcasecmp": None},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare null as non-array argument",
    ),
    StrcasecmpTest(
        "arity_object",
        expr={"$strcasecmp": {"a": 1}},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare object as non-array argument",
    ),
    StrcasecmpTest(
        "arity_binary",
        expr={"$strcasecmp": Binary(b"data")},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare binary as non-array argument",
    ),
    StrcasecmpTest(
        "arity_date",
        expr={"$strcasecmp": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare datetime as non-array argument",
    ),
    StrcasecmpTest(
        "arity_objectid",
        expr={"$strcasecmp": ObjectId()},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare ObjectId as non-array argument",
    ),
    StrcasecmpTest(
        "arity_regex",
        expr={"$strcasecmp": Regex("pattern")},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare regex as non-array argument",
    ),
    StrcasecmpTest(
        "arity_timestamp",
        expr={"$strcasecmp": Timestamp(1, 1)},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare Timestamp as non-array argument",
    ),
    StrcasecmpTest(
        "arity_minkey",
        expr={"$strcasecmp": MinKey()},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare MinKey as non-array argument",
    ),
    StrcasecmpTest(
        "arity_maxkey",
        expr={"$strcasecmp": MaxKey()},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare MaxKey as non-array argument",
    ),
    StrcasecmpTest(
        "arity_code",
        expr={"$strcasecmp": Code("function() {}")},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare Code as non-array argument",
    ),
    StrcasecmpTest(
        "arity_code_scope",
        expr={"$strcasecmp": Code("function() {}", {"x": 1})},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strcasecmp should reject bare Code with scope as non-array argument",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_ARITY_ERROR_TESTS))
def test_strcasecmp_invalid_args_cases(collection, test_case: StrcasecmpTest):
    """Test $strcasecmp arity error cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
