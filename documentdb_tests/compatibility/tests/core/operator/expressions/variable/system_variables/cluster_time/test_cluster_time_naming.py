"""
$$CLUSTER_TIME reference syntax and namespace exactness.

Exact-match name, no case folding or prefix matching. Silent traps: the
single-dollar form resolves as a field path, and references outside $expr or a
pipeline update are treated as literal strings. Reserved-name conflicts with
$let/$map/$filter live with those features.

Not covered here because an identical case already exists elsewhere: bare "$"
and "$$" tokens and embedded whitespace or a triple-dollar prefix, which the
variable-name lexer rejects regardless of the name (see the $$USER_ROLES,
$$PRUNE and $$DESCEND naming files); the ".t" sub-path, covered by the shared
expression-engine file; and $literal suppression, covered by the $literal
folder.
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
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    LET_UNDEFINED_VARIABLE_ERROR,
    PROJECT_UNKNOWN_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.aggregate, pytest.mark.requires(cluster_time=True)]


# Property [Namespace Exactness]: the system-variable namespace is matched
# exactly. Near-miss spellings are undefined variables, not the system variable.
NEAR_MISS_NAME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="lower_case",
        expression="$$cluster_time",
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="A lower-case spelling should not resolve to the system variable",
    ),
    ExpressionTestCase(
        id="mixed_case",
        expression="$$Cluster_Time",
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="A mixed-case spelling should not resolve to the system variable",
    ),
    ExpressionTestCase(
        id="no_underscore",
        expression="$$CLUSTERTIME",
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="A spelling without the underscore should not resolve to the system variable",
    ),
    ExpressionTestCase(
        id="prefix_only",
        expression="$$CLUSTER",
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="A prefix of the name should not resolve to the system variable",
    ),
    ExpressionTestCase(
        id="suffixed",
        expression="$$CLUSTER_TIME_2",
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="A suffixed name should not resolve to the system variable",
    ),
    ExpressionTestCase(
        id="plural",
        expression="$$CLUSTER_TIMES",
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="A pluralized name should not resolve to the system variable",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NEAR_MISS_NAME_TESTS))
def test_cluster_time_near_miss_name(collection, test: ExpressionTestCase):
    """Test near-miss spellings do not resolve to the $$CLUSTER_TIME system variable."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


