"""Shared test case class and helpers for $allElementsTrue tests."""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase

_OMIT = object()


@dataclass(frozen=True)
class AllElementsTrueTest(BaseTestCase):
    """Test case for $allElementsTrue operator.

    Fields:
        array: The array to evaluate. Used for both literal and field-ref tests.
        document: Document to insert for field-ref tests. If provided, array is ignored
                  and the expression uses "$arr" field reference.
        expression: Raw expression override. If provided, used as-is.
    """

    array: Any = _OMIT
    document: Any = _OMIT
    expression: Any = _OMIT


def build_expr(test: AllElementsTrueTest):
    """Build $allElementsTrue expression with literal array value."""
    if test.expression is not _OMIT:
        return test.expression
    return {"$allElementsTrue": [test.array]}


def build_expr_with_field_ref(test: AllElementsTrueTest):
    """Build $allElementsTrue expression with $arr field reference."""
    return {"$allElementsTrue": ["$arr"]}


def build_insert_doc(test: AllElementsTrueTest):
    """Build document for insert tests."""
    if test.document is not _OMIT:
        return test.document
    return {"arr": test.array}
