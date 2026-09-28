"""
Shared expression-engine wiring tests for $$CLUSTER_TIME (TEST_COVERAGE.md §3).
One case per context; deeper behavior lives in ``cluster_time/``.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.error_codes import CLUSTER_TIME_NOT_AVAILABLE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

REQUIRES_NO_CLUSTER_TIME = (pytest.mark.requires(cluster_time=False),)

pytestmark = pytest.mark.requires(cluster_time=True)

# Property [Expression Engine Wiring]: $$CLUSTER_TIME resolves to a timestamp
# wherever the expression engine accepts an expression.
CLUSTER_TIME_EXPRESSION_ENGINE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="cluster_time_in_project",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"kind": {"$type": "$$CLUSTER_TIME"}}}],
        expected=[{"_id": 1, "kind": "timestamp"}],
        msg="$$CLUSTER_TIME in $project should resolve to a timestamp",
    ),
    StageTestCase(
        id="cluster_time_in_add_fields",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {"$addFields": {"t": "$$CLUSTER_TIME"}},
            {"$project": {"a": 1, "kind": {"$type": "$t"}}},
        ],
        expected=[{"_id": 1, "a": 1, "kind": "timestamp"}],
        msg="$$CLUSTER_TIME in $addFields should resolve to a timestamp",
    ),
    StageTestCase(
        id="cluster_time_inside_cond",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"kind": {"$type": {"$cond": [True, "$$CLUSTER_TIME", None]}}}}],
        expected=[{"_id": 1, "kind": "timestamp"}],
        msg="$$CLUSTER_TIME returned from a $cond branch should resolve to a timestamp",
    ),
    StageTestCase(
        id="cluster_time_inside_let",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$project": {
                    "kind": {"$let": {"vars": {"v": "$$CLUSTER_TIME"}, "in": {"$type": "$$v"}}}
                }
            }
        ],
        expected=[{"_id": 1, "kind": "timestamp"}],
        msg="$$CLUSTER_TIME bound through $let should resolve to a timestamp",
    ),
    StageTestCase(
        id="cluster_time_in_match_expr",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {"$match": {"$expr": {"$eq": [{"$type": "$$CLUSTER_TIME"}, "timestamp"]}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": 1}, {"_id": 2}],
        msg="$$CLUSTER_TIME in a $match $expr should resolve and select every document",
    ),
    StageTestCase(
        id="cluster_time_dot_notation_is_missing",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"kind": {"$type": "$$CLUSTER_TIME.t"}}}],
        expected=[{"_id": 1, "kind": "missing"}],
        msg="Dot notation on the scalar $$CLUSTER_TIME should resolve to missing",
    ),
    StageTestCase(
        id="cluster_time_inside_object_expression",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$project": {
                    "kind": {
                        "$type": {"$getField": {"field": "a", "input": {"a": "$$CLUSTER_TIME"}}}
                    }
                }
            }
        ],
        expected=[{"_id": 1, "kind": "timestamp"}],
        msg="$$CLUSTER_TIME nested in an object expression should stay a timestamp",
    ),
    StageTestCase(
        id="cluster_time_inside_array_expression",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"kind": {"$type": {"$arrayElemAt": [["$$CLUSTER_TIME"], 0]}}}}],
        expected=[{"_id": 1, "kind": "timestamp"}],
        msg="$$CLUSTER_TIME nested in an array expression should stay a timestamp",
    ),
    StageTestCase(
        id="cluster_time_as_operator_operand",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"kind": {"$type": {"$max": ["$$CLUSTER_TIME"]}}}}],
        expected=[{"_id": 1, "kind": "timestamp"}],
        msg="$$CLUSTER_TIME should be usable as an expression operator operand",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CLUSTER_TIME_EXPRESSION_ENGINE_TESTS))
def test_cluster_time_expression_engine(collection, test: StageTestCase):
    """$$CLUSTER_TIME resolves across shared expression-engine contexts."""
    populate_collection(collection, test)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, msg=test.msg)


# Property [Type Verification]: two operators that report or coerce a type
# either see through $$CLUSTER_TIME's timestamp type or reject it as an
# unsupported target, moved here from the type/operator-specific file since
# they exercise the shared expression engine rather than deeper timestamp
# semantics.
CLUSTER_TIME_TYPE_VERIFICATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="is_number",
        expression={"$isNumber": "$$CLUSTER_TIME"},
        expected=False,
        msg="$isNumber should report false for $$CLUSTER_TIME",
    ),
    ExpressionTestCase(
        id="convert_to_date_returns_date",
        expression={"$type": {"$convert": {"input": "$$CLUSTER_TIME", "to": "date"}}},
        expected="date",
        msg="$convert to date should accept $$CLUSTER_TIME",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CLUSTER_TIME_TYPE_VERIFICATION_TESTS))
def test_cluster_time_type_verification(collection, test: ExpressionTestCase):
    """$$CLUSTER_TIME's type is verified or converted correctly by these operators."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Unavailable Without a Cluster Clock]: where the deployment has no
# logical cluster clock, both a direct reference and an operator wrapping it
# fail with the same bespoke error, moved here from the errors file since they
# exercise the shared expression engine's resolution failure rather than a
# rejected command surface.
CLUSTER_TIME_AVAILABILITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="direct_reference",
        marks=REQUIRES_NO_CLUSTER_TIME,
        expression="$$CLUSTER_TIME",
        error_code=CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="A direct $$CLUSTER_TIME reference should fail without a cluster clock",
    ),
    ExpressionTestCase(
        id="type_operator",
        marks=REQUIRES_NO_CLUSTER_TIME,
        expression={"$type": "$$CLUSTER_TIME"},
        error_code=CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="$type of $$CLUSTER_TIME should fail without a cluster clock",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CLUSTER_TIME_AVAILABILITY_TESTS))
def test_cluster_time_availability(collection, test: ExpressionTestCase):
    """Test referencing $$CLUSTER_TIME without a cluster clock is a hard error."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
