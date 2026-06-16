"""Tests for the $replaceWith aggregation stage."""

from __future__ import annotations

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Core Replacement Behavior]: the input document is replaced entirely
# by the object the argument resolves to against the pre-replacement input; no
# original field survives unless the resolved object provides it.
REPLACEWITH_CORE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "core_promote_embedded_doc",
        docs=[{"_id": 1, "name": {"first": "Alice", "last": "Smith"}, "age": 30}],
        pipeline=[{"$replaceWith": "$name"}],
        expected=[{"first": "Alice", "last": "Smith"}],
        msg="$replaceWith should promote a referenced embedded document to the top level",
    ),
    StageTestCase(
        "core_replaces_entirely_no_input_fields",
        docs=[{"_id": 1, "data": {"_id": 1, "x": 1}, "other": "keep_out"}],
        pipeline=[{"$replaceWith": "$data"}],
        expected=[{"_id": 1, "x": 1}],
        msg="$replaceWith should drop all original input fields not present in the resolved object",
    ),
    StageTestCase(
        "core_constructed_document",
        docs=[{"_id": 1, "name": {"first": "Alice", "last": "Smith"}, "age": 30}],
        pipeline=[
            {
                "$replaceWith": {
                    "fullName": "$name.first",
                    "doubled": {"$multiply": ["$age", 2]},
                }
            }
        ],
        expected=[{"fullName": "Alice", "doubled": 60}],
        msg="$replaceWith should replace the input with a constructed document evaluated on input",
    ),
    StageTestCase(
        "core_option_resembling_key",
        docs=[{"_id": 5, "details": {"score": 42}}],
        pipeline=[{"$replaceWith": {"replacement": "$details"}}],
        expected=[{"replacement": {"score": 42}}],
        msg="$replaceWith should treat an option-like single-field literal as an ordinary document",
    ),
]

# Property [Identity]: $$ROOT and $$CURRENT as the argument return the input
# document unchanged, including its original _id.
REPLACEWITH_IDENTITY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "identity_root",
        docs=[{"_id": 1, "a": 10, "b": {"c": 2}}],
        pipeline=[{"$replaceWith": "$$ROOT"}],
        expected=[{"_id": 1, "a": 10, "b": {"c": 2}}],
        msg="$replaceWith with $$ROOT should return the input document unchanged",
    ),
    StageTestCase(
        "identity_current",
        docs=[{"_id": 1, "a": 10, "b": {"c": 2}}],
        pipeline=[{"$replaceWith": "$$CURRENT"}],
        expected=[{"_id": 1, "a": 10, "b": {"c": 2}}],
        msg="$replaceWith with $$CURRENT should return the input document unchanged",
    ),
]

# Property [_id Handling]: the stage neither auto-generates nor validates _id; a
# resolved object's _id passes through unchanged, with no type or cross-document
# uniqueness enforcement.
REPLACEWITH_ID_HANDLING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "idhandling_no_id_not_generated",
        docs=[{"_id": 1, "data": {"name": "Alice"}}],
        pipeline=[{"$replaceWith": "$data"}],
        expected=[{"name": "Alice"}],
        msg="$replaceWith should not auto-generate an _id when the resolved object has none",
    ),
    StageTestCase(
        "idhandling_explicit_id_preserved",
        docs=[{"_id": 1, "data": {"_id": 99, "name": "Bob"}}],
        pipeline=[{"$replaceWith": "$data"}],
        expected=[{"_id": 99, "name": "Bob"}],
        msg="$replaceWith should preserve an explicit _id in the resolved object",
    ),
    StageTestCase(
        "idhandling_array_id_no_type_enforcement",
        docs=[{"_id": 1, "data": {"_id": [1, 2, 3], "name": "x"}}],
        pipeline=[{"$replaceWith": "$data"}],
        expected=[{"_id": [1, 2, 3], "name": "x"}],
        msg="$replaceWith should pass through an array _id with no type enforcement",
    ),
    StageTestCase(
        "idhandling_null_id_no_type_enforcement",
        docs=[{"_id": 1, "data": {"_id": None, "name": "x"}}],
        pipeline=[{"$replaceWith": "$data"}],
        expected=[{"_id": None, "name": "x"}],
        msg="$replaceWith should pass through a null _id with no type enforcement",
    ),
    StageTestCase(
        "idhandling_regex_id_no_type_enforcement",
        docs=[{"_id": 1, "data": {"_id": Regex("abc", "i"), "name": "x"}}],
        pipeline=[{"$replaceWith": "$data"}],
        expected=[{"_id": Regex("abc", "i"), "name": "x"}],
        msg="$replaceWith should pass through a regex _id with no type enforcement",
    ),
    StageTestCase(
        "idhandling_duplicate_id_no_uniqueness_enforcement",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        pipeline=[{"$replaceWith": {"_id": "same", "v": "$a"}}],
        expected=[
            {"_id": "same", "v": 1},
            {"_id": "same", "v": 2},
            {"_id": "same", "v": 3},
        ],
        msg="$replaceWith should emit all documents sharing one _id with no uniqueness error",
    ),
]

