from __future__ import annotations

import pytest
from bson import Binary, Code, Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Object Comparison]: objects are compared field-by-field in
# insertion order using BSON comparison on values.
MIN_OBJECT_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "object_first_value_diff",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"a": 1}, "b": {"a": 2}},
        expected={"a": 1},
        msg="$min should pick the object with the smaller first field value",
    ),
    ExpressionTestCase(
        "object_second_value_diff",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"a": 1, "b": 2}, "b": {"a": 1, "b": 3}},
        expected={"a": 1, "b": 2},
        msg="$min should compare field-by-field and pick the object with the smaller second value",
    ),
    ExpressionTestCase(
        "object_key_order_matters",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"a": 1, "b": 2}, "b": {"b": 2, "a": 1}},
        expected={"a": 1, "b": 2},
        msg=(
            "$min should compare objects by field insertion order,"
            " picking the one whose first key is smaller"
        ),
    ),
    ExpressionTestCase(
        "object_key_a_vs_b",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"a": 1}, "b": {"b": 1}},
        expected={"a": 1},
        msg="$min should pick the object with the smaller first key name",
    ),
    ExpressionTestCase(
        "object_key_b_vs_a",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"b": 1}, "b": {"a": 1}},
        expected={"a": 1},
        msg="$min should pick the object with key 'a' over key 'b' regardless of order",
    ),
    ExpressionTestCase(
        "object_more_fields_wins",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"a": 1}, "b": {"a": 1, "b": 2}},
        expected={"a": 1},
        msg="$min should pick the object with fewer fields when the prefix matches",
    ),
    ExpressionTestCase(
        "object_more_fields_reversed",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"a": 1, "b": 2}, "b": {"a": 1}},
        expected={"a": 1},
        msg="$min should pick the object with fewer fields regardless of argument order",
    ),
    ExpressionTestCase(
        "object_empty_vs_nonempty",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {}, "b": {"a": 1}},
        expected={},
        msg="$min should pick an empty object over a non-empty object",
    ),
    ExpressionTestCase(
        "object_value_beats_more_fields",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"a": 2}, "b": {"a": 1, "b": 99}},
        expected={"a": 1, "b": 99},
        msg="$min should prefer a smaller field value over having fewer fields",
    ),
    ExpressionTestCase(
        "object_nested_value_diff",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"a": {"x": 1}}, "b": {"a": {"x": 2}}},
        expected={"a": {"x": 1}},
        msg="$min should compare nested object values recursively",
    ),
    ExpressionTestCase(
        "object_value_type_bson_order",
        expression={"$min": ["$a", "$b"]},
        doc={"a": {"a": 1}, "b": {"a": "hello"}},
        expected={"a": 1},
        msg="$min should use BSON type order when comparing field values of different types",
    ),
]

# Property [Binary Comparison]: binary values are compared by content, and
# lower subtype beats higher subtype for same content.
MIN_BINARY_COMPARISON_TESTS: list[ExpressionTestCase] = [
    # Content comparison: same subtype, different content.
    ExpressionTestCase(
        "binary_content_second_byte_diff",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Binary(b"\x00\x01"), "b": Binary(b"\x00\x02")},
        expected=b"\x00\x01",
        msg="$min should pick binary with lower byte content",
    ),
    ExpressionTestCase(
        "binary_content_first_byte_diff",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Binary(b"\x01\x00"), "b": Binary(b"\x02\x00")},
        expected=b"\x01\x00",
        msg="$min should compare binary content byte-by-byte from the start",
    ),
    ExpressionTestCase(
        "binary_content_reversed",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Binary(b"\xff"), "b": Binary(b"\x00")},
        expected=b"\x00",
        msg="$min should pick binary with lower content regardless of order",
    ),
    ExpressionTestCase(
        "binary_content_equal",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Binary(b"\x01\x02"), "b": Binary(b"\x01\x02")},
        expected=b"\x01\x02",
        msg="$min should return the value when both binaries have identical content",
    ),
    # Subtype comparison: same content, different subtypes.
    ExpressionTestCase(
        "binary_subtype_0_vs_5",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Binary(b"\x01", 0), "b": Binary(b"\x01", 5)},
        expected=b"\x01",
        msg="$min should pick binary with lower subtype for same content",
    ),
    ExpressionTestCase(
        "binary_subtype_5_vs_0",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Binary(b"\x01", 5), "b": Binary(b"\x01", 0)},
        expected=b"\x01",
        msg="$min should pick binary with lower subtype regardless of order",
    ),
]

