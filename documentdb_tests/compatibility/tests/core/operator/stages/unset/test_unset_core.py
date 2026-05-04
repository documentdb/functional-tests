"""Tests for $unset stage core behavior."""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Removal]: $unset removes specified fields from output
# documents while leaving all other fields intact.
UNSET_CORE_REMOVAL_TESTS: list[StageTestCase] = [
    StageTestCase(
        "removal_top_level_field",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[{"$unset": "b"}],
        expected=[{"_id": 1, "a": 10, "c": 30}],
        msg="$unset should remove the specified top-level field from output",
    ),
    StageTestCase(
        "removal_id_retained",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": "a"}],
        expected=[{"_id": 1}],
        msg="$unset should retain _id when it is not explicitly unset",
    ),
    StageTestCase(
        "removal_nonexistent_ignored",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$unset": "z"}],
        expected=[{"_id": 1, "a": 10, "b": 20}],
        msg="$unset should silently ignore a nonexistent field name",
    ),
    StageTestCase(
        "removal_mix_existent_nonexistent",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[{"$unset": ["a", "z", "c"]}],
        expected=[{"_id": 1, "b": 20}],
        msg="$unset should remove only existent fields when mixed with nonexistent ones",
    ),
    StageTestCase(
        "removal_all_fields_including_id",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["_id", "a"]}],
        expected=[{}],
        msg="$unset should produce an empty document when all fields including _id are removed",
    ),
]

# Property [Syntax Forms]: $unset accepts both a single string and an array
# of strings, and both forms produce identical results.
UNSET_SYNTAX_FORMS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "syntax_string_form",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$unset": "a"}],
        expected=[{"_id": 1, "b": 20}],
        msg="$unset with a string should remove the specified field",
    ),
    StageTestCase(
        "syntax_single_element_array",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$unset": ["a"]}],
        expected=[{"_id": 1, "b": 20}],
        msg="$unset with a single-element array should produce the same result as a string",
    ),
    StageTestCase(
        "syntax_multi_element_array",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[{"$unset": ["a", "c"]}],
        expected=[{"_id": 1, "b": 20}],
        msg="$unset with a multi-element array should remove all specified fields",
    ),
]

# Property [Empty and Non-Existent Collections]: running $unset on an empty
# collection or a non-existent collection returns an empty result with no
# error.
UNSET_EMPTY_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_collection",
        docs=[],
        pipeline=[{"$unset": "a"}],
        expected=[],
        msg="$unset on an empty collection should return an empty result",
    ),
    StageTestCase(
        "nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": "a"}],
        expected=[],
        msg="$unset on a non-existent collection should return an empty result",
    ),
]

# Property [Multiple Documents]: $unset applies to every document in the
# collection, including documents that lack the specified field.
UNSET_MULTIPLE_DOCUMENTS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "multiple_documents_all_have_field",
        docs=[
            {"_id": 1, "a": 10, "b": 20},
            {"_id": 2, "a": 30, "b": 40},
            {"_id": 3, "a": 50, "b": 60},
        ],
        pipeline=[{"$unset": "b"}],
        expected=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 30},
            {"_id": 3, "a": 50},
        ],
        msg="$unset should apply to every document in the collection",
    ),
    StageTestCase(
        "multiple_documents_some_have_field",
        docs=[
            {"_id": 1, "a": 10, "b": 20},
            {"_id": 2, "a": 30},
            {"_id": 3, "a": 50, "b": 60},
        ],
        pipeline=[{"$unset": "b"}],
        expected=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 30},
            {"_id": 3, "a": 50},
        ],
        msg="$unset should succeed when some documents lack the specified field",
    ),
    StageTestCase(
        "multiple_documents_none_have_field",
        docs=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 30},
        ],
        pipeline=[{"$unset": "b"}],
        expected=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 30},
        ],
        msg="$unset should succeed when no documents have the specified field",
    ),
]

# Property [Chained Stages]: multiple $unset stages in the same pipeline
# apply sequentially, each removing fields from the previous stage's output.
UNSET_CHAINED_STAGES_TESTS: list[StageTestCase] = [
    StageTestCase(
        "chained_unset_stages",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[{"$unset": "a"}, {"$unset": "b"}],
        expected=[{"_id": 1, "c": 30}],
        msg="Two consecutive $unset stages should each remove their specified field",
    ),
]

UNSET_CORE_TESTS = (
    UNSET_CORE_REMOVAL_TESTS
    + UNSET_SYNTAX_FORMS_TESTS
    + UNSET_EMPTY_COLLECTION_TESTS
    + UNSET_MULTIPLE_DOCUMENTS_TESTS
    + UNSET_CHAINED_STAGES_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNSET_CORE_TESTS))
def test_unset_core(collection: Any, test_case: StageTestCase) -> None:
    """Test $unset stage core behavior."""
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
