"""
Tests for $not query operator core logic.

Covers basic NOT negation semantics, missing field inclusion,
comparison operator interactions, and equivalence with $ne/$lte/$gte.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CORE_LOGIC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="negates_true_condition",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=[{"_id": 1, "val": 15}],
        expected=[],
        msg="$not should negate a true condition — doc with val=15 not returned for $not $gt:10",
    ),
    QueryTestCase(
        id="negates_false_condition",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=[{"_id": 1, "val": 5}],
        expected=[{"_id": 1, "val": 5}],
        msg="$not should negate a false condition — doc with val=5 returned for $not $gt:10",
    ),
    QueryTestCase(
        id="includes_missing_field",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "other": 20}],
        expected=[{"_id": 1, "val": 5}, {"_id": 2, "other": 20}],
        msg="$not should include documents where the field does not exist",
    ),
    QueryTestCase(
        id="not_gt_differs_from_lte_on_missing",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}, {"_id": 3, "other": 1}],
        expected=[{"_id": 1, "val": 5}, {"_id": 3, "other": 1}],
        msg="$not $gt includes missing field docs unlike $lte",
    ),
    QueryTestCase(
        id="lte_excludes_missing",
        filter={"val": {"$lte": 10}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}, {"_id": 3, "other": 1}],
        expected=[{"_id": 1, "val": 5}],
        msg="$lte does NOT include missing field docs",
    ),
    QueryTestCase(
        id="not_lt_differs_from_gte_on_missing",
        filter={"val": {"$not": {"$lt": 10}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 15}, {"_id": 3, "other": 1}],
        msg="$not $lt includes missing field docs unlike $gte",
    ),
    QueryTestCase(
        id="gte_excludes_missing",
        filter={"val": {"$gte": 10}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 15}],
        msg="$gte does NOT include missing field docs",
    ),
    QueryTestCase(
        id="not_eq_equivalent_to_ne",
        filter={"val": {"$not": {"$eq": 5}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 10}, {"_id": 3, "other": 1}],
        msg="$not $eq should be equivalent to $ne",
    ),
    QueryTestCase(
        id="ne_equivalent_to_not_eq",
        filter={"val": {"$ne": 5}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 10}, {"_id": 3, "other": 1}],
        msg="$ne should produce same results as $not $eq",
    ),
    QueryTestCase(
        id="not_ne_double_negation",
        filter={"val": {"$not": {"$ne": 10}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 10}],
        msg="$not $ne (double negation) should return only val==10, NOT including missing",
    ),
    QueryTestCase(
        id="not_in_equivalent_to_nin",
        filter={"val": {"$not": {"$in": [1, 2]}}},
        doc=[{"_id": 1, "val": 1}, {"_id": 2, "val": 3}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 3}, {"_id": 3, "other": 1}],
        msg="$not $in should be equivalent to $nin",
    ),
    QueryTestCase(
        id="nin_equivalent_to_not_in",
        filter={"val": {"$nin": [1, 2]}},
        doc=[{"_id": 1, "val": 1}, {"_id": 2, "val": 3}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 3}, {"_id": 3, "other": 1}],
        msg="$nin should produce same results as $not $in",
    ),
]

COMPARISON_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_gt_returns_lte_or_missing",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}, {"_id": 3, "val": 15}],
        expected=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}],
        msg="$not $gt:10 should return val <= 10",
    ),
    QueryTestCase(
        id="not_gte_returns_lt_or_missing",
        filter={"val": {"$not": {"$gte": 10}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}, {"_id": 3, "val": 15}],
        expected=[{"_id": 1, "val": 5}],
        msg="$not $gte:10 should return val < 10",
    ),
    QueryTestCase(
        id="not_lt_returns_gte_or_missing",
        filter={"val": {"$not": {"$lt": 10}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}, {"_id": 3, "val": 15}],
        expected=[{"_id": 2, "val": 10}, {"_id": 3, "val": 15}],
        msg="$not $lt:10 should return val >= 10",
    ),
    QueryTestCase(
        id="not_lte_returns_gt_or_missing",
        filter={"val": {"$not": {"$lte": 10}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}, {"_id": 3, "val": 15}],
        expected=[{"_id": 3, "val": 15}],
        msg="$not $lte:10 should return val > 10",
    ),
]

MULTIPLE_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_with_multiple_operators_gt_lt",
        filter={"val": {"$not": {"$gt": 5, "$lt": 20}}},
        doc=[{"_id": 1, "val": 3}, {"_id": 2, "val": 10}, {"_id": 3, "val": 25}],
        expected=[{"_id": 1, "val": 3}, {"_id": 3, "val": 25}],
        msg="$not with multiple operators ($gt and $lt) should negate the compound condition",
    ),
]

AND_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_inside_and_range",
        filter={"$and": [{"val": {"$not": {"$gt": 20}}}, {"val": {"$not": {"$lt": 10}}}]},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}, {"_id": 3, "val": 25}],
        expected=[{"_id": 2, "val": 15}],
        msg="$not inside $and should create range 10 <= val <= 20",
    ),
    QueryTestCase(
        id="not_inside_and_with_equality",
        filter={"$and": [{"val": {"$not": {"$gt": 5}}}, {"val": {"$not": {"$lt": 5}}}]},
        doc=[{"_id": 1, "val": 3}, {"_id": 2, "val": 5}, {"_id": 3, "val": 7}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not inside $and with $gt:5 and $lt:5 should return only val==5",
    ),
]

ALL_TESTS = (
    CORE_LOGIC_TESTS + COMPARISON_OPERATOR_TESTS + MULTIPLE_OPERATOR_TESTS + AND_COMBINATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_core_logic(collection, test):
    """Test $not query operator core negation logic."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
