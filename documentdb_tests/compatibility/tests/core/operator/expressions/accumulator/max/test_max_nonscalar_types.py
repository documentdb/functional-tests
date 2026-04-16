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
MAX_OBJECT_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "object_first_value_diff",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"a": 1}, "b": {"a": 2}},
        expected={"a": 2},
        msg="$max should pick the object with the larger first field value",
    ),
    ExpressionTestCase(
        "object_second_value_diff",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"a": 1, "b": 2}, "b": {"a": 1, "b": 3}},
        expected={"a": 1, "b": 3},
        msg="$max should compare field-by-field and pick the object with the larger second value",
    ),
    ExpressionTestCase(
        "object_key_order_matters",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"a": 1, "b": 2}, "b": {"b": 2, "a": 1}},
        expected={"b": 2, "a": 1},
        msg=(
            "$max should compare objects by field insertion order,"
            " picking the one whose first key is greater"
        ),
    ),
    ExpressionTestCase(
        "object_key_a_vs_b",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"a": 1}, "b": {"b": 1}},
        expected={"b": 1},
        msg="$max should pick the object with the greater first key name",
    ),
    ExpressionTestCase(
        "object_key_b_vs_a",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"b": 1}, "b": {"a": 1}},
        expected={"b": 1},
        msg="$max should pick the object with key 'b' over key 'a' regardless of order",
    ),
    ExpressionTestCase(
        "object_more_fields_wins",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"a": 1}, "b": {"a": 1, "b": 2}},
        expected={"a": 1, "b": 2},
        msg="$max should pick the object with more fields when the prefix matches",
    ),
    ExpressionTestCase(
        "object_more_fields_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"a": 1, "b": 2}, "b": {"a": 1}},
        expected={"a": 1, "b": 2},
        msg="$max should pick the object with more fields regardless of argument order",
    ),
    ExpressionTestCase(
        "object_empty_vs_nonempty",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {}, "b": {"a": 1}},
        expected={"a": 1},
        msg="$max should pick a non-empty object over an empty object",
    ),
    ExpressionTestCase(
        "object_value_beats_more_fields",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"a": 2}, "b": {"a": 1, "b": 99}},
        expected={"a": 2},
        msg="$max should prefer a greater field value over having more fields",
    ),
    ExpressionTestCase(
        "object_nested_value_diff",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"a": {"x": 1}}, "b": {"a": {"x": 2}}},
        expected={"a": {"x": 2}},
        msg="$max should compare nested object values recursively",
    ),
    ExpressionTestCase(
        "object_value_type_bson_order",
        expression={"$max": ["$a", "$b"]},
        doc={"a": {"a": 1}, "b": {"a": "hello"}},
        expected={"a": "hello"},
        msg="$max should use BSON type order when comparing field values of different types",
    ),
]

# Property [Binary Comparison]: binary values are compared by content, and
# higher subtype beats lower subtype for same content.
MAX_BINARY_COMPARISON_TESTS: list[ExpressionTestCase] = [
    # Content comparison: same subtype, different content.
    ExpressionTestCase(
        "binary_content_second_byte_diff",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Binary(b"\x00\x01"), "b": Binary(b"\x00\x02")},
        expected=b"\x00\x02",
        msg="$max should pick binary with higher byte content",
    ),
    ExpressionTestCase(
        "binary_content_first_byte_diff",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Binary(b"\x01\x00"), "b": Binary(b"\x02\x00")},
        expected=b"\x02\x00",
        msg="$max should compare binary content byte-by-byte from the start",
    ),
    ExpressionTestCase(
        "binary_content_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Binary(b"\xff"), "b": Binary(b"\x00")},
        expected=b"\xff",
        msg="$max should pick binary with higher content regardless of order",
    ),
    ExpressionTestCase(
        "binary_content_equal",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Binary(b"\x01\x02"), "b": Binary(b"\x01\x02")},
        expected=b"\x01\x02",
        msg="$max should return the value when both binaries have identical content",
    ),
    # Subtype comparison: same content, different subtypes.
    ExpressionTestCase(
        "binary_subtype_0_vs_5",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Binary(b"\x01", 0), "b": Binary(b"\x01", 5)},
        expected=Binary(b"\x01", 5),
        msg="$max should pick binary with higher subtype for same content",
    ),
    ExpressionTestCase(
        "binary_subtype_5_vs_0",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Binary(b"\x01", 5), "b": Binary(b"\x01", 0)},
        expected=Binary(b"\x01", 5),
        msg="$max should pick binary with higher subtype regardless of order",
    ),
]

