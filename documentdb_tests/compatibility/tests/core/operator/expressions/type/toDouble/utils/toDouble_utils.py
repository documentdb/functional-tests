from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    convert_expr,
    convert_field_expr,
)
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ToDoubleTest(BaseTestCase):
    """Test case for $toDouble operator."""

    value: Any = None


_EXPR_FORMS = [
    pytest.param(lambda test: {"$toDouble": test.value}, id="toDouble"),
    convert_expr("double"),
]

_DOC_EXPR_FORMS = [
    pytest.param(lambda field: {"$toDouble": field}, id="toDouble"),
    convert_field_expr("double"),
]
