"""
$$CURRENT naming rules and error cases.

Covers a field literally named CURRENT, a document key spelled like the
variable token, and malformed variable references.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    LET_UNDEFINED_VARIABLE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Naming]: $$CURRENT is matched by exact case-sensitive name; a field literally
# named CURRENT is only reachable through $$CURRENT.CURRENT, and any other casing of the
# token is an ordinary, undefined user variable.
NAMING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="field_literally_named_current_is_accessible_through_current",
        expression={"whole": "$$CURRENT", "field": "$$CURRENT.CURRENT"},
        doc={"_id": 1, "CURRENT": {"inner": 1}},
        expected=[{"whole": {"_id": 1, "CURRENT": {"inner": 1}}, "field": {"inner": 1}}],
        msg="$$CURRENT should stay the document while $$CURRENT.CURRENT reads the field",
    ),
    ExpressionTestCase(
        id="lowercase_current_is_an_undefined_user_variable",
        expression={"v": "$$current"},
        doc={"_id": 1, "a": 1},
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$$current should be an undefined user variable",
    ),
    ExpressionTestCase(
        id="mixed_case_current_is_an_undefined_user_variable",
        expression={"v": "$$Current"},
        doc={"_id": 1, "a": 1},
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$$Current should be an undefined user variable",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAMING_TESTS))
def test_system_variables_current_naming(collection, test):
    """$$CURRENT naming rules and malformed variable references behave as documented."""
    result = execute_project_with_insert(collection, test.doc, test.expression)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
