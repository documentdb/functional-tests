"""
Tests for findAndModify error cases: argument conflicts, immutable field
violations, invalid projections, constraint violations, and arrayFilters errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
    IndexModel,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    DOCUMENT_VALIDATION_FAILURE_ERROR,
    DOLLAR_PREFIXED_FIELD_NAME_ERROR,
    DUPLICATE_KEY_ERROR,
    FAILED_TO_PARSE_ERROR,
    IMMUTABLE_FIELD_ERROR,
    INVALID_OPTIONS_ERROR,
    LET_UNDEFINED_VARIABLE_ERROR,
    PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
    PROJECT_UNKNOWN_EXPRESSION_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ARGUMENT_CONFLICT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "neither-update-nor-remove",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="findAndModify with neither update nor remove should fail",
    ),
    CommandTestCase(
        "both-remove-and-update",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
            "remove": True,
            "update": {"$set": {"x": 1}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="findAndModify with both remove and update should fail",
    ),
    CommandTestCase(
        "remove-and-new-true",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
            "remove": True,
            "new": True,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="findAndModify with remove:true and new:true should fail",
    ),
    CommandTestCase(
        "remove-and-upsert",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
            "remove": True,
            "upsert": True,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="findAndModify with remove:true and upsert:true should fail",
    ),
    CommandTestCase(
        "remove-and-update-with-sort",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
            "remove": True,
            "update": {"$set": {"x": 1}},
            "sort": {"_id": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="findAndModify with both remove and update plus sort should fail",
    ),
    CommandTestCase(
        "remove-update-and-upsert",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
            "remove": True,
            "update": {"$set": {"x": 1}},
            "upsert": True,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="findAndModify with remove, update and upsert all set should fail",
    ),
    CommandTestCase(
        "unknown-field",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 1}},
            "unknownField": True,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="findAndModify with unrecognized top-level field should fail",
    ),
    CommandTestCase(
        "mixed-dollar-and-plain-keys",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}, "y": 30},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="update mixing dollar-prefixed and plain keys should fail",
    ),
    CommandTestCase(
        "pipeline-disallowed-stage",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": [{"$match": {"x": 10}}],
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="pipeline update with disallowed stage ($match) should fail",
    ),
]

BAD_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint-nonexistent-index",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "hint": "nonexistent_index",
        },
        error_code=BAD_VALUE_ERROR,
        msg="hint referencing non-existent index should fail with BadValue",
    ),
    CommandTestCase(
        "maxTimeMS-negative",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 1}},
            "maxTimeMS": -1,
        },
        error_code=BAD_VALUE_ERROR,
        msg="negative maxTimeMS should fail with BadValue",
    ),
]

PARSE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "maxTimeMS-fractional-double",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 1}},
            "maxTimeMS": 100.5,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS as fractional double should fail",
    ),
]

IMMUTABLE_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "replacement-change-id",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"_id": 2, "x": 20},
        },
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="replacement attempting to change _id should fail",
    ),
    CommandTestCase(
        "update-change-id-via-operator",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"_id": 2}},
        },
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="changing _id via $set operator should fail",
    ),
    CommandTestCase(
        "setOnInsert-duplicate-id",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 2},
            "update": {"$setOnInsert": {"_id": 1}},
            "upsert": True,
        },
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="upsert with $setOnInsert producing duplicate _id should fail",
    ),
    CommandTestCase(
        "setOnInsert-id-mismatch",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"$setOnInsert": {"_id": 2, "x": 10}},
            "upsert": True,
        },
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="upsert with selector _id differing from $setOnInsert _id should fail",
    ),
    CommandTestCase(
        "setOnInsert-document-id-different-values",
        docs=[],
        command={
            "query": {"_id": {"a": 1, "b": 2}},
            "update": {"$setOnInsert": {"_id": {"a": 1, "b": 99}, "x": 10}},
            "upsert": True,
        },
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="upsert with document-typed _id having different field values should fail",
    ),
    CommandTestCase(
        "setOnInsert-dotted-id-mismatch",
        docs=[],
        command={
            "query": {"_id.a": 1},
            "update": {"$setOnInsert": {"_id": {"a": 2}, "x": 10}},
            "upsert": True,
        },
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="upsert with dotted id values differing should fail",
    ),
    CommandTestCase(
        "setOnInsert-array-id-different-order",
        docs=[],
        command={
            "query": {"_id": [1, 2, 3]},
            "update": {"$setOnInsert": {"_id": [3, 2, 1], "x": 10}},
            "upsert": True,
        },
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="upsert with array id having different element ordering should fail",
    ),
]

PROJECTION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "projection-mixed-inclusion-exclusion",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 99}},
            "fields": {"x": 1, "y": 0},
        },
        error_code=PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
        msg="fields projection mixing inclusion and exclusion should fail",
    ),
    CommandTestCase(
        "projection-invalid-operator-no-flags",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "fields": {"x": {"$inc": 1}},
        },
        error_code=PROJECT_UNKNOWN_EXPRESSION_ERROR,
        msg="update-style operator in projection should fail (no upsert/new flags)",
    ),
    CommandTestCase(
        "projection-invalid-operator-upsert-only",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "upsert": True,
            "fields": {"x": {"$inc": 1}},
        },
        error_code=PROJECT_UNKNOWN_EXPRESSION_ERROR,
        msg="update-style operator in projection should fail (upsert only)",
    ),
    CommandTestCase(
        "projection-invalid-operator-new-only",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "new": True,
            "fields": {"x": {"$inc": 1}},
        },
        error_code=PROJECT_UNKNOWN_EXPRESSION_ERROR,
        msg="update-style operator in projection should fail (new only)",
    ),
    CommandTestCase(
        "projection-invalid-operator-upsert-and-new",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "upsert": True,
            "new": True,
            "fields": {"x": {"$inc": 1}},
        },
        error_code=PROJECT_UNKNOWN_EXPRESSION_ERROR,
        msg="update-style operator in projection should fail (upsert + new)",
    ),
    CommandTestCase(
        "projection-invalid-operator-insert-no-match",
        docs=[],
        command={
            "query": {"_id": 99},
            "update": {"$set": {"x": 20}},
            "upsert": True,
            "new": True,
            "fields": {"x": {"$inc": 1}},
        },
        error_code=PROJECT_UNKNOWN_EXPRESSION_ERROR,
        msg="update-style operator in projection should fail (upsert insert path)",
    ),
]

DUPLICATE_KEY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "duplicate-key-violation",
        docs=[{"_id": 1, "key": "a"}, {"_id": 2, "key": "b"}],
        indexes=[IndexModel("key", unique=True)],
        command={
            "query": {"_id": 2},
            "update": {"$set": {"key": "a"}},
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="update causing unique index violation should fail with DuplicateKey",
    ),
]

ARGUMENT_ERROR_TESTS: list[CommandTestCase] = (
    ARGUMENT_CONFLICT_TESTS
    + BAD_VALUE_TESTS
    + PARSE_ERROR_TESTS
    + IMMUTABLE_FIELD_TESTS
    + PROJECTION_ERROR_TESTS
    + DUPLICATE_KEY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_ERROR_TESTS))
def test_findAndModify_argument_errors(database_client, collection, test):
    """Test findAndModify argument validation errors."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = {"findAndModify": collection.name, **test.build_command(ctx)}
    result = execute_command(collection, command)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


