"""Tests for $redact per-level field environment and document-valued _id handling."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Per-Level Field Environment]: $field and $$CURRENT re-root to the
# current level on each re-evaluation while $$ROOT stays pinned to the original
# top-level document.
REDACT_PER_LEVEL_TESTS: list[StageTestCase] = [
    StageTestCase(
        "perlevel_bare_field_rerooted",
        docs=[{"_id": 1, "keep": True, "child": {"keep": False, "data": 1}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$keep", True]}, "$$DESCEND", "$$PRUNE"]}}],
        expected=[{"_id": 1, "keep": True}],
        msg="$redact should resolve a bare $field reference relative to the current "
        "embedded level, not the top-level document",
    ),
    StageTestCase(
        "perlevel_bare_dotted_path_rerooted",
        docs=[
            {"_id": 1, "meta": {"score": 9}},
            {"_id": 2, "meta": {"score": 4}},
        ],
        pipeline=[{"$redact": {"$cond": [{"$gte": ["$meta.score", 9]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "meta": {"score": 9}}],
        msg="$redact should resolve a bare dotted-path field reference through an "
        "embedded document at the current level when driving a sentinel",
    ),
    StageTestCase(
        "perlevel_current_rerooted",
        docs=[{"_id": 1, "keep": True, "child": {"keep": False, "data": 1}}],
        pipeline=[
            {"$redact": {"$cond": [{"$eq": ["$$CURRENT.keep", True]}, "$$DESCEND", "$$PRUNE"]}}
        ],
        expected=[{"_id": 1, "keep": True}],
        msg="$redact should rebind $$CURRENT to the current embedded level, matching a "
        "bare $field reference",
    ),
    StageTestCase(
        "perlevel_root_pinned_no_rebind",
        docs=[{"_id": 1, "top": True, "child": {"top": False, "data": 1}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$$ROOT.top", True]}, "$$DESCEND", "$$PRUNE"]}}],
        expected=[{"_id": 1, "top": True, "child": {"top": False, "data": 1}}],
        msg="$redact should keep $$ROOT pinned to the top-level document and not rebind "
        "it during descent",
    ),
    StageTestCase(
        "perlevel_root_exposes_pruned_sibling",
        docs=[{"_id": 1, "x": {"drop": True}, "y": {"data": 5}}],
        pipeline=[
            {
                "$redact": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$drop", True]}, "then": "$$PRUNE"},
                            {
                                "case": {"$eq": ["$data", 5]},
                                "then": {
                                    "$cond": [
                                        {"$eq": ["$$ROOT.x.drop", True]},
                                        "$$KEEP",
                                        "$$PRUNE",
                                    ]
                                },
                            },
                        ],
                        "default": "$$DESCEND",
                    }
                }
            }
        ],
        expected=[{"_id": 1, "y": {"data": 5}}],
        msg="$redact should expose a sibling's original value through $$ROOT even after "
        "that sibling was pruned earlier in the walk",
    ),
    StageTestCase(
        "perlevel_field_present_root_absent_deeper",
        docs=[{"_id": 1, "flag": True, "child": {"data": 1}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$flag", True]}, "$$DESCEND", "$$PRUNE"]}}],
        expected=[{"_id": 1, "flag": True}],
        msg="$redact should resolve a field absent at a deeper level to missing rather "
        "than leaking the root's value downward",
    ),
    StageTestCase(
        "perlevel_field_absent_root_present_deeper",
        docs=[{"_id": 1, "child": {"deep": True, "data": 1}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$deep", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1}],
        msg="$redact should resolve a field absent at the root to missing while binding "
        "it to its value at the deeper level",
    ),
]

# Property [_id Field Handling]: a document-valued _id is treated as an ordinary
# embedded document under each sentinel and per-level field reference.
REDACT_ID_FIELD_TESTS: list[StageTestCase] = [
    StageTestCase(
        "id_descend_empties_to_empty_document",
        docs=[{"_id": {"k": {"secret": True}}, "top": 1}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": {}, "top": 1}],
        msg="$redact under $$DESCEND should descend into a document-valued _id and "
        "retain it emptied as an empty document",
    ),
    StageTestCase(
        "id_keep_wholesale_discriminating",
        docs=[{"_id": {"k": {"secret": True}}, "top": 1}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$KEEP"]}}],
        expected=[{"_id": {"k": {"secret": True}}, "top": 1}],
        msg="$redact under $$KEEP should keep a document-valued _id wholesale without "
        "descending into it, leaving nested would-prune content intact",
    ),
    StageTestCase(
        "id_descend_field_ref_rebinds",
        docs=[{"_id": {"sub": {"drop": True}, "scalar": 9}, "top": 1}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$drop", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": {"scalar": 9}, "top": 1}],
        msg="$redact under $$DESCEND should rebind a bare field reference to the _id "
        "subdocument so a matching nested doc is pruned while a sibling scalar survives",
    ),
    StageTestCase(
        "id_descend_current_rebinds",
        docs=[{"_id": {"sub": {"drop": True}, "scalar": 9}, "top": 1}],
        pipeline=[
            {"$redact": {"$cond": [{"$eq": ["$$CURRENT.drop", True]}, "$$PRUNE", "$$DESCEND"]}}
        ],
        expected=[{"_id": {"scalar": 9}, "top": 1}],
        msg="$redact under $$DESCEND should rebind $$CURRENT to the _id subdocument so a "
        "matching nested doc is pruned while a sibling scalar survives",
    ),
    StageTestCase(
        "id_only_descend_retained",
        docs=[{"_id": {"k": 1}}],
        pipeline=[{"$redact": "$$DESCEND"}],
        expected=[{"_id": {"k": 1}}],
        msg="$redact under $$DESCEND should retain an _id-only document",
    ),
]

REDACT_SCOPING_TESTS = REDACT_PER_LEVEL_TESTS + REDACT_ID_FIELD_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REDACT_SCOPING_TESTS))
def test_redact_scoping_cases(collection, test_case: StageTestCase):
    """Test $redact per-level field environment and document-valued _id handling."""
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
