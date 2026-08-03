"""
$$REMOVE as a conditional branch result.

Covers $cond, nested $cond, and $switch, confirming only the targeted field
is affected per document.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (  # noqa: E501
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Conditional Branch Selection]: $$REMOVE returned from a conditional
# branch ($cond, nested $cond, or $switch) omits the target field only for the
# documents where that branch is selected, leaving sibling fields and
# non-matching documents unaffected.
#
# The basic $cond+$$REMOVE case is covered once, as shared expression-engine
# wiring, in ``test_system_variables_remove_expression_engine.py``. The cases
# below are deeper/edge behavior: sibling-field preservation, $switch, and
# self-nesting of $cond.
CONDITIONAL_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="in_cond_leaves_other_fields_unchanged",
        docs=[{"_id": 1, "a": 1, "b": "keep1"}, {"_id": 2, "a": 2, "b": "keep2"}],
        pipeline=[{"$addFields": {"a": {"$cond": [{"$eq": ["$a", 1]}, "$$REMOVE", "$a"]}}}],
        expected=[{"_id": 1, "b": "keep1"}, {"_id": 2, "a": 2, "b": "keep2"}],
        msg="Only the target field should be affected by the conditional $$REMOVE",
    ),
    StageTestCase(
        id="in_switch_branch_excludes_field",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        pipeline=[
            {
                "$project": {
                    "v": {
                        "$switch": {
                            "branches": [{"case": {"$eq": ["$a", 1]}, "then": "$$REMOVE"}],
                            "default": "$a",
                        }
                    }
                }
            }
        ],
        expected=[{"_id": 1}, {"_id": 2, "v": 2}],
        msg="Should omit the field for the branch returning $$REMOVE",
    ),
    StageTestCase(
        id="in_nested_cond_excludes_field_per_document",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        pipeline=[
            {
                "$project": {
                    "v": {
                        "$cond": [
                            {"$gt": ["$a", 1]},
                            {"$cond": [{"$eq": ["$a", 2]}, "$$REMOVE", "$a"]},
                            "$a",
                        ]
                    }
                }
            }
        ],
        expected=[{"_id": 1, "v": 1}, {"_id": 2}, {"_id": 3, "v": 3}],
        msg="Nested $cond should omit the field only where $$REMOVE is selected",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONDITIONAL_TESTS))
def test_remove_variable_as_conditional_branch(collection, test: StageTestCase):
    """$$REMOVE as a conditional branch result excludes the field only for matching documents."""
    populate_collection(collection, test)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, test.msg, ignore_doc_order=True)
