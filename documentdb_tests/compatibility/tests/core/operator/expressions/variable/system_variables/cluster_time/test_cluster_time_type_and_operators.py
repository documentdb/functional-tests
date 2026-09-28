"""
$$CLUSTER_TIME value type, operator-input handling, and type conversion.

Resolved BSON type, null/missing behavior, accept/reject per operator, and
conversion to a date. No test pins a literal value — only type, relation, and
coarse-bound assertions. Full per-operator matrices live in each operator's own
folder, including the Timestamp rows for $isArray, $toDate, $year,
$dateToString, $dateAdd, $sortArray, $add and the sort type-order suite, so
those operators are not re-tested here.
"""

from datetime import datetime

import pytest
from bson import Int64, ObjectId, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    TS_EPOCH,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

pytestmark = [pytest.mark.aggregate, pytest.mark.requires(cluster_time=True)]


# Property [Value Type and Semantics]: the timestamp is neither a number nor an
# array; it's never the null-timestamp sentinel and falls in the current era;
# it's distinguishable from null/missing; typed and any-type consumers accept
# or round-trip it correctly; it's distinct from other BSON types denoting the
# same instant; it sorts by canonical BSON type order; $convert/$toDate agree;
# and it sits inside the timestamp domain.
CLUSTER_TIME_VALUE_TESTS: list[ExpressionTestCase] = [
    # Property [Value Shape]
    ExpressionTestCase(
        id="not_null_timestamp",
        expression={"$ne": ["$$CLUSTER_TIME", Timestamp(0, 0)]},
        expected=True,
        msg="$$CLUSTER_TIME should never be the null timestamp the server substitutes on insert",
    ),
    ExpressionTestCase(
        id="derived_date_is_current_era",
        expression={
            "$and": [
                {"$gt": [{"$toDate": "$$CLUSTER_TIME"}, datetime(2020, 1, 1)]},
                {"$lt": [{"$toDate": "$$CLUSTER_TIME"}, datetime(2100, 1, 1)]},
            ]
        },
        expected=True,
        msg="The date derived from $$CLUSTER_TIME should fall in the current era",
    ),
    # Property [Not Null, Not Missing]
    ExpressionTestCase(
        id="if_null_returns_timestamp",
        expression={"$type": {"$ifNull": ["$$CLUSTER_TIME", "fallback"]}},
        expected="timestamp",
        msg="$ifNull should return $$CLUSTER_TIME rather than the fallback",
    ),
    ExpressionTestCase(
        id="not_equal_to_null",
        expression={"$eq": ["$$CLUSTER_TIME", None]},
        expected=False,
        msg="$$CLUSTER_TIME should not compare equal to null",
    ),
    ExpressionTestCase(
        id="not_equal_to_missing",
        expression={"$eq": ["$$CLUSTER_TIME", "$missing"]},
        expected=False,
        msg="$$CLUSTER_TIME should not compare equal to a missing field path",
    ),
    ExpressionTestCase(
        id="type_differs_from_missing",
        expression={"$eq": [{"$type": "$$CLUSTER_TIME"}, {"$type": "$missing"}]},
        expected=False,
        msg="$$CLUSTER_TIME should be type-distinguishable from a missing field",
    ),
    ExpressionTestCase(
        id="ne",
        expression={"$ne": ["$$CLUSTER_TIME", TS_EPOCH]},
        expected=True,
        msg="$ne should accept $$CLUSTER_TIME",
    ),
    ExpressionTestCase(
        id="cmp",
        expression={"$cmp": ["$$CLUSTER_TIME", TS_EPOCH]},
        expected=1,
        msg="$cmp should accept $$CLUSTER_TIME",
    ),
    ExpressionTestCase(
        id="min",
        expression={"$type": {"$min": ["$$CLUSTER_TIME", "$$CLUSTER_TIME"]}},
        expected="timestamp",
        msg="$min should round-trip $$CLUSTER_TIME as a timestamp",
    ),
    ExpressionTestCase(
        id="not_equal_to_derived_date",
        expression={"$eq": ["$$CLUSTER_TIME", {"$toDate": "$$CLUSTER_TIME"}]},
        expected=False,
        msg="A timestamp should not equal the date derived from it",
    ),
    ExpressionTestCase(
        id="not_equal_to_epoch_millis",
        expression={"$eq": ["$$CLUSTER_TIME", {"$toLong": {"$toDate": "$$CLUSTER_TIME"}}]},
        expected=False,
        msg="A timestamp should not equal the long epoch milliseconds of the same instant",
    ),
    ExpressionTestCase(
        id="not_equal_to_object_id",
        expression={"$eq": ["$$CLUSTER_TIME", ObjectId()]},
        expected=False,
        msg="A timestamp should not equal an ObjectId generated at the same instant",
    ),
    ExpressionTestCase(
        id="not_equal_to_long",
        expression={"$eq": ["$$CLUSTER_TIME", Int64(0)]},
        expected=False,
        msg="A timestamp should not equal a long",
    ),
    ExpressionTestCase(
        id="to_date_and_convert_agree",
        expression={
            "$eq": [
                {"$toDate": "$$CLUSTER_TIME"},
                {"$convert": {"input": "$$CLUSTER_TIME", "to": "date"}},
            ]
        },
        expected=True,
        msg="$toDate and $convert to date should produce the same value",
    ),
    ExpressionTestCase(
        id="convert_to_bool_is_true",
        expression={"$convert": {"input": "$$CLUSTER_TIME", "to": "bool"}},
        expected=True,
        msg="Converting a non-zero timestamp to bool should yield true",
    ),
    ExpressionTestCase(
        id="on_error_branch_is_taken",
        expression={"$convert": {"input": "$$CLUSTER_TIME", "to": "int", "onError": "failed"}},
        expected="failed",
        msg="An unsupported conversion target should take the onError branch, not throw",
    ),
    ExpressionTestCase(
        id="on_null_branch_is_not_taken",
        expression={
            "$type": {"$convert": {"input": "$$CLUSTER_TIME", "to": "date", "onNull": "was null"}}
        },
        expected="date",
        msg="The onNull branch should never be taken for $$CLUSTER_TIME",
    ),
    ExpressionTestCase(
        id="after_epoch",
        expression={"$gt": ["$$CLUSTER_TIME", TS_EPOCH]},
        expected=True,
        msg="The live cluster time should be after the Unix epoch",
    ),
    ExpressionTestCase(
        id="below_unsigned_maximum",
        expression={"$lt": ["$$CLUSTER_TIME", TS_MAX_UNSIGNED32]},
        expected=True,
        msg="The live cluster time should be inside the unsigned 32-bit seconds range",
    ),
    ExpressionTestCase(
        id="below_signed_maximum_in_the_current_era",
        expression={"$lt": ["$$CLUSTER_TIME", TS_MAX_SIGNED32]},
        expected=True,
        msg="The live cluster time should currently be below the signed 32-bit boundary",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CLUSTER_TIME_VALUE_TESTS))
