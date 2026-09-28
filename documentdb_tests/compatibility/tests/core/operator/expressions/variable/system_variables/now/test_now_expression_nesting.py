"""$$NOW expression nesting: deep date-operator nesting, $let/iteration constancy,
sub-pipelines, $getField. Basic wiring lives in the parent
system_variables/test_system_variables_now_expression_engine.py; this file covers
the deeper property that binding and iteration boundaries do not re-evaluate $$NOW.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.aggregate


DRIFT_BOUND_MS = 500

NOW_EXPRESSION_NESTING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="now_deeply_nested_date_operators",
        expression={
            "$eq": [
                {
                    "$dateTrunc": {
                        "date": {
                            "$dateAdd": {
                                "startDate": {
                                    "$dateSubtract": {
                                        "startDate": "$$NOW",
                                        "unit": "hour",
                                        "amount": 1,
                                    }
                                },
                                "unit": "hour",
                                "amount": 1,
                            }
                        },
                        "unit": "millisecond",
                    }
                },
                "$$NOW",
            ]
        },
        expected=True,
        msg="$$NOW should resolve consistently inside deeply nested date operators",
    ),
    ExpressionTestCase(
        id="now_constant_across_let_binding",
        expression={"$let": {"vars": {"bound": "$$NOW"}, "in": {"$eq": ["$$bound", "$$NOW"]}}},
        expected=True,
        msg="$$NOW bound through $let should equal $$NOW read directly in the same expression",
    ),
    ExpressionTestCase(
        id="now_constant_across_nested_let_bindings",
        expression={
            "$let": {
                "vars": {"outer": "$$NOW"},
                "in": {
                    "$let": {
                        "vars": {"inner": "$$NOW"},
                        "in": {"$eq": ["$$outer", "$$inner"]},
                    }
                },
            }
        },
        expected=True,
        msg="$$NOW should be the same value in an outer and a nested $let binding",
    ),
    ExpressionTestCase(
        id="now_constant_across_map_iterations",
        expression={
            "$size": {"$setUnion": {"$map": {"input": [1, 2, 3], "as": "x", "in": "$$NOW"}}}
        },
        expected=1,
        msg="$$NOW inside $map should be the same value on every iteration",
    ),
    ExpressionTestCase(
        id="now_inside_filter_condition",
        expression={
            "$size": {
                "$filter": {
                    "input": [
                        {"$subtract": ["$$NOW", 2000]},
                        {"$subtract": ["$$NOW", 1000]},
                        {"$add": ["$$NOW", 3600000]},
                    ],
                    "as": "d",
                    "cond": {"$lte": ["$$d", "$$NOW"]},
                }
            }
        },
        expected=2,
        msg="$$NOW inside a $filter condition should select only the elements at or before it",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NOW_EXPRESSION_NESTING_TESTS))
def test_now_expression_nesting(collection, test: ExpressionTestCase):
    """$$NOW keeps its date type and value across object/array/operator nesting."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


def test_now_in_lookup_sub_pipeline(collection):
    """Test $$NOW inside a $lookup sub-pipeline stays within a bounded lag of the outer value."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"outer": "$$NOW"}},
                {
                    "$lookup": {
                        "from": collection.name,
                        "let": {"outer": "$outer"},
                        "pipeline": [
                            {"$limit": 1},
                            {"$project": {"_id": 0, "inner": "$$NOW", "carried": "$$outer"}},
                        ],
                        "as": "probe",
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "probeCount": {"$size": "$probe"},
                        "letCarried": {"$eq": [{"$first": "$probe.carried"}, "$outer"]},
                        "drift": {
                            "$let": {
                                "vars": {
                                    "ms": {"$subtract": [{"$first": "$probe.inner"}, "$outer"]}
                                },
                                "in": {
                                    "$cond": [
                                        {
                                            "$and": [
                                                {"$gte": ["$$ms", 0]},
                                                {"$lt": ["$$ms", DRIFT_BOUND_MS]},
                                            ]
                                        },
                                        "within-bound",
                                        {"$concat": ["drift=", {"$toString": "$$ms"}, "ms"]},
                                    ]
                                },
                            }
                        },
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"probeCount": 1, "letCarried": True, "drift": "within-bound"}],
        msg="$$NOW in a $lookup sub-pipeline should closely follow the outer pipeline's value",
    )


def test_now_in_facet_sub_pipeline(collection):
    """Test $$NOW inside a $facet sub-pipeline equals the outer pipeline's value."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"outer": "$$NOW"}},
                {
                    "$facet": {
                        "same": [
                            {"$match": {"$expr": {"$eq": ["$outer", "$$NOW"]}}},
                            {"$count": "matched"},
                        ]
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"same": [{"matched": 1}]}],
        msg="$$NOW in a $facet sub-pipeline should match the outer pipeline's value",
    )


def test_now_in_union_with_sub_pipeline(collection):
    """Test $$NOW inside a $unionWith sub-pipeline equals the outer pipeline's value."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"outer": "$$NOW"}},
                {
                    "$unionWith": {
                        "coll": collection.name,
                        "pipeline": [
                            {"$addFields": {"outer": "$$NOW"}},
                            {"$project": {"_id": 0, "outer": 1}},
                        ],
                    }
                },
                {"$group": {"_id": "$outer"}},
                {"$count": "groups"},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"groups": 1}],
        msg="$$NOW in a $unionWith sub-pipeline should match the outer pipeline's value",
    )


def test_now_as_get_field_stringified(collection):
    """Test $getField with a stringified $$NOW resolves to missing."""
    result = execute_expression(
        collection, {"$getField": {"field": {"$toString": "$$NOW"}, "input": {"a": 1}}}
    )
    assertSuccess(
        result,
        [{}],
        msg="A stringified $$NOW is not a document field, so $getField returns missing",
    )
