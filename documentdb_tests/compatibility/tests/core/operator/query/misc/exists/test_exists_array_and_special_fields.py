"""
Tests for $exists array field behavior, special field names, and multiple fields.

Covers $exists on array fields, $elemMatch with $exists, _id field behavior,
and multiple $exists conditions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

MULTI_DOCS = [
    {"_id": 1, "a": 1, "b": 2},
    {"_id": 2, "a": 1},
    {"_id": 3, "b": 2},
    {"_id": 4},
]

ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="elemMatch_exists_true",
        filter={"a": {"$elemMatch": {"y": {"$exists": True}}}},
        doc=[{"_id": 1, "a": [{"x": 1, "y": 2}, {"x": 3}]}],
        expected=[{"_id": 1, "a": [{"x": 1, "y": 2}, {"x": 3}]}],
        msg="$elemMatch with $exists: true matches element with field",
    ),
    QueryTestCase(
        id="elemMatch_exists_false",
        filter={"a": {"$elemMatch": {"y": {"$exists": False}}}},
        doc=[{"_id": 1, "a": [{"x": 1, "y": 2}, {"x": 3}]}],
        expected=[{"_id": 1, "a": [{"x": 1, "y": 2}, {"x": 3}]}],
        msg="$elemMatch with $exists: false matches element without field",
    ),
    QueryTestCase(
        id="elemMatch_compound",
        filter={"a": {"$elemMatch": {"y": {"$exists": True}, "x": {"$gt": 0}}}},
        doc=[{"_id": 1, "a": [{"x": 1, "y": 2}, {"x": 3}]}],
        expected=[{"_id": 1, "a": [{"x": 1, "y": 2}, {"x": 3}]}],
        msg="$elemMatch compound with $exists and $gt",
    ),
    QueryTestCase(
        id="dot_notation_nested_fields",
        filter={"a.x": {"$exists": True}},
        doc=[
            {"_id": 1, "a": [{"x": 1}, {"x": 2}, {"y": 3}]},
            {"_id": 2, "a": [{"y": 1}, {"y": 2}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 1}, {"x": 2}, {"y": 3}]}],
        msg="Dot notation on array elements matches when any has field",
    ),
]

SPECIAL_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="id_always_true",
        filter={"_id": {"$exists": True}},
        doc=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        expected=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="_id always exists — $exists: true matches all",
    ),
    QueryTestCase(
        id="id_false_no_match",
        filter={"_id": {"$exists": False}},
        doc=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        expected=[],
        msg="_id always exists — $exists: false matches none",
    ),
    QueryTestCase(
        id="both_exist",
        filter={"a": {"$exists": True}, "b": {"$exists": True}},
        doc=MULTI_DOCS,
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="Both fields must exist",
    ),
    QueryTestCase(
        id="a_exists_b_not",
        filter={"a": {"$exists": True}, "b": {"$exists": False}},
        doc=MULTI_DOCS,
        expected=[{"_id": 2, "a": 1}],
        msg="a exists, b does not",
    ),
    QueryTestCase(
        id="neither_exists",
        filter={"a": {"$exists": False}, "b": {"$exists": False}},
        doc=MULTI_DOCS,
        expected=[{"_id": 4}],
        msg="Neither field exists",
    ),
]

ALL_TESTS = ARRAY_TESTS + SPECIAL_FIELD_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_exists_array_and_special_fields(collection, test):
    """Parametrized test for $exists array behavior, special fields, and multiple conditions."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
