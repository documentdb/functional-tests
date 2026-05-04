from __future__ import annotations

from datetime import datetime, timezone

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

# Property [BSON Comparison Order]: $max uses BSON comparison order to
# determine the maximum across values of different types.
MAX_BSON_ORDER_TESTS: list[ExpressionTestCase] = [
    # Adjacent type pairs: higher BSON type wins regardless of values.
    ExpressionTestCase(
        "bson_minkey_vs_number",
        expression={"$max": ["$a", "$b"]},
        doc={"a": MinKey(), "b": 0},
        expected=0,
        msg="$max should pick number over MinKey per BSON order",
    ),
    ExpressionTestCase(
        "bson_number_vs_string",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 999_999, "b": "a"},
        expected="a",
        msg="$max should pick string over number per BSON order",
    ),
    ExpressionTestCase(
        "bson_string_vs_object",
        expression={"$max": ["$a", "$b"]},
        doc={"a": "zzz", "b": {"a": 1}},
        expected={"a": 1},
        msg="$max should pick object over string per BSON order",
    ),
    ExpressionTestCase(
        "bson_object_vs_array",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"z": 99}, "b": [1]},
        expected=[1],
        msg="$max should pick array over object per BSON order",
    ),
    ExpressionTestCase(
        "bson_array_vs_binary",
        expression={"$max": ["$a", "$b"]},
        doc={"a": [99, 99], "b": Binary(b"\x00")},
        expected=b"\x00",
        msg="$max should pick binary over array per BSON order",
    ),
    ExpressionTestCase(
        "bson_binary_vs_objectid",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Binary(b"\xff" * 100), "b": ObjectId("000000000000000000000000")},
        expected=ObjectId("000000000000000000000000"),
        msg="$max should pick ObjectId over binary per BSON order",
    ),
    ExpressionTestCase(
        "bson_objectid_vs_boolean",
        expression={"$max": ["$a", "$b"]},
        doc={"a": ObjectId("000000000000000000000000"), "b": False},
        expected=False,
        msg="$max should pick boolean over ObjectId per BSON order",
    ),
    ExpressionTestCase(
        "bson_boolean_vs_date",
        expression={"$max": ["$a", "$b"]},
        doc={"a": True, "b": datetime(1970, 1, 1, tzinfo=timezone.utc)},
        expected=datetime(1970, 1, 1, tzinfo=timezone.utc),
        msg="$max should pick date over boolean per BSON order",
    ),
    ExpressionTestCase(
        "bson_date_vs_timestamp",
        expression={"$max": ["$a", "$b"]},
        doc={"a": datetime(1970, 1, 1, tzinfo=timezone.utc), "b": Timestamp(1, 1)},
        expected=Timestamp(1, 1),
        msg="$max should pick timestamp over date per BSON order",
    ),
    ExpressionTestCase(
        "bson_timestamp_vs_regex",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Timestamp(1, 1), "b": Regex("a")},
        expected=Regex("a"),
        msg="$max should pick regex over timestamp per BSON order",
    ),
    ExpressionTestCase(
        "bson_regex_vs_code",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Regex("a"), "b": Code("function(){}")},
        expected=Code("function(){}"),
        msg="$max should pick Code over regex per BSON order",
    ),
    ExpressionTestCase(
        "bson_code_vs_codewithscope",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("z"), "b": Code("a", {"x": 1})},
        expected=Code("a", {"x": 1}),
        msg="$max should pick CodeWithScope over Code regardless of code string",
    ),
    ExpressionTestCase(
        "bson_codewithscope_vs_maxkey",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("a", {"x": 1}), "b": MaxKey()},
        expected=MaxKey(),
        msg="$max should pick MaxKey over CodeWithScope per BSON order",
    ),
    # Reversed order: higher-ranked type first, verifying $max does not just
    # return the last element.
    ExpressionTestCase(
        "bson_string_vs_number_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": "a", "b": 999_999},
        expected="a",
        msg="$max should pick string over number even when string is first",
    ),
    ExpressionTestCase(
        "bson_boolean_vs_objectid_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": False, "b": ObjectId("000000000000000000000000")},
        expected=False,
        msg="$max should pick boolean over ObjectId even when boolean is first",
    ),
    ExpressionTestCase(
        "bson_maxkey_vs_minkey_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": MaxKey(), "b": MinKey()},
        expected=MaxKey(),
        msg="$max should pick MaxKey over MinKey even when MaxKey is first",
    ),
    ExpressionTestCase(
        "bson_date_vs_string_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": datetime(1970, 1, 1, tzinfo=timezone.utc), "b": "zzz"},
        expected=datetime(1970, 1, 1, tzinfo=timezone.utc),
        msg="$max should pick date over string even when date is first",
    ),
    # Full range: MinKey vs MaxKey.
    ExpressionTestCase(
        "bson_minkey_vs_maxkey",
        expression={"$max": ["$a", "$b"]},
        doc={"a": MinKey(), "b": MaxKey()},
        expected=MaxKey(),
        msg="$max should pick MaxKey over MinKey per BSON order",
    ),
    # Non-adjacent: False > any number (boolean > number in BSON order).
    ExpressionTestCase(
        "bson_false_beats_large_number",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 999_999, "b": False},
        expected=False,
        msg="$max should pick False over any number per BSON order",
    ),
    # Null is excluded, not ranked in BSON order.
    ExpressionTestCase(
        "bson_null_excluded_minkey_survives",
        expression={"$max": ["$a", "$b"]},
        doc={"a": None, "b": MinKey()},
        expected=MinKey(),
        msg="$max should exclude null and return MinKey",
    ),
]

# Property [Within-Type Ordering]: for types that have a within-type ordering
# but are not tested with dedicated coverage elsewhere, $max picks the
# greater value within the same BSON type.
MAX_WITHIN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "within_boolean_true_vs_false",
        expression={"$max": ["$a", "$b"]},
        doc={"a": True, "b": False},
        expected=True,
        msg="$max should pick True over False within boolean type",
    ),
    ExpressionTestCase(
        "within_objectid_lower_vs_higher",
        expression={"$max": ["$a", "$b"]},
        doc={"a": ObjectId("000000000000000000000001"), "b": ObjectId("000000000000000000000002")},
        expected=ObjectId("000000000000000000000002"),
        msg="$max should pick the higher ObjectId within ObjectId type",
    ),
    ExpressionTestCase(
        "within_binary_by_content",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Binary(b"\x01"), "b": Binary(b"\x02")},
        expected=b"\x02",
        msg="$max should pick the Binary with higher byte value",
    ),
    ExpressionTestCase(
        "within_regex_by_pattern",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Regex("abc", ""), "b": Regex("def", "")},
        expected=Regex("def", ""),
        msg="$max should pick the Regex with the higher pattern",
    ),
    ExpressionTestCase(
        "within_code_by_value",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("a()"), "b": Code("b()")},
        expected=Code("b()"),
        msg="$max should pick the Code with the higher string value",
    ),
    ExpressionTestCase(
        "within_codewithscope_by_code",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("a()", {}), "b": Code("b()", {})},
        expected=Code("b()", {}),
        msg="$max should pick the CodeWithScope with the higher code string",
    ),
]

MAX_BSON_ALL_TESTS = MAX_BSON_ORDER_TESTS + MAX_WITHIN_TYPE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MAX_BSON_ALL_TESTS))
def test_max_bson_order_cases(collection, test_case: ExpressionTestCase):
    """Test $max BSON comparison order cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
