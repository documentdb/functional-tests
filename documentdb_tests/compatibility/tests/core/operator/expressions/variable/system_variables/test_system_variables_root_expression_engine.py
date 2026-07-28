"""
Shared expression-engine tests for the $$ROOT system variable.

These cover the expression parser/evaluator mechanics that are shared across
operators (TEST_COVERAGE.md §3 "Expression Engine Tests"): that $$ROOT resolves
to the current document wherever an expression is accepted. They live at the
``system-variables/`` level because they are foundational wiring, not $$ROOT's
own deep behavior — that (BSON type fidelity, error/reserved-name rules,
accumulator/redact/replaceRoot interactions, the full field-path matrix) lives
in ``system-variables/root/``.

Contexts covered here, each with one representative case:
- $$ROOT in $project
- $$ROOT in $addFields
- $$ROOT nested field path ($$ROOT.a.b)
- $$ROOT inside $cond (and through nested expression layers)
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Engine Wiring]: $$ROOT resolves to the document currently being
# processed wherever the expression engine accepts an expression — as a $project/$addFields
# value, as a dotted field path, and nested inside an operator such as $cond.
ROOT_EXPRESSION_ENGINE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="root_in_project",
        docs=[{"_id": 1, "a": 10, "nested": {"x": 2}}],
        pipeline=[{"$project": {"_id": 0, "snap": "$$ROOT"}}],
        expected=[{"snap": {"_id": 1, "a": 10, "nested": {"x": 2}}}],
        msg="$$ROOT in $project should resolve to the whole current document",
    ),
    StageTestCase(
        id="root_in_add_fields",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$addFields": {"snap": "$$ROOT"}}],
        expected=[{"_id": 1, "a": 10, "snap": {"_id": 1, "a": 10}}],
        msg="$$ROOT in $addFields should resolve to the document entering the stage",
    ),
    StageTestCase(
        id="root_nested_path",
        docs=[{"_id": 1, "a": {"b": 20}}],
        pipeline=[{"$project": {"_id": 0, "result": "$$ROOT.a.b"}}],
        expected=[{"result": 20}],
        msg="$$ROOT.<a>.<b> should resolve a nested field path against the root document",
    ),
    StageTestCase(
        id="root_inside_cond",
        docs=[{"_id": 1, "a": 2, "b": 3, "arr": [10, 20], "nested": {"x": 5}}],
        pipeline=[
            {
                "$project": {
                    "_id": 0,
                    "result": {
                        "$cond": [
                            {"$gt": [{"$size": {"$objectToArray": "$$ROOT"}}, 2]},
                            "$$ROOT.a",
                            "$$ROOT.b",
                        ]
                    },
                }
            }
        ],
        expected=[{"result": 2}],
        msg="$$ROOT should resolve inside a $cond and through nested expression layers",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ROOT_EXPRESSION_ENGINE_TESTS))
def test_root_expression_engine(collection, test: StageTestCase):
    """$$ROOT resolves to the current document across shared expression-engine contexts."""
    populate_collection(collection, test)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, msg=test.msg)
