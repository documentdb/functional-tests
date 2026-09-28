"""
$$CURRENT equivalence invariants in the default (unrebound) context.

Covers $<field> equaling $$CURRENT.<field>, across path shapes, and $$CURRENT
still equaling $$ROOT after the document has been reshaped by a preceding
stage. The base equivalence claim (bare field == $$CURRENT.<field> ==
$$ROOT.<field>, unmodified $$CURRENT == $$ROOT) is covered once as shared
expression-engine wiring in
``test_system_variables_current_expression_engine.py``.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Root Equivalence]: in the default (unrebound) context, a bare field path and
# $$CURRENT.<path> resolve identically across path shapes, including through a missing path.
EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="eq_nested_field",
        expression={"$eq": ["$a.b", "$$CURRENT.a.b"]},
        doc={"_id": 1, "a": {"b": 9}},
        expected=True,
        msg="Nested path should resolve identically with and without $$CURRENT",
    ),
    ExpressionTestCase(
        id="eq_composite_array_path",
        expression={"$eq": ["$a.b", "$$CURRENT.a.b"]},
        doc={"_id": 1, "a": [{"b": 1}, {"b": 2}]},
        expected=True,
        msg="Composite array path should resolve identically in both forms",
    ),
    ExpressionTestCase(
        id="numeric_index_path",
        expression={"$eq": ["$arr.0", "$$CURRENT.arr.0"]},
        doc={"_id": 1, "arr": [10, 20]},
        expected=True,
        msg="Numeric index path should resolve identically in both forms",
    ),
    ExpressionTestCase(
        id="missing_path",
        expression={"$eq": ["$nope", "$$CURRENT.nope"]},
        doc={"_id": 1, "a": 1},
        expected=True,
        msg="Both forms should resolve a missing path to the same value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EQUIVALENCE_TESTS))
def test_system_variables_current_equivalence(collection, test):
    """$$CURRENT is interchangeable with the bare field path form and with $$ROOT."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertSuccess(result, [{"result": test.expected}], msg=test.msg)


def test_system_variables_current_still_equals_root_after_reshaping(collection):
    """$$CURRENT and $$ROOT both refer to the reshaped document in a later stage."""
    collection.insert_many([{"_id": 1, "a": 1, "b": 2}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"a": 1}},
                {"$project": {"_id": 0, "same": {"$eq": ["$$CURRENT", "$$ROOT"]}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"same": True}],
        msg="$$CURRENT should still equal $$ROOT after reshaping",
    )
