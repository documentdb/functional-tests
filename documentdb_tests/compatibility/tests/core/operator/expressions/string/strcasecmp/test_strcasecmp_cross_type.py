from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Code, Int64, Timestamp

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.string.strcasecmp.utils.strcasecmp_common import (
    StrcasecmpTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Cross-Type Ordering]: numeric arguments are coerced to their string
# representation and then compared as strings.
STRCASECMP_CROSS_TYPE_TESTS: list[StrcasecmpTest] = [
    # Numbers are coerced to strings.
    StrcasecmpTest(
        "cross_int_eq_string_repr",
        string1=42,
        string2="42",
        expected=0,
        msg="$strcasecmp should coerce int 42 to '42' for comparison",
    ),
    StrcasecmpTest(
        "cross_float_eq_string_repr",
        string1=2.5,
        string2="2.5",
        expected=0,
        msg="$strcasecmp should coerce float 2.5 to '2.5' for comparison",
    ),
    StrcasecmpTest(
        "cross_neg_eq_string_repr",
        string1=-1,
        string2="-1",
        expected=0,
        msg="$strcasecmp should coerce -1 to '-1' for comparison",
    ),
    StrcasecmpTest(
        "cross_zero_eq_string_repr",
        string1=0,
        string2="0",
        expected=0,
        msg="$strcasecmp should coerce 0 to '0' for comparison",
    ),
    # Lexicographic after coercion: "42" < "9" because '4' < '9'.
    StrcasecmpTest(
        "cross_num_lexicographic",
        string1=42,
        string2="9",
        expected=-1,
        msg="$strcasecmp should compare coerced '42' < '9' lexicographically",
    ),
    # "100" < "20" lexicographically ('1' < '2'), not numerically.
    StrcasecmpTest(
        "cross_num_string_not_numeric",
        string1=100,
        string2=20,
        expected=-1,
        msg="$strcasecmp should compare '100' < '20' lexicographically, not numerically",
    ),
    # Whole-number float equals integer: 3.0 coerces to "3", not "3.0".
    StrcasecmpTest(
        "cross_float_eq_int",
        string1=3.0,
        string2=3,
        expected=0,
        msg="$strcasecmp should coerce 3.0 and 3 to the same string",
    ),
    StrcasecmpTest(
        "cross_float_coerces_to_int_str",
        string1=3.0,
        string2="3",
        expected=0,
        msg="$strcasecmp should coerce 3.0 to '3', not '3.0'",
    ),
    StrcasecmpTest(
        "cross_float_ne_dotted_str",
        string1=3.0,
        string2="3.0",
        expected=-1,
        msg="$strcasecmp should rank coerced 3.0 ('3') before literal '3.0'",
    ),
    # Negative zero coerces to "-0", not "0".
    StrcasecmpTest(
        "cross_neg_zero_str_repr",
        string1=DOUBLE_NEGATIVE_ZERO,
        string2="-0",
        expected=0,
        msg="$strcasecmp should coerce -0.0 to '-0'",
    ),
    StrcasecmpTest(
        "cross_neg_zero_ne_zero",
        string1=DOUBLE_NEGATIVE_ZERO,
        string2="0",
        expected=-1,
        msg="$strcasecmp should distinguish -0.0 ('-0') from '0'",
    ),
    # Large/small floats use scientific notation.
    StrcasecmpTest(
        "cross_sci_notation_large",
        string1=1e20,
        string2="1e+20",
        expected=0,
        msg="$strcasecmp should coerce 1e20 to '1e+20'",
    ),
    StrcasecmpTest(
        "cross_sci_notation_small",
        string1=1e-10,
        string2="1e-10",
        expected=0,
        msg="$strcasecmp should coerce 1e-10 to '1e-10'",
    ),
    # NaN coerces to "NaN".
    StrcasecmpTest(
        "cross_nan_string_repr",
        string1=FLOAT_NAN,
        string2="NaN",
        expected=0,
        msg="$strcasecmp should coerce NaN to 'NaN'",
    ),
    StrcasecmpTest(
        "cross_nan_vs_nan",
        string1=FLOAT_NAN,
        string2=FLOAT_NAN,
        expected=0,
        msg="$strcasecmp should return 0 for NaN vs NaN",
    ),
    # Infinity coerces to "inf", -Infinity to "-inf".
    StrcasecmpTest(
        "cross_inf_string_repr",
        string1=FLOAT_INFINITY,
        string2="inf",
        expected=0,
        msg="$strcasecmp should coerce Infinity to 'inf'",
    ),
    StrcasecmpTest(
        "cross_neg_inf_string_repr",
        string1=FLOAT_NEGATIVE_INFINITY,
        string2="-inf",
        expected=0,
        msg="$strcasecmp should coerce -Infinity to '-inf'",
    ),
    StrcasecmpTest(
        "cross_inf_vs_neg_inf",
        string1=FLOAT_INFINITY,
        string2=FLOAT_NEGATIVE_INFINITY,
        expected=1,
        msg="$strcasecmp should rank 'inf' after '-inf'",
    ),
    # Datetime coerced to ISO string.
    StrcasecmpTest(
        "cross_datetime_str_repr",
        string1=datetime(2024, 1, 1, tzinfo=timezone.utc),
        string2="2024-01-01T00:00:00.000Z",
        expected=0,
        msg="$strcasecmp should coerce datetime to ISO 8601 string",
    ),
    # Decimal128 coerced to its string representation.
    StrcasecmpTest(
        "cross_decimal128_str_repr",
        string1=DECIMAL128_ONE_AND_HALF,
        string2="1.5",
        expected=0,
        msg="$strcasecmp should coerce Decimal128 1.5 to '1.5'",
    ),
    # Int64 coerced same as int.
    StrcasecmpTest(
        "cross_int64_str_repr",
        string1=Int64(42),
        string2="42",
        expected=0,
        msg="$strcasecmp should coerce Int64(42) to '42'",
    ),
    # Timestamp is coerced internally; same Timestamp compares equal.
    StrcasecmpTest(
        "cross_timestamp_eq_self",
        string1=Timestamp(1, 1),
        string2=Timestamp(1, 1),
        expected=0,
        msg="$strcasecmp should coerce identical Timestamps to the same string",
    ),
    StrcasecmpTest(
        "cross_timestamp_ordering",
        string1=Timestamp(1, 1),
        string2=Timestamp(2, 1),
        expected=-1,
        msg="$strcasecmp should order Timestamp(1,1) before Timestamp(2,1)",
    ),
    # Code (without scope) is coerced to its body string.
    StrcasecmpTest(
        "cross_code_eq_body",
        string1=Code("function() {}"),
        string2="function() {}",
        expected=0,
        msg="$strcasecmp should coerce Code to its body string",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_CROSS_TYPE_TESTS))
def test_strcasecmp_cross_type_cases(collection, test_case: StrcasecmpTest):
    """Test $strcasecmp cross-type ordering cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
