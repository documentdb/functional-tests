"""
Tests for $bitsAllClear and $bitsAllSet combined with other query operators.

Validates combinations with $not, $exists, $elemMatch, $type, $gt, $lt, $gte, $lte,
$and, $or, and compound bitwise operators across single and multiple fields.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

BITSALLCLEAR_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="compound_bitsAllSet_and_bitsAllClear",
        filter={"a": {"$bitsAllSet": 2, "$bitsAllClear": 1}},
        doc=[{"_id": 1, "a": 2}, {"_id": 2, "a": 3}, {"_id": 3, "a": 0}],
        expected=[{"_id": 1, "a": 2}],
        msg="Compound: bit 1 set AND bit 0 clear matches only 2 (binary 10)",
    ),
    QueryTestCase(
        id="not_bitsAllClear_inverts",
        filter={"a": {"$not": {"$bitsAllClear": 1}}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}, {"_id": 3, "a": 3}, {"_id": 4, "a": "str"}],
        expected=[{"_id": 2, "a": 1}, {"_id": 3, "a": 3}, {"_id": 4, "a": "str"}],
        msg="$not inverts: matches where bit 0 is NOT clear plus non-numeric",
    ),
    QueryTestCase(
        id="exists_true_with_bitsAllClear",
        filter={"a": {"$exists": True, "$bitsAllClear": 1}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "b": 1}, {"_id": 3, "a": 1}],
        expected=[{"_id": 1, "a": 0}],
        msg="$exists true AND $bitsAllClear: field must exist and bit 0 clear",
    ),
    QueryTestCase(
        id="elemMatch_with_bitsAllClear",
        filter={"a": {"$elemMatch": {"$bitsAllClear": [0, 1]}}},
        doc=[{"_id": 1, "a": [20, 35, 255]}, {"_id": 2, "a": [3, 7]}],
        expected=[{"_id": 1, "a": [20, 35, 255]}],
        msg="$elemMatch with $bitsAllClear on array of scalars",
    ),
    QueryTestCase(
        id="type_int_with_bitsAllClear",
        filter={"a": {"$type": "int", "$bitsAllClear": 1}},
        doc=[
            {"_id": 1, "a": 2},
            {"_id": 2, "a": 3},
            {"_id": 3, "a": "hello"},
            {"_id": 4, "a": 2.0},
        ],
        expected=[{"_id": 1, "a": 2}],
        msg="$type int AND $bitsAllClear: only int32 fields with bit 0 clear",
    ),
    QueryTestCase(
        id="bitsAllClear_with_gt",
        filter={"a": {"$bitsAllClear": 3, "$gt": 5}},
        doc=[
            {"_id": 1, "a": 4},
            {"_id": 2, "a": 8},
            {"_id": 3, "a": 7},
            {"_id": 4, "a": 12},
        ],
        expected=[{"_id": 2, "a": 8}, {"_id": 4, "a": 12}],
        msg="$bitsAllClear bits 0,1 AND $gt 5: 8 and 12 have bits 0,1 clear and > 5",
    ),
    QueryTestCase(
        id="bitsAllClear_with_lt",
        filter={"a": {"$bitsAllClear": 3, "$lt": 50}},
        doc=[
            {"_id": 1, "a": 4},
            {"_id": 2, "a": 40},
            {"_id": 3, "a": 55},
            {"_id": 4, "a": 60},
        ],
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 40}],
        msg="$bitsAllClear bits 0,1 AND $lt 50: 4 and 40 have bits 0,1 clear and < 50",
    ),
    QueryTestCase(
        id="bitsAllClear_with_gte_lte_range",
        filter={"a": {"$bitsAllClear": 3, "$gte": 10, "$lte": 50}},
        doc=[
            {"_id": 1, "a": 4},
            {"_id": 2, "a": 16},
            {"_id": 3, "a": 40},
            {"_id": 4, "a": 55},
            {"_id": 5, "a": 60},
        ],
        expected=[{"_id": 2, "a": 16}, {"_id": 3, "a": 40}],
        msg="$bitsAllClear bits 0,1 AND 10 <= a <= 50: 16 and 40 qualify",
    ),
    QueryTestCase(
        id="and_bitsAllClear_across_fields",
        filter={"$and": [{"a": {"$bitsAllClear": 1}}, {"b": {"$bitsAllClear": 2}}]},
        doc=[
            {"_id": 1, "a": 2, "b": 1},
            {"_id": 2, "a": 2, "b": 3},
            {"_id": 3, "a": 1, "b": 1},
        ],
        expected=[{"_id": 1, "a": 2, "b": 1}],
        msg="$and: bit 0 clear on field a AND bit 1 clear on field b",
    ),
    QueryTestCase(
        id="or_bitsAllClear_across_fields",
        filter={"$or": [{"a": {"$bitsAllClear": 1}}, {"b": {"$bitsAllClear": 2}}]},
        doc=[
            {"_id": 1, "a": 2, "b": 3},
            {"_id": 2, "a": 1, "b": 1},
            {"_id": 3, "a": 1, "b": 3},
        ],
        expected=[{"_id": 1, "a": 2, "b": 3}, {"_id": 2, "a": 1, "b": 1}],
        msg="$or: bit 0 clear on field a OR bit 1 clear on field b",
    ),
    QueryTestCase(
        id="not_bitsAllClear_across_fields",
        filter={
            "$and": [{"a": {"$not": {"$bitsAllClear": 1}}}, {"b": {"$not": {"$bitsAllClear": 2}}}]
        },
        doc=[
            {"_id": 1, "a": 1, "b": 3},
            {"_id": 2, "a": 2, "b": 3},
            {"_id": 3, "a": 1, "b": 1},
        ],
        expected=[{"_id": 1, "a": 1, "b": 3}],
        msg="$not $bitsAllClear across fields: bit 0 NOT clear on a AND bit 1 NOT clear on b",
    ),
    QueryTestCase(
        id="nor_bitsAllClear_across_fields",
        filter={"$nor": [{"a": {"$bitsAllClear": 1}}, {"b": {"$bitsAllClear": 2}}]},
        doc=[
            {"_id": 1, "a": 1, "b": 3},
            {"_id": 2, "a": 2, "b": 1},
            {"_id": 3, "a": 1, "b": 1},
        ],
        expected=[{"_id": 1, "a": 1, "b": 3}],
        msg="$nor: neither bit 0 clear on a NOR bit 1 clear on b",
    ),
]


BITS_ALL_SET_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="contradictory_bitsAllSet_and_bitsAllClear",
        filter={"a": {"$bitsAllSet": [1], "$bitsAllClear": [1]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}, {"_id": 3, "a": 3}],
        expected=[],
        msg="Contradictory: bit 1 must be both set AND clear — always empty result",
    ),
    QueryTestCase(
        id="bitsAllSet_with_not",
        filter={"a": {"$not": {"$bitsAllSet": 1}}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}, {"_id": 3, "a": 3}, {"_id": 4, "a": "str"}],
        expected=[{"_id": 1, "a": 0}, {"_id": 4, "a": "str"}],
        msg="$not inverts: matches docs where bit 0 is NOT set, plus non-numeric",
    ),
    QueryTestCase(
        id="bitsAllSet_with_exists",
        filter={"a": {"$exists": True, "$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "b": 1}, {"_id": 3, "a": 0}],
        expected=[{"_id": 1, "a": 1}],
        msg="$exists true AND $bitsAllSet: field must exist and bit 0 set",
    ),
    QueryTestCase(
        id="bitsAllSet_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$bitsAllSet": [0, 1]}}},
        doc=[{"_id": 1, "a": [3, 20, 255]}, {"_id": 2, "a": [4, 8]}],
        expected=[{"_id": 1, "a": [3, 20, 255]}],
        msg="$elemMatch with $bitsAllSet on array of scalars",
    ),
    QueryTestCase(
        id="type_int_with_bitsAllSet",
        filter={"a": {"$type": "int", "$bitsAllSet": 1}},
        doc=[
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 2},
            {"_id": 3, "a": "hello"},
            {"_id": 4, "a": 3.0},
        ],
        expected=[{"_id": 1, "a": 3}],
        msg="$type int AND $bitsAllSet: only int32 fields with bit 0 set",
    ),
    QueryTestCase(
        id="bitsAllSet_with_gt",
        filter={"a": {"$bitsAllSet": 3, "$gt": 5}},
        doc=[
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3, "a": 8},
            {"_id": 4, "a": 15},
        ],
        expected=[{"_id": 2, "a": 7}, {"_id": 4, "a": 15}],
        msg="$bitsAllSet bits 0,1 AND $gt 5: 7 and 15 have bits 0,1 set and > 5",
    ),
    QueryTestCase(
        id="bitsAllSet_with_lt",
        filter={"a": {"$bitsAllSet": 3, "$lt": 50}},
        doc=[
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3, "a": 55},
            {"_id": 4, "a": 60},
        ],
        expected=[{"_id": 1, "a": 3}, {"_id": 2, "a": 7}],
        msg="$bitsAllSet bits 0,1 AND $lt 50: 3 and 7 have bits 0,1 set and < 50",
    ),
    QueryTestCase(
        id="bitsAllSet_with_gte_lte_range",
        filter={"a": {"$bitsAllSet": 3, "$gte": 5, "$lte": 50}},
        doc=[
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3, "a": 15},
            {"_id": 4, "a": 55},
            {"_id": 5, "a": 8},
        ],
        expected=[{"_id": 2, "a": 7}, {"_id": 3, "a": 15}],
        msg="$bitsAllSet bits 0,1 AND 5 <= a <= 50: 7 and 15 qualify",
    ),
    QueryTestCase(
        id="and_bitsAllSet_across_fields",
        filter={"$and": [{"a": {"$bitsAllSet": 1}}, {"b": {"$bitsAllSet": 2}}]},
        doc=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 1, "b": 1},
            {"_id": 3, "a": 2, "b": 2},
        ],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="$and: bit 0 set on field a AND bit 1 set on field b",
    ),
    QueryTestCase(
        id="or_bitsAllSet_across_fields",
        filter={"$or": [{"a": {"$bitsAllSet": 1}}, {"b": {"$bitsAllSet": 2}}]},
        doc=[
            {"_id": 1, "a": 1, "b": 0},
            {"_id": 2, "a": 0, "b": 2},
            {"_id": 3, "a": 0, "b": 0},
        ],
        expected=[{"_id": 1, "a": 1, "b": 0}, {"_id": 2, "a": 0, "b": 2}],
        msg="$or: bit 0 set on field a OR bit 1 set on field b",
    ),
    QueryTestCase(
        id="not_bitsAllSet_across_fields",
        filter={"$and": [{"a": {"$not": {"$bitsAllSet": 1}}}, {"b": {"$not": {"$bitsAllSet": 2}}}]},
        doc=[
            {"_id": 1, "a": 0, "b": 1},
            {"_id": 2, "a": 1, "b": 1},
            {"_id": 3, "a": 0, "b": 2},
        ],
        expected=[{"_id": 1, "a": 0, "b": 1}],
        msg="$not $bitsAllSet across fields: bit 0 NOT set on a AND bit 1 NOT set on b",
    ),
    QueryTestCase(
        id="nor_bitsAllSet_across_fields",
        filter={"$nor": [{"a": {"$bitsAllSet": 1}}, {"b": {"$bitsAllSet": 2}}]},
        doc=[
            {"_id": 1, "a": 0, "b": 1},
            {"_id": 2, "a": 1, "b": 0},
            {"_id": 3, "a": 0, "b": 0},
        ],
        expected=[{"_id": 1, "a": 0, "b": 1}, {"_id": 3, "a": 0, "b": 0}],
        msg="$nor: neither bit 0 set on a NOR bit 1 set on b",
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(BITSALLCLEAR_COMBINATION_TESTS + BITS_ALL_SET_COMBINATION_TESTS)
)
def test_bitwise_operator_combinations(collection, test):
    """Test $bitsAllClear and $bitsAllSet combined with other query operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
