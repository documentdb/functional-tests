"""
Shared expression-engine tests for the $$NOW system variable.

Covers parser/evaluator wiring shared across operators (TEST_COVERAGE.md §3): one
representative case per context, asserting BSON type or a relational property (never
a pinned instant, since the value comes from the server clock). Deeper behavior lives
in ``now/``.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Engine Wiring]: $$NOW resolves to a date wherever the
# expression engine accepts an expression.
NOW_EXPRESSION_ENGINE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="now_in_project",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"kind": {"$type": "$$NOW"}}}],
        expected=[{"_id": 1, "kind": "date"}],
        msg="$$NOW in $project should resolve to a date",
    ),
    StageTestCase(
        id="now_in_add_fields",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {"$addFields": {"t": "$$NOW"}},
            {"$project": {"a": 1, "kind": {"$type": "$t"}}},
        ],
        expected=[{"_id": 1, "a": 1, "kind": "date"}],
        msg="$$NOW in $addFields should resolve to a date",
    ),
    StageTestCase(
        id="now_inside_cond",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"kind": {"$type": {"$cond": [True, "$$NOW", None]}}}}],
        expected=[{"_id": 1, "kind": "date"}],
        msg="$$NOW returned from a $cond branch should resolve to a date",
    ),
    StageTestCase(
        id="now_inside_let",
        docs=[{"_id": 1}],
        pipeline=[
            {"$project": {"kind": {"$let": {"vars": {"v": "$$NOW"}, "in": {"$type": "$$v"}}}}}
        ],
        expected=[{"_id": 1, "kind": "date"}],
        msg="$$NOW bound through $let should resolve to a date",
    ),
    StageTestCase(
        id="now_in_match_expr",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {"$match": {"$expr": {"$eq": [{"$type": "$$NOW"}, "date"]}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": 1}, {"_id": 2}],
        msg="$$NOW in a $match $expr should resolve and select every document",
    ),
    StageTestCase(
        id="now_dot_notation_is_missing",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"kind": {"$type": "$$NOW.t"}}}],
        expected=[{"_id": 1, "kind": "missing"}],
        msg="Dot notation on the scalar $$NOW should resolve to missing",
    ),
    StageTestCase(
        id="now_inside_object_expression",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$project": {
                    "kind": {"$type": {"$getField": {"field": "a", "input": {"a": "$$NOW"}}}}
                }
            }
        ],
        expected=[{"_id": 1, "kind": "date"}],
        msg="$$NOW nested in an object expression should stay a date",
    ),
    StageTestCase(
        id="now_inside_array_expression",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"kind": {"$type": {"$arrayElemAt": [["$$NOW"], 0]}}}}],
        expected=[{"_id": 1, "kind": "date"}],
        msg="$$NOW nested in an array expression should stay a date",
    ),
    StageTestCase(
        id="now_as_operator_operand",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"kind": {"$type": {"$add": ["$$NOW", 1]}}}}],
        expected=[{"_id": 1, "kind": "date"}],
        msg="$$NOW should be usable as an expression operator operand",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NOW_EXPRESSION_ENGINE_TESTS))
def test_now_expression_engine(collection, test: StageTestCase):
    """$$NOW resolves across shared expression-engine contexts."""
    populate_collection(collection, test)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, msg=test.msg)


def test_now_identical_within_one_pipeline_execution(collection):
    """Every reference to $$NOW in one pipeline execution resolves to the same value: an
    early-stage capture, a late-stage read, and a per-document read all agree."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"early": "$$NOW"}},
                {"$addFields": {"late": "$$NOW", "sameAsEarly": {"$eq": ["$early", "$$NOW"]}}},
                {
                    "$group": {
                        "_id": None,
                        "distinctLate": {"$addToSet": "$late"},
                        "allSameAsEarly": {"$min": "$sameAsEarly"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "distinct": {"$size": "$distinctLate"},
                        "allSameAsEarly": 1,
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"distinct": 1, "allSameAsEarly": True}],
        msg="Every $$NOW reference across stages and documents in one execution should agree",
    )


def test_now_usable_as_date_expression_operand(collection):
    """$$NOW is usable as the date operand wherever one is accepted: a unary argument
    ($dateToParts), a named field ($dateTrunc), and a pair of arguments ($dateDiff)."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {
                    "$project": {
                        "_id": 0,
                        "partsKind": {"$type": {"$dateToParts": {"date": "$$NOW"}}},
                        "truncKind": {"$type": {"$dateTrunc": {"date": "$$NOW", "unit": "day"}}},
                        "diffToItself": {
                            "$dateDiff": {
                                "startDate": "$$NOW",
                                "endDate": "$$NOW",
                                "unit": "millisecond",
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
        [{"partsKind": "object", "truncKind": "date", "diffToItself": Int64(0)}],
        msg="$$NOW should be usable as the date operand to $dateToParts, $dateTrunc, and $dateDiff",
    )
