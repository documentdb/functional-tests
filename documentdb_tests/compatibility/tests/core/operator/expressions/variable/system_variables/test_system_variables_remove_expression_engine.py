"""
Shared expression-engine tests for the $$REMOVE system variable.

Covers the parser/evaluator wiring shared across operators (TEST_COVERAGE.md §3):
$$REMOVE resolves to missing wherever an expression is accepted, omitting the
target field. One representative case each for $project, $addFields, a $cond
branch, and a nested field path. Deeper behavior lives in ``remove/``.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Engine Wiring]: $$REMOVE resolves to missing wherever an
# expression is accepted, omitting the target field.
REMOVE_EXPRESSION_ENGINE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="remove_in_project",
        docs=[{"_id": 1, "a": 1, "b": 2}],
        pipeline=[{"$project": {"a": "$$REMOVE", "b": 1}}],
        expected=[{"_id": 1, "b": 2}],
        msg="$$REMOVE in $project should omit the target field",
    ),
    StageTestCase(
        id="remove_in_add_fields",
        docs=[{"_id": 1, "a": 1, "b": 2}],
        pipeline=[{"$addFields": {"a": "$$REMOVE"}}],
        expected=[{"_id": 1, "b": 2}],
        msg="$$REMOVE in $addFields should omit the field it is assigned to",
    ),
    StageTestCase(
        id="remove_inside_cond",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        pipeline=[{"$project": {"v": {"$cond": [{"$eq": ["$a", 1]}, "$a", "$$REMOVE"]}}}],
        expected=[{"_id": 1, "v": 1}, {"_id": 2}],
        msg="$$REMOVE returned from a $cond branch should omit the field for that document",
    ),
    StageTestCase(
        id="remove_nested_path",
        docs=[{"_id": 1, "a": {"b": 1, "c": 2}}],
        pipeline=[{"$project": {"a.b": "$$REMOVE"}}],
        expected=[{"_id": 1, "a": {}}],
        msg="$$REMOVE on a nested field path should omit that field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(REMOVE_EXPRESSION_ENGINE_TESTS))
def test_remove_expression_engine(collection, test: StageTestCase):
    """$$REMOVE resolves to missing across shared expression-engine contexts."""
    populate_collection(collection, test)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, msg=test.msg)
