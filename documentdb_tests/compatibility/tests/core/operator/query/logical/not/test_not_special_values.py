"""
Tests for $not query operator with special values and edge cases.

Covers $not with NaN, Infinity, -Infinity, negative zero, deeply nested
field paths, empty collections, null values, missing fields, $exists
interactions, and $eq null semantics.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SPECIAL_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_eq_nan",
        filter={"val": {"$not": {"$eq": float("nan")}}},
        doc=[{"_id": 1, "val": float("nan")}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $eq:NaN should NOT return NaN doc (NaN == NaN in matching)",
    ),
    QueryTestCase(
        id="not_gt_infinity",
        filter={"val": {"$not": {"$gt": 999999}}},
        doc=[{"_id": 1, "val": float("inf")}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $gt:999999 should NOT return Infinity doc",
    ),
    QueryTestCase(
        id="not_lt_neg_infinity",
        filter={"val": {"$not": {"$lt": -999999}}},
        doc=[{"_id": 1, "val": float("-inf")}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $lt:-999999 should NOT return -Infinity doc",
    ),
    QueryTestCase(
        id="not_on_empty_collection",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=[{"_id": 1, "placeholder": True}],
        expected=[{"_id": 1, "placeholder": True}],
        msg="$not on doc without the field should return it",
    ),
    QueryTestCase(
        id="not_deeply_nested_path",
        filter={"a.b.c.d": {"$not": {"$eq": 1}}},
        doc=[
            {"_id": 1, "a": {"b": {"c": {"d": 1}}}},
            {"_id": 2, "a": {"b": {"c": {"d": 2}}}},
            {"_id": 3, "a": {"b": {"c": {}}}},
        ],
        expected=[
            {"_id": 2, "a": {"b": {"c": {"d": 2}}}},
            {"_id": 3, "a": {"b": {"c": {}}}},
        ],
        msg="$not on deeply nested field path should work correctly",
    ),
    QueryTestCase(
        id="not_on_id_field",
        filter={"_id": {"$not": {"$gt": 2}}},
        doc=[{"_id": 1, "val": "a"}, {"_id": 2, "val": "b"}, {"_id": 3, "val": "c"}],
        expected=[{"_id": 1, "val": "a"}, {"_id": 2, "val": "b"}],
        msg="$not should work on _id field",
    ),
    QueryTestCase(
        id="not_with_dotted_path",
        filter={"a.b": {"$not": {"$eq": 1}}},
        doc=[
            {"_id": 1, "a": {"b": 1}},
            {"_id": 2, "a": {"b": 2}},
            {"_id": 3, "a": {"c": 1}},
        ],
        expected=[{"_id": 2, "a": {"b": 2}}, {"_id": 3, "a": {"c": 1}}],
        msg="$not on dotted path should include docs where nested field is missing",
    ),
    QueryTestCase(
        id="not_eq_on_nested_dotted_path",
        filter={"a.b.c": {"$not": {"$eq": "value"}}},
        doc=[
            {"_id": 1, "a": {"b": {"c": "value"}}},
            {"_id": 2, "a": {"b": {"c": "other"}}},
            {"_id": 3, "a": {"b": {}}},
        ],
        expected=[
            {"_id": 2, "a": {"b": {"c": "other"}}},
            {"_id": 3, "a": {"b": {}}},
        ],
        msg="$not $eq on nested dotted path should exclude matching and include missing",
    ),
    QueryTestCase(
        id="not_eq_negative_zero",
        filter={"val": {"$not": {"$eq": 0}}},
        doc=[{"_id": 1, "val": -0.0}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $eq:0 on -0.0 — negative zero equals zero in matching so excluded",
    ),
    QueryTestCase(
        id="not_with_decimal128_nan",
        filter={"val": {"$not": {"$eq": Decimal128("NaN")}}},
        doc=[{"_id": 1, "val": Decimal128("NaN")}, {"_id": 2, "val": Decimal128("5")}],
        expected=[{"_id": 2, "val": Decimal128("5")}],
        msg="$not $eq:Decimal128 NaN should exclude Decimal128 NaN docs (NaN==NaN in matching)",
    ),
    QueryTestCase(
        id="not_with_decimal128_infinity",
        filter={"val": {"$not": {"$gt": Decimal128("999999")}}},
        doc=[{"_id": 1, "val": Decimal128("Infinity")}, {"_id": 2, "val": Decimal128("5")}],
        expected=[{"_id": 2, "val": Decimal128("5")}],
        msg="$not $gt on Decimal128 Infinity should exclude it",
    ),
    QueryTestCase(
        id="not_with_decimal128_negative_zero",
        filter={"val": {"$not": {"$eq": Decimal128("0")}}},
        doc=[{"_id": 1, "val": Decimal128("-0")}, {"_id": 2, "val": Decimal128("5")}],
        expected=[{"_id": 2, "val": Decimal128("5")}],
        msg="$not $eq:0 on Decimal128 -0 — negative zero equals zero in matching so excluded",
    ),
    QueryTestCase(
        id="empty_collection",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=[],
        expected=[],
        msg="$not on empty collection should return empty result",
    ),
]

DOCS_WITH_NULL_AND_MISSING: list[dict] = [
    {"_id": 1, "val": 5},
    {"_id": 2, "val": None},
    {"_id": 3, "other": 10},
]

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_gt_includes_null",
        filter={"val": {"$not": {"$gt": 5}}},
        doc=[{"_id": 1, "val": 10}, {"_id": 2, "val": None}],
        expected=[{"_id": 2, "val": None}],
        msg="$not $gt:5 should include null doc (null is not > 5)",
    ),
    QueryTestCase(
        id="not_gt_includes_missing",
        filter={"val": {"$not": {"$gt": 5}}},
        doc=[{"_id": 1, "val": 10}, {"_id": 2, "other": 1}],
        expected=[{"_id": 2, "other": 1}],
        msg="$not $gt should include docs where field is missing",
    ),
    QueryTestCase(
        id="not_exists_true",
        filter={"val": {"$not": {"$exists": True}}},
        doc=DOCS_WITH_NULL_AND_MISSING,
        expected=[{"_id": 3, "other": 10}],
        msg="$not $exists:true should return docs where field does NOT exist",
    ),
    QueryTestCase(
        id="not_exists_false",
        filter={"val": {"$not": {"$exists": False}}},
        doc=DOCS_WITH_NULL_AND_MISSING,
        expected=[{"_id": 1, "val": 5}, {"_id": 2, "val": None}],
        msg="$not $exists:false should return docs where field DOES exist",
    ),
    QueryTestCase(
        id="not_eq_null_excludes_null_and_missing",
        filter={"val": {"$not": {"$eq": None}}},
        doc=DOCS_WITH_NULL_AND_MISSING,
        expected=[{"_id": 1, "val": 5}],
        msg="$not $eq:null should exclude both null and missing field docs",
    ),
    QueryTestCase(
        id="not_ne_null_returns_null_and_missing",
        filter={"val": {"$not": {"$ne": None}}},
        doc=DOCS_WITH_NULL_AND_MISSING,
        expected=[{"_id": 2, "val": None}, {"_id": 3, "other": 10}],
        msg="$not $ne:null should return docs where val IS null or field is missing",
    ),
    QueryTestCase(
        id="not_type_null",
        filter={"val": {"$not": {"$type": "null"}}},
        doc=DOCS_WITH_NULL_AND_MISSING,
        expected=[{"_id": 1, "val": 5}, {"_id": 3, "other": 10}],
        msg="$not $type:null should return non-null docs (includes missing)",
    ),
    QueryTestCase(
        id="exists_true_equivalent_to_not_exists_false",
        filter={"val": {"$exists": True}},
        doc=DOCS_WITH_NULL_AND_MISSING,
        expected=[{"_id": 1, "val": 5}, {"_id": 2, "val": None}],
        msg="$exists:true should be equivalent to $not $exists:false",
    ),
    QueryTestCase(
        id="exists_false_equivalent_to_not_exists_true",
        filter={"val": {"$exists": False}},
        doc=DOCS_WITH_NULL_AND_MISSING,
        expected=[{"_id": 3, "other": 10}],
        msg="$exists:false should be equivalent to $not $exists:true",
    ),
]

ALL_TESTS = SPECIAL_VALUE_TESTS + NULL_MISSING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_special_values(collection, test):
    """Test $not query operator with special values and edge cases."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
