"""
Core missing-value semantics for the $$REMOVE system variable.

$$REMOVE evaluates to missing, so assigning it to a field omits that field
instead of setting it to null. Covers type-independence, {$type} reporting
"missing", the null-vs-missing distinction, reserved-name handling, and
$group/$match with $expr.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_project,
    execute_project_with_insert,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (  # noqa: E501
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    LET_UNDEFINED_VARIABLE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import BSON_TYPE_SAMPLES

# Property [Type Independence]: $$REMOVE evaluates to missing regardless of the
# BSON type of the value it replaces, since it takes no input and cannot behave
# differently per replaced-value type.
VALUE_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"{bson_type.value}_value",
        expression={"a": "$$REMOVE"},
        doc={"a": sample},
        expected=[{}],
        msg=f"Should omit field holding a {bson_type.value} value",
    )
    for bson_type, sample in BSON_TYPE_SAMPLES.items()
]


@pytest.mark.parametrize("test", pytest_params(VALUE_TYPE_TESTS))
def test_remove_variable_omits_field_regardless_of_value_type(collection, test):
    """$$REMOVE evaluates to missing regardless of the replaced value's BSON type."""
    result = execute_project_with_insert(collection, test.doc, test.expression)
    assertSuccess(result, test.expected, test.msg)


def test_remove_variable_distinct_from_explicit_null(collection):
    """Assigning null keeps the field present with a null value, unlike $$REMOVE."""
    result = execute_project_with_insert(
        collection, {"a": 1, "b": 1}, {"a": "$$REMOVE", "b": {"$literal": None}}
    )
    assertSuccess(
        result,
        [{"b": None}],
        "$$REMOVE should omit its field while an explicit null stays present",
    )


def test_remove_variable_field_absent_for_downstream_exists_check(collection):
    """A field set to $$REMOVE is seen as non-existent by a later stage."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"a": "$$REMOVE"}},
                {"$match": {"a": {"$exists": False}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1}],
        "Downstream stage should observe the removed field as non-existent",
    )


def test_remove_variable_field_not_matched_as_null_downstream(collection):
    """A field set to $$REMOVE is missing, not null, for a later stage's type match."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"a": "$$REMOVE"}},
                {"$match": {"a": {"$type": "null"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [],
        "Removed field should not match a null type check downstream",
    )


def test_remove_variable_projection_shape_matches_inclusion_projection(collection):
    """Removing a field yields the same shape as an inclusion projection omitting it."""
    collection.insert_one({"_id": 1, "a": 1, "b": 2})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"a": "$$REMOVE", "b": 1}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "b": 2}],
        "$$REMOVE projection should match inclusion projection that omits the field",
    )


def test_remove_variable_lowercase_reference_is_undefined_variable(collection):
    """Lowercase $$remove is an ordinary user variable, so it is undefined here."""
    result = execute_project(collection, {"v": "$$remove"})
    assertFailureCode(
        result,
        LET_UNDEFINED_VARIABLE_ERROR,
        "$$remove should be treated as an undefined user variable",
    )


def test_remove_variable_mixed_case_reference_is_undefined_variable(collection):
    """Mixed-case $$Remove is an ordinary user variable, so it is undefined here."""
    result = execute_project(collection, {"v": "$$Remove"})
    assertFailureCode(
        result,
        LET_UNDEFINED_VARIABLE_ERROR,
        "$$Remove should be treated as an undefined user variable",
    )


# Property [Pipeline Stage Resolution]: $$REMOVE resolves to missing wherever a
# pipeline stage evaluates it as an expression — as a $group key and inside
# $match's $expr — not just in $project/$addFields field assignment.
PIPELINE_CONTEXT_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="as_group_id_expression",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        pipeline=[{"$group": {"_id": "$$REMOVE", "n": {"$sum": 1}}}],
        expected=[{"_id": None, "n": 3}],
        msg="Documents with a missing group key should group together",
    ),
    StageTestCase(
        id="in_match_expr",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        pipeline=[{"$match": {"$expr": {"$eq": [{"$type": "$$REMOVE"}, "missing"]}}}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        msg="$match with $expr should evaluate $$REMOVE as missing",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PIPELINE_CONTEXT_TESTS))
def test_remove_variable_in_pipeline_context(collection, test: StageTestCase):
    """$$REMOVE resolves to missing in $group and $match with $expr contexts."""
    populate_collection(collection, test)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, test.msg, ignore_doc_order=True)


def test_remove_variable_removed_field_observed_missing_by_later_group(collection):
    """A field removed in an early stage is grouped as missing by a later stage."""
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"a": "$$REMOVE"}},
                {"$group": {"_id": "$a", "n": {"$sum": 1}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": None, "n": 2}],
        "Later stage should see the removed field as missing and group it as null",
    )
