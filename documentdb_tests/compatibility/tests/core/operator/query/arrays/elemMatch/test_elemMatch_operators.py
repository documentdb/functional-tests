"""
Tests for comparison operators inside $elemMatch.

Covers $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin,
embedded document matching, nested $elemMatch,
and bitwise operators $bitsAllSet, $bitsAnySet, $bitsAllClear, $bitsAnyClear.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="eq",
        filter={"a": {"$elemMatch": {"$eq": 5}}},
        doc=[{"_id": 1, "a": [5, 10]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [5, 10]}],
        msg="$eq inside $elemMatch",
    ),
    QueryTestCase(
        id="ne",
        filter={"a": {"$elemMatch": {"$ne": 5}}},
        doc=[{"_id": 1, "a": [5]}, {"_id": 2, "a": [5, 10]}],
        expected=[{"_id": 2, "a": [5, 10]}],
        msg="$ne inside $elemMatch — at least one element != 5",
    ),
    QueryTestCase(
        id="gt",
        filter={"a": {"$elemMatch": {"$gt": 5}}},
        doc=[{"_id": 1, "a": [3, 7]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [3, 7]}],
        msg="$gt inside $elemMatch",
    ),
    QueryTestCase(
        id="gte",
        filter={"a": {"$elemMatch": {"$gte": 5}}},
        doc=[{"_id": 1, "a": [5, 3]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [5, 3]}],
        msg="$gte inside $elemMatch",
    ),
    QueryTestCase(
        id="lt",
        filter={"a": {"$elemMatch": {"$lt": 5}}},
        doc=[{"_id": 1, "a": [3, 7]}, {"_id": 2, "a": [6, 8]}],
        expected=[{"_id": 1, "a": [3, 7]}],
        msg="$lt inside $elemMatch",
    ),
    QueryTestCase(
        id="lte",
        filter={"a": {"$elemMatch": {"$lte": 5}}},
        doc=[{"_id": 1, "a": [5, 7]}, {"_id": 2, "a": [6, 8]}],
        expected=[{"_id": 1, "a": [5, 7]}],
        msg="$lte inside $elemMatch",
    ),
    QueryTestCase(
        id="in",
        filter={"a": {"$elemMatch": {"$in": [3, 5]}}},
        doc=[{"_id": 1, "a": [3, 7]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [3, 7]}],
        msg="$in inside $elemMatch",
    ),
    QueryTestCase(
        id="nin",
        filter={"a": {"$elemMatch": {"$nin": [3, 5]}}},
        doc=[{"_id": 1, "a": [3, 5]}, {"_id": 2, "a": [3, 7]}],
        expected=[{"_id": 2, "a": [3, 7]}],
        msg="$nin inside $elemMatch — at least one not in [3,5]",
    ),
]

EMBEDDED_DOC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="multiple_field_conditions",
        filter={"results": {"$elemMatch": {"product": "abc", "score": {"$gte": 8}}}},
        doc=[
            {
                "_id": 1,
                "results": [
                    {"product": "abc", "score": 9},
                    {"product": "def", "score": 7},
                ],
            },
            {
                "_id": 2,
                "results": [
                    {"product": "abc", "score": 5},
                    {"product": "def", "score": 9},
                ],
            },
        ],
        expected=[
            {
                "_id": 1,
                "results": [
                    {"product": "abc", "score": 9},
                    {"product": "def", "score": 7},
                ],
            }
        ],
        msg="Single element must match all conditions",
    ),
    QueryTestCase(
        id="partial_match_no_single_doc",
        filter={"results": {"$elemMatch": {"product": "abc", "score": {"$gte": 8}}}},
        doc=[
            {
                "_id": 1,
                "results": [
                    {"product": "abc", "score": 5},
                    {"product": "def", "score": 9},
                ],
            }
        ],
        expected=[],
        msg="No single embedded doc matches all conditions",
    ),
    QueryTestCase(
        id="nested_field_path",
        filter={"a": {"$elemMatch": {"x.y": 1}}},
        doc=[
            {"_id": 1, "a": [{"x": {"y": 1}}, {"x": {"y": 2}}]},
            {"_id": 2, "a": [{"x": {"y": 3}}]},
        ],
        expected=[{"_id": 1, "a": [{"x": {"y": 1}}, {"x": {"y": 2}}]}],
        msg="$elemMatch with nested field path in embedded docs",
    ),
    QueryTestCase(
        id="in_on_embedded_doc_field",
        filter={"a": {"$elemMatch": {"x": {"$in": [1, 2]}}}},
        doc=[
            {"_id": 1, "a": [{"x": 1}, {"x": 3}]},
            {"_id": 2, "a": [{"x": 4}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 1}, {"x": 3}]}],
        msg="$in on embedded doc field inside $elemMatch",
    ),
    QueryTestCase(
        id="nin_on_embedded_doc_field",
        filter={"a": {"$elemMatch": {"x": {"$nin": [1, 2]}}}},
        doc=[
            {"_id": 1, "a": [{"x": 1}, {"x": 3}]},
            {"_id": 2, "a": [{"x": 1}, {"x": 2}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 1}, {"x": 3}]}],
        msg="$nin on embedded doc field inside $elemMatch",
    ),
    QueryTestCase(
        id="ne_on_embedded_doc_field",
        filter={"a": {"$elemMatch": {"x": {"$ne": 1}}}},
        doc=[
            {"_id": 1, "a": [{"x": 1}]},
            {"_id": 2, "a": [{"x": 1}, {"x": 2}]},
        ],
        expected=[{"_id": 2, "a": [{"x": 1}, {"x": 2}]}],
        msg="$ne on embedded doc field inside $elemMatch",
    ),
    QueryTestCase(
        id="gt_on_embedded_doc_field",
        filter={"a": {"$elemMatch": {"x": {"$gt": 80}}}},
        doc=[
            {"_id": 1, "a": [{"x": 82}, {"x": 75}]},
            {"_id": 2, "a": [{"x": 60}, {"x": 70}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 82}, {"x": 75}]}],
        msg="$gt on embedded doc field inside $elemMatch",
    ),
    QueryTestCase(
        id="lt_on_embedded_doc_field",
        filter={"a": {"$elemMatch": {"x": {"$lt": 70}}}},
        doc=[
            {"_id": 1, "a": [{"x": 82}, {"x": 75}]},
            {"_id": 2, "a": [{"x": 60}, {"x": 70}]},
        ],
        expected=[{"_id": 2, "a": [{"x": 60}, {"x": 70}]}],
        msg="$lt on embedded doc field inside $elemMatch",
    ),
]

NESTED_ELEMMATCH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_basic",
        filter={"a": {"$elemMatch": {"nested": {"$elemMatch": {"$gt": 1}}}}},
        doc=[
            {"_id": 1, "a": [{"nested": [1, 5]}, {"nested": [0]}]},
            {"_id": 2, "a": [{"nested": [0, 1]}]},
        ],
        expected=[{"_id": 1, "a": [{"nested": [1, 5]}, {"nested": [0]}]}],
        msg="Nested $elemMatch matches inner array element",
    ),
    QueryTestCase(
        id="deeply_nested_three_levels",
        filter={"a": {"$elemMatch": {"b": {"$elemMatch": {"c": {"$elemMatch": {"$gt": 0}}}}}}},
        doc=[
            {"_id": 1, "a": [{"b": [{"c": [1, 2]}]}]},
            {"_id": 2, "a": [{"b": [{"c": [0, -1]}]}]},
        ],
        expected=[{"_id": 1, "a": [{"b": [{"c": [1, 2]}]}]}],
        msg="Three levels of nested $elemMatch",
    ),
    QueryTestCase(
        id="nested_on_embedded_doc_array",
        filter={"a": {"$elemMatch": {"items": {"$elemMatch": {"x": {"$gt": 5}}}}}},
        doc=[
            {"_id": 1, "a": [{"items": [{"x": 3}, {"x": 7}]}]},
            {"_id": 2, "a": [{"items": [{"x": 1}, {"x": 2}]}]},
        ],
        expected=[{"_id": 1, "a": [{"items": [{"x": 3}, {"x": 7}]}]}],
        msg="Nested $elemMatch on embedded doc array field",
    ),
]

BITWISE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bitsAllSet",
        filter={"a": {"$elemMatch": {"$bitsAllSet": [0, 1]}}},
        doc=[{"_id": 1, "a": [3, 4]}, {"_id": 2, "a": [4, 8]}],
        expected=[{"_id": 1, "a": [3, 4]}],
        msg="$bitsAllSet inside $elemMatch — element with bits 0 and 1 set",
    ),
    QueryTestCase(
        id="bitsAnySet",
        filter={"a": {"$elemMatch": {"$bitsAnySet": [0, 1]}}},
        doc=[{"_id": 1, "a": [2, 4]}, {"_id": 2, "a": [4, 8]}],
        expected=[{"_id": 1, "a": [2, 4]}],
        msg="$bitsAnySet inside $elemMatch — element with bit 0 or 1 set",
    ),
    QueryTestCase(
        id="bitsAllClear",
        filter={"a": {"$elemMatch": {"$bitsAllClear": [0, 1]}}},
        doc=[{"_id": 1, "a": [3, 4]}, {"_id": 2, "a": [3, 1]}],
        expected=[{"_id": 1, "a": [3, 4]}],
        msg="$bitsAllClear inside $elemMatch — element with bits 0 and 1 clear",
    ),
    QueryTestCase(
        id="bitsAnyClear",
        filter={"a": {"$elemMatch": {"$bitsAnyClear": [0, 1]}}},
        doc=[{"_id": 1, "a": [3, 7]}, {"_id": 2, "a": [2, 4]}],
        expected=[{"_id": 2, "a": [2, 4]}],
        msg="$bitsAnyClear inside $elemMatch — element with bit 0 or 1 clear",
    ),
]

ALL_OPERATOR_TESTS = COMPARISON_TESTS + EMBEDDED_DOC_TESTS + NESTED_ELEMMATCH_TESTS + BITWISE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_OPERATOR_TESTS))
def test_elemMatch_operators(collection, test):
    """Test comparison operators inside $elemMatch."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)
