"""Tests for $$ROOT and $$CURRENT context inside a $lookup correlated sub-pipeline.

Inside the sub-pipeline, $$ROOT and $$CURRENT refer to the FOREIGN document
context, not the outer document. Outer context must be captured via let.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Correlated Subquery System Variables]: inside the sub-pipeline
# $$ROOT and $$CURRENT refer to the foreign document context; outer context must
# be captured via let before the sub-pipeline executes.
LOOKUP_SYSTEM_VARS_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "ROOT_inside_sub_pipeline_refers_to_foreign",
        foreign_docs=[{"_id": 10, "name": "foreign_doc"}],
        docs=[{"_id": 1, "name": "outer_doc"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$addFields": {"rootName": "$$ROOT.name"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "name": "outer_doc",
                "joined": [{"_id": 10, "name": "foreign_doc", "rootName": "foreign_doc"}],
            }
        ],
        msg="$$ROOT inside sub-pipeline should refer to the foreign document, not outer",
    ),
    LookupTestCase(
        "CURRENT_inside_sub_pipeline_refers_to_foreign",
        foreign_docs=[{"_id": 10, "name": "foreign_doc"}],
        docs=[{"_id": 1, "name": "outer_doc"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$addFields": {"currentName": "$$CURRENT.name"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "name": "outer_doc",
                "joined": [{"_id": 10, "name": "foreign_doc", "currentName": "foreign_doc"}],
            }
        ],
        msg="$$CURRENT inside sub-pipeline should refer to the foreign document, not outer",
    ),
    LookupTestCase(
        "let_captures_outer_ROOT_vs_inner_ROOT",
        foreign_docs=[{"_id": 10, "name": "foreign"}],
        docs=[{"_id": 1, "name": "outer"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"outerRoot": "$$ROOT"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "outerName": "$$outerRoot.name",
                                "innerName": "$$ROOT.name",
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "name": "outer",
                "joined": [
                    {
                        "_id": 10,
                        "name": "foreign",
                        "outerName": "outer",
                        "innerName": "foreign",
                    }
                ],
            }
        ],
        msg=(
            "let capturing $$ROOT should preserve outer doc context while"
            " $$ROOT inside pipeline refers to foreign doc"
        ),
    ),
    LookupTestCase(
        "nested_ROOT_refers_to_innermost_foreign",
        foreign_docs=[{"_id": 10, "name": "L1"}],
        docs=[{"_id": 1, "name": "L0"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"outerRoot": "$$ROOT"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "pipeline": [
                                    {
                                        "$addFields": {
                                            "deepRoot": "$$ROOT.name",
                                            "fromOuter": "$$outerRoot.name",
                                        }
                                    }
                                ],
                                "as": "inner",
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "name": "L0",
                "joined": [
                    {
                        "_id": 10,
                        "name": "L1",
                        "inner": [
                            {
                                "_id": 10,
                                "name": "L1",
                                "deepRoot": "L1",
                                "fromOuter": "L0",
                            }
                        ],
                    }
                ],
            }
        ],
        msg=(
            "In nested $lookup, $$ROOT in innermost pipeline refers to"
            " that level's foreign doc while outer let preserves L0 context"
        ),
    ),
    LookupTestCase(
        "NOW_accessible_inside_sub_pipeline",
        foreign_docs=[{"_id": 10}],
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$addFields": {"nowType": {"$type": "$$NOW"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "joined": [{"_id": 10, "nowType": "date"}]}],
        msg="$$NOW should be accessible inside $lookup sub-pipeline as date type",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_SYSTEM_VARS_TESTS))
def test_lookup_correlated_system_vars(collection, test_case: LookupTestCase):
    """Test $lookup correlated subquery $$ROOT/$$CURRENT/$$NOW context semantics."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
