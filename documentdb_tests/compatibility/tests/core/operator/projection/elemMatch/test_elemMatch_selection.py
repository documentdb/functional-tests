"""
Tests element selection behavior for the $elemMatch projection operator.
"""

from __future__ import annotations

from functools import reduce
from typing import Any

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DECIMAL128_HALF,
    OID_EPOCH,
    TS_EPOCH,
)

# Property [Missing or Empty Field]: when the projected field is missing or is an
# empty array, the field is omitted from the result.
ELEMMATCH_MISSING_OR_EMPTY_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "null_field_missing",
        doc=[{"_id": 1, "other": "value"}],
        projection={"arr": {"$elemMatch": {"$gte": 1}}},
        expected=[{"_id": 1}],
        msg="$elemMatch should omit the field when it is missing from the document",
    ),
    ProjectionTestCase(
        "null_field_empty_array",
        doc=[{"_id": 1, "arr": []}],
        projection={"arr": {"$elemMatch": {"$gte": 1}}},
        expected=[{"_id": 1}],
        msg="$elemMatch should omit the field when it is an empty array",
    ),
]

# Property [Non-Array Field Type]: when the projected field is a non-array BSON type,
# the field is omitted from the result, even when the value would satisfy the condition.
ELEMMATCH_NON_ARRAY_TYPE_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        f"null_field_type_{tid}",
        doc=[{"_id": 1, "arr": val}],
        projection={"arr": {"$elemMatch": {"$gte": 1}}},
        expected=[{"_id": 1}],
        msg=f"$elemMatch should omit the field when it is a {tid} (non-array) value",
    )
    for tid, val in [
        ("null", None),
        ("bool", True),
        ("int32", 42),
        ("int64", Int64(99)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_HALF),
        ("string", "hello"),
        ("object", {"x": 1}),
        ("objectid", OID_EPOCH),
        ("datetime", DATE_EPOCH),
        ("timestamp", TS_EPOCH),
        ("binary", Binary(b"\x00\x01\x02")),
        ("regex", Regex("^abc", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Core Matching - First Match]: $elemMatch returns only the first element
# that matches the condition, wrapped in a single-element array.
ELEMMATCH_FIRST_MATCH_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "core_single_match_wrapped_in_array",
        doc=[{"_id": 1, "scores": [70, 80, 85, 90, 95]}],
        projection={"scores": {"$elemMatch": {"$eq": 85}}},
        expected=[{"_id": 1, "scores": [85]}],
        msg="$elemMatch should return the single matching element wrapped in an array",
    ),
    ProjectionTestCase(
        "core_multiple_matches_returns_first",
        doc=[
            {
                "_id": 1,
                "items": [
                    {"x": 1, "y": "a"},
                    {"x": 2, "y": "b"},
                    {"x": 3, "y": "c"},
                ],
            }
        ],
        projection={"items": {"$elemMatch": {"x": {"$gte": 2}}}},
        expected=[{"_id": 1, "items": [{"x": 2, "y": "b"}]}],
        msg="$elemMatch should return only the first matching element when multiple match",
    ),
    ProjectionTestCase(
        "core_preserves_nested_fields",
        doc=[
            {
                "_id": 1,
                "items": [
                    {"name": "a", "qty": 5, "price": 1.0, "tags": ["x", "y"]},
                    {"name": "b", "qty": 15, "price": 2.5, "tags": ["z"]},
                ],
            }
        ],
        projection={"items": {"$elemMatch": {"qty": {"$gt": 10}}}},
        expected=[{"_id": 1, "items": [{"name": "b", "qty": 15, "price": 2.5, "tags": ["z"]}]}],
        msg="$elemMatch should preserve all nested fields of the matched element",
    ),
    ProjectionTestCase(
        "core_deep_nesting_preserved",
        doc=[
            {
                "_id": 1,
                "nested": [
                    reduce(
                        lambda inner, lvl: {"level": lvl, "child": inner},
                        range(9, 0, -1),
                        dict[str, Any](level=10),
                    ),
                    {"level": 0},
                ],
            }
        ],
        projection={"nested": {"$elemMatch": {"level": 1}}},
        expected=[
            {
                "_id": 1,
                "nested": [
                    reduce(
                        lambda inner, lvl: {"level": lvl, "child": inner},
                        range(9, 0, -1),
                        dict[str, Any](level=10),
                    ),
                ],
            }
        ],
        msg="$elemMatch should preserve the full matched element including deeply nested structure",
    ),
    ProjectionTestCase(
        "core_large_array_match_at_end",
        doc=[{"_id": 1, "arr": list(range(10_000)) + [99_999]}],
        projection={"arr": {"$elemMatch": {"$eq": 99_999}}},
        expected=[{"_id": 1, "arr": [99_999]}],
        msg="$elemMatch should find a match at any index position including in large arrays",
    ),
]

# Property [No-Match Behavior]: when no element in the array matches the condition,
# the field is omitted from the result document entirely.
ELEMMATCH_NO_MATCH_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "no_match_field_omitted",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={"arr": {"$elemMatch": {"$gte": 100}}},
        expected=[{"_id": 1}],
        msg="$elemMatch should omit the field when no element matches the condition",
    ),
    ProjectionTestCase(
        "no_match_id_field_empty_doc",
        doc=[{"_id": 1, "x": "hello"}],
        projection={"_id": {"$elemMatch": {"$gte": 1}}},
        expected=[{}],
        msg="$elemMatch on _id field should produce empty document as only projection",
    ),
]

SELECTION_TESTS = (
    ELEMMATCH_MISSING_OR_EMPTY_TESTS
    + ELEMMATCH_NON_ARRAY_TYPE_TESTS
    + ELEMMATCH_FIRST_MATCH_TESTS
    + ELEMMATCH_NO_MATCH_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SELECTION_TESTS))
def test_elemmatch_selection(collection, test):
    """Test $elemMatch projection element selection cases."""
    collection.insert_many(test.doc)
    cmd = {
        "find": collection.name,
        "projection": test.projection,
    }
    if test.filter is not None:
        cmd["filter"] = test.filter
    result = execute_command(collection, cmd)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