# Property [Object-Literal Field-Value Semantics]: a field whose value in the
# constructed argument literal is $$REMOVE or a missing reference is omitted from
# the result; a literal whose every field is omitted yields the empty document;
# and within a nested sub-object the (now empty) sub-object is kept rather than
# dropping its parent.
REPLACEWITH_OBJECT_LITERAL_FIELD_VALUE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "objlit_remove_value_omits_field",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"a": "$a", "b": "$$REMOVE"}}],
        expected=[{"a": 1}],
        msg="$replaceWith should omit a field whose value is $$REMOVE",
    ),
    StageTestCase(
        "objlit_missing_value_omits_field",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"a": "$a", "b": "$nonexistent"}}],
        expected=[{"a": 1}],
        msg="$replaceWith should omit a field whose value references a missing field",
    ),
    StageTestCase(
        "objlit_only_remove_value_yields_empty",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"b": "$$REMOVE"}}],
        expected=[{}],
        msg="$replaceWith should yield the empty document when the sole field's value is $$REMOVE",
    ),
    StageTestCase(
        "objlit_only_missing_value_yields_empty",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"b": "$nonexistent"}}],
        expected=[{}],
        msg="$replaceWith should yield empty document when the sole field is a missing reference",
    ),
    StageTestCase(
        "objlit_remove_value_omits_present_field",
        docs=[{"_id": 1, "a": 1, "b": 2}],
        pipeline=[{"$replaceWith": {"a": "$a", "b": "$$REMOVE"}}],
        expected=[{"a": 1}],
        msg="$replaceWith should omit a field set to $$REMOVE that exists in the input",
    ),
    StageTestCase(
        "objlit_nested_sole_remove_keeps_subobject",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"a": {"b": "$$REMOVE"}}}],
        expected=[{"a": {}}],
        msg="$replaceWith should keep an emptied sub-object rather than dropping its parent field",
    ),
    StageTestCase(
        "objlit_nested_partial_remove_keeps_siblings",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"a": {"x": "$a", "y": "$$REMOVE"}}}],
        expected=[{"a": {"x": 1}}],
        msg="$replaceWith should keep surviving siblings when one sub-object field is omitted",
    ),
]

# Property [Promoted Stored-Document Field Names]: when a stored sub-document is
# promoted via a field reference, its keys are promoted to the top level
# verbatim with no field-name validation, even when those keys contain a dot or
# begin with a dollar sign.
REPLACEWITH_PROMOTED_FIELD_NAMES_TESTS: list[StageTestCase] = [
    StageTestCase(
        "promoted_field_names_dotted_key",
        docs=[{"_id": 1, "data": {"a.b": 1, "x": 2}}],
        pipeline=[{"$replaceWith": "$data"}],
        expected=[{"a.b": 1, "x": 2}],
        msg="$replaceWith should promote a stored dotted key verbatim without validation",
    ),
    StageTestCase(
        "promoted_field_names_dollar_key",
        docs=[{"_id": 1, "data": {"$x": 5}}],
        pipeline=[{"$replaceWith": "$data"}],
        expected=[{"$x": 5}],
        msg="$replaceWith should promote a stored dollar-prefixed key verbatim without validation",
    ),
]

