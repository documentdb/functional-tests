"""
Combination tests for $objectToArray composed with other operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

OBJECT_TO_ARRAY_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="objectToArray_roundtrip_with_arrayToObject",
        expression={"$arrayToObject": {"$objectToArray": "$obj"}},
        doc={"obj": {"a": 1, "b": 2, "c": 3}},
        expected={"a": 1, "b": 2, "c": 3},
        msg="Roundtrip should restore original object",
    ),
    ExpressionTestCase(
        id="objectToArray_roundtrip_preserves_null_in_nested",
        expression={"$arrayToObject": {"$objectToArray": "$nested"}},
        doc={"nested": {"empty_nested": {}, "null_nested": None}},
        expected={"empty_nested": {}, "null_nested": None},
        msg="Round-trip should preserve null values in nested doc",
    ),
    ExpressionTestCase(
        id="objectToArray_of_arrayToObject",
        expression={"$objectToArray": {"$arrayToObject": "$kv"}},
        doc={"kv": [{"k": "a", "v": 1}, {"k": "b", "v": 2}]},
        expected=[{"k": "a", "v": 1}, {"k": "b", "v": 2}],
        msg="Array-side inverse: objectToArray(arrayToObject(kv_array)) restores the kv array",
    ),
    ExpressionTestCase(
        id="objectToArray_on_mergeObjects",
        expression={"$objectToArray": {"$mergeObjects": ["$a", "$b"]}},
        doc={"a": {"a": 1}, "b": {"b": 2}},
        expected=[{"k": "a", "v": 1}, {"k": "b", "v": 2}],
        msg="Should convert merged object",
    ),
    ExpressionTestCase(
        id="objectToArray_1000_fields",
        expression={"$size": {"$objectToArray": "$obj"}},
        doc={"obj": {f"field_{i}": i for i in range(1000)}},
        expected=1000,
        msg="Should handle 1000 fields",
    ),
    ExpressionTestCase(
        id="objectToArray_with_arrayElemAt",
        expression={"$arrayElemAt": [{"$objectToArray": "$obj"}, 0]},
        doc={"obj": {"a": 1, "b": 2, "c": 3}},
        expected={"k": "a", "v": 1},
        msg="Should return first element",
    ),
    ExpressionTestCase(
        id="objectToArray_with_concatArrays",
        expression={"$concatArrays": [{"$objectToArray": "$a"}, {"$objectToArray": "$b"}]},
        doc={"a": {"a": 1}, "b": {"b": 2}},
        expected=[{"k": "a", "v": 1}, {"k": "b", "v": 2}],
        msg="Should concatenate two arrays",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OBJECT_TO_ARRAY_COMBINATION_TESTS))
def test_objectToArray_combination(collection, test):
    """Test $objectToArray composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
