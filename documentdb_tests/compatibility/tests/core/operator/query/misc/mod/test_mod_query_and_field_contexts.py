"""
Tests for $mod query operator in different field contexts.

Covers array field matching (element traversal, mixed types, empty/nested arrays),
nested field paths (dot notation, array indexes, composite paths), and operator
combinations ($elemMatch, $all, $size with $mod).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_element_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": [3, 6, 9]}],
        expected=[{"_id": 1, "a": [3, 6, 9]}],
        msg="$mod on array should match if any element satisfies condition",
    ),
    QueryTestCase(
        id="array_no_element_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": [1, 2, 5]}],
        expected=[],
        msg="$mod on array should not match if no element satisfies condition",
    ),
    QueryTestCase(
        id="array_mixed_types",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": [1, "a", 3]}],
        expected=[{"_id": 1, "a": [1, "a", 3]}],
        msg="$mod on mixed-type array should match if any numeric element satisfies",
    ),
    QueryTestCase(
        id="array_empty",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": []}],
        expected=[],
        msg="$mod on empty array should not match",
    ),
    QueryTestCase(
        id="array_nested",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        expected=[],
        msg="$mod on nested array should not match (nested arrays are not traversed)",
    ),
    QueryTestCase(
        id="array_with_zero_and_non_numeric",
        filter={"a": {"$mod": [5, 0]}},
        doc=[
            {"_id": 1, "a": [0, "str"]},
            {"_id": 2, "a": [10, None]},
            {"_id": 3, "a": [7]},
        ],
        expected=[
            {"_id": 1, "a": [0, "str"]},
            {"_id": 2, "a": [10, None]},
        ],
        msg="$mod on array should match docs where any numeric element satisfies",
    ),
]


NESTED_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="deeply_nested_a_b_c_d",
        filter={"a.b.c.d": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": {"b": {"c": {"d": 9}}}}],
        expected=[{"_id": 1, "a": {"b": {"c": {"d": 9}}}}],
        msg="$mod on deeply nested field a.b.c.d should match",
    ),
    QueryTestCase(
        id="array_index_dot_notation",
        filter={"a.0": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": [6, 7]}],
        expected=[{"_id": 1, "a": [6, 7]}],
        msg="$mod on array element via dot notation a.0 should match",
    ),
    QueryTestCase(
        id="composite_array_path",
        filter={"a.b": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": [{"b": 6}, {"b": 7}]}],
        expected=[{"_id": 1, "a": [{"b": 6}, {"b": 7}]}],
        msg="$mod on composite array path a.b should match if any element satisfies",
    ),
    QueryTestCase(
        id="composite_array_path_no_match",
        filter={"a.b": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        expected=[],
        msg="$mod on composite array path should not match if no element satisfies",
    ),
    QueryTestCase(
        id="deeply_nested_dotted_no_match",
        filter={"a.b.c": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": {"b": {"x": 9}}}],
        expected=[],
        msg="$mod on non-existent nested path should not match",
    ),
]

COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="elemMatch_with_mod",
        filter={"a": {"$elemMatch": {"$mod": [3, 0], "$gte": 6}}},
        doc=[
            {"_id": 1, "a": [3, 7]},
            {"_id": 2, "a": [6, 7]},
            {"_id": 3, "a": [1, 2]},
        ],
        expected=[{"_id": 2, "a": [6, 7]}],
        msg="$elemMatch with $mod should require same element to satisfy both conditions",
    ),
    QueryTestCase(
        id="all_with_mod",
        filter={"a": {"$all": [3], "$mod": [3, 0]}},
        doc=[
            {"_id": 1, "a": [3, 6]},
            {"_id": 2, "a": [6, 9]},
            {"_id": 3, "a": [3, 5]},
        ],
        expected=[{"_id": 1, "a": [3, 6]}, {"_id": 3, "a": [3, 5]}],
        msg="$all combined with $mod should require array contains 3 "
        "and has element divisible by 3",
    ),
    QueryTestCase(
        id="size_with_mod",
        filter={"a": {"$size": 2, "$mod": [3, 0]}},
        doc=[
            {"_id": 1, "a": [3, 5]},
            {"_id": 2, "a": [6]},
            {"_id": 3, "a": [1, 2]},
        ],
        expected=[{"_id": 1, "a": [3, 5]}],
        msg="$size combined with $mod should require array length 2 and element divisible by 3",
    ),
]

PARAMETRIZED_TESTS = ARRAY_TESTS + NESTED_TESTS + COMBINATION_TESTS


@pytest.mark.parametrize("test", pytest_params(PARAMETRIZED_TESTS))
def test_mod_query_and_field_contexts(collection, test):
    """Parametrized test for $mod in different field contexts."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
