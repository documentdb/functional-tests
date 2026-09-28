"""
$$CURRENT composed with other expression operators.

Covers how $$CURRENT resolves inside $map/$filter/$reduce iteration scopes
(including rebinding via `as`), plus $mergeObjects reading $$CURRENT.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# Property [Scope Isolation]: $$CURRENT composes correctly with other operators — accepted
# as $mergeObjects input — and, inside $map/$filter/$reduce, resolves to the outer
# document by default but rebinds to each iterated element when the iteration variable is
# explicitly named CURRENT via `as`.
COMPOSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="merge_objects_with_current_adds_fields",
        expression={"merged": {"$mergeObjects": ["$$CURRENT", {"b": 2}]}},
        doc={"_id": 1, "a": 1},
        expected=[{"merged": {"_id": 1, "a": 1, "b": 2}}],
        msg="$mergeObjects should merge $$CURRENT with the given object",
    ),
    ExpressionTestCase(
        id="map_with_as_current_rebinds_to_each_element",
        expression={"v": {"$map": {"input": "$arr", "as": "CURRENT", "in": "$$CURRENT"}}},
        doc={"_id": 1, "arr": [1, 2, 3]},
        expected=[{"v": [1, 2, 3]}],
        msg="$map with as = CURRENT should bind $$CURRENT to each element",
    ),
    ExpressionTestCase(
        id="map_with_as_current_rebinds_bare_field_path",
        expression={"v": {"$map": {"input": "$arr", "as": "CURRENT", "in": "$b"}}},
        doc={"_id": 1, "arr": [{"b": 1}, {"b": 2}]},
        expected=[{"v": [1, 2]}],
        msg="Rebinding $$CURRENT via as = CURRENT should also change what bare $b resolves to",
    ),
    ExpressionTestCase(
        id="map_default_iteration_variable_leaves_current_unchanged",
        expression={"v": {"$map": {"input": "$arr", "in": "$$CURRENT.a"}}},
        doc={"_id": 1, "arr": [1, 2], "a": 8},
        expected=[{"v": [8, 8]}],
        msg="$$CURRENT should remain the outer document inside $map",
    ),
    ExpressionTestCase(
        id="filter_cond_sees_outer_document_through_current",
        expression={
            "v": {
                "$filter": {
                    "input": "$arr",
                    "cond": {"$gt": ["$$this", "$$CURRENT.threshold"]},
                }
            }
        },
        doc={"_id": 1, "arr": [1, 2, 3], "threshold": 2},
        expected=[{"v": [3]}],
        msg="$$CURRENT inside $filter should resolve to the outer document",
    ),
    ExpressionTestCase(
        id="reduce_in_sees_outer_document_through_current",
        expression={
            "v": {
                "$reduce": {
                    "input": "$arr",
                    "initialValue": 0,
                    "in": {"$add": ["$$value", "$$this", "$$CURRENT.bonus"]},
                }
            }
        },
        doc={"_id": 1, "arr": [1, 2], "bonus": 10},
        expected=[{"v": 23}],
        msg="$$CURRENT inside $reduce should resolve to the outer document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMPOSITION_TESTS))
def test_system_variables_current_composition(collection, test):
    """$$CURRENT composes with $mergeObjects and $map/$filter/$reduce scoping."""
    result = execute_project_with_insert(collection, test.doc, test.expression)
    assertSuccess(result, test.expected, msg=test.msg)
