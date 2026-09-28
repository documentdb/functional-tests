"""$$NOW core semantics: BSON date type, current server time, server-side evaluation,
constancy invariants, and monotonicity across executions.
"""

import time
from datetime import datetime

import pytest
from bson import Int64

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

NOW_TYPE_AND_SEMANTICS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="now_returns_date_type",
        expression={"$type": "$$NOW"},
        expected="date",
        msg="$$NOW should be a BSON date",
    ),
    ExpressionTestCase(
        id="now_usable_as_date_operator_input",
        expression={"$type": {"$dateTrunc": {"date": "$$NOW", "unit": "day"}}},
        expected="date",
        msg="$$NOW should be usable as input to date operators",
    ),
    ExpressionTestCase(
        id="now_usable_as_date_to_string_input",
        expression={"$type": {"$dateToString": {"date": "$$NOW"}}},
        expected="string",
        msg="$dateToString should accept $$NOW and return a string",
    ),
    ExpressionTestCase(
        id="now_usable_as_date_to_parts_input",
        expression={"$type": {"$dateToParts": {"date": "$$NOW"}}},
        expected="object",
        msg="$dateToParts should accept $$NOW and return an object",
    ),
    ExpressionTestCase(
        id="now_represents_current_server_time",
        expression={
            "$and": [
                {"$gt": ["$$NOW", datetime(2020, 1, 1)]},
                {"$lt": ["$$NOW", datetime(2100, 1, 1)]},
            ]
        },
        expected=True,
        msg="$$NOW should represent the current server time",
    ),
    ExpressionTestCase(
        id="now_evaluated_without_document_input",
        expression={"$eq": [{"$type": "$$NOW"}, "date"]},
        expected=True,
        msg="$$NOW should be evaluated server-side without any document input",
    ),
]

# Number of separate executions sampled to prove sub-second granularity. A server with
# millisecond resolution yields a zero millisecond component about 1 time in 1000, so the
# chance of every sample being second-aligned by coincidence is (1/1000) ** 20. A server with
# whole-second resolution yields zero on every sample and fails deterministically.
MILLISECOND_SAMPLE_COUNT = 20


@pytest.mark.parametrize("test", pytest_params(NOW_TYPE_AND_SEMANTICS_TESTS))
def test_now_type_and_semantics(collection, test: ExpressionTestCase):
    """$$NOW resolves to a BSON date reflecting current server time, evaluated server-side."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_now_has_millisecond_resolution(collection):
    """Test $$NOW carries a non-zero millisecond component, proving sub-second granularity."""
    samples = []
    for _ in range(MILLISECOND_SAMPLE_COUNT):
        sample = execute_command(
            collection,
            {
                "aggregate": 1,
                "pipeline": [{"$documents": [{}]}, {"$project": {"_id": 0, "t": "$$NOW"}}],
                "cursor": {},
            },
        )
        samples.append(sample["cursor"]["firstBatch"][0]["t"])

    result = execute_expression(
        collection,
        {
            "$gt": [
                {"$max": {"$map": {"input": samples, "as": "d", "in": {"$millisecond": "$$d"}}}},
                0,
            ]
        },
    )
    assert_expression_result(
        result,
        expected=True,
        msg="$$NOW should carry a non-zero millisecond component in at least one execution",
    )


NOW_SELF_CONSTANCY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="now_equals_itself_within_one_expression",
        expression={"$eq": ["$$NOW", "$$NOW"]},
        expected=True,
        msg="Two $$NOW references in one expression should be equal",
    ),
    ExpressionTestCase(
        id="now_difference_within_one_expression_is_zero",
        expression={"$subtract": ["$$NOW", "$$NOW"]},
        expected=Int64(0),
        msg="$subtract of two $$NOW references should be 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NOW_SELF_CONSTANCY_TESTS))
def test_now_self_constancy(collection, test: ExpressionTestCase):
    """Test $$NOW is self-consistent within a single expression."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_now_identical_for_every_document(collection):
    """Test $$NOW collapses to a single distinct value across all documents."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"t": "$$NOW"}},
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}}},
                {"$project": {"_id": 0, "distinct": {"$size": "$values"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"distinct": 1}],
        msg="$$NOW should be identical for every document in one aggregation",
    )


def test_now_identical_across_pipeline_stages(collection):
    """Test $$NOW read in a later stage equals the value read in an earlier stage."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"early": "$$NOW"}},
                {"$match": {"$expr": {"$eq": ["$early", "$$NOW"]}}},
                {"$count": "matched"},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"matched": 3}],
        msg="$$NOW should be identical across all stages of one pipeline",
    )


def test_now_identical_across_getmore_batches(collection):
    """Test $$NOW is identical in the first batch and every getMore batch of one cursor."""
    collection.insert_many([{"_id": i} for i in range(300)])

    first = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "t": "$$NOW"}}],
            "cursor": {"batchSize": 2},
        },
    )
    seen = [doc["t"] for doc in first["cursor"]["firstBatch"]]
    cursor_id = first["cursor"]["id"]
    while cursor_id:
        batch = execute_command(
            collection,
            {"getMore": cursor_id, "collection": collection.name, "batchSize": 2},
        )
        seen.extend(doc["t"] for doc in batch["cursor"]["nextBatch"])
        cursor_id = batch["cursor"]["id"]

    result = execute_expression(collection, {"$size": {"$setUnion": [seen]}})
    assert_expression_result(
        result,
        expected=1,
        msg="$$NOW should be identical across every getMore batch of one cursor",
    )


def test_now_advances_across_executions(collection):
    """Test $$NOW advances after a delay between two separate executions."""
    first = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [{"$documents": [{}]}, {"$project": {"_id": 0, "t": "$$NOW"}}],
            "cursor": {},
        },
    )
    earlier = first["cursor"]["firstBatch"][0]["t"]
    time.sleep(0.05)
    result = execute_expression(collection, {"$gt": ["$$NOW", earlier]})
    assert_expression_result(
        result,
        expected=True,
        msg="$$NOW should advance between executions separated by a delay",
    )