# Property [Scalar Has No Sub-Fields]: dot notation on the timestamp yields
# missing rather than exposing the timestamp's seconds and increment parts. The
# seconds component is covered once in the shared expression-engine file.
DOT_SUFFIX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="increment_component",
        expression={"$type": "$$CLUSTER_TIME.i"},
        expected="missing",
        msg="Dot notation should not expose the timestamp's increment component",
    ),
    ExpressionTestCase(
        id="unknown_field",
        expression={"$type": "$$CLUSTER_TIME.foo"},
        expected="missing",
        msg="An unknown sub-field of $$CLUSTER_TIME should be missing, not an error",
    ),
    ExpressionTestCase(
        id="numeric_index",
        expression={"$type": "$$CLUSTER_TIME.0"},
        expected="missing",
        msg="A numeric sub-path of $$CLUSTER_TIME should be missing, not an error",
    ),
    ExpressionTestCase(
        id="deep_path",
        expression={"$type": "$$CLUSTER_TIME.a.b.c"},
        expected="missing",
        msg="A deep sub-path of $$CLUSTER_TIME should be missing, not an error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DOT_SUFFIX_TESTS))
def test_cluster_time_dot_suffix(collection, test: ExpressionTestCase):
    """Test dot notation on the scalar $$CLUSTER_TIME resolves to missing."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_cluster_time_without_dollars_is_a_string(collection):
    """Test the bare name without dollar signs is an ordinary string literal."""
    result = execute_expression(collection, {"$type": "CLUSTER_TIME"})
    assert_expression_result(
        result,
        expected="string",
        msg="The bare name without dollars should be a string literal",
    )


def test_single_dollar_cluster_time_is_missing_without_the_field(collection):
    """Test the single-dollar form resolves to missing on a document lacking that field."""
    result = execute_expression_with_insert(collection, {"$type": "$CLUSTER_TIME"}, {"_id": 1})
    assert_expression_result(
        result,
        expected="missing",
        msg="The single-dollar form is a field path and should be missing when absent",
    )


def test_single_dollar_cluster_time_returns_the_document_field(collection):
    """Test the single-dollar form returns a document field literally named CLUSTER_TIME."""
    result = execute_expression_with_insert(
        collection, "$CLUSTER_TIME", {"_id": 1, "CLUSTER_TIME": "field value"}
    )
    assert_expression_result(
        result,
        expected="field value",
        msg="The single-dollar form should return the same-named document field",
    )


def test_field_and_variable_forms_coexist_in_one_projection(collection):
    """Test a same-named document field and the system variable resolve independently."""
    collection.insert_one({"_id": 1, "CLUSTER_TIME": "field value"})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        "field": "$CLUSTER_TIME",
                        "variable": {"$type": "$$CLUSTER_TIME"},
                    }
                }
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"field": "field value", "variable": "timestamp"}],
        msg="A same-named document field and $$CLUSTER_TIME should not collide",
    )


def test_nested_same_named_field_is_unaffected_by_the_variable(collection):
    """Test a nested field named CLUSTER_TIME resolves to the document value."""
    result = execute_expression_with_insert(
        collection, "$a.CLUSTER_TIME", {"_id": 1, "a": {"CLUSTER_TIME": 7}}
    )
    assert_expression_result(
        result,
        expected=7,
        msg="A nested same-named field should resolve to the document value",
    )


def test_same_named_field_and_variable_group_independently(collection):
    """Test grouping by a same-named field is unaffected by the system variable."""
    collection.insert_many([{"_id": 1, "CLUSTER_TIME": "a"}, {"_id": 2, "CLUSTER_TIME": "b"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$CLUSTER_TIME"}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": "a"}, {"_id": "b"}],
        msg="Grouping by a same-named document field should use the field, not the variable",
    )


def test_cluster_time_rejected_as_an_operator_name(collection):
    """Test the variable name used as an operator is an unknown-operator error."""
    result = execute_expression(collection, {"$CLUSTER_TIME": []})
    assert_expression_result(
        result,
        error_code=PROJECT_UNKNOWN_EXPRESSION_ERROR,
        msg="The variable name should not be usable as an operator",
    )


def test_cluster_time_rejected_as_a_projection_key(collection):
    """Test a variable reference used as a field name is rejected."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"$$CLUSTER_TIME": 1}}],
            "cursor": {},
        },
    )

    assertFailureCode(
        result,
        FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="A variable reference should not be usable as a projection field name",
    )


def test_cluster_time_rejected_as_an_add_fields_key(collection):
    """Test assigning to a variable reference through $addFields is rejected."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$addFields": {"$$CLUSTER_TIME": 1}}],
            "cursor": {},
        },
    )

    assertFailureCode(
        result,
        FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="A variable reference should not be assignable through $addFields",
    )


@pytest.mark.find
def test_cluster_time_in_a_plain_find_filter_is_a_string(collection):
    """Test a reference in a non-$expr find filter matches the literal string only."""
    collection.insert_many([{"_id": 1, "ts": "$$CLUSTER_TIME"}, {"_id": 2, "ts": "other"}])

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"ts": "$$CLUSTER_TIME"},
            "projection": {"_id": 1},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1}],
        msg="A non-$expr filter should compare against the literal string, not the variable",
    )


def test_cluster_time_in_a_plain_match_is_a_string(collection):
    """Test a reference in a $match without $expr matches the literal string only."""
    collection.insert_many([{"_id": 1, "ts": "$$CLUSTER_TIME"}, {"_id": 2, "ts": "other"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"ts": "$$CLUSTER_TIME"}}, {"$project": {"_id": 1}}],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1}],
        msg="A $match without $expr should compare against the literal string",
    )


@pytest.mark.update
def test_cluster_time_in_a_non_pipeline_update_stores_a_string(collection):
    """Test a non-pipeline update stores the reference text rather than a timestamp."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"ts": "$$CLUSTER_TIME"}}}],
        },
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "kind": {"$type": "$ts"}}}],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"kind": "string"}],
        msg="A non-pipeline update should store the reference text as a string",
    )
