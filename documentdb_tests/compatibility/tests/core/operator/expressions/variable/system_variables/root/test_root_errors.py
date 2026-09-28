"""
Error and validation tests for the $$ROOT aggregation system variable.

Covers malformed variable references, invalid $$ROOT field paths, and the
reserved status of the ROOT name for user variables. Generic $let structural
validation lives in expressions/misc/let/test_let_invalid.py and
test_let_variable_names.py. Generic field-path validation errors are
represented by one case (`root_dollar_prefixed_subfield`); the rest are
deferred to a future generic field-path suite (Issue #118).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    LET_UNDEFINED_VARIABLE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOC = {"_id": 1, "a": {"b": 1}, "arr": [1, 2]}


# Property [Rejected Expressions]: malformed variable references, structurally invalid
# $$ROOT field paths, and uses of the reserved ROOT name as a user variable are all
# rejected, each with its own specific error code. The reserved name is matched exactly:
# a different case or any suffix resolves as an undefined user variable instead.
REJECTED_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="root_dollar_prefixed_subfield",
        expression="$$ROOT.$a",
        doc=DOC,
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="A dollar-prefixed subfield name after $$ROOT should be rejected",
    ),
    ExpressionTestCase(
        id="triple_dollar",
        expression="$$$",
        doc=DOC,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$$$ should be rejected as a malformed variable reference",
    ),
    ExpressionTestCase(
        id="empty_variable_name",
        expression="$$",
        doc=DOC,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Bare $$ (empty variable name) should be rejected",
    ),
    ExpressionTestCase(
        id="empty_variable_name_with_dot",
        expression="$$.",
        doc=DOC,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$$. should be rejected as an empty variable name",
    ),
    ExpressionTestCase(
        id="lowercase_root_with_path",
        expression="$$root.a",
        doc=DOC,
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="Lowercase $$root should be an undefined user variable, not the system variable, "
        "including when followed by a path",
    ),
    ExpressionTestCase(
        id="root_name_with_digit_suffix",
        expression="$$ROOT2",
        doc=DOC,
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$$ROOT2 should be an undefined user variable, not a prefix match on ROOT",
    ),
    ExpressionTestCase(
        id="map_as_root",
        expression={"$map": {"input": "$arr", "as": "ROOT", "in": "$$ROOT"}},
        doc=DOC,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="ROOT should be rejected as a $map 'as' variable name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(REJECTED_EXPRESSION_TESTS))
def test_root_rejected_expression(collection, test):
    """Malformed variable references, invalid $$ROOT paths, and reserved ROOT uses are rejected."""
    result = execute_expression_with_insert(collection, test.expression, dict(test.doc))
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_root_as_command_level_let_variable_name(collection):
    """ROOT is rejected as a command-level 'let' variable name."""
    collection.insert_one(dict(DOC))
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "x": "$a"}}],
            "cursor": {},
            "let": {"ROOT": 1},
        },
    )
    assertFailureCode(
        result,
        FAILED_TO_PARSE_ERROR,
        msg="ROOT should be reserved as a command-level let variable name",
    )
