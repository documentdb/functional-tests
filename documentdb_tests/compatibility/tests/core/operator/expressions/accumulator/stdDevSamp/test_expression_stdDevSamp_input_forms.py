from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR, INVALID_DOLLAR_FIELD_PATH
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class StdDevSampTest(BaseTestCase):
    values: Any = None
    document: dict[str, Any] | None = None


STDDEVSAMP_INPUT_FORMS_TESTS: list[StdDevSampTest] = [
    # basic traversal
    StdDevSampTest(
        "traversal_basic",
        values={"$literal": [1, 2, 3]},
        document=None,
        expected=pytest.approx(1.0),
        msg="Should compute stdDevSamp traversing the literal array",
    ),
    StdDevSampTest(
        "traversal_empty_array",
        values={"$literal": []},
        document=None,
        expected=None,
        msg="Should return null for an empty traversed array",
    ),
    StdDevSampTest(
        "traversal_single_element",
        values={"$literal": [5]},
        document=None,
        expected=None,
        msg="Should return null for a single traversed element",
    ),
    StdDevSampTest(
        "nested_array",
        values={"$literal": [[1, 2, 3]]},
        document=None,
        expected=None,
        msg="Should return null for a nested array",
    ),
    # expression with operand args
    StdDevSampTest(
        "expression_operand_add",
        values=[{"$add": [1, 1]}, 4, 6],
        document=None,
        expected=pytest.approx(2.0),
        msg="Should compute stdDevSamp dev from expression operands",
    ),
    StdDevSampTest(
        "expression_operand_null",
        values=[{"$literal": None}, 4, 6],
        document=None,
        expected=pytest.approx(1.4142135623730951),
        msg="should calculate stdDevSamp ignoring expressions returning null",
    ),
    # document traversal
    StdDevSampTest(
        "field_refs",
        values=["$a", "$b", "$c"],
        document={"a": 1, "b": 2, "c": 3},
        expected=pytest.approx(1.0),
        msg="Should compute stdDevSamp from multiple field references",
    ),
    StdDevSampTest(
        "nested_object_path",
        values=["$a.x", "$a.y", "$a.z"],
        document={"a": {"x": 1, "y": 2, "z": 3}},
        expected=pytest.approx(1.0),
        msg="Should compute stdDevSamp from nested object paths",
    ),
    StdDevSampTest(
        "composite_array_path",
        values="$a.val",
        document={"a": [{"val": 1}, {"val": 5}]},
        expected=pytest.approx(2.8284271247461903),
        msg="Should compute stdDevSamp from a composite array path",
    ),
    # field path errors
    StdDevSampTest(
        "fieldpath_bare_dollar",
        values="$",
        document=None,
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="Should reject bare '$' as an invalid field path",
    ),
    StdDevSampTest(
        "fieldpath_double_dollar",
        values="$$",
        document=None,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject '$$' as an empty variable name",
    ),
]


@pytest.mark.parametrize(
    "test_case", pytest_params([t for t in STDDEVSAMP_INPUT_FORMS_TESTS if t.document is None])
)
def test_stdDevSamp_expression(collection, test_case):
    """Test $stdDevSamp expression input form expressions from a literal argument list."""
    result = execute_expression(collection, {"$stdDevSamp": test_case.values})

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


@pytest.mark.parametrize(
    "test_case",
    pytest_params([t for t in STDDEVSAMP_INPUT_FORMS_TESTS if t.document is not None]),
)
def test_stdDevSamp_expression_from_document(collection, test_case):
    """Test $stdDevSamp expression input forms from inserted document fields."""
    result = execute_expression_with_insert(
        collection, {"$stdDevSamp": test_case.values}, test_case.document
    )

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
