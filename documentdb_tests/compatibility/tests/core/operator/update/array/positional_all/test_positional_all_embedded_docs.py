"""Tests for $[] positional-all with embedded documents, dot notation, and nested arrays.

Covers: updating fields in all embedded documents, dot notation paths,
nested arrays, and nested $[] usage.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EMBEDDED_DOC_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "set_field_in_all_docs",
        setup_docs=[{"_id": 1, "arr": [{"val": 1}, {"val": 2}, {"val": 3}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[].val": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update field in all embedded documents",
    ),
    UpdateTestCase(
        "inc_field_in_all_docs",
        setup_docs=[{"_id": 1, "arr": [{"val": 10}, {"val": 20}]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[].val": 5}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $inc should increment field in all embedded documents",
    ),
    UpdateTestCase(
        "unset_field_in_all_docs",
        setup_docs=[{"_id": 1, "arr": [{"val": 1, "x": "a"}, {"val": 2, "x": "b"}]}],
        query={"_id": 1},
        update={"$unset": {"arr.$[].x": ""}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $unset should remove field from all embedded documents",
    ),
    UpdateTestCase(
        "deeply_nested_field",
        setup_docs=[{"_id": 1, "arr": [{"nested": {"field": 1}}, {"nested": {"field": 2}}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[].nested.field": 99}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] updating deeply nested field should work",
    ),
    UpdateTestCase(
        "nested_array_dot_notation",
        setup_docs=[{"_id": 1, "outer": {"arr": [1, 2, 3]}}],
        query={"_id": 1},
        update={"$set": {"outer.arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] on nested array field using dot notation should succeed",
    ),
    UpdateTestCase(
        "nested_dollar_bracket_usage",
        setup_docs=[{"_id": 1, "arr": [{"sub": [1, 2]}, {"sub": [3, 4]}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[].sub.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="Nested $[] should update all elements in all subarrays",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EMBEDDED_DOC_TESTS))
def test_positional_all_embedded_docs(collection, test: UpdateTestCase):
    """Test $[] positional-all with embedded documents and dot notation."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
