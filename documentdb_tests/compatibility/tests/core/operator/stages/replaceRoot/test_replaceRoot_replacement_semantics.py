"""Tests for the $replaceRoot aggregation stage."""

from __future__ import annotations

import pytest
from bson import (
    Regex,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Replacement Behavior]: the input document is replaced entirely
# by the object newRoot resolves to against the pre-replacement input; no
# original field survives unless the resolved object provides it.
REPLACEROOT_CORE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "core_promote_embedded_doc",
        docs=[{"_id": 1, "data": {"_id": 1, "name": "Alice", "age": 30}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected=[{"_id": 1, "name": "Alice", "age": 30}],
        msg="$replaceRoot should promote a referenced embedded document to the top level",
    ),
    StageTestCase(
        "core_replaces_entirely_no_input_fields",
        docs=[{"_id": 1, "data": {"_id": 1, "x": 1}, "other": "keep_out"}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected=[{"_id": 1, "x": 1}],
        msg="$replaceRoot should drop all original input fields not present in the resolved object",
    ),
    StageTestCase(
        "core_constructed_document",
        docs=[{"_id": 1, "a": 2, "b": 3}],
        pipeline=[
            {
                "$replaceRoot": {
                    "newRoot": {"_id": "$_id", "sum": {"$add": ["$a", "$b"]}, "label": "$_id"}
                }
            }
        ],
        expected=[{"_id": 1, "sum": 5, "label": 1}],
        msg="$replaceRoot should replace the input with a constructed document evaluated on input",
    ),
]

# Property [Identity]: $$ROOT and $$CURRENT as newRoot return the input document
# unchanged, including its original _id.
REPLACEROOT_IDENTITY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "identity_root",
        docs=[{"_id": 1, "a": 10, "b": {"c": 2}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$$ROOT"}}],
        expected=[{"_id": 1, "a": 10, "b": {"c": 2}}],
        msg="$replaceRoot with $$ROOT should return the input document unchanged",
    ),
    StageTestCase(
        "identity_current",
        docs=[{"_id": 1, "a": 10, "b": {"c": 2}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$$CURRENT"}}],
        expected=[{"_id": 1, "a": 10, "b": {"c": 2}}],
        msg="$replaceRoot with $$CURRENT should return the input document unchanged",
    ),
]

# Property [_id Handling]: the stage neither auto-generates nor validates _id; a
# resolved object's _id passes through unchanged, with no type or cross-document
# uniqueness enforcement.
REPLACEROOT_ID_HANDLING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "idhandling_no_id_not_generated",
        docs=[{"_id": 1, "data": {"name": "Alice"}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected=[{"name": "Alice"}],
        msg="$replaceRoot should not auto-generate an _id when the resolved object has none",
    ),
    StageTestCase(
        "idhandling_explicit_id_preserved",
        docs=[{"_id": 1, "data": {"_id": 99, "name": "Bob"}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected=[{"_id": 99, "name": "Bob"}],
        msg="$replaceRoot should preserve an explicit _id in the resolved object",
    ),
    StageTestCase(
        "idhandling_array_id_no_type_enforcement",
        docs=[{"_id": 1, "data": {"_id": [1, 2, 3], "name": "x"}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected=[{"_id": [1, 2, 3], "name": "x"}],
        msg="$replaceRoot should pass through an array _id with no type enforcement",
    ),
    StageTestCase(
        "idhandling_null_id_no_type_enforcement",
        docs=[{"_id": 1, "data": {"_id": None, "name": "x"}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected=[{"_id": None, "name": "x"}],
        msg="$replaceRoot should pass through a null _id with no type enforcement",
    ),
    StageTestCase(
        "idhandling_regex_id_no_type_enforcement",
        docs=[{"_id": 1, "data": {"_id": Regex("abc", "i"), "name": "x"}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected=[{"_id": Regex("abc", "i"), "name": "x"}],
        msg="$replaceRoot should pass through a regex _id with no type enforcement",
    ),
    StageTestCase(
        "idhandling_duplicate_id_no_uniqueness_enforcement",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        pipeline=[{"$replaceRoot": {"newRoot": {"_id": "same", "v": "$a"}}}],
        expected=[
            {"_id": "same", "v": 1},
            {"_id": "same", "v": 2},
            {"_id": "same", "v": 3},
        ],
        msg="$replaceRoot should emit all documents sharing one _id with no uniqueness error",
    ),
]

# Property [Object-Literal Field-Value Semantics]: a field whose value in the
# constructed newRoot literal is $$REMOVE or a missing reference is omitted from
# the result; a literal whose every field is omitted yields the empty document;
# and within a nested sub-object the (now empty) sub-object is kept rather than
# dropping its parent.
REPLACEROOT_OBJECT_LITERAL_FIELD_VALUE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "objlit_remove_value_omits_field",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"a": "$a", "b": "$$REMOVE"}}}],
        expected=[{"a": 1}],
        msg="$replaceRoot should omit a field whose value is $$REMOVE",
    ),
    StageTestCase(
        "objlit_missing_value_omits_field",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"a": "$a", "b": "$nonexistent"}}}],
        expected=[{"a": 1}],
        msg="$replaceRoot should omit a field whose value references a missing field",
    ),
    StageTestCase(
        "objlit_only_remove_value_yields_empty",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"b": "$$REMOVE"}}}],
        expected=[{}],
        msg="$replaceRoot should yield the empty document when the sole field's value is $$REMOVE",
    ),
    StageTestCase(
        "objlit_only_missing_value_yields_empty",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"b": "$nonexistent"}}}],
        expected=[{}],
        msg="$replaceRoot should yield empty document when the sole field is a missing reference",
    ),
    StageTestCase(
        "objlit_remove_value_omits_present_field",
        docs=[{"_id": 1, "a": 1, "b": 2}],
        pipeline=[{"$replaceRoot": {"newRoot": {"a": "$a", "b": "$$REMOVE"}}}],
        expected=[{"a": 1}],
        msg="$replaceRoot should omit a field set to $$REMOVE that exists in the input",
    ),
    StageTestCase(
        "objlit_nested_sole_remove_keeps_subobject",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"a": {"b": "$$REMOVE"}}}}],
        expected=[{"a": {}}],
        msg="$replaceRoot should keep an emptied sub-object rather than dropping its parent field",
    ),
    StageTestCase(
        "objlit_nested_partial_remove_keeps_siblings",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"a": {"x": "$a", "y": "$$REMOVE"}}}}],
        expected=[{"a": {"x": 1}}],
        msg="$replaceRoot should keep surviving siblings when one sub-object field is omitted",
    ),
]

