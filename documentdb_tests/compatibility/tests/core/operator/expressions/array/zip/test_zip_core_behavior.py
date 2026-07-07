"""
Core behavior tests for $zip expression.

Tests zipping arrays of various element types, equal/unequal lengths,
useLongestLength, defaults, empty arrays, single arrays, nested arrays,
null propagation, and large arrays.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.array.zip.utils.zip_common import (  # noqa: E501
    ZipTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Success: basic zipping — equal length arrays
# Property [Basic Transform]: $map applies an expression to each element.
BASIC_TESTS: list[ZipTest] = [
    ZipTest(
        id="two_int_arrays",
        inputs=[[1, 2, 3], [10, 20, 30]],
        expected=[[1, 10], [2, 20], [3, 30]],
        msg="Should zip two int arrays",
    ),
    ZipTest(
        id="two_string_arrays",
        inputs=[["a", "b"], ["c", "d"]],
        expected=[["a", "c"], ["b", "d"]],
        msg="Should zip two string arrays",
    ),
    ZipTest(
        id="three_arrays",
        inputs=[[1, 2], [10, 20], [100, 200]],
        expected=[[1, 10, 100], [2, 20, 200]],
        msg="Should zip three arrays",
    ),
    ZipTest(
        id="mixed_type_elements",
        inputs=[[1, "two"], [True, None]],
        expected=[[1, True], ["two", None]],
        msg="Should zip arrays with mixed types",
    ),
    ZipTest(
        id="numeric_cross_types",
        inputs=[[1, Int64(2)], [3.0, Decimal128("4")]],
        expected=[[1, 3.0], [Int64(2), Decimal128("4")]],
        msg="Should zip mixed numeric type arrays",
    ),
]

# Success: unequal length — truncate to shortest (default)
# Property [Unequal Length]: $zip truncates to the shortest array.
UNEQUAL_LENGTH_TESTS: list[ZipTest] = [
    ZipTest(
        id="first_shorter",
        inputs=[[1, 2], [10, 20, 30]],
        expected=[[1, 10], [2, 20]],
        msg="Should truncate to shorter first array",
    ),
    ZipTest(
        id="second_shorter",
        inputs=[[1, 2, 3], [10, 20]],
        expected=[[1, 10], [2, 20]],
        msg="Should truncate to shorter second array",
    ),
    ZipTest(
        id="one_empty",
        inputs=[[], [1, 2, 3]],
        expected=[],
        msg="Empty array should produce empty result",
    ),
]

# Success: useLongestLength
USE_LONGEST_TESTS: list[ZipTest] = [
    ZipTest(
        id="longest_pads_null",
        inputs=[[1, 2, 3], [10, 20]],
        use_longest_length=True,
        expected=[[1, 10], [2, 20], [3, None]],
        msg="Should pad shorter array with null",
    ),
    ZipTest(
        id="longest_both_short",
        inputs=[[1], [10, 20], [100, 200, 300]],
        use_longest_length=True,
        expected=[[1, 10, 100], [None, 20, 200], [None, None, 300]],
        msg="Should pad multiple shorter arrays with null",
    ),
    ZipTest(
        id="longest_equal_length",
        inputs=[[1, 2], [10, 20]],
        use_longest_length=True,
        expected=[[1, 10], [2, 20]],
        msg="Equal length with useLongestLength should behave same",
    ),
    ZipTest(
        id="longest_false_truncates",
        inputs=[[1, 2, 3], [10, 20]],
        use_longest_length=False,
        expected=[[1, 10], [2, 20]],
        msg="useLongestLength false should truncate",
    ),
]

# Success: defaults
# Property [Defaults]: $zip pads shorter arrays with default values.
DEFAULTS_TESTS: list[ZipTest] = [
    ZipTest(
        id="defaults_fill_shorter",
        inputs=[[1, 2, 3], [10, 20]],
        use_longest_length=True,
        defaults=[0, 0],
        expected=[[1, 10], [2, 20], [3, 0]],
        msg="Should fill shorter array with default value",
    ),
    ZipTest(
        id="defaults_multiple_arrays",
        inputs=[[1], [10, 20], [100, 200, 300]],
        use_longest_length=True,
        defaults=[-1, -2, -3],
        expected=[[1, 10, 100], [-1, 20, 200], [-1, -2, 300]],
        msg="Should fill multiple shorter arrays with respective defaults",
    ),
    ZipTest(
        id="defaults_null_value",
        inputs=[[1, 2, 3], [10]],
        use_longest_length=True,
        defaults=[None, None],
        expected=[[1, 10], [2, None], [3, None]],
        msg="Null defaults should work same as no defaults",
    ),
    ZipTest(
        id="defaults_string",
        inputs=[[1, 2, 3], ["a"]],
        use_longest_length=True,
        defaults=[0, "missing"],
        expected=[[1, "a"], [2, "missing"], [3, "missing"]],
        msg="Should use string default value",
    ),
    ZipTest(
        id="defaults_not_used_equal_length",
        inputs=[[1, 2], [10, 20]],
        use_longest_length=True,
        defaults=[0, 0],
        expected=[[1, 10], [2, 20]],
        msg="Defaults not used when arrays are equal length",
    ),
    ZipTest(
        id="defaults_falsy_empty_string",
        inputs=[[1, 2], ["a"]],
        use_longest_length=True,
        defaults=[0, ""],
        expected=[[1, "a"], [2, ""]],
        msg="Falsy defaults (empty string) used correctly",
    ),
    ZipTest(
        id="defaults_false",
        inputs=[[1, 2], ["a"]],
        use_longest_length=True,
        defaults=[0, False],
        expected=[[1, "a"], [2, False]],
        msg="False default used correctly",
    ),
    ZipTest(
        id="defaults_complex_types",
        inputs=[[1, 2], ["a"]],
        use_longest_length=True,
        defaults=[{"x": 1}, [1, 2]],
        expected=[[1, "a"], [2, [1, 2]]],
        msg="Complex type defaults used correctly",
    ),
    ZipTest(
        id="defaults_nested_array",
        inputs=[[1, 2], ["a"]],
        use_longest_length=True,
        defaults=[[1, 2], "fallback"],
        expected=[[1, "a"], [2, "fallback"]],
        msg="Nested array default used as-is",
    ),
]

# Success: empty and single element
DEGENERATE_TESTS: list[ZipTest] = [
    ZipTest(
        id="both_empty",
        inputs=[[], []],
        expected=[],
        msg="Should return empty for two empty arrays",
    ),
    ZipTest(
        id="three_empty",
        inputs=[[], [], []],
        expected=[],
        msg="Three empty arrays return []",
    ),
    ZipTest(
        id="single_empty",
        inputs=[[]],
        expected=[],
        msg="Single empty array returns []",
    ),
    ZipTest(
        id="single_element_each",
        inputs=[[1], [10]],
        expected=[[1, 10]],
        msg="Should zip single-element arrays",
    ),
    ZipTest(
        id="single_input_array",
        inputs=[[1, 2, 3]],
        expected=[[1], [2], [3]],
        msg="Single input should wrap each element",
    ),
    ZipTest(
        id="all_single_element_three",
        inputs=[[1], ["a"], [True]],
        expected=[[1, "a", True]],
        msg="All single-element arrays produce one row",
    ),
    ZipTest(
        id="empty_with_longest_false",
        inputs=[[], [1, 2, 3]],
        expected=[],
        msg="Empty array with shortest length returns []",
    ),
    ZipTest(
        id="empty_with_longest_true",
        inputs=[[], [1, 2, 3]],
        use_longest_length=True,
        expected=[[None, 1], [None, 2], [None, 3]],
        msg="Empty array with longest length pads with null",
    ),
    ZipTest(
        id="two_empty_longest_true",
        inputs=[[], []],
        use_longest_length=True,
        expected=[],
        msg="Two empty arrays with longest length return []",
    ),
]

# Success: nested arrays as elements
# Property [Nested Arrays]: $map operates on nested array structures.
NESTED_ARRAY_TESTS: list[ZipTest] = [
    ZipTest(
        id="nested_arrays",
        inputs=[[[1, 2], [3, 4]], ["a", "b"]],
        expected=[[[1, 2], "a"], [[3, 4], "b"]],
        msg="Should zip nested arrays as elements",
    ),
    ZipTest(
        id="objects_as_elements",
        inputs=[[{"x": 1}, {"x": 2}], [{"y": 10}, {"y": 20}]],
        expected=[[{"x": 1}, {"y": 10}], [{"x": 2}, {"y": 20}]],
        msg="Objects preserved as elements",
    ),
    ZipTest(
        id="mixed_types_six",
        inputs=[[1, "a", None, True, {"k": 1}, [9]], [10, 20, 30, 40, 50, 60]],
        expected=[[1, 10], ["a", 20], [None, 30], [True, 40], [{"k": 1}, 50], [[9], 60]],
        msg="Mixed types preserved in transposition",
    ),
]

# Success: null propagation
NULL_TESTS: list[ZipTest] = [
    ZipTest(
        id="null_first_input",
        inputs=[None, [1, 2]],
        expected=None,
        msg="Should return null when first input is null",
    ),
    ZipTest(
        id="null_second_input",
        inputs=[[1, 2], None],
        expected=None,
        msg="Should return null when second input is null",
    ),
    ZipTest(
        id="all_null_inputs",
        inputs=[None, None],
        expected=None,
        msg="Should return null when all inputs are null",
    ),
    ZipTest(
        id="null_elements_in_arrays",
        inputs=[[1, None], [None, 2]],
        expected=[[1, None], [None, 2]],
        msg="Should preserve null elements within arrays",
    ),
]

# Success: objects as elements
OBJECT_TESTS: list[ZipTest] = [
    ZipTest(
        id="arrays_of_objects",
        inputs=[[{"a": 1}], [{"b": 2}]],
        expected=[[{"a": 1}, {"b": 2}]],
        msg="Should zip arrays of objects",
    ),
]

# Success: large arrays
# Property [Large Arrays]: $map handles large arrays.
LARGE_ARRAY_TESTS: list[ZipTest] = [
    ZipTest(
        id="large_arrays",
        inputs=[list(range(1000)), list(range(1000, 2000))],
        expected=[[i, i + 1000] for i in range(1000)],
        msg="Should zip large arrays",
    ),
]

# Success: many input arrays
MANY_INPUTS_TESTS: list[ZipTest] = [
    ZipTest(
        id="ten_inputs",
        inputs=[[i] for i in range(10)],
        expected=[list(range(10))],
        msg="Ten inputs transpose correctly",
    ),
    ZipTest(
        id="fifty_inputs",
        inputs=[[i] for i in range(50)],
        expected=[list(range(50))],
        msg="50 single-element inputs produce one 50-element row",
    ),
]

# Success: multiple arrays of different lengths
MULTI_LENGTH_TESTS: list[ZipTest] = [
    ZipTest(
        id="three_arrays_shortest",
        inputs=[[1], [10, 20, 30], [100, 200, 300, 400, 500]],
        expected=[[1, 10, 100]],
        msg="Three arrays shortest = 1",
    ),
    ZipTest(
        id="three_arrays_longest_no_defaults",
        inputs=[[1], [10, 20, 30], [100, 200, 300, 400, 500]],
        use_longest_length=True,
        expected=[
            [1, 10, 100],
            [None, 20, 200],
            [None, 30, 300],
            [None, None, 400],
            [None, None, 500],
        ],
        msg="Three arrays longest pads with null",
    ),
    ZipTest(
        id="three_arrays_longest_with_defaults",
        inputs=[[1], [10, 20, 30], [100, 200, 300, 400, 500]],
        use_longest_length=True,
        defaults=[0, "x", False],
        expected=[[1, 10, 100], [0, 20, 200], [0, 30, 300], [0, "x", 400], [0, "x", 500]],
        msg="Three arrays longest with defaults",
    ),
    ZipTest(
        id="four_arrays_two_empty",
        inputs=[[], [], [1, 2], [3, 4, 5]],
        use_longest_length=True,
        expected=[[None, None, 1, 3], [None, None, 2, 4], [None, None, None, 5]],
        msg="Four arrays two empty with longest",
    ),
]

# Aggregate and test
ALL_TESTS = (
    BASIC_TESTS
    + UNEQUAL_LENGTH_TESTS
    + USE_LONGEST_TESTS
    + DEFAULTS_TESTS
    + DEGENERATE_TESTS
    + NESTED_ARRAY_TESTS
    + NULL_TESTS
    + OBJECT_TESTS
    + LARGE_ARRAY_TESTS
    + MANY_INPUTS_TESTS
    + MULTI_LENGTH_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_zip_insert(collection, test):
    """Test $zip with values from inserted documents."""
    expr = {}
    expr["inputs"] = [f"$arr{i}" for i in range(len(test.inputs))]
    if test.use_longest_length is not None:
        expr["useLongestLength"] = test.use_longest_length
    if test.defaults is not None:
        expr["defaults"] = test.defaults
    doc = {f"arr{i}": arr for i, arr in enumerate(test.inputs)}
    result = execute_expression_with_insert(collection, {"$zip": expr}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


TEST_SUBSET_FOR_LITERAL = [
    BASIC_TESTS[0],  # two_int_arrays
    BASIC_TESTS[2],  # three_arrays
    UNEQUAL_LENGTH_TESTS[0],  # first_shorter
    DEGENERATE_TESTS[0],  # both_empty
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_zip_literal(collection, test):
    """Test $zip with literal values."""
    expr = {}
    expr["inputs"] = [{"$literal": a} for a in test.inputs]
    if test.use_longest_length is not None:
        expr["useLongestLength"] = test.use_longest_length
    if test.defaults is not None:
        expr["defaults"] = test.defaults
    result = execute_expression(collection, {"$zip": expr})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