# Property [Literal Field Value]: a $-prefixed string wrapped in $literal as a
# field value inside a constructed argument literal is preserved verbatim rather
# than interpreted as a field path.
REPLACEWITH_LITERAL_FIELD_VALUE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "literal_dollar_string_preserved",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"a": {"$literal": "$hello"}}}],
        expected=[{"a": "$hello"}],
        msg="$replaceWith should preserve a $literal-wrapped $-prefixed string verbatim",
    ),
]

# Property [Expression Arguments]: the argument promotes whatever object an
# object-resolving expression yields independent of which operator produced it.
REPLACEWITH_EXPRESSION_ARGUMENT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "expr_arg_object_producing_operator",
        docs=[{"_id": 1, "a": {"x": 1}, "b": {"y": 2}}],
        pipeline=[{"$replaceWith": {"$mergeObjects": ["$a", "$b"]}}],
        expected=[{"x": 1, "y": 2}],
        msg="$replaceWith should promote the object an object-producing expression yields",
    ),
    StageTestCase(
        "expr_arg_literal_object",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"$literal": {"k1": 1, "k2": 2}}}],
        expected=[{"k1": 1, "k2": 2}],
        msg="$replaceWith should promote the object wrapped in $literal",
    ),
]

# Property [Accepted Input]: an empty object is accepted and yields an empty
# output document, whether supplied as a literal argument or a stored reference.
REPLACEWITH_ACCEPTED_INPUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "accepted_empty_object_literal",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {}}],
        expected=[{}],
        msg="$replaceWith should accept an empty object literal and yield the empty document",
    ),
    StageTestCase(
        "accepted_stored_empty_object",
        docs=[{"_id": 1, "data": {}}],
        pipeline=[{"$replaceWith": "$data"}],
        expected=[{}],
        msg="$replaceWith should accept a stored empty object and yield the empty document",
    ),
]

# Property [Consecutive Stages]: consecutive $replaceWith stages compose, each
# promoting a sub-document of the shape produced by the previous one.
REPLACEWITH_CONSECUTIVE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "consecutive_two_stages",
        docs=[{"_id": 1, "a": {"b": {"c": 42}}}],
        pipeline=[
            {"$replaceWith": "$a"},
            {"$replaceWith": "$b"},
        ],
        expected=[{"c": 42}],
        msg="consecutive $replaceWith stages should each promote a sub-document of the prior root",
    ),
]

# Property [Empty and Non-Existent Collections]: running $replaceWith on an
# empty collection or a non-existent collection returns an empty result with no
# error.
REPLACEWITH_EMPTY_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_collection",
        docs=[],
        pipeline=[{"$replaceWith": MISSING}],
        expected=[],
        msg="$replaceWith on an empty collection should return an empty result",
    ),
    StageTestCase(
        "nonexistent_collection",
        docs=None,
        pipeline=[{"$replaceWith": MISSING}],
        expected=[],
        msg="$replaceWith on a non-existent collection should return an empty result",
    ),
]

REPLACEWITH_REPLACEMENT_SEMANTICS_TESTS = (
    REPLACEWITH_CORE_TESTS
    + REPLACEWITH_IDENTITY_TESTS
    + REPLACEWITH_ID_HANDLING_TESTS
    + REPLACEWITH_OBJECT_LITERAL_FIELD_VALUE_TESTS
    + REPLACEWITH_PROMOTED_FIELD_NAMES_TESTS
    + REPLACEWITH_LITERAL_FIELD_VALUE_TESTS
    + REPLACEWITH_EXPRESSION_ARGUMENT_TESTS
    + REPLACEWITH_ACCEPTED_INPUT_TESTS
    + REPLACEWITH_CONSECUTIVE_TESTS
    + REPLACEWITH_EMPTY_COLLECTION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REPLACEWITH_REPLACEMENT_SEMANTICS_TESTS))
def test_replaceWith_replacement_semantics_cases(collection, test_case: StageTestCase):
    """Test $replaceWith replacement semantics cases."""
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
