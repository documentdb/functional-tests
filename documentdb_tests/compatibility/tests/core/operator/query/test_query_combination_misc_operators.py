"""
Tests for $mod query operator combinations.

Covers $mod combined with logical operators ($not, $and, $or, $nor),
comparison operators ($gt), and array operators ($elemMatch).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": i, "a": i} for i in range(1, 13)]

MOD_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_mod_4_0",
        filter={"a": {"$not": {"$mod": [4, 0]}}},
        doc=DOCS,
        expected=[d for d in DOCS if d["a"] % 4 != 0],
        msg="$not $mod [4,0] should match docs where field % 4 != 0",
    ),
    QueryTestCase(
        id="not_mod_missing_field",
        filter={"a": {"$not": {"$mod": [4, 0]}}},
        doc=[{"_id": 1, "b": 4}],
        expected=[{"_id": 1, "b": 4}],
        msg="$not $mod on missing field should match",
    ),
    QueryTestCase(
        id="mod_with_gt",
        filter={"a": {"$mod": [2, 0], "$gt": 5}},
        doc=DOCS,
        expected=[d for d in DOCS if d["a"] % 2 == 0 and d["a"] > 5],
        msg="$mod [2,0] with $gt 5 should match even numbers > 5",
    ),
    QueryTestCase(
        id="and_mod_2_mod_3",
        filter={"$and": [{"a": {"$mod": [2, 0]}}, {"a": {"$mod": [3, 0]}}]},
        doc=DOCS,
        expected=[d for d in DOCS if d["a"] % 2 == 0 and d["a"] % 3 == 0],
        msg="$and with $mod [2,0] and $mod [3,0] should match divisible by both",
    ),
    QueryTestCase(
        id="or_mod_2_mod_3",
        filter={"$or": [{"a": {"$mod": [2, 0]}}, {"a": {"$mod": [3, 0]}}]},
        doc=DOCS,
        expected=[d for d in DOCS if d["a"] % 2 == 0 or d["a"] % 3 == 0],
        msg="$or with $mod [2,0] and $mod [3,0] should match divisible by 2 or 3",
    ),
    QueryTestCase(
        id="nor_mod_2",
        filter={"$nor": [{"a": {"$mod": [2, 0]}}]},
        doc=DOCS,
        expected=[d for d in DOCS if d["a"] % 2 != 0],
        msg="$nor with $mod [2,0] should match odd numbers",
    ),
    QueryTestCase(
        id="elemmatch_mod_3_0",
        filter={"a": {"$elemMatch": {"$mod": [3, 0]}}},
        doc=[{"_id": 1, "a": [1, 3, 5]}],
        expected=[{"_id": 1, "a": [1, 3, 5]}],
        msg="$elemMatch with $mod should match if any element satisfies",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_COMBINATION_TESTS))
def test_query_combination_misc_mod(collection, test):
    """Parametrized test for $mod operator combinations."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
