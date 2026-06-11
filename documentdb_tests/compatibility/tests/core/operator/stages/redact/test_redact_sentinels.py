"""Tests for $redact $$KEEP/$$PRUNE/$$DESCEND semantics."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [$$KEEP Semantics]: $$KEEP keeps the current level wholesale without
# descending into it.
REDACT_KEEP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "keep_no_descend_embedded_document",
        docs=[{"_id": 1, "level": 1, "child": {"level": 2, "secret": True}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$level", 1]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "level": 1, "child": {"level": 2, "secret": True}}],
        msg="$redact under $$KEEP should keep a nested document that would prune if descended",
    ),
    StageTestCase(
        "keep_no_descend_array_element",
        docs=[{"_id": 1, "level": 1, "items": [{"level": 2, "secret": True}]}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$level", 1]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "level": 1, "items": [{"level": 2, "secret": True}]}],
        msg="$redact under $$KEEP should keep an array element that would prune if descended",
    ),
    StageTestCase(
        "keep_embedded_level_halts_descent",
        docs=[
            {
                "_id": 1,
                "level": 1,
                "child": {"level": 2, "grandchild": {"level": 3, "secret": True}},
            }
        ],
        pipeline=[
            {
                "$redact": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$level", 1]}, "then": "$$DESCEND"},
                            {"case": {"$eq": ["$level", 2]}, "then": "$$KEEP"},
                        ],
                        "default": "$$PRUNE",
                    }
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "level": 1,
                "child": {"level": 2, "grandchild": {"level": 3, "secret": True}},
            }
        ],
        msg="$redact under $$KEEP at an embedded level should keep that level "
        "wholesale and halt descent into a would-prune subtree",
    ),
]

# Property [$$PRUNE Semantics]: $$PRUNE removes the current level outright
# without descending, compacting a pruned array element with no placeholder.
REDACT_PRUNE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "prune_no_descend_into_subtree",
        docs=[
            {
                "_id": 1,
                "level": 1,
                "child": {"level": 2, "grandchild": {"level": 1, "keepme": 7}},
            }
        ],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$level", 1]}, "$$DESCEND", "$$PRUNE"]}}],
        expected=[{"_id": 1, "level": 1}],
        msg="$redact under $$PRUNE should drop a subtree without descending into a "
        "would-keep nested document",
    ),
    StageTestCase(
        "prune_removes_embedded_document_field",
        docs=[{"_id": 1, "level": 1, "child": {"secret": True}, "keepme": 7}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$level", 1]}, "$$DESCEND", "$$PRUNE"]}}],
        expected=[{"_id": 1, "level": 1, "keepme": 7}],
        msg="$redact under $$PRUNE should remove a pruned embedded-document field "
        "entirely rather than retain an empty document",
    ),
    StageTestCase(
        "prune_compacts_array_element",
        docs=[
            {
                "_id": 1,
                "level": 1,
                "items": [
                    {"keep": 1, "level": 1},
                    {"drop": 1, "level": 2},
                    {"keep": 2, "level": 1},
                ],
            }
        ],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$level", 1]}, "$$DESCEND", "$$PRUNE"]}}],
        expected=[
            {"_id": 1, "level": 1, "items": [{"keep": 1, "level": 1}, {"keep": 2, "level": 1}]}
        ],
        msg="$redact under $$PRUNE should remove a pruned array element and compact "
        "the array with no placeholder",
    ),
]

# Property [$$DESCEND Semantics]: $$DESCEND keeps scalar fields and recurses
# into each embedded document, retaining a level emptied by deeper pruning.
REDACT_DESCEND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "descend_recurses_embedded_document",
        docs=[{"_id": 1, "a": 1, "child": {"b": 2, "sub": {"secret": True}}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1, "a": 1, "child": {"b": 2}}],
        msg="$redact under $$DESCEND should keep scalar fields and recurse into an "
        "embedded document rather than keep or prune it wholesale",
    ),
    StageTestCase(
        "descend_recurses_embedded_document_in_array",
        docs=[{"_id": 1, "a": 1, "items": [{"b": 2, "sub": {"secret": True}}, {"c": 3}]}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1, "a": 1, "items": [{"b": 2}, {"c": 3}]}],
        msg="$redact under $$DESCEND should recurse into embedded documents nested "
        "inside an array",
    ),
    StageTestCase(
        "descend_keeps_non_document_array_elements",
        docs=[{"_id": 1, "items": [1, "x", [2, 3], {"secret": True}, {"keep": 9}]}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1, "items": [1, "x", [2, 3], {"keep": 9}]}],
        msg="$redact under $$DESCEND should keep non-document array elements as-is "
        "while evaluating document elements",
    ),
    StageTestCase(
        "descend_array_of_arrays_with_documents",
        docs=[{"_id": 1, "matrix": [[{"keep": 1}, {"secret": True}], [{"keep": 2}]]}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1, "matrix": [[{"keep": 1}], [{"keep": 2}]]}],
        msg="$redact under $$DESCEND should descend into a nested array of arrays and "
        "evaluate each embedded document independently",
    ),
    StageTestCase(
        "descend_prune_all_array_elements_retains_empty_array",
        docs=[{"_id": 1, "items": [{"secret": True}, {"secret": True}]}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1, "items": []}],
        msg="$redact under $$DESCEND should retain an array emptied by pruning every "
        "document element as an empty array",
    ),
    StageTestCase(
        "descend_empty_embedded_document_retained",
        docs=[{"_id": 1, "child": {"sub": {"secret": True}}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1, "child": {}}],
        msg="$redact under $$DESCEND should retain an embedded document emptied by "
        "deeper pruning as an empty document",
    ),
    StageTestCase(
        "descend_multilevel_intermediate_empty_retained",
        docs=[{"_id": 1, "a": {"b": {"c": {"secret": True}}}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1, "a": {"b": {}}}],
        msg="$redact under $$DESCEND should retain an intermediate document emptied by "
        "deeper pruning without propagating emptiness upward",
    ),
    StageTestCase(
        "descend_array_element_empty_retained_not_compacted",
        docs=[{"_id": 1, "items": [{"keep": 1}, {"sub": {"secret": True}}, {"keep": 2}]}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1, "items": [{"keep": 1}, {}, {"keep": 2}]}],
        msg="$redact under $$DESCEND should retain a document array element emptied by "
        "deeper pruning as an empty document without compacting the array",
    ),
]

REDACT_SENTINEL_TESTS = REDACT_KEEP_TESTS + REDACT_PRUNE_TESTS + REDACT_DESCEND_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REDACT_SENTINEL_TESTS))
def test_redact_sentinel_cases(collection, test_case: StageTestCase):
    """Test $redact sentinel resolution and $$KEEP/$$PRUNE/$$DESCEND semantics."""
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
    )
