"""$toDate expression tests: field references, nested paths, expression input,
and composite array path."""

from datetime import datetime

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    oid_from_args,
    ts_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import INVALID_DATE_STRING_ERROR
from documentdb_tests.framework.test_constants import DATE_EPOCH

_oid_2024_06_15 = oid_from_args(2024, 6, 15, 12, 0, 0)
_ts_2024_06_15 = ts_from_args(2024, 6, 15, 12, 0, 0)


TODATE_FIELD_REF_TESTS = [
    ("field_ref", "$v", {"v": Int64(86400000)}, datetime(1970, 1, 2, 0, 0, 0)),
    ("nested_field", "$doc.v", {"doc": {"v": "2024-06-15"}}, datetime(2024, 6, 15, 0, 0, 0)),
    ("missing_nested", "$doc.missing", {"doc": {"x": 1}}, None),
    ("oid_field", "$v", {"v": _oid_2024_06_15}, datetime(2024, 6, 15, 12, 0, 0)),
    ("ts_field", "$v", {"v": _ts_2024_06_15}, datetime(2024, 6, 15, 12, 0, 0)),
    ("string_field", "$v", {"v": "2024-01-01"}, datetime(2024, 1, 1, 0, 0, 0)),
    ("long_field", "$v", {"v": Int64(0)}, DATE_EPOCH),
    ("double_field", "$v", {"v": 86400000.0}, datetime(1970, 1, 2, 0, 0, 0)),
]


@pytest.mark.parametrize(
    "name,expr,doc,expected", TODATE_FIELD_REF_TESTS, ids=[t[0] for t in TODATE_FIELD_REF_TESTS]
)
def test_toDate_field_ref(collection, name, expr, doc, expected):
    """Test $toDate with field references."""
    result = execute_expression_with_insert(collection, {"$toDate": expr}, doc)
    assert_expression_result(result, expected=expected)


def test_toDate_nested_field_path(collection):
    """Test $toDate with nested field path"""
    result = execute_expression_with_insert(
        collection,
        {"$toDate": "$a.b"},
        {"a": {"b": "2024-06-15"}},
    )
    assert_expression_result(result, expected=datetime(2024, 6, 15, 0, 0, 0))


def test_toDate_expression_as_input(collection):
    """Test $toDate with expression operator as input"""
    result = execute_expression(
        collection,
        {"$toDate": {"$concat": ["2024", "-06-15"]}},
    )
    assert_expression_result(result, expected=datetime(2024, 6, 15, 0, 0, 0))


def test_toDate_composite_array_path(collection):
    """Test $toDate with composite array field path errors"""
    result = execute_expression_with_insert(
        collection,
        {"$toDate": "$a.b"},
        {"a": [{"b": "2024-06-15"}, {"b": "2024-07-01"}]},
    )
    assert_expression_result(result, error_code=INVALID_DATE_STRING_ERROR)


def test_toDate_return_type(collection):
    """$toDate should return date type"""
    result = execute_expression(
        collection,
        {"$type": {"$toDate": "2024-06-15"}},
    )
    assert_expression_result(result, expected="date")
