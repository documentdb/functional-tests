"""
Tests for $nor query operator null and missing field handling.

Covers $nor behavior with null values, missing fields, and $exists interaction.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="missing_field_returned",
        filter={"$nor": [{"val": 5}]},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 10}, {"_id": 3, "other": 1}],
        msg="$nor should return docs where field does not exist (fails the match)",
    ),
    QueryTestCase(
        id="null_field_excluded_by_null_match",
        filter={"$nor": [{"val": None}]},
        doc=[{"_id": 1, "val": None}, {"_id": 2, "val": 5}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 5}],
        msg="$nor with null condition excludes docs with val=null AND missing field docs",
    ),
    QueryTestCase(
        id="type_null_excludes_null_and_missing",
        filter={"$nor": [{"val": {"$type": "null"}}]},
        doc=[{"_id": 1, "val": None}, {"_id": 2, "val": 5}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 5}, {"_id": 3, "other": 1}],
        msg="$nor with $type null excludes docs where val is null but not missing-field docs",
    ),
    QueryTestCase(
        id="null_field_with_gt_operator",
        filter={"$nor": [{"val": {"$gt": 5}}]},
        doc=[{"_id": 1, "val": None}, {"_id": 2, "val": 10}, {"_id": 3, "val": 3}],
        expected=[{"_id": 1, "val": None}, {"_id": 3, "val": 3}],
        msg="$nor with $gt — docs with val=null are returned (null doesn't satisfy $gt)",
    ),
]

EXISTS_INTERACTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="exists_true",
        filter={"$nor": [{"val": {"$exists": True}}]},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "other": 1}],
        expected=[{"_id": 2, "other": 1}],
        msg="$nor with $exists:true returns only docs without the field",
    ),
    QueryTestCase(
        id="exists_false",
        filter={"$nor": [{"val": {"$exists": False}}]},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "other": 1}],
        expected=[{"_id": 1, "val": 5}],
        msg="$nor with $exists:false returns only docs with the field",
    ),
    QueryTestCase(
        id="value_and_exists_false_combined",
        filter={"$nor": [{"price": 1.99}, {"price": {"$exists": False}}]},
        doc=[
            {"_id": 1, "price": 1.99},
            {"_id": 2, "price": 5.00},
            {"_id": 3, "other": 1},
        ],
        expected=[{"_id": 2, "price": 5.00}],
        msg="$nor combining value and $exists:false returns docs where field exists AND != match",
    ),
    QueryTestCase(
        id="multiple_fields_with_exists",
        filter={
            "$nor": [
                {"price": 1.99},
                {"price": {"$exists": False}},
                {"sale": True},
                {"sale": {"$exists": False}},
            ]
        },
        doc=[
            {"_id": 1, "price": 1.99, "sale": False},
            {"_id": 2, "price": 5.00, "sale": True},
            {"_id": 3, "price": 5.00, "sale": False},
            {"_id": 4, "price": 5.00},
        ],
        expected=[{"_id": 3, "price": 5.00, "sale": False}],
        msg="$nor with multiple fields & $exists returns docs where both exist, neither matches",
    ),
]

ALL_TESTS = NULL_MISSING_TESTS + EXISTS_INTERACTION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_nor_null_missing(collection, test):
    """Test $nor query operator null and missing field handling."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