# Property [Regex Comparison]: regex values are compared by pattern first,
# then by flags numerically, with higher values winning.
MAX_REGEX_COMPARISON_TESTS: list[ExpressionTestCase] = [
    # Pattern comparison: higher pattern string wins.
    ExpressionTestCase(
        "regex_pattern_b_vs_a",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Regex("b"), "b": Regex("a")},
        expected=Regex("b"),
        msg="$max should pick regex with higher pattern string",
    ),
    ExpressionTestCase(
        "regex_pattern_a_vs_b",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Regex("a"), "b": Regex("b")},
        expected=Regex("b"),
        msg="$max should pick regex with higher pattern regardless of order",
    ),
    # Pattern takes priority over flags.
    ExpressionTestCase(
        "regex_pattern_priority_over_flags",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Regex("b"), "b": Regex("a", "m")},
        expected=Regex("b"),
        msg="$max should compare pattern before flags",
    ),
    # Same pattern, flag comparison: m (8) > i (2).
    ExpressionTestCase(
        "regex_flags_m_vs_i",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Regex("abc", "i"), "b": Regex("abc", "m")},
        expected=Regex("abc", "m"),
        msg="$max should pick regex with higher flag value when patterns are equal",
    ),
    ExpressionTestCase(
        "regex_flags_m_vs_i_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Regex("abc", "m"), "b": Regex("abc", "i")},
        expected=Regex("abc", "m"),
        msg="$max should pick regex with higher flag value regardless of order",
    ),
    # Same pattern, flags vs no flags: flags win.
    ExpressionTestCase(
        "regex_flags_vs_none",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Regex("abc"), "b": Regex("abc", "i")},
        expected=Regex("abc", "i"),
        msg="$max should pick regex with flags over regex with no flags",
    ),
]

# Property [Code Comparison]: CodeWithScope is a higher BSON type than Code
# regardless of code string content, and within the same type comparison is
# by code string.
MAX_CODE_COMPARISON_TESTS: list[ExpressionTestCase] = [
    # Code vs Code: higher code string wins.
    ExpressionTestCase(
        "code_a_vs_b",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("a"), "b": Code("b")},
        expected=Code("b"),
        msg="$max should pick Code with higher code string",
    ),
    ExpressionTestCase(
        "code_b_vs_a",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("b"), "b": Code("a")},
        expected=Code("b"),
        msg="$max should pick Code with higher code string regardless of order",
    ),
    # CodeWithScope vs CodeWithScope: higher code string wins.
    ExpressionTestCase(
        "codewithscope_a_vs_b",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("a", {}), "b": Code("b", {})},
        expected=Code("b", {}),
        msg="$max should pick CodeWithScope with higher code string",
    ),
    ExpressionTestCase(
        "codewithscope_b_vs_a",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("b", {}), "b": Code("a", {})},
        expected=Code("b", {}),
        msg="$max should pick CodeWithScope with higher code string regardless of order",
    ),
    ExpressionTestCase(
        "codewithscope_equal_scope_diff",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("abc", {"x": 1}), "b": Code("abc", {"y": 2})},
        expected=Code("abc", {"y": 2}),
        msg="$max should compare scope as object when code strings are equal",
    ),
    # CodeWithScope beats Code regardless of code string content.
    ExpressionTestCase(
        "code_z_vs_codewithscope_a",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("z"), "b": Code("a", {})},
        expected=Code("a", {}),
        msg="$max should pick CodeWithScope over Code regardless of code string",
    ),
    ExpressionTestCase(
        "codewithscope_a_vs_code_z",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Code("a", {}), "b": Code("z")},
        expected=Code("a", {}),
        msg="$max should pick CodeWithScope over Code regardless of order",
    ),
]

MAX_NONSCALAR_TYPE_TESTS = (
    MAX_OBJECT_COMPARISON_TESTS
    + MAX_BINARY_COMPARISON_TESTS
    + MAX_REGEX_COMPARISON_TESTS
    + MAX_CODE_COMPARISON_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_NONSCALAR_TYPE_TESTS))
def test_max_nonscalar_type_cases(collection, test_case: ExpressionTestCase):
    """Test $max non-scalar type comparison cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
