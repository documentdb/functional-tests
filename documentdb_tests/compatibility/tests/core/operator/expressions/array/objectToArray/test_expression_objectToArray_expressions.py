"""
Expression and field path tests for $objectToArray expression.

Tests field path lookups (including nested paths), nested object values,
$let variables, system variables ($$ROOT/$$CURRENT), null/missing field
handling, field references inside literal objects, expression-type operands
($mergeObjects / $literal / computed-value objects), algebraic properties
($arrayToObject round-trip inverse and output-length invariant via $size), and
BSON type distinction (k always string; v subtypes not collapsed) via $map/$type.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field-path operand]: the operand may be a (possibly nested) field
# path, not just a literal object; the object it resolves to is converted the
# same way as a literal.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_field_path",
        expression={"$objectToArray": "$a.b"},
        doc={"a": {"b": {"x": 1}}},
        expected=[{"k": "x", "v": 1}],
        msg="Should resolve nested field path",
    ),
    ExpressionTestCase(
        id="deeply_nested_field",
        expression={"$objectToArray": "$a.b.c"},
        doc={"a": {"b": {"c": {"x": 1}}}},
        expected=[{"k": "x", "v": 1}],
        msg="Should resolve deeply nested field path",
    ),
]

# Property [$let variable operand]: the operand may be a $let-bound variable
# referencing an object, resolved before conversion.
LET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="let_variable",
        expression={"$let": {"vars": {"obj": "$obj"}, "in": {"$objectToArray": "$$obj"}}},
        doc={"obj": {"a": 1, "b": 2}},
        expected=[{"k": "a", "v": 1}, {"k": "b", "v": 2}],
        msg="Should convert $let variable object",
    ),
]

# Property [System variable operand]: the operand may be a system variable
# ($$ROOT for the whole document including _id, $$CURRENT for the field-path
# equivalent of the current document) rather than a plain field path.
SYSTEM_VAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="root_variable",
        expression={"$objectToArray": "$$ROOT"},
        doc={"_id": 4, "a": 1, "b": 2, "c": 3},
        expected=[{"k": "_id", "v": 4}, {"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "c", "v": 3}],
        msg="$$ROOT should include all fields including _id",
    ),
    ExpressionTestCase(
        id="current_variable_field_path",
        expression={"$objectToArray": "$$CURRENT.obj"},
        doc={"_id": 5, "obj": {"a": 1, "b": 2}},
        expected=[{"k": "a", "v": 1}, {"k": "b", "v": 2}],
        msg="$$CURRENT.<field> should resolve like the field path $<field>",
    ),
]

# Property [Null/missing operand]: a missing field path or a null-valued
# operand returns null rather than an error or an empty array.
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_field",
        expression={"$objectToArray": "$nonexistent"},
        doc={"other": 1},
        expected=None,
        msg="Missing field should return null",
    ),
    ExpressionTestCase(
        id="null_type_check",
        expression={"$type": {"$objectToArray": "$obj"}},
        doc={"obj": None},
        expected="null",
        msg="Type of null input result should be 'null'",
    ),
]

# Property [Field references inside a literal object operand]: field paths
# nested as values within a literal object operand are resolved before
# conversion; a reference to a missing field omits that key from the result.
FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="literal_object_with_field_ref",
        expression={"$objectToArray": {"key1": "$a"}},
        doc={"a": 1},
        expected=[{"k": "key1", "v": 1}],
        msg="Should resolve field reference in literal object",
    ),
    ExpressionTestCase(
        id="literal_object_with_missing_field_ref",
        expression={"$objectToArray": {"key1": "$t"}},
        doc={"a": 1},
        expected=[],
        msg="Missing field reference in literal object should exclude field",
    ),
]

# Property [Algebraic]: round-trip inverse ($arrayToObject undoes
# $objectToArray) and output-length invariant (one element per top-level field).
ALGEBRAIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="roundtrip_single_field",
        expression={"$arrayToObject": {"$objectToArray": "$obj"}},
        doc={"obj": {"only": 5}},
        expected={"only": 5},
        msg="Round-trip should preserve a single-field object",
    ),
    ExpressionTestCase(
        id="roundtrip_empty_object",
        expression={"$arrayToObject": {"$objectToArray": "$obj"}},
        doc={"obj": {}},
        expected={},
        msg="Round-trip should preserve an empty object",
    ),
    ExpressionTestCase(
        id="size_zero_fields",
        expression={"$size": {"$objectToArray": "$obj"}},
        doc={"obj": {}},
        expected=0,
        msg="Output length should equal the number of top-level fields (0)",
    ),
    ExpressionTestCase(
        id="size_one_field",
        expression={"$size": {"$objectToArray": "$obj"}},
        doc={"obj": {"a": 1}},
        expected=1,
        msg="Output length should equal the number of top-level fields (1)",
    ),
    ExpressionTestCase(
        id="size_five_fields",
        expression={"$size": {"$objectToArray": "$obj"}},
        doc={"obj": {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}},
        expected=5,
        msg="Output length should equal the number of top-level fields (5)",
    ),
]

# Property [Expression-type operand]: the operand may be produced by an
# expression operator, a $literal wrapper, or an object with computed values
# (Rule 3), not just a plain literal object or field path.
EXPRESSION_OPERAND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="operand_from_mergeObjects",
        expression={"$objectToArray": {"$mergeObjects": [{"a": 1}, {"b": 2}]}},
        doc={"x": 0},
        expected=[{"k": "a", "v": 1}, {"k": "b", "v": 2}],
        msg="Should accept operand produced by $mergeObjects",
    ),
    ExpressionTestCase(
        id="operand_literal_object",
        expression={"$objectToArray": {"$literal": {"a": 1, "b": 2}}},
        doc={"x": 0},
        expected=[{"k": "a", "v": 1}, {"k": "b", "v": 2}],
        msg="Should accept a $literal-wrapped object operand",
    ),
    ExpressionTestCase(
        id="operand_object_computed_values",
        expression={"$objectToArray": {"a": {"$add": [1, 2]}, "b": "$x"}},
        doc={"x": 9},
        expected=[{"k": "a", "v": 3}, {"k": "b", "v": 9}],
        msg="Should resolve computed values inside an object operand",
    ),
]

# Property [BSON type distinction] (Rule 11): k is always a string; v
# preserves the source BSON type without collapsing numerically-equal subtypes.
BSON_DISTINCTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="k_is_always_string",
        expression={
            "$map": {
                "input": {"$objectToArray": "$obj"},
                "as": "kv",
                "in": {"$type": "$$kv.k"},
            }
        },
        doc={"obj": {"a": 1, "0": 2, "$x": 3}},
        expected=["string", "string", "string"],
        msg="Every k in the output should be BSON type string",
    ),
    ExpressionTestCase(
        id="v_numeric_subtypes_not_collapsed",
        expression={
            "$map": {
                "input": {"$objectToArray": "$obj"},
                "as": "kv",
                "in": {"$type": "$$kv.v"},
            }
        },
        doc={"obj": {"a": 1, "b": 1.0, "c": Int64(1), "d": Decimal128("1")}},
        expected=["int", "double", "long", "decimal"],
        msg="Numerically-equal values retain distinct BSON subtypes (not collapsed)",
    ),
    ExpressionTestCase(
        id="v_empty_string_vs_null_distinct",
        expression={
            "$map": {
                "input": {"$objectToArray": "$obj"},
                "as": "kv",
                "in": {"$type": "$$kv.v"},
            }
        },
        doc={"obj": {"a": "", "b": None}},
        expected=["string", "null"],
        msg="Empty string and null values remain distinct types",
    ),
]

ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + LET_TESTS
    + SYSTEM_VAR_TESTS
    + NULL_MISSING_EXPR_TESTS
    + FIELD_REF_TESTS
    + ALGEBRAIC_TESTS
    + EXPRESSION_OPERAND_TESTS
    + BSON_DISTINCTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_objectToArray_expression(collection, test):
    """Test $objectToArray with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