ARRAY_FILTERS_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unreferenced_identifier_fails",
        docs=[{"_id": 1, "grades": [85, 92]}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"grades.0": 100}},
            "arrayFilters": [{"elem": {"$gte": 90}}],
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="arrayFilters identifier not referenced in update should produce an error",
    ),
    CommandTestCase(
        "identifier_no_corresponding_filter_fails",
        docs=[{"_id": 1, "grades": [85, 92]}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"grades.$[elem]": 100}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="update with $[identifier] but no matching arrayFilters entry should produce an error",
    ),
    CommandTestCase(
        "duplicate_identifier_fails",
        docs=[{"_id": 1, "grades": [85, 92]}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"grades.$[elem]": 100}},
            "arrayFilters": [{"elem": {"$gte": 90}}, {"elem": {"$lte": 80}}],
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="two arrayFilters for the same identifier should produce an error",
    ),
    CommandTestCase(
        "with_pipeline_update_fails",
        docs=[{"_id": 1, "grades": [85, 92]}],
        command={
            "query": {"_id": 1},
            "update": [{"$set": {"modified": True}}],
            "arrayFilters": [{"elem": {"$gte": 90}}],
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="arrayFilters with aggregation-pipeline update should produce an error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_FILTERS_ERROR_TESTS))
def test_findAndModify_array_filters_errors(database_client, collection, test):
    """Test findAndModify arrayFilters validation errors."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = {"findAndModify": collection.name, **test.build_command(ctx)}
    result = execute_command(collection, command)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


DOLLAR_PREFIXED_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "set_top_level_dollar_field_fails",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"$bad": 1}},
        },
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="$set on top-level dollar-prefixed field should fail",
    ),
    CommandTestCase(
        "inc_top_level_dollar_field_fails",
        docs=[{"_id": 1, "$val": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$inc": {"$val": 1}},
        },
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="$inc on top-level dollar-prefixed field should fail",
    ),
    CommandTestCase(
        "mul_top_level_dollar_field_fails",
        docs=[{"_id": 1, "$val": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$mul": {"$val": 2}},
        },
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="$mul on top-level dollar-prefixed field should fail",
    ),
    CommandTestCase(
        "max_top_level_dollar_field_fails",
        docs=[{"_id": 1, "$val": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$max": {"$val": 20}},
        },
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="$max on top-level dollar-prefixed field should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DOLLAR_PREFIXED_ERROR_TESTS))
def test_findAndModify_dollar_prefixed_errors(database_client, collection, test):
    """Test findAndModify dollar-prefixed field validation errors."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = {"findAndModify": collection.name, **test.build_command(ctx)}
    result = execute_command(collection, command)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


def test_findAndModify_validation_rejects_invalid_write(database_client, request):
    """Test bypassDocumentValidation:false rejects non-conforming update."""
    db = database_client
    coll_name = f"{request.node.name}_validated"
    db.create_collection(coll_name, validator={"$jsonSchema": {"required": ["name"]}})
    coll = db[coll_name]
    coll.insert_one({"_id": 1, "name": "test"})
    result = execute_command(
        coll,
        {
            "findAndModify": coll.name,
            "query": {"_id": 1},
            "update": {"$unset": {"name": ""}},
        },
    )
    assertFailureCode(result, DOCUMENT_VALIDATION_FAILURE_ERROR)


def test_findAndModify_expr_undefined_variable_fails(collection):
    """Test $expr referencing undefined variable produces an error."""
    collection.insert_one({"_id": 1, "a": 10})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"$expr": {"$eq": ["$a", "$$undefined_var"]}},
            "update": {"$set": {"x": 1}},
        },
    )
    assertFailureCode(result, LET_UNDEFINED_VARIABLE_ERROR)
