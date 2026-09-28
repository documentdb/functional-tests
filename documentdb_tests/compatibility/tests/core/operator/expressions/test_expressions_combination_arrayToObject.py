"""
Combination tests for $arrayToObject composed with other operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR
from documentdb_tests.framework.parametrize import pytest_params

ARRAY_TO_OBJECT_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="arrayToObject_roundtrip_with_objectToArray",
        expression={"$arrayToObject": {"$objectToArray": "$obj"}},
        doc={"obj": {"a": 1, "b": 2}},
        expected={"a": 1, "b": 2},
        msg="Roundtrip should restore original object",
    ),
    ExpressionTestCase(
        id="arrayToObject_double_roundtrip",
        expression={"$arrayToObject": {"$objectToArray": {"$arrayToObject": "$arr"}}},
        doc={"arr": [["a", 1], ["b", 2]]},
        expected={"a": 1, "b": 2},
        msg="Double roundtrip: array → object → array → object should restore",
    ),
    ExpressionTestCase(
        id="arrayToObject_on_concatArrays",
        expression={"$arrayToObject": {"$concatArrays": ["$a", "$b"]}},
        doc={"a": [["a", 1]], "b": [["b", 2]]},
        expected={"a": 1, "b": 2},
        msg="Should work on $concatArrays result",
    ),
    ExpressionTestCase(
        id="arrayToObject_formats_produce_same_result",
        expression={
            "$eq": [
                {"$arrayToObject": "$pairs"},
                {"$arrayToObject": "$kv"},
            ]
        },
        doc={"pairs": [["a", 1], ["b", 2]], "kv": [{"k": "a", "v": 1}, {"k": "b", "v": 2}]},
        expected=True,
        msg="Both formats should produce identical output",
    ),
    ExpressionTestCase(
        id="arrayToObject_on_slice",
        expression={"$arrayToObject": {"$slice": ["$arr", 2]}},
        doc={"arr": [["a", 1], ["b", 2], ["c", 3]]},
        expected={"a": 1, "b": 2},
        msg="Should work on $slice result",
    ),
    ExpressionTestCase(
        id="arrayToObject_on_range_fails",
        expression={"$arrayToObject": {"$range": ["$start", "$end"]}},
        doc={"start": 0, "end": 3},
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$range produces numbers, should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_TO_OBJECT_COMBINATION_TESTS))
def test_arrayToObject_combination(collection, test):
    """Test $arrayToObject composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    expected = [{"result": test.expected}] if test.error_code is None else None
    assertResult(result, expected=expected, error_code=test.error_code, msg=test.msg)
