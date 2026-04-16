from __future__ import annotations

from datetime import datetime

import pytest
from bson import (
    Binary,
    Code,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [BSON Comparison Order]: $min uses BSON comparison order to
# determine the minimum across values of different types.
MIN_BSON_ORDER_TESTS: list[ExpressionTestCase] = [
    # Adjacent type pairs: lower BSON type wins regardless of values.
    ExpressionTestCase(
        "bson_minkey_vs_number",
        expression={"$min": ["$a", "$b"]},
        doc={"a": MinKey(), "b": 0},
        expected=MinKey(),
        msg="$min should pick MinKey over number per BSON order",
    ),
    ExpressionTestCase(
        "bson_number_vs_string",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 999_999, "b": "a"},
        expected=999_999,
        msg="$min should pick number over string per BSON order",
    ),
    ExpressionTestCase(
        "bson_string_vs_object",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "zzz", "b": {"a": 1}},
        expected="zzz",
        msg="$min should pick string over object per BSON order",
    ),
    ExpressionTestCase(
        "bson_object_vs_array",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"z": 99}, "b": [1]},
        expected={"z": 99},
        msg="$min should pick object over array per BSON order",
    ),
    ExpressionTestCase(
        "bson_array_vs_binary",
        expression={"$min": ["$a", "$b"]},
        doc={"a": [99, 99], "b": Binary(b"\x00")},
        expected=[99, 99],
        msg="$min should pick array over binary per BSON order",
    ),
    ExpressionTestCase(
        "bson_binary_vs_objectid",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Binary(b"\xff" * 100), "b": ObjectId("000000000000000000000000")},
        expected=b"\xff" * 100,
        msg="$min should pick binary over ObjectId per BSON order",
    ),
    ExpressionTestCase(
        "bson_objectid_vs_boolean",
        expression={"$min": ["$a", "$b"]},
        doc={"a": ObjectId("000000000000000000000000"), "b": False},
        expected=ObjectId("000000000000000000000000"),
        msg="$min should pick ObjectId over boolean per BSON order",
    ),
    ExpressionTestCase(
        "bson_boolean_vs_date",
        expression={"$min": ["$a", "$b"]},
        doc={"a": True, "b": datetime(1970, 1, 1)},
        expected=True,
        msg="$min should pick boolean over date per BSON order",
    ),
    ExpressionTestCase(
        "bson_date_vs_timestamp",
        expression={"$min": ["$a", "$b"]},
        doc={"a": datetime(1970, 1, 1), "b": Timestamp(1, 1)},
        expected=datetime(1970, 1, 1),
        msg="$min should pick date over timestamp per BSON order",
    ),
    ExpressionTestCase(
        "bson_timestamp_vs_regex",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Timestamp(1, 1), "b": Regex("a")},
        expected=Timestamp(1, 1),
        msg="$min should pick timestamp over regex per BSON order",
    ),
    ExpressionTestCase(
        "bson_regex_vs_code",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Regex("a"), "b": Code("function(){}")},
        expected=Regex("a"),
        msg="$min should pick regex over Code per BSON order",
    ),
    ExpressionTestCase(
        "bson_code_vs_codewithscope",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("z"), "b": Code("a", {"x": 1})},
        expected=Code("z"),
        msg="$min should pick Code over CodeWithScope regardless of code string",
    ),
    ExpressionTestCase(
        "bson_codewithscope_vs_maxkey",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("a", {"x": 1}), "b": MaxKey()},
        expected=Code("a", {"x": 1}),
        msg="$min should pick CodeWithScope over MaxKey per BSON order",
    ),
    # Reversed order: lower-ranked type second in the doc, verifying $min does
    # not just return the first element.
    ExpressionTestCase(
        "bson_number_vs_string_reversed",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "a", "b": 999_999},
        expected=999_999,
        msg="$min should pick number over string even when number comes second",
    ),
    ExpressionTestCase(
        "bson_objectid_vs_boolean_reversed",
        expression={"$min": ["$a", "$b"]},
        doc={"a": False, "b": ObjectId("000000000000000000000000")},
        expected=ObjectId("000000000000000000000000"),
        msg="$min should pick ObjectId over boolean even when ObjectId comes second",
    ),
    ExpressionTestCase(
        "bson_minkey_vs_maxkey_reversed",
        expression={"$min": ["$a", "$b"]},
        doc={"a": MinKey(), "b": MaxKey()},
        expected=MinKey(),
        msg="$min should pick MinKey over MaxKey even when MinKey is first",
    ),
    ExpressionTestCase(
        "bson_string_vs_date_reversed",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "zzz", "b": datetime(1970, 1, 1)},
        expected="zzz",
        msg="$min should pick string over date even when string is first",
    ),
    # Full range: MinKey vs MaxKey.
    ExpressionTestCase(
        "bson_maxkey_vs_minkey",
        expression={"$min": ["$a", "$b"]},
        doc={"a": MaxKey(), "b": MinKey()},
        expected=MinKey(),
        msg="$min should pick MinKey over MaxKey per BSON order",
    ),
    # Non-adjacent: number < boolean in BSON order.
    ExpressionTestCase(
        "bson_number_beats_false",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 999_999, "b": False},
        expected=999_999,
        msg="$min should pick any number over False per BSON order",
    ),
    # Null is excluded, not ranked in BSON order.
    ExpressionTestCase(
        "bson_null_excluded_maxkey_survives",
        expression={"$min": ["$a", "$b"]},
        doc={"a": None, "b": MaxKey()},
        expected=MaxKey(),
        msg="$min should exclude null and return MaxKey",
    ),
]

# Property [Within-Type Ordering]: for types that have a within-type ordering
# but are not tested with dedicated coverage elsewhere, $min picks the
# lesser value within the same BSON type.
MIN_WITHIN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "within_boolean_true_vs_false",
        expression={"$min": ["$a", "$b"]},
        doc={"a": True, "b": False},
        expected=False,
        msg="$min should pick False over True within boolean type",
    ),
    ExpressionTestCase(
        "within_objectid_lower_vs_higher",
        expression={"$min": ["$a", "$b"]},
        doc={"a": ObjectId("000000000000000000000001"), "b": ObjectId("000000000000000000000002")},
        expected=ObjectId("000000000000000000000001"),
        msg="$min should pick the lower ObjectId within ObjectId type",
    ),
    ExpressionTestCase(
        "within_binary_by_content",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Binary(b"\x01"), "b": Binary(b"\x02")},
        expected=b"\x01",
        msg="$min should pick the Binary with lower byte value",
    ),
    ExpressionTestCase(
        "within_regex_by_pattern",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Regex("abc", ""), "b": Regex("def", "")},
        expected=Regex("abc", ""),
        msg="$min should pick the Regex with the lower pattern",
    ),
    ExpressionTestCase(
        "within_code_by_value",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("a()"), "b": Code("b()")},
        expected=Code("a()"),
        msg="$min should pick the Code with the lower string value",
    ),
    ExpressionTestCase(
        "within_codewithscope_by_code",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("a()", {}), "b": Code("b()", {})},
        expected=Code("a()", {}),
        msg="$min should pick the CodeWithScope with the lower code string",
    ),
]

MIN_BSON_ALL_TESTS = MIN_BSON_ORDER_TESTS + MIN_WITHIN_TYPE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MIN_BSON_ALL_TESTS))
def test_min_bson_order_cases(collection, test_case: ExpressionTestCase):
    """Test $min BSON comparison order cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