def test_cluster_time_value(collection, test: ExpressionTestCase):
    """Test $$CLUSTER_TIME's resolved type, shape, and relational properties."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_cluster_time_round_trips_through_group_accumulators(collection):
    """Test $first, $last, $min, $max and $push preserve the timestamp type in $group."""
    collection.insert_many([{"_id": i} for i in range(5)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$group": {
                        "_id": None,
                        "first": {"$first": "$$CLUSTER_TIME"},
                        "last": {"$last": "$$CLUSTER_TIME"},
                        "min": {"$min": "$$CLUSTER_TIME"},
                        "max": {"$max": "$$CLUSTER_TIME"},
                        "pushed": {"$push": "$$CLUSTER_TIME"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "kinds": [
                            {"$type": "$first"},
                            {"$type": "$last"},
                            {"$type": "$min"},
                            {"$type": "$max"},
                            {"$type": {"$arrayElemAt": ["$pushed", 0]}},
                        ],
                    }
                },
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"kinds": ["timestamp"] * 5}],
        msg="Accumulators should preserve the timestamp type for $$CLUSTER_TIME",
    )


def test_cluster_time_date_diff_against_now_is_not_negative(collection):
    """Test the seconds between the cluster time and $$NOW is not negative."""
    result = execute_expression(
        collection,
        {
            "$gte": [
                {
                    "$dateDiff": {
                        "startDate": "$$CLUSTER_TIME",
                        "endDate": "$$NOW",
                        "unit": "second",
                    }
                },
                0,
            ]
        },
    )
    assert_expression_result(
        result,
        expected=True,
        msg="$$NOW should not precede the cluster time's derived date",
    )
