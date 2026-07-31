"""
Expression context tests for the $$ROOT system variable.

Covers how $$ROOT resolves within nested/inner expressions ($filter, $reduce,
object/array literals, operator arguments) and its divergence from $$CURRENT
inside $redact. Shared expression-engine wiring lives in
../test_system-variables_root_expression_engine.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NESTING_DOC = {"_id": 1, "a": 2, "b": 3, "arr": [10, 20], "nested": {"x": 5}}


# Property [Expression Resolution]: $$ROOT resolves to the outer document wherever an
# expression is accepted — nested in object/array literals, through multiple operator
# layers, as an operator argument, and inside $filter/$reduce inner scopes where a
# local variable like $$this or $$value is also bound.
EXPRESSION_RESOLUTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="inside_object_expression",
        expression={"inner": "$$ROOT"},
        doc=NESTING_DOC,
        expected={"inner": NESTING_DOC},
        msg="$$ROOT should resolve as an object expression field value",
    ),
    ExpressionTestCase(
        id="inside_array_expression",
        expression=["$$ROOT"],
        doc=NESTING_DOC,
        expected=[NESTING_DOC],
        msg="$$ROOT should resolve as an array expression element",
    ),
    ExpressionTestCase(
        id="operand_of_arithmetic_operator",
        expression={"$add": ["$$ROOT.nested.x", "$$CURRENT.a"]},
        doc=NESTING_DOC,
        expected=7,
        msg="$$ROOT.<path> and $$CURRENT.<path> should resolve as arithmetic operands",
    ),
    ExpressionTestCase(
        id="filter_cond_expression",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", "$$ROOT.a"]}}},
        doc={"_id": 1, "a": 15, "arr": [10, 20]},
        expected=[20],
        msg="$$ROOT inside a $filter 'cond' should refer to the outer document",
    ),
    ExpressionTestCase(
        id="reduce_in_expression",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 0,
                "in": {"$add": ["$$value", {"$multiply": ["$$this", "$$ROOT.a"]}]},
            }
        },
        doc=NESTING_DOC,
        expected=60,
        msg="$$ROOT inside a $reduce 'in' should refer to the outer document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EXPRESSION_RESOLUTION_TESTS))
def test_root_resolves_in_expression(collection, test):
    """$$ROOT resolves correctly wherever an expression is accepted."""
    result = execute_expression_with_insert(collection, test.expression, dict(test.doc))
    assert_expression_result(result, expected=test.expected, msg=test.msg)


REDACT_DOCS = [
    {"_id": 0, "b": {"a": 1}},
    {"_id": 1, "a": 1, "b": {}},
    {"_id": 2, "a": 1, "b": {"a": 1}},
    {"_id": 3, "a": 1, "b": {"a": 2}},
]


# Property [Redact Level Independence]: inside $redact, $$ROOT stays pinned to the
# top-level document at every recursion level while a bare field path resolves against
# the level currently being visited, so $$DESCEND can be driven by comparing the two.
# This is the one representative case kept here; $$KEEP/$$PRUNE/$$DESCEND sentinel
# semantics themselves (including $$ROOT pinning across levels) are owned by
# stages/redact/test_redact_scoping.py (see perlevel_root_pinned_no_rebind and friends).
REDACT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="descend_else_prune",
        expression={
            "$cond": {"if": {"$eq": ["$$ROOT.a", "$a"]}, "then": "$$DESCEND", "else": "$$PRUNE"}
        },
        expected=[
            {"_id": 0},
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 1, "b": {"a": 1}},
            {"_id": 3, "a": 1},
        ],
        msg="$$DESCEND should compare $$ROOT.<field> against each level's own field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(REDACT_TESTS))
def test_root_in_redact_condition(collection, test):
    """$redact compares $$ROOT.<field> against the current level's field."""
    collection.insert_many([dict(d) for d in REDACT_DOCS])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$redact": test.expression}, {"$sort": {"_id": 1}}],
            "cursor": {},
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)
