"""
Tests for object expression operator combinations and interactions.

Covers cross-operator tests ($setField, $unsetField, $mergeObjects with
$getField, $let, $cond, $ifNull, $switch, $map, $reduce, $add, $concat, $concatArrays),
self-nesting, alias equivalence, non-persistence, and subfield removal patterns.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.error_codes import (
    SET_FIELD_INVALID_INPUT_TYPE_ERROR,
    SET_FIELD_NON_CONST_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

EXPR_OP_SMOKE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "input_mergeObjects",
        expression={
            "$setField": {
                "field": "x",
                "input": {"$mergeObjects": [{"a": 1}, {"b": 2}]},
                "value": 3,
            }
        },
        expected={"a": 1, "b": 2, "x": 3},
        msg="$mergeObjects as input expression should succeed",
    ),
    ExpressionTestCase(
        "value_add",
        expression={"$setField": {"field": "x", "input": {}, "value": {"$add": [1, 2]}}},
        expected={"x": 3},
        msg="$add as value expression should succeed",
    ),
    ExpressionTestCase(
        "sf_let_input",
        expression={
            "$let": {
                "vars": {"doc": {"a": 1}},
                "in": {"$setField": {"field": "b", "input": "$$doc", "value": 2}},
            }
        },
        expected={"a": 1, "b": 2},
        msg="$let variable as input should succeed",
    ),
    ExpressionTestCase(
        "sf_let_value",
        expression={
            "$let": {
                "vars": {"val": 42},
                "in": {"$setField": {"field": "x", "input": {}, "value": "$$val"}},
            }
        },
        expected={"x": 42},
        msg="$let variable as value should succeed",
    ),
    ExpressionTestCase(
        "sf_cond_null_input",
        expression={
            "$setField": {"field": "x", "input": {"$cond": [False, {"a": 1}, None]}, "value": 1}
        },
        expected=None,
        msg="Conditional null input should return null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EXPR_OP_SMOKE_TESTS))
def test_setField_expr_op_smoke(collection, test):
    """Test $setField with other expression operators as input/value."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


