"""Tests for $[<identifier>] with embedded documents, dot notation, and nested arrays.

Covers: filtering on embedded document fields, updating fields in matched docs,
nested arrays with multiple identifiers, and dot notation paths.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.array.positional_filtered.utils.filtered_update_test_case import (  # noqa: E501
    FilteredUpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EMBEDDED_DOC_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "filter_on_embedded_field",
        setup_docs=[{"_id": 1, "arr": [{"grade": 80}, {"grade": 90}, {"grade": 70}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem].grade": 100}},
        array_filters=[{"elem.grade": {"$gte": 85}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with arrayFilters on embedded doc field should work",
    ),
    FilteredUpdateTestCase(
        "filter_multiple_fields",
        setup_docs=[
            {"_id": 1, "arr": [{"x": 1, "y": "a"}, {"x": 2, "y": "b"}, {"x": 3, "y": "a"}]}
        ],
        query={"_id": 1},
        update={"$set": {"arr.$[elem].x": 99}},
        array_filters=[{"elem.x": {"$gte": 2}, "elem.y": "a"}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with arrayFilters on multiple embedded doc fields should work",
    ),
    FilteredUpdateTestCase(
        "update_specific_field_in_matched",
        setup_docs=[{"_id": 1, "items": [{"name": "A", "qty": 5}, {"name": "B", "qty": 15}]}],
        query={"_id": 1},
        update={"$set": {"items.$[elem].qty": 0}},
        array_filters=[{"elem.qty": {"$gt": 10}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] updating specific field in matched embedded documents",
    ),
    FilteredUpdateTestCase(
        "deeply_nested_field",
        setup_docs=[{"_id": 1, "arr": [{"nested": {"val": 1}}, {"nested": {"val": 2}}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem].nested.val": 99}},
        array_filters=[{"elem.nested.val": {"$gte": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] on deeply nested field should work",
    ),
    FilteredUpdateTestCase(
        "unset_field_in_embedded_docs",
        setup_docs=[
            {"_id": 1, "arr": [{"x": 1, "y": "a"}, {"x": 2, "y": "b"}, {"x": 3, "y": "c"}]}
        ],
        query={"_id": 1},
        update={"$unset": {"arr.$[elem].y": ""}},
        array_filters=[{"elem.x": {"$gte": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $unset on embedded doc field should remove field from matching docs",
    ),
]


# --- Nested Arrays with Multiple Identifiers ---

NESTED_ARRAY_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "nested_with_all_bracket",
        setup_docs=[{"_id": 1, "arr": [{"sub": [1, 2, 3]}, {"sub": [4, 5, 6]}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem].sub.$[]": 0}},
        array_filters=[{"elem.sub": {"$size": 3}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] combined with $[] for nested arrays should work",
    ),
    FilteredUpdateTestCase(
        "multiple_identifiers_nested",
        setup_docs=[
            {
                "_id": 1,
                "grades": [
                    {"class": "math", "scores": [80, 90, 70]},
                    {"class": "eng", "scores": [60, 95, 85]},
                ],
            }
        ],
        query={"_id": 1},
        update={"$set": {"grades.$[t].scores.$[s]": 100}},
        array_filters=[{"t.class": "math"}, {"s": {"$gte": 85}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with multiple identifiers for nested arrays should work",
    ),
]


# --- Dot Notation ---

DOT_NOTATION_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "nested_array_dot_notation",
        setup_docs=[{"_id": 1, "outer": {"arr": [1, 2, 3, 4]}}],
        query={"_id": 1},
        update={"$set": {"outer.arr.$[elem]": 0}},
        array_filters=[{"elem": {"$gte": 3}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] on nested array field using dot notation should work",
    ),
]


ALL_TESTS = EMBEDDED_DOC_TESTS + NESTED_ARRAY_TESTS + DOT_NOTATION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_positional_filtered_embedded_docs(collection, test: FilteredUpdateTestCase):
    """Test $[<identifier>] with embedded documents and nested arrays."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update, "arrayFilters": test.array_filters}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
