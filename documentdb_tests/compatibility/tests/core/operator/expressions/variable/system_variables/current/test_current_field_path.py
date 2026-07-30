"""
Field path resolution through the $$CURRENT system variable.

Covers dot-notation access and missing/null fields. Basic resolution inside
object/array/operator sub-expressions is covered once as shared
expression-engine wiring in
``test_system_variables_current_expression_engine.py``.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# Property [Path Resolution]: $$CURRENT.<path> resolves dot-notation paths against the
# current document, including nested objects, arrays of objects, and numeric keys, the same
# way a bare field path would.
FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="simple_field",
        expression="$$CURRENT.a",
        doc={"_id": 1, "a": 5},
        expected=5,
        msg="$$CURRENT.<field> should resolve a top-level field",
    ),
    ExpressionTestCase(
        id="nested_field",
        expression="$$CURRENT.a.b",
        doc={"_id": 1, "a": {"b": 7}},
        expected=7,
        msg="$$CURRENT.<a>.<b> should resolve a nested field",
    ),
    ExpressionTestCase(
        id="nested_composite_array_path",
        expression="$$CURRENT.a.b.c.d",
        doc={"_id": 1, "a": {"b": [{"c": [{"d": 1}]}]}},
        expected=[[1]],
        msg="$$CURRENT should traverse arrays of objects, nesting one array per array level",
    ),
    ExpressionTestCase(
        id="composite_array_path",
        expression="$$CURRENT.a.b",
        doc={"_id": 1, "a": [{"b": 1}, {"b": 2}]},
        expected=[1, 2],
        msg="Composite array path should resolve to the array of subfield values",
    ),
    ExpressionTestCase(
        id="numeric_index_path_on_array",
        expression="$$CURRENT.arr.0",
        doc={"_id": 1, "arr": [10, 20, 30]},
        expected=[],
        msg="Numeric index path in expression context should resolve to an empty array",
    ),
    ExpressionTestCase(
        id="numeric_key_path_on_object",
        expression="$$CURRENT.a.0.b",
        doc={"_id": 1, "a": {"0": {"b": 3}}},
        expected=3,
        msg="Numeric object key should resolve as a field name",
    ),
    ExpressionTestCase(
        id="null_field",
        expression="$$CURRENT.a",
        doc={"_id": 1, "a": None},
        expected=None,
        msg="$$CURRENT should return null for a null-valued field",
    ),
    ExpressionTestCase(
        id="array_field",
        expression="$$CURRENT.arr",
        doc={"_id": 1, "arr": [1, 2]},
        expected=[1, 2],
        msg="$$CURRENT.<arrayField> should return the array intact",
    ),
    ExpressionTestCase(
        id="multiple_operands",
        expression={"$add": ["$$CURRENT.a", "$$CURRENT.b"]},
        doc={"_id": 1, "a": 2, "b": 3},
        expected=5,
        msg="$$CURRENT-prefixed paths should be usable throughout one expression",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_PATH_TESTS))
def test_system_variables_current_field_path(collection, test):
    """$$CURRENT dot-notation paths resolve against the current document."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertSuccess(result, [{"result": test.expected}], msg=test.msg)


# Property [Missing Path Omission]: a $$CURRENT path through a nonexistent field or a
# missing parent resolves to missing, omitting the output field rather than producing null.
MISSING_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nonexistent_field_is_omitted",
        expression="$$CURRENT.missing",
        doc={"_id": 1, "a": 1},
        msg="$$CURRENT.<missing> should resolve to missing and omit the output field",
    ),
    ExpressionTestCase(
        id="nested_path_through_missing_parent_is_omitted",
        expression="$$CURRENT.x.y",
        doc={"_id": 1, "a": 1},
        msg="$$CURRENT path through a missing parent should resolve to missing",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MISSING_PATH_TESTS))
def test_system_variables_current_missing_path_is_omitted(collection, test):
    """$$CURRENT paths through nonexistent or missing fields resolve to missing."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertSuccess(result, [{}], msg=test.msg)


def test_system_variables_current_null_field_distinct_from_missing_field(collection):
    """A null $$CURRENT field is emitted as null while a missing $$CURRENT field is omitted."""
    result = execute_project_with_insert(
        collection,
        {"_id": 1, "nullField": None},
        {"fromNull": "$$CURRENT.nullField", "fromMissing": "$$CURRENT.absent"},
    )

    assertSuccess(
        result,
        [{"fromNull": None}],
        msg="null should be projected while missing should be omitted",
    )