# Property [Promoted Stored-Document Field Names]: when a stored sub-document is
# promoted via a field reference, its keys are promoted to the top level
# verbatim with no field-name validation, even when those keys contain a dot or
# begin with a dollar sign.
REPLACEROOT_PROMOTED_FIELD_NAMES_TESTS: list[StageTestCase] = [
    StageTestCase(
        "promoted_field_names_dotted_key",
        docs=[{"_id": 1, "data": {"a.b": 1, "x": 2}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected=[{"a.b": 1, "x": 2}],
        msg="$replaceRoot should promote a stored dotted key verbatim without validation",
    ),
    StageTestCase(
        "promoted_field_names_dollar_key",
        docs=[{"_id": 1, "data": {"$x": 5}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected=[{"$x": 5}],
        msg="$replaceRoot should promote a stored dollar-prefixed key verbatim without validation",
    ),
]

# Property [Expression Arguments]: newRoot promotes whatever object an
# object-resolving expression yields independent of which operator produced it.
REPLACEROOT_EXPRESSION_ARGUMENT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "expr_arg_object_producing_operator",
        docs=[{"_id": 1, "a": {"x": 1}, "b": {"y": 2}}],
        pipeline=[{"$replaceRoot": {"newRoot": {"$mergeObjects": ["$a", "$b"]}}}],
        expected=[{"x": 1, "y": 2}],
        msg="$replaceRoot should promote the object an object-producing expression yields",
    ),
    StageTestCase(
        "expr_arg_literal_object",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"$literal": {"k1": 1, "k2": 2}}}}],
        expected=[{"k1": 1, "k2": 2}],
        msg="$replaceRoot should promote the object wrapped in $literal",
    ),
]

# Property [Accepted Input]: an empty object is accepted and yields an empty
# output document, whether supplied as a literal newRoot or a stored reference.
REPLACEROOT_ACCEPTED_INPUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "accepted_empty_object_literal",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {}}}],
        expected=[{}],
        msg="$replaceRoot should accept an empty object literal and yield the empty document",
    ),
    StageTestCase(
        "accepted_stored_empty_object",
        docs=[{"_id": 1, "data": {}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected=[{}],
        msg="$replaceRoot should accept a stored empty object and yield the empty document",
    ),
]

# Property [Consecutive Stages]: consecutive $replaceRoot stages compose, each
# promoting a sub-document of the shape produced by the previous one.
REPLACEROOT_CONSECUTIVE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "consecutive_two_stages",
        docs=[{"_id": 1, "a": {"b": {"c": 42}}}],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$a"}},
            {"$replaceRoot": {"newRoot": "$b"}},
        ],
        expected=[{"c": 42}],
        msg="consecutive $replaceRoot stages should each promote a sub-document of the prior root",
    ),
]

REPLACEROOT_REPLACEMENT_SEMANTICS_TESTS = (
    REPLACEROOT_CORE_TESTS
    + REPLACEROOT_IDENTITY_TESTS
    + REPLACEROOT_ID_HANDLING_TESTS
    + REPLACEROOT_OBJECT_LITERAL_FIELD_VALUE_TESTS
    + REPLACEROOT_PROMOTED_FIELD_NAMES_TESTS
    + REPLACEROOT_EXPRESSION_ARGUMENT_TESTS
    + REPLACEROOT_ACCEPTED_INPUT_TESTS
    + REPLACEROOT_CONSECUTIVE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REPLACEROOT_REPLACEMENT_SEMANTICS_TESTS))
def test_replaceRoot_replacement_semantics_cases(collection, test_case: StageTestCase):
    """Test $replaceRoot replacement semantics cases."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
