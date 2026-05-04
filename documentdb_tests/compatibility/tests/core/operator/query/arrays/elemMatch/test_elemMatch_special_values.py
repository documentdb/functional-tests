"""
Tests for $elemMatch special value handling.

Covers null/missing fields, numeric equivalence, BSON type distinction,
field lookup patterns, and Decimal128 special values (NaN, Infinity).
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

NULL_AND_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="field_is_null",
        filter={"a": {"$elemMatch": {"$gt": 0}}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 2, "a": [1]}],
        msg="$elemMatch on null field returns no match",
    ),
    QueryTestCase(
        id="field_is_missing",
        filter={"a": {"$elemMatch": {"$gt": 0}}},
        doc=[{"_id": 1, "b": 1}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 2, "a": [1]}],
        msg="$elemMatch on missing field returns no match",
    ),
    QueryTestCase(
        id="eq_null_no_null_elements",
        filter={"a": {"$elemMatch": {"$eq": None}}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[],
        msg="$eq null on array with no null elements returns no match",
    ),
    QueryTestCase(
        id="eq_null_with_null_element",
        filter={"a": {"$elemMatch": {"$eq": None}}},
        doc=[
            {"_id": 1, "a": [1, None, 3]},
            {"_id": 2, "a": [1, 2]},
        ],
        expected=[{"_id": 1, "a": [1, None, 3]}],
        msg="$eq null matches null element in array",
    ),
    QueryTestCase(
        id="ne_null_all_null",
        filter={"a": {"$elemMatch": {"$ne": None}}},
        doc=[
            {"_id": 1, "a": [None, None]},
            {"_id": 2, "a": [1, None]},
        ],
        expected=[{"_id": 2, "a": [1, None]}],
        msg="$ne null on all-null array returns no match",
    ),
    QueryTestCase(
        id="ne_null_with_non_null",
        filter={"a": {"$elemMatch": {"$ne": None}}},
        doc=[
            {"_id": 1, "a": [1, None]},
            {"_id": 2, "a": [None]},
        ],
        expected=[{"_id": 1, "a": [1, None]}],
        msg="$ne null matches when at least one non-null element",
    ),
]

NUMERIC_EQUIVALENCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_matches_long",
        filter={"a": {"$elemMatch": {"$eq": 1}}},
        doc=[{"_id": 1, "a": [Int64(1)]}],
        expected=[{"_id": 1, "a": [Int64(1)]}],
        msg="$eq 1 (int) matches Int64(1)",
    ),
    QueryTestCase(
        id="int_matches_double",
        filter={"a": {"$elemMatch": {"$eq": 1}}},
        doc=[{"_id": 1, "a": [1.0]}],
        expected=[{"_id": 1, "a": [1.0]}],
        msg="$eq 1 (int) matches 1.0 (double)",
    ),
    QueryTestCase(
        id="int_matches_decimal128",
        filter={"a": {"$elemMatch": {"$eq": 1}}},
        doc=[{"_id": 1, "a": [Decimal128("1")]}],
        expected=[{"_id": 1, "a": [Decimal128("1")]}],
        msg="$eq 1 (int) matches Decimal128('1')",
    ),
    QueryTestCase(
        id="long_gt_matches_int",
        filter={"a": {"$elemMatch": {"$gt": Int64(5)}}},
        doc=[{"_id": 1, "a": [6]}, {"_id": 2, "a": [4]}],
        expected=[{"_id": 1, "a": [6]}],
        msg="$gt Int64(5) matches int 6",
    ),
    QueryTestCase(
        id="positive_negative_zero_equal",
        filter={"a": {"$elemMatch": {"$eq": DOUBLE_ZERO}}},
        doc=[{"_id": 1, "a": [DOUBLE_NEGATIVE_ZERO]}],
        expected=[{"_id": 1, "a": [DOUBLE_NEGATIVE_ZERO]}],
        msg="0.0 and -0.0 are equal per IEEE 754",
    ),
    QueryTestCase(
        id="eq_infinity",
        filter={"a": {"$elemMatch": {"$eq": FLOAT_INFINITY}}},
        doc=[
            {"_id": 1, "a": [FLOAT_INFINITY]},
            {"_id": 2, "a": [1]},
        ],
        expected=[{"_id": 1, "a": [FLOAT_INFINITY]}],
        msg="$eq Infinity matches Infinity",
    ),
    QueryTestCase(
        id="eq_negative_infinity",
        filter={"a": {"$elemMatch": {"$eq": FLOAT_NEGATIVE_INFINITY}}},
        doc=[
            {"_id": 1, "a": [FLOAT_NEGATIVE_INFINITY]},
            {"_id": 2, "a": [1]},
        ],
        expected=[{"_id": 1, "a": [FLOAT_NEGATIVE_INFINITY]}],
        msg="$eq -Infinity matches -Infinity",
    ),
    QueryTestCase(
        id="eq_decimal128_infinity",
        filter={"a": {"$elemMatch": {"$eq": Decimal128("Infinity")}}},
        doc=[
            {"_id": 1, "a": [Decimal128("Infinity")]},
            {"_id": 2, "a": [1]},
        ],
        expected=[{"_id": 1, "a": [Decimal128("Infinity")]}],
        msg="$eq Decimal128('Infinity') matches Decimal128('Infinity')",
    ),
]


BSON_TYPE_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="false_does_not_match_zero",
        filter={"a": {"$elemMatch": {"$eq": False}}},
        doc=[{"_id": 1, "a": [0]}, {"_id": 2, "a": [False]}],
        expected=[{"_id": 2, "a": [False]}],
        msg="false does NOT match 0",
    ),
    QueryTestCase(
        id="zero_does_not_match_false",
        filter={"a": {"$elemMatch": {"$eq": 0}}},
        doc=[{"_id": 1, "a": [False]}, {"_id": 2, "a": [0]}],
        expected=[{"_id": 2, "a": [0]}],
        msg="0 does NOT match false",
    ),
    QueryTestCase(
        id="true_does_not_match_one",
        filter={"a": {"$elemMatch": {"$eq": True}}},
        doc=[{"_id": 1, "a": [1]}, {"_id": 2, "a": [True]}],
        expected=[{"_id": 2, "a": [True]}],
        msg="true does NOT match 1",
    ),
    QueryTestCase(
        id="empty_string_does_not_match_null",
        filter={"a": {"$elemMatch": {"$eq": ""}}},
        doc=[{"_id": 1, "a": [None]}, {"_id": 2, "a": [""]}],
        expected=[{"_id": 2, "a": [""]}],
        msg="Empty string does NOT match null",
    ),
]

FIELD_LOOKUP_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_field",
        filter={"a.b": {"$elemMatch": {"$gt": 1}}},
        doc=[
            {"_id": 1, "a": {"b": [1, 5]}},
            {"_id": 2, "a": {"b": [0, 1]}},
        ],
        expected=[{"_id": 1, "a": {"b": [1, 5]}}],
        msg="$elemMatch on nested field a.b",
    ),
    QueryTestCase(
        id="deeply_nested_field",
        filter={"a.b.c": {"$elemMatch": {"$gt": 1}}},
        doc=[
            {"_id": 1, "a": {"b": {"c": [1, 5]}}},
            {"_id": 2, "a": {"b": {"c": [0, 1]}}},
        ],
        expected=[{"_id": 1, "a": {"b": {"c": [1, 5]}}}],
        msg="$elemMatch on deeply nested field a.b.c",
    ),
    QueryTestCase(
        id="dotted_path_with_in",
        filter={"a.b": {"$elemMatch": {"$in": [1, 2]}}},
        doc=[
            {"_id": 1, "a": {"b": [1, 3]}},
            {"_id": 2, "a": {"b": [4, 5]}},
        ],
        expected=[{"_id": 1, "a": {"b": [1, 3]}}],
        msg="$elemMatch with $in on dotted path",
    ),
    QueryTestCase(
        id="numeric_path_component",
        filter={"a.0.b": {"$elemMatch": {"$gt": 0}}},
        doc=[
            {"_id": 1, "a": [{"b": [1, 2]}]},
            {"_id": 2, "a": [{"b": [-1, 0]}]},
        ],
        expected=[{"_id": 1, "a": [{"b": [1, 2]}]}],
        msg="$elemMatch on numeric dotted path a.0.b",
    ),
    QueryTestCase(
        id="in_containing_nested_array",
        filter={"a.b": {"$elemMatch": {"$in": [[1, 2], [3, 4]]}}},
        doc=[
            {"_id": 1, "a": {"b": [[1, 2], [5, 6]]}},
            {"_id": 2, "a": {"b": [[7, 8]]}},
        ],
        expected=[{"_id": 1, "a": {"b": [[1, 2], [5, 6]]}}],
        msg="$elemMatch with $in containing nested array values",
    ),
]

ALL_SPECIAL_VALUE_TESTS = (
    NULL_AND_MISSING_TESTS
    + NUMERIC_EQUIVALENCE_TESTS
    + BSON_TYPE_DISTINCTION_TESTS
    + FIELD_LOOKUP_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_SPECIAL_VALUE_TESTS))
def test_elemMatch_special_values(collection, test):
    """Test $elemMatch special value handling and combinations."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)


NAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="eq_nan",
        filter={"a": {"$elemMatch": {"$eq": FLOAT_NAN}}},
        doc=[
            {"_id": 1, "a": [FLOAT_NAN]},
            {"_id": 2, "a": [1]},
        ],
        expected=[{"_id": 1, "a": [FLOAT_NAN]}],
        msg="$eq NaN matches NaN",
    ),
    QueryTestCase(
        id="eq_decimal128_nan",
        filter={"a": {"$elemMatch": {"$eq": Decimal128("NaN")}}},
        doc=[
            {"_id": 1, "a": [Decimal128("NaN")]},
            {"_id": 2, "a": [1]},
        ],
        expected=[{"_id": 1, "a": [Decimal128("NaN")]}],
        msg="$eq Decimal128('NaN') matches Decimal128('NaN')",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAN_TESTS))
def test_elemMatch_nan_equivalence(collection, test):
    """Test NaN matching within $elemMatch."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
    )
    assertSuccessNaN(result, test.expected)
