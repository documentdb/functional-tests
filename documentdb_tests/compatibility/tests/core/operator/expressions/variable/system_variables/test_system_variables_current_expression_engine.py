"""
Shared expression-engine tests for the $$CURRENT system variable.

Covers the parser/evaluator wiring shared across operators (TEST_COVERAGE.md §3):
$$CURRENT resolves to the document as it stands at that point in the pipeline
wherever an expression is accepted, is interchangeable with a bare field path
and with $$ROOT by default, and resolves inside object/array/operator
sub-expressions. One representative case per context. Deeper behavior
(missing/null semantics, array traversal, rebinding, BSON fidelity) lives in
``current/``.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Engine Wiring]: $$CURRENT resolves to the document as it stands
# at that point in the pipeline wherever the expression engine accepts an expression.
CURRENT_EXPRESSION_ENGINE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="current_in_add_fields",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {"$addFields": {"doc": "$$CURRENT"}},
            {"$project": {"_id": 0, "doc": 1}},
        ],
        expected=[{"doc": {"_id": 1, "a": 1}}],
        msg="$$CURRENT in $addFields should capture the document as it stands at that stage",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CURRENT_EXPRESSION_ENGINE_TESTS))
def test_current_expression_engine(collection, test: StageTestCase):
    """$$CURRENT resolves to the current document across shared expression-engine contexts."""
    populate_collection(collection, test)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, msg=test.msg)


# Property [Sub-expression Wiring]: $$CURRENT resolves correctly when nested inside an
# object expression, an array expression, or as an operator operand — not just as a
# top-level expression.
CURRENT_SUBEXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="inside_object_expression",
        expression={"inner": "$$CURRENT.a"},
        doc={"_id": 1, "a": 1},
        expected={"inner": 1},
        msg="$$CURRENT should resolve inside an object expression",
    ),
    ExpressionTestCase(
        id="inside_array_expression",
        expression=["$$CURRENT.a", 1],
        doc={"_id": 1, "a": 1},
        expected=[1, 1],
        msg="$$CURRENT should resolve inside an array expression",
    ),
    ExpressionTestCase(
        id="as_operator_operand",
        expression={"$add": ["$$CURRENT.a", 1]},
        doc={"_id": 1, "a": 4},
        expected=5,
        msg="$$CURRENT.<field> should resolve as an operator operand",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CURRENT_SUBEXPRESSION_TESTS))
def test_current_in_subexpression(collection, test: ExpressionTestCase):
    """$$CURRENT resolves correctly when nested inside object/array/operator expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertSuccess(result, [{"result": test.expected}], msg=test.msg)


# Property [Equivalence Wiring]: in the default (unrebound) context, a bare field path,
# $$CURRENT.<field>, and $$ROOT.<field> all resolve to the same value, and unmodified
# $$CURRENT equals $$ROOT.
def test_current_equivalence_with_bare_field_and_root(collection):
    """$<field>, $$CURRENT.<field>, $$ROOT.<field>, and $$CURRENT itself all agree."""
    result = execute_expression_with_insert(
        collection,
        {
            "bareMatchesCurrent": {"$eq": ["$a", "$$CURRENT.a"]},
            "bareMatchesRoot": {"$eq": ["$a", "$$ROOT.a"]},
            "currentEqualsRoot": {"$eq": ["$$CURRENT", "$$ROOT"]},
        },
        {"_id": 1, "a": 5},
    )
    assertSuccess(
        result,
        [
            {
                "result": {
                    "bareMatchesCurrent": True,
                    "bareMatchesRoot": True,
                    "currentEqualsRoot": True,
                }
            }
        ],
        msg="Bare field, $$CURRENT.<field>, and $$ROOT.<field> should all resolve identically",
    )
