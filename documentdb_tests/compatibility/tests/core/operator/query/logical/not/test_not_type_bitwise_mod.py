"""
Tests for $not query operator with $type and $mod.

Covers $not combined with $type (single and multiple types)
and $mod on non-numeric fields.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_type_string",
        filter={"val": {"$not": {"$type": "string"}}},
        doc=[{"_id": 1, "val": "hello"}, {"_id": 2, "val": 42}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": 42}, {"_id": 3, "other": 1}],
        msg="$not $type:string should return non-string and missing field docs",
    ),
    QueryTestCase(
        id="not_type_number",
        filter={"val": {"$not": {"$type": "number"}}},
        doc=[{"_id": 1, "val": 42}, {"_id": 2, "val": "hello"}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "val": "hello"}, {"_id": 3, "other": 1}],
        msg="$not $type:number should return non-number and missing field docs",
    ),
    QueryTestCase(
        id="not_type_multiple",
        filter={"val": {"$not": {"$type": ["string", "int"]}}},
        doc=[{"_id": 1, "val": "hello"}, {"_id": 2, "val": 42}, {"_id": 3, "val": 3.14}],
        expected=[{"_id": 3, "val": 3.14}],
        msg="$not $type with multiple types should return docs matching neither type",
    ),
]

MOD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_mod_non_numeric_field",
        filter={"val": {"$not": {"$mod": [2, 0]}}},
        doc=[{"_id": 1, "val": "hello"}, {"_id": 2, "val": 4}],
        expected=[{"_id": 1, "val": "hello"}],
        msg="$not $mod on non-numeric field should return doc (doesn't match $mod)",
    ),
]

ALL_TESTS = TYPE_TESTS + MOD_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_type_bitwise_mod(collection, test):
    """Test $not query operator with $type, $mod, and bitwise operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