INVALID_INPUT_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "input_resolves_to_int",
        expression={"$setField": {"field": "x", "input": {"$add": [1, 2]}, "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Input expression resolving to integer should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_resolves_to_array",
        expression={
            "$setField": {"field": "x", "input": {"$concatArrays": [[1], [2]]}, "value": 1}
        },
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Input expression resolving to array should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_resolves_to_string",
        expression={"$setField": {"field": "x", "input": {"$concat": ["a", "b"]}, "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Input expression resolving to string should error with invalid input type",
    ),
    ExpressionTestCase(
        "field_non_const_expr",
        expression={"$setField": {"field": {"$concat": ["a", "b"]}, "input": {}, "value": 1}},
        error_code=SET_FIELD_NON_CONST_FIELD_ERROR,
        msg="Non-constant $concat expression as field should error with non-const field",
    ),
    ExpressionTestCase(
        "field_non_const_cond",
        expression={"$setField": {"field": {"$cond": [True, "a", "b"]}, "input": {}, "value": 1}},
        error_code=SET_FIELD_NON_CONST_FIELD_ERROR,
        msg="Non-constant $cond expression as field should error with non-const field",
    ),
    ExpressionTestCase(
        "unset_field_non_const_concat",
        expression={"$unsetField": {"field": {"$concat": ["a", "b"]}, "input": {}}},
        error_code=SET_FIELD_NON_CONST_FIELD_ERROR,
        msg="$unsetField with non-constant $concat field should error with non-const field",
    ),
    ExpressionTestCase(
        "unset_field_non_const_cond",
        expression={"$unsetField": {"field": {"$cond": [True, "a", "b"]}, "input": {}}},
        error_code=SET_FIELD_NON_CONST_FIELD_ERROR,
        msg="$unsetField with non-constant $cond field should error with non-const field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_INPUT_EXPR_TESTS))
def test_setField_invalid_input_expr(collection, test):
    """Test $setField with expressions resolving to invalid types."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


GETFIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "roundtrip",
        expression={
            "$getField": {
                "field": "x",
                "input": {"$setField": {"field": "x", "input": {}, "value": 42}},
            }
        },
        expected=42,
        msg="Round-trip $setField then $getField should succeed and return set value",
    ),
    ExpressionTestCase(
        "roundtrip_dotted",
        expression={
            "$getField": {
                "field": "a.b",
                "input": {"$setField": {"field": "a.b", "input": {}, "value": 99}},
            }
        },
        expected=99,
        msg="Round-trip dotted field via $setField/$getField should succeed",
    ),
    ExpressionTestCase(
        "roundtrip_dollar",
        expression={
            "$getField": {
                "field": {"$literal": "$x"},
                "input": {"$setField": {"field": {"$literal": "$x"}, "input": {}, "value": 77}},
            }
        },
        expected=77,
        msg="Round-trip dollar field via $setField/$getField should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(GETFIELD_TESTS))
def test_setField_getField_interaction(collection, test):
    """Test $setField and $getField interaction."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_setField_getField_after_remove(collection):
    """Test $getField after $setField $$REMOVE returns missing."""
    result = execute_expression(
        collection,
        {
            "$getField": {
                "field": "a",
                "input": {"$setField": {"field": "a", "input": {"a": 1}, "value": "$$REMOVE"}},
            }
        },
    )
    assertSuccess(result, [{}])


MERGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "setField_then_merge",
        expression={
            "$mergeObjects": [{"$setField": {"field": "x", "input": {}, "value": 1}}, {"y": 2}]
        },
        expected={"x": 1, "y": 2},
        msg="$setField result merged with literal object should succeed",
    ),
    ExpressionTestCase(
        "merge_then_setField",
        expression={
            "$setField": {
                "field": "z",
                "input": {"$mergeObjects": [{"a": 1}, {"b": 2}]},
                "value": 3,
            }
        },
        expected={"a": 1, "b": 2, "z": 3},
        msg="$mergeObjects result as input to $setField should succeed",
    ),
    ExpressionTestCase(
        "merge_conflict",
        expression={
            "$mergeObjects": [{"$setField": {"field": "a", "input": {}, "value": 1}}, {"a": 2}]
        },
        expected={"a": 2},
        msg="Merge conflict with $setField result should succeed with last value winning",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MERGE_TESTS))
def test_setField_mergeObjects_interaction(collection, test):
    """Test $setField and $mergeObjects interaction."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


UNSET_GETFIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "getField_on_kept",
        expression={
            "$getField": {
                "field": "b",
                "input": {"$unsetField": {"field": "a", "input": {"a": 1, "b": 2}}},
            }
        },
        expected=2,
        msg="$getField on non-removed field should return value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_GETFIELD_TESTS))
def test_unsetField_getField_interaction(collection, test):
    """Test $unsetField and $getField interaction."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_unsetField_getField_on_removed(collection):
    """Test $getField on removed field returns missing."""
    result = execute_expression(
        collection,
        {
            "$getField": {
                "field": "a",
                "input": {"$unsetField": {"field": "a", "input": {"a": 1, "b": 2}}},
            }
        },
    )
    assertSuccess(result, [{}])


UNSET_MERGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "merge_after_unset",
        expression={
            "$mergeObjects": [{"$unsetField": {"field": "a", "input": {"a": 1, "b": 2}}}, {"c": 3}]
        },
        expected={"b": 2, "c": 3},
        msg="$mergeObjects after $unsetField should succeed and exclude removed field",
    ),
    ExpressionTestCase(
        "merge_readd_removed",
        expression={
            "$mergeObjects": [{"$unsetField": {"field": "a", "input": {"a": 1, "b": 2}}}, {"a": 99}]
        },
        expected={"b": 2, "a": 99},
        msg="$mergeObjects re-adding removed field should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_MERGE_TESTS))
def test_unsetField_mergeObjects_interaction(collection, test):
    """Test $unsetField and $mergeObjects interaction."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


UNSET_SETFIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "setField_then_unset",
        expression={
            "$unsetField": {
                "field": "a",
                "input": {"$setField": {"field": "a", "input": {"b": 1}, "value": 99}},
            }
        },
        expected={"b": 1},
        msg="$setField then $unsetField on same field should succeed and cancel out",
    ),
    ExpressionTestCase(
        "unset_then_setField",
        expression={
            "$setField": {
                "field": "a",
                "input": {"$unsetField": {"field": "a", "input": {"a": 1, "b": 2}}},
                "value": 99,
            }
        },
        expected={"b": 2, "a": 99},
        msg="$unsetField then $setField on same field should succeed and re-add",
    ),
    ExpressionTestCase(
        "uf_input_mergeObjects",
        expression={"$unsetField": {"field": "a", "input": {"$mergeObjects": [{"a": 1, "b": 2}]}}},
        expected={"b": 2},
        msg="$mergeObjects as $unsetField input expression should succeed",
    ),
    ExpressionTestCase(
        "uf_literal_field_setField",
        expression={
            "$unsetField": {
                "field": {"$literal": "$x"},
                "input": {"$setField": {"field": {"$literal": "$x"}, "input": {}, "value": 1}},
            }
        },
        expected={},
        msg="$literal field should succeed and remove dollar-prefixed field",
    ),
    ExpressionTestCase(
        "uf_let_input",
        expression={
            "$let": {
                "vars": {"doc": {"a": 1, "b": 2}},
                "in": {"$unsetField": {"field": "a", "input": "$$doc"}},
            }
        },
        expected={"b": 2},
        msg="$let variable as $unsetField input should succeed",
    ),
    ExpressionTestCase(
        "uf_idempotent",
        expression={
            "$unsetField": {
                "field": "a",
                "input": {"$unsetField": {"field": "a", "input": {"a": 1, "b": 2}}},
            }
        },
        expected={"b": 2},
        msg="Double unset of same field should succeed and be idempotent",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_SETFIELD_TESTS))
def test_unsetField_setField_interaction(collection, test):
    """Test $unsetField and $setField interaction."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


UNSET_INVALID_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "input_resolves_to_int",
        expression={"$unsetField": {"field": "x", "input": {"$add": [1, 2]}}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Input expression resolving to integer should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_resolves_to_array",
        expression={"$unsetField": {"field": "x", "input": {"$concatArrays": [[1], [2]]}}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Input expression resolving to array should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_resolves_to_string",
        expression={"$unsetField": {"field": "x", "input": {"$concat": ["a", "b"]}}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Input expression resolving to string should error with invalid input type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_INVALID_EXPR_TESTS))
def test_unsetField_invalid_input_expr(collection, test):
    """Test $unsetField with expressions resolving to invalid types."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


MERGE_GETFIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "getField_on_merged",
        expression={"$getField": {"field": "b", "input": {"$mergeObjects": [{"a": 1}, {"b": 2}]}}},
        expected=2,
        msg="$getField on $mergeObjects result should succeed and return value",
    ),
    ExpressionTestCase(
        "getField_overwritten",
        expression={"$getField": {"field": "a", "input": {"$mergeObjects": [{"a": 1}, {"a": 99}]}}},
        expected=99,
        msg="$getField on overwritten merged field should succeed and return last value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MERGE_GETFIELD_TESTS))
def test_mergeObjects_getField_interaction(collection, test):
    """Test $mergeObjects and $getField interaction."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


MERGE_SETFIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "merge_setField_results",
        expression={
            "$mergeObjects": [
                {"$setField": {"field": "a", "input": {}, "value": 1}},
                {"$setField": {"field": "b", "input": {}, "value": 2}},
            ]
        },
        expected={"a": 1, "b": 2},
        msg="Merging two $setField results should succeed",
    ),
    ExpressionTestCase(
        "setField_on_merged",
        expression={
            "$setField": {
                "field": "c",
                "input": {"$mergeObjects": [{"a": 1}, {"b": 2}]},
                "value": 3,
            }
        },
        expected={"a": 1, "b": 2, "c": 3},
        msg="$setField on $mergeObjects result should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MERGE_SETFIELD_TESTS))
def test_mergeObjects_setField_interaction(collection, test):
    """Test $mergeObjects and $setField interaction."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


MERGE_UNSETFIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "unsetField_on_merged",
        expression={
            "$unsetField": {"field": "b", "input": {"$mergeObjects": [{"a": 1}, {"b": 2, "c": 3}]}}
        },
        expected={"a": 1, "c": 3},
        msg="$unsetField on $mergeObjects result should succeed",
    ),
    ExpressionTestCase(
        "merge_unsetField_result",
        expression={
            "$mergeObjects": [
                {"$unsetField": {"field": "a", "input": {"a": 1, "b": 2}}},
                {"c": 3},
            ]
        },
        expected={"b": 2, "c": 3},
        msg="Merging $unsetField result with literal should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MERGE_UNSETFIELD_TESTS))
def test_mergeObjects_unsetField_interaction(collection, test):
    """Test $mergeObjects and $unsetField interaction."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


MERGE_COMBINATION_TESTS: list[ExpressionTestCase] = [
    # Self-nesting
    ExpressionTestCase(
        "merge_simple_nesting",
        expression={"$mergeObjects": [{"$mergeObjects": [{"a": 1}, {"b": 2}]}, {"c": 3}]},
        expected={"a": 1, "b": 2, "c": 3},
        msg="Nested $mergeObjects should succeed and merge all fields",
    ),
    ExpressionTestCase(
        "merge_deep_nesting",
        expression={
            "$mergeObjects": [
                {"$mergeObjects": [{"$mergeObjects": [{"a": 1}, {"b": 2}]}, {"c": 3}]},
                {"d": 4},
            ]
        },
        expected={"a": 1, "b": 2, "c": 3, "d": 4},
        msg="Deeply nested $mergeObjects should succeed and merge all fields",
    ),
    ExpressionTestCase(
        "merge_nested_conflict",
        expression={"$mergeObjects": [{"$mergeObjects": [{"a": 1}, {"b": 2}]}, {"a": 99}]},
        expected={"a": 99, "b": 2},
        msg="Nested $mergeObjects with conflicting key at outer level should succeed with last winning",  # noqa: E501
    ),
    # $cond interaction
    ExpressionTestCase(
        "merge_cond_true",
        expression={"$mergeObjects": [{"$cond": [True, {"a": 1}, {"b": 2}]}, {"c": 3}]},
        expected={"a": 1, "c": 3},
        msg="$cond true branch as merge input should succeed",
    ),
    ExpressionTestCase(
        "merge_cond_null",
        expression={"$mergeObjects": [{"$cond": [False, {"a": 1}, None]}, {"b": 2}]},
        expected={"b": 2},
        msg="$cond returning null should succeed and be ignored in merge",
    ),
    # $let interaction
    ExpressionTestCase(
        "merge_let",
        expression={"$let": {"vars": {"x": {"a": 1}}, "in": {"$mergeObjects": ["$$x", {"b": 2}]}}},
        expected={"a": 1, "b": 2},
        msg="$let variable as $mergeObjects input should succeed",
    ),
    # $switch interaction
    ExpressionTestCase(
        "merge_switch",
        expression={
            "$mergeObjects": [
                {"$switch": {"branches": [{"case": True, "then": {"a": 1}}], "default": {}}},
                {"b": 2},
            ]
        },
        expected={"a": 1, "b": 2},
        msg="$switch providing document as merge input should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MERGE_COMBINATION_TESTS))
def test_mergeObjects_combinations(collection, test):
    """Test $mergeObjects self-nesting and expression operator interactions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_mergeObjects_ifNull(collection):
    """Test $mergeObjects with $ifNull providing default."""
    result = execute_expression_with_insert(
        collection,
        {"$mergeObjects": [{"$ifNull": ["$missing", {"default": 1}]}, {"b": 2}]},
        {"x": 1},
    )
    assert_expression_result(
        result,
        expected={"default": 1, "b": 2},
        msg="$ifNull providing default doc as merge input should succeed",
    )


def test_mergeObjects_expression_operator(collection):
    """Test $mergeObjects with expression operator as element."""
    result = execute_expression_with_insert(
        collection,
        {"$mergeObjects": [{"$cond": [{"$eq": ["$x", 1]}, {"a": 1}, {"b": 2}]}, {"c": 3}]},
        {"x": 1},
    )
    assert_expression_result(
        result, expected={"a": 1, "c": 3}, msg="Expression operator as merge element should succeed"
    )


SETFIELD_NESTING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sf_nested_two_fields",
        expression={
            "$setField": {
                "field": "b",
                "input": {"$setField": {"field": "a", "input": {}, "value": 1}},
                "value": 2,
            }
        },
        expected={"a": 1, "b": 2},
        msg="Nested $setField adding two fields should succeed",
    ),
    ExpressionTestCase(
        "sf_triple_nested",
        expression={
            "$setField": {
                "field": "c",
                "input": {
                    "$setField": {
                        "field": "b",
                        "input": {"$setField": {"field": "a", "input": {}, "value": 1}},
                        "value": 2,
                    }
                },
                "value": 3,
            }
        },
        expected={"a": 1, "b": 2, "c": 3},
        msg="Triple nested $setField should succeed",
    ),
    ExpressionTestCase(
        "sf_nested_overwrite_same",
        expression={
            "$setField": {
                "field": "a",
                "input": {"$setField": {"field": "a", "input": {}, "value": 1}},
                "value": 2,
            }
        },
        expected={"a": 2},
        msg="Nested $setField overwriting same field should succeed with outer value winning",
    ),
    ExpressionTestCase(
        "sf_in_value",
        expression={
            "$setField": {
                "field": "x",
                "input": {},
                "value": {"$setField": {"field": "y", "input": {}, "value": 1}},
            }
        },
        expected={"x": {"y": 1}},
        msg="$setField in value position should succeed and produce nested document",
    ),
    ExpressionTestCase(
        "sf_add_then_remove",
        expression={
            "$setField": {
                "field": "x",
                "input": {"$setField": {"field": "x", "input": {}, "value": 1}},
                "value": "$$REMOVE",
            }
        },
        expected={},
        msg="Adding then removing same field should succeed and return empty",
    ),
    ExpressionTestCase(
        "sf_remove_then_add",
        expression={
            "$setField": {
                "field": "x",
                "input": {
                    "$setField": {"field": "x", "input": {"x": 1, "y": 2}, "value": "$$REMOVE"}
                },
                "value": 99,
            }
        },
        expected={"y": 2, "x": 99},
        msg="Removing then re-adding same field should succeed",
    ),
    ExpressionTestCase(
        "sf_double_remove",
        expression={
            "$setField": {
                "field": "a",
                "input": {"$setField": {"field": "a", "input": {"a": 1}, "value": "$$REMOVE"}},
                "value": "$$REMOVE",
            }
        },
        expected={},
        msg="Double remove of same field should succeed and return empty",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETFIELD_NESTING_TESTS))
def test_setField_nesting(collection, test):
    """Test nested $setField operations."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


UNSET_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "uf_equivalence_unset",
        expression={"$unsetField": {"field": "x", "input": {"x": 1, "y": 2}}},
        expected={"y": 2},
        msg="$unsetField should succeed and remove field",
    ),
    ExpressionTestCase(
        "sf_equivalence_remove",
        expression={"$setField": {"field": "x", "input": {"x": 1, "y": 2}, "value": "$$REMOVE"}},
        expected={"y": 2},
        msg="$setField with $$REMOVE should succeed and produce same result as $unsetField",
    ),
    ExpressionTestCase(
        "uf_case_sensitive_lower",
        expression={
            "$unsetField": {
                "field": "name",
                "input": {
                    "$setField": {
                        "field": "name",
                        "input": {"$setField": {"field": "Name", "input": {}, "value": 1}},
                        "value": 2,
                    }
                },
            }
        },
        expected={"Name": 1},
        msg="Should remove lowercase name, keep uppercase Name",
    ),
    ExpressionTestCase(
        "uf_case_sensitive_upper",
        expression={
            "$unsetField": {
                "field": "Name",
                "input": {
                    "$setField": {
                        "field": "Name",
                        "input": {"$setField": {"field": "name", "input": {}, "value": 2}},
                        "value": 1,
                    }
                },
            }
        },
        expected={"name": 2},
        msg="Should remove uppercase Name, keep lowercase name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_EQUIVALENCE_TESTS))
def test_unsetField_equivalence(collection, test):
    """Test $unsetField/$setField equivalence and case sensitivity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


UNSET_CHAIN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "uf_chain_two",
        expression={
            "$unsetField": {
                "field": "a",
                "input": {"$unsetField": {"field": "b", "input": {"a": 1, "b": 2, "c": 3}}},
            }
        },
        expected={"c": 3},
        msg="Chaining two $unsetField operations should succeed",
    ),
    ExpressionTestCase(
        "uf_chain_three_empty",
        expression={
            "$unsetField": {
                "field": "a",
                "input": {
                    "$unsetField": {
                        "field": "b",
                        "input": {"$unsetField": {"field": "c", "input": {"a": 1, "b": 2, "c": 3}}},
                    }
                },
            }
        },
        expected={},
        msg="Chaining three $unsetField operations should succeed and return empty doc",
    ),
    ExpressionTestCase(
        "uf_chain_inner_null",
        expression={
            "$unsetField": {"field": "a", "input": {"$unsetField": {"field": "x", "input": None}}}
        },
        expected=None,
        msg="Chaining $unsetField where inner returns null should succeed and return null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_CHAIN_TESTS))
def test_unsetField_chaining(collection, test):
    """Test chaining multiple $unsetField operations."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_unsetField_subfield_removal(collection):
    """Test removing subfield using $setField + nested $unsetField."""
    result = execute_expression(
        collection,
        {
            "$setField": {
                "field": "price",
                "input": {"price": {"usd": 45.99, "euro": 38.77}},
                "value": {
                    "$unsetField": {
                        "field": "euro",
                        "input": {
                            "$getField": {
                                "field": "price",
                                "input": {"price": {"usd": 45.99, "euro": 38.77}},
                            }
                        },
                    }
                },
            }
        },
    )
    assert_expression_result(
        result,
        expected={"price": {"usd": 45.99}},
        msg="Removing subfield via nested $setField/$unsetField/$getField should succeed",
    )
