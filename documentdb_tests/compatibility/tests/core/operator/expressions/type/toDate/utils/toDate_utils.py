"""Shared test case class and helpers for $toDate tests."""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    convert_expr,
    convert_field_expr,
)
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ToDateTest(BaseTestCase):
    """Test case for $toDate operator."""

    value: Any = None


_EXPR_FORMS = [
    pytest.param(lambda test: {"$toDate": test.value}, id="toDate"),
    convert_expr("date"),
]

_DOC_EXPR_FORMS = [
    pytest.param(lambda field: {"$toDate": field}, id="toDate"),
    convert_field_expr("date"),
]
