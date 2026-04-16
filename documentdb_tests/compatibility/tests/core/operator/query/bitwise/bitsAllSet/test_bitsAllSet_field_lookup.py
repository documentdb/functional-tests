"""
Tests for $bitsAllSet field lookup patterns, cross-type combinations, and algebraic properties.

Validates simple/nested/array field paths, deeply nested paths through arrays of objects,
cross-type field/bitmask combinations (numeric field with BinData bitmask and vice versa),
position list order invariance, and three-form equivalence (numeric, position list, BinData).
"""

import pytest
from bson import Binary

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

FIELD_LOOKUP_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="simple_field_path",
        filter={"a": {"$bitsAllSet": [0, 1]}},
        doc=[{"_id": 1, "a": 3}, {"_id": 2, "a": 2}],
        expected=[{"_id": 1, "a": 3}],
        msg="Simple field path matches when bits 0,1 are set in 3 (binary 11)",
    ),
    QueryTestCase(
        id="nested_field_dot_notation",
        filter={"a.b": {"$bitsAllSet": [0, 1]}},
        doc=[{"_id": 1, "a": {"b": 3}}, {"_id": 2, "a": {"b": 2}}],
        expected=[{"_id": 1, "a": {"b": 3}}],
        msg="Nested field path with dot notation",
    ),
    QueryTestCase(
        id="array_field_any_element_match",
        filter={"a": {"$bitsAllSet": [0, 1]}},
        doc=[{"_id": 1, "a": [3, 20]}, {"_id": 2, "a": [4, 8]}],
        expected=[{"_id": 1, "a": [3, 20]}],
        msg="Array field matches if any element satisfies (3 has bits 0,1 set)",
    ),
    QueryTestCase(
        id="array_index_path",
        filter={"a.0": {"$bitsAllSet": [0, 1]}},
        doc=[{"_id": 1, "a": [3, 20]}, {"_id": 2, "a": [2, 3]}],
        expected=[{"_id": 1, "a": [3, 20]}],
        msg="Array index path checks element at index 0",
    ),
    QueryTestCase(
        id="deep_nested_path_through_array_of_objects",
        filter={"a.b.c.d": {"$bitsAllSet": [0, 1]}},
        doc=[
            {"_id": 1, "a": {"b": [{"c": {"d": 3}}, {"c": {"d": 2}}]}},
            {"_id": 2, "a": {"b": [{"c": {"d": 4}}, {"c": {"d": 8}}]}},
        ],
        expected=[{"_id": 1, "a": {"b": [{"c": {"d": 3}}, {"c": {"d": 2}}]}}],
        msg="Deep nested path traverses array of objects at intermediate level",
    ),
]

CROSS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="numeric_field_with_bindata_bitmask",
        filter={"a": {"$bitsAllSet": Binary(b"\x01")}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": 1}],
        msg="Numeric field with BinData bitmask checking bit 0",
    ),
    QueryTestCase(
        id="bindata_field_with_position_list",
        filter={"a": {"$bitsAllSet": [0]}},
        doc=[{"_id": 1, "a": Binary(b"\x01", 128)}, {"_id": 2, "a": Binary(b"\x06", 128)}],
        expected=[{"_id": 1, "a": Binary(b"\x01", 128)}],
        msg="BinData field with position list bitmask",
    ),
    QueryTestCase(
        id="bindata_field_with_longer_bindata_bitmask",
        filter={"a": {"$bitsAllSet": Binary(b"\x01\x00\x00")}},
        doc=[{"_id": 1, "a": Binary(b"\x01", 128)}, {"_id": 2, "a": Binary(b"\x06", 128)}],
        expected=[{"_id": 1, "a": Binary(b"\x01", 128)}],
        msg="BinData field with BinData bitmask of different length",
    ),
]

ALGEBRAIC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="position_order_invariance_asc",
        filter={"a": {"$bitsAllSet": [0, 1, 5]}},
        doc=[{"_id": 1, "a": 35}, {"_id": 2, "a": 3}, {"_id": 3, "a": 255}],
        expected=[{"_id": 1, "a": 35}, {"_id": 3, "a": 255}],
        msg="Position list [0,1,5] ascending order",
    ),
    QueryTestCase(
        id="position_order_invariance_desc",
        filter={"a": {"$bitsAllSet": [5, 1, 0]}},
        doc=[{"_id": 1, "a": 35}, {"_id": 2, "a": 3}, {"_id": 3, "a": 255}],
        expected=[{"_id": 1, "a": 35}, {"_id": 3, "a": 255}],
        msg="Position list [5,1,0] descending order produces same result",
    ),
    QueryTestCase(
        id="three_form_equivalence_bindata",
        filter={"a": {"$bitsAllSet": Binary(b"\x23")}},
        doc=[{"_id": 1, "a": 35}, {"_id": 2, "a": 3}, {"_id": 3, "a": 255}],
        expected=[{"_id": 1, "a": 35}, {"_id": 3, "a": 255}],
        msg="BinData 0x23 (bits 0,1,5) equivalent to numeric 35 and position list [0,1,5]",
    ),
]

ALL_TESTS = FIELD_LOOKUP_TESTS + CROSS_TYPE_TESTS + ALGEBRAIC_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_bitsAllSet_field_lookup(collection, test):
    """Test $bitsAllSet field lookup, cross-type combinations, and algebraic properties."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