# Property [Regex Comparison]: regex values are compared by pattern first,
# then by flags numerically, with lower values winning.
MIN_REGEX_COMPARISON_TESTS: list[ExpressionTestCase] = [
    # Pattern comparison: lower pattern string wins.
    ExpressionTestCase(
        "regex_pattern_b_vs_a",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Regex("b"), "b": Regex("a")},
        expected=Regex("a"),
        msg="$min should pick regex with lower pattern string",
    ),
    ExpressionTestCase(
        "regex_pattern_a_vs_b",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Regex("a"), "b": Regex("b")},
        expected=Regex("a"),
        msg="$min should pick regex with lower pattern regardless of order",
    ),
    # Pattern takes priority over flags.
    ExpressionTestCase(
        "regex_pattern_priority_over_flags",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Regex("b"), "b": Regex("a", "m")},
        expected=Regex("a", "m"),
        msg="$min should compare pattern before flags",
    ),
    # Same pattern, flag comparison: m (8) > i (2).
    ExpressionTestCase(
        "regex_flags_m_vs_i",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Regex("abc", "i"), "b": Regex("abc", "m")},
        expected=Regex("abc", "i"),
        msg="$min should pick regex with lower flag value when patterns are equal",
    ),
    ExpressionTestCase(
        "regex_flags_m_vs_i_reversed",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Regex("abc", "m"), "b": Regex("abc", "i")},
        expected=Regex("abc", "i"),
        msg="$min should pick regex with lower flag value regardless of order",
    ),
    # Same pattern, flags vs no flags: no flags wins.
    ExpressionTestCase(
        "regex_flags_vs_none",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Regex("abc"), "b": Regex("abc", "i")},
        expected=Regex("abc"),
        msg="$min should pick regex with no flags over regex with flags",
    ),
]

# Property [Code Comparison]: Code is a lower BSON type than CodeWithScope,
# so $min picks Code regardless of code string content. Within the same type,
# comparison is by code string.
MIN_CODE_COMPARISON_TESTS: list[ExpressionTestCase] = [
    # Code vs Code: lower code string wins.
    ExpressionTestCase(
        "code_a_vs_b",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("a"), "b": Code("b")},
        expected=Code("a"),
        msg="$min should pick Code with lower code string",
    ),
    ExpressionTestCase(
        "code_b_vs_a",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("b"), "b": Code("a")},
        expected=Code("a"),
        msg="$min should pick Code with lower code string regardless of order",
    ),
    # CodeWithScope vs CodeWithScope: lower code string wins.
    ExpressionTestCase(
        "codewithscope_a_vs_b",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("a", {}), "b": Code("b", {})},
        expected=Code("a", {}),
        msg="$min should pick CodeWithScope with lower code string",
    ),
    ExpressionTestCase(
        "codewithscope_b_vs_a",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("b", {}), "b": Code("a", {})},
        expected=Code("a", {}),
        msg="$min should pick CodeWithScope with lower code string regardless of order",
    ),
    ExpressionTestCase(
        "codewithscope_equal_scope_diff",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("abc", {"x": 1}), "b": Code("abc", {"y": 2})},
        expected=Code("abc", {"x": 1}),
        msg="$min should compare scope as object when code strings are equal",
    ),
    # Code beats CodeWithScope (Code is lower BSON type).
    ExpressionTestCase(
        "code_z_vs_codewithscope_a",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("z"), "b": Code("a", {})},
        expected=Code("z"),
        msg="$min should pick Code over CodeWithScope regardless of code string",
    ),
    ExpressionTestCase(
        "codewithscope_a_vs_code_z",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Code("a", {}), "b": Code("z")},
        expected=Code("z"),
        msg="$min should pick Code over CodeWithScope regardless of order",
    ),
]

MIN_NONSCALAR_TYPE_TESTS = (
    MIN_OBJECT_COMPARISON_TESTS
    + MIN_BINARY_COMPARISON_TESTS
    + MIN_REGEX_COMPARISON_TESTS
    + MIN_CODE_COMPARISON_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MIN_NONSCALAR_TYPE_TESTS))
def test_min_nonscalar_type_cases(collection, test_case: ExpressionTestCase):
    """Test $min non-scalar type comparison cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
