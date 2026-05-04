"""$toDate expression tests: field references, nested paths, expression input,
and composite array path."""

from datetime import datetime, timezone

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
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.test_constants import DATE_EPOCH, INT64_ZERO

from .utils.toDate_utils import _DOC_EXPR_FORMS, _EXPR_FORMS, ToDateTest

_oid_2024_06_15 = oid_from_args(2024, 6, 15, 12, 0, 0)
_ts_2024_06_15 = ts_from_args(2024, 6, 15, 12, 0, 0)


# Property [Field References]: $toDate resolves field paths, nested paths,
# and various BSON types from documents.
TODATE_FIELD_REF_TESTS = [
    ("field_ref", "$v", {"v": Int64(86400000)}, datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc)),
    (
        "nested_field",
        "$doc.v",
        {"doc": {"v": "2024-06-15"}},
        datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ("missing_nested", "$doc.missing", {"doc": {"x": 1}}, None),
    (
        "oid_field",
        "$v",
        {"v": _oid_2024_06_15},
        datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    ),
    ("ts_field", "$v", {"v": _ts_2024_06_15}, datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)),
    ("string_field", "$v", {"v": "2024-01-01"}, datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
    ("long_field", "$v", {"v": INT64_ZERO}, DATE_EPOCH),
    ("double_field", "$v", {"v": 86400000.0}, datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc)),
]


@pytest.mark.parametrize("expr_fn", _DOC_EXPR_FORMS)
@pytest.mark.parametrize(
    "name,expr,doc,expected", TODATE_FIELD_REF_TESTS, ids=[t[0] for t in TODATE_FIELD_REF_TESTS]
)
def test_toDate_field_ref(collection, name, expr, doc, expected, expr_fn):
    """Test $toDate with field references."""
    result = execute_expression_with_insert(collection, expr_fn(expr), doc)
    assert_expression_result(result, expected=expected)


@pytest.mark.parametrize("expr_fn", _DOC_EXPR_FORMS)
def test_toDate_nested_field_path(collection, expr_fn):
    """Test $toDate with nested field path"""
    result = execute_expression_with_insert(
        collection,
        expr_fn("$a.b"),
        {"a": {"b": "2024-06-15"}},
    )
    assert_expression_result(result, expected=datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc))


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDate_expression_as_input(collection, expr_fn):
    """Test $toDate with expression operator as input"""
    test = ToDateTest(
        "expr_concat",
        value={"$concat": ["2024", "-06-15"]},
        msg="$toDate should accept expression operator as input",
    )
    result = execute_expression(
        collection,
        expr_fn(test),
    )
    assert_expression_result(result, expected=datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc))


@pytest.mark.parametrize("expr_fn", _DOC_EXPR_FORMS)
def test_toDate_composite_array_path(collection, expr_fn):
    """Test $toDate with composite array field path errors"""
    result = execute_expression_with_insert(
        collection,
        expr_fn("$a.b"),
        {"a": [{"b": "2024-06-15"}, {"b": "2024-07-01"}]},
    )
    assert_expression_result(result, error_code=CONVERSION_FAILURE_ERROR)


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDate_return_type(collection, expr_fn):
    """$toDate should return date type"""
    test = ToDateTest("return_type", value="2024-06-15", msg="$toDate should return date type")
    result = execute_expression(
        collection,
        {"$type": expr_fn(test)},
    )
    assert_expression_result(result, expected="date")
