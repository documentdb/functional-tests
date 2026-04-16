"""
Tests for $mergeObjects basic operations.

Covers core merge behavior, null/missing/undefined handling, expression types,
field lookup, $$ROOT/$$CURRENT, empty documents, passthrough, literal-only,
array-of-objects input, and multiple field references.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import MERGE_OBJECTS_INVALID_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

LITERAL_TESTS: list[ExpressionTestCase] = [
    # Argument count variations
    ExpressionTestCase(
        "empty_array",
        expression={"$mergeObjects": []},
        expected={},
        msg="Empty array should succeed and return empty document",
    ),
    ExpressionTestCase(
        "five_docs",
        expression={"$mergeObjects": [{"a": 1}, {"b": 2}, {"c": 3}, {"d": 4}, {"e": 5}]},
        expected={"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        msg="Five disjoint documents should succeed and include all keys",
    ),
    ExpressionTestCase(
        "non_array_single_doc",
        expression={"$mergeObjects": {"a": 1}},
        expected={"a": 1},
        msg="Non-array single document argument should succeed as valid input",
    ),
    ExpressionTestCase(
        "nested_array_arg",
        expression={"$mergeObjects": [[{"a": 1}, {"b": 2}]]},
        expected={"a": 1, "b": 2},
        msg="Nested array should succeed and be treated as array-of-objects input",
    ),
    # Core merge behavior
    ExpressionTestCase(
        "disjoint_keys",
        expression={"$mergeObjects": [{"a": 1}, {"b": 2}]},
        expected={"a": 1, "b": 2},
        msg="Disjoint keys should succeed and merge all fields",
    ),
    ExpressionTestCase(
        "overlapping_key_last_wins",
        expression={"$mergeObjects": [{"a": 1, "b": 2}, {"b": 3, "c": 4}]},
        expected={"a": 1, "b": 3, "c": 4},
        msg="Overlapping key should succeed with last value winning",
    ),
    ExpressionTestCase(
        "three_args_with_nested",
        expression={"$mergeObjects": [{"a": 1}, {"b": {"nested": 2}}, {"c": 3}]},
        expected={"a": 1, "b": {"nested": 2}, "c": 3},
        msg="Three args including nested subdocument should succeed",
    ),
    # Null handling
    ExpressionTestCase(
        "all_null",
        expression={"$mergeObjects": [None, None]},
        expected={},
        msg="All nulls should succeed and return empty doc",
    ),
    ExpressionTestCase(
        "single_null",
        expression={"$mergeObjects": [None]},
        expected={},
        msg="Single null should succeed and return empty doc",
    ),
    ExpressionTestCase(
        "null_first",
        expression={"$mergeObjects": [None, {"a": 1}]},
        expected={"a": 1},
        msg="Null in first position should succeed and be ignored",
    ),
    ExpressionTestCase(
        "null_last",
        expression={"$mergeObjects": [{"a": 1}, None]},
        expected={"a": 1},
        msg="Null in last position should succeed and be ignored",
    ),
    ExpressionTestCase(
        "null_middle",
        expression={"$mergeObjects": [{"a": 1}, None, {"b": 2}]},
        expected={"a": 1, "b": 2},
        msg="Null in middle position should succeed and be ignored",
    ),
    ExpressionTestCase(
        "multiple_nulls",
        expression={"$mergeObjects": [None, {"a": 1}, None, {"b": 2}, None]},
        expected={"a": 1, "b": 2},
        msg="Multiple interspersed nulls should succeed and be ignored",
    ),
    # Empty documents
    ExpressionTestCase(
        "single_empty",
        expression={"$mergeObjects": [{}]},
        expected={},
        msg="Single empty doc should succeed and return empty doc",
    ),
    ExpressionTestCase(
        "two_empty",
        expression={"$mergeObjects": [{}, {}]},
        expected={},
        msg="Two empty docs should succeed and return empty doc",
    ),
    ExpressionTestCase(
        "three_empty",
        expression={"$mergeObjects": [{}, {}, {}]},
        expected={},
        msg="Three empty docs should succeed and return empty doc",
    ),
    ExpressionTestCase(
        "empty_with_nonempty",
        expression={"$mergeObjects": [{}, {"a": 1}]},
        expected={"a": 1},
        msg="Empty doc merged with non-empty should succeed and return non-empty",
    ),
    ExpressionTestCase(
        "nonempty_with_empty",
        expression={"$mergeObjects": [{"a": 1}, {}]},
        expected={"a": 1},
        msg="Non-empty merged with empty should succeed and return non-empty",
    ),
    ExpressionTestCase(
        "mixed_empty",
        expression={"$mergeObjects": [{}, {"a": 1}, {}, {"b": 2}, {}]},
        expected={"a": 1, "b": 2},
        msg="Mixed empty and non-empty docs should succeed and merge non-empty fields",
    ),
    # Literal-only merge
    ExpressionTestCase(
        "single_literal",
        expression={"$mergeObjects": [{"a": 1}]},
        expected={"a": 1},
        msg="Single literal document should succeed and pass through unchanged",
    ),
    ExpressionTestCase(
        "two_literals_disjoint",
        expression={"$mergeObjects": [{"a": 1}, {"b": 2}]},
        expected={"a": 1, "b": 2},
        msg="Two disjoint literal documents should succeed and merge all keys",
    ),
    ExpressionTestCase(
        "two_literals_overlap",
        expression={"$mergeObjects": [{"a": 1}, {"a": 2}]},
        expected={"a": 2},
        msg="Two literal documents with overlapping key should succeed with last value winning",
    ),
    # $$REMOVE
    ExpressionTestCase(
        "remove_first",
        expression={"$mergeObjects": ["$$REMOVE", {"a": 1}]},
        expected={"a": 1},
        msg="$$REMOVE in first position should succeed and be treated as missing/null",
    ),
    ExpressionTestCase(
        "remove_last",
        expression={"$mergeObjects": [{"a": 1}, "$$REMOVE"]},
        expected={"a": 1},
        msg="$$REMOVE in last position should succeed and be treated as missing/null",
    ),
    ExpressionTestCase(
        "all_remove",
        expression={"$mergeObjects": ["$$REMOVE", "$$REMOVE"]},
        expected={},
        msg="All $$REMOVE should succeed and return empty doc",
    ),
    # Document shapes
    ExpressionTestCase(
        "deeply_nested",
        expression={"$mergeObjects": [{"a": {"b": {"c": {"d": 1}}}}, {"e": 2}]},
        expected={"a": {"b": {"c": {"d": 1}}}, "e": 2},
        msg="Merging with deeply nested document should succeed and preserve nesting",
    ),
    ExpressionTestCase(
        "nested_arrays",
        expression={"$mergeObjects": [{"arr": [[1, 2], [3, 4]]}, {"x": 1}]},
        expected={"arr": [[1, 2], [3, 4]], "x": 1},
        msg="Merging document with nested arrays should succeed and preserve array structure",
    ),
    ExpressionTestCase(
        "obj_with_array",
        expression={"$mergeObjects": [{"obj": {"arr": [1, 2, 3]}}, {"y": 2}]},
        expected={"obj": {"arr": [1, 2, 3]}, "y": 2},
        msg="Merging document containing object with array should succeed and preserve structure",
    ),
    # Overwrite behavior (last wins)
    ExpressionTestCase(
        "simple_overwrite",
        expression={"$mergeObjects": [{"a": 1}, {"a": 2}]},
        expected={"a": 2},
        msg="Overlapping key should succeed with last value overwriting first",
    ),
    ExpressionTestCase(
        "triple_overwrite",
        expression={"$mergeObjects": [{"a": 1}, {"a": 2}, {"a": 3}]},
        expected={"a": 3},
        msg="Three documents with same key should succeed with last value winning",
    ),
    ExpressionTestCase(
        "partial_overlap",
        expression={"$mergeObjects": [{"a": 1, "b": 2}, {"b": 3, "c": 4}]},
        expected={"a": 1, "b": 3, "c": 4},
        msg="Partially overlapping keys should succeed with last-wins for conflicts",
    ),
    ExpressionTestCase(
        "overwrite_diff_type",
        expression={"$mergeObjects": [{"a": 1}, {"a": "hello"}]},
        expected={"a": "hello"},
        msg="Overwriting int with string should succeed with type change",
    ),
    ExpressionTestCase(
        "overwrite_with_null",
        expression={"$mergeObjects": [{"a": 1}, {"a": None}]},
        expected={"a": None},
        msg="Overwriting value with null should succeed and set field to null",
    ),
    ExpressionTestCase(
        "overwrite_with_nested",
        expression={"$mergeObjects": [{"a": 1}, {"a": {"b": 2}}]},
        expected={"a": {"b": 2}},
        msg="Overwriting scalar with nested doc should succeed",
    ),
    ExpressionTestCase(
        "overwrite_nested_with_scalar",
        expression={"$mergeObjects": [{"a": {"b": 2}}, {"a": 1}]},
        expected={"a": 1},
        msg="Overwriting nested doc with scalar should succeed",
    ),
    ExpressionTestCase(
        "null_overwrites_value",
        expression={"$mergeObjects": [{"a": {"b": 1}}, {"a": None}]},
        expected={"a": None},
        msg="Null overwriting existing value should succeed and set field to null",
    ),
    ExpressionTestCase(
        "value_overwrites_null",
        expression={"$mergeObjects": [{"a": None}, {"a": {"b": 1}}]},
        expected={"a": {"b": 1}},
        msg="Value overwriting null should succeed and set field to value",
    ),
    # Shallow merge (NOT deep merge)
    ExpressionTestCase(
        "shallow_not_deep",
        expression={"$mergeObjects": [{"a": {"x": 1, "y": 2}}, {"a": {"y": 3, "z": 4}}]},
        expected={"a": {"y": 3, "z": 4}},
        msg="Shallow merge should succeed: entire 'a' replaced, not deep merged",
    ),
    ExpressionTestCase(
        "array_replaced_not_concat",
        expression={"$mergeObjects": [{"a": [1, 2, 3]}, {"a": [4, 5]}]},
        expected={"a": [4, 5]},
        msg="Conflicting array field should succeed with replacement, not concatenation",
    ),
    ExpressionTestCase(
        "deep_nested_replaced_by_scalar",
        expression={"$mergeObjects": [{"a": {"b": {"c": 1}}}, {"a": 42}]},
        expected={"a": 42},
        msg="Deep nested value should be successfully replaced by scalar",
    ),
    ExpressionTestCase(
        "scalar_replaced_by_deep_nested",
        expression={"$mergeObjects": [{"a": 42}, {"a": {"b": {"c": 1}}}]},
        expected={"a": {"b": {"c": 1}}},
        msg="Scalar value should be successfully replaced by deep nested doc",
    ),
    # _id field handling
    ExpressionTestCase(
        "both_have_id",
        expression={"$mergeObjects": [{"_id": 1, "a": 1}, {"_id": 2, "b": 2}]},
        expected={"_id": 2, "a": 1, "b": 2},
        msg="Both documents with _id should succeed with last _id winning",
    ),
    ExpressionTestCase(
        "first_has_id",
        expression={"$mergeObjects": [{"_id": 1, "a": 1}, {"b": 2}]},
        expected={"_id": 1, "a": 1, "b": 2},
        msg="Only first document with _id should succeed and preserve _id",
    ),
    ExpressionTestCase(
        "second_has_id",
        expression={"$mergeObjects": [{"a": 1}, {"_id": 2, "b": 2}]},
        expected={"a": 1, "_id": 2, "b": 2},
        msg="Only second document with _id should succeed and include _id",
    ),
    # Array-valued fields
    ExpressionTestCase(
        "disjoint_arrays",
        expression={"$mergeObjects": [{"a": [1, 2]}, {"b": [3, 4]}]},
        expected={"a": [1, 2], "b": [3, 4]},
        msg="Disjoint array-valued fields should succeed and preserve both arrays",
    ),
    ExpressionTestCase(
        "conflict_arrays",
        expression={"$mergeObjects": [{"a": [1, 2]}, {"a": [3, 4, 5]}]},
        expected={"a": [3, 4, 5]},
        msg="Conflicting array-valued fields should succeed with last array replacing, not concatenating",  # noqa: E501
    ),
    ExpressionTestCase(
        "nested_array_objects",
        expression={"$mergeObjects": [{"a": [{"x": 1}]}, {"b": [{"y": 2}]}]},
        expected={"a": [{"x": 1}], "b": [{"y": 2}]},
        msg="Disjoint fields with nested array of objects should succeed and preserve structure",
    ),
    # BSON boundary values
    ExpressionTestCase(
        "overwrite_with_long_min",
        expression={"$mergeObjects": [{"a": 1}, {"a": Int64(-9223372036854775808)}]},
        expected={"a": Int64(-9223372036854775808)},
        msg="Overwriting with LONG_MIN should succeed and preserve value",
    ),
    ExpressionTestCase(
        "overwrite_with_long_max",
        expression={"$mergeObjects": [{"a": 1}, {"a": Int64(9223372036854775807)}]},
        expected={"a": Int64(9223372036854775807)},
        msg="Overwriting with LONG_MAX should succeed and preserve value",
    ),
    ExpressionTestCase(
        "overwrite_with_neg_infinity",
        expression={"$mergeObjects": [{"a": 1}, {"a": float("-inf")}]},
        expected={"a": float("-inf")},
        msg="Overwriting with -Infinity should succeed and preserve value",
    ),
    ExpressionTestCase(
        "overwrite_with_decimal128_max",
        expression={
            "$mergeObjects": [
                {"a": 1},
                {"a": Decimal128("9.999999999999999999999999999999999E+6144")},
            ]
        },
        expected={"a": Decimal128("9.999999999999999999999999999999999E+6144")},
        msg="Overwriting with DECIMAL128_MAX should succeed and preserve value",
    ),
    ExpressionTestCase(
        "overwrite_with_decimal128_min",
        expression={
            "$mergeObjects": [
                {"a": 1},
                {"a": Decimal128("-9.999999999999999999999999999999999E+6144")},
            ]
        },
        expected={"a": Decimal128("-9.999999999999999999999999999999999E+6144")},
        msg="Overwriting with DECIMAL128_MIN should succeed and preserve value",
    ),
    # BSON type preservation
    ExpressionTestCase(
        "bson_int_long",
        expression={"$mergeObjects": [{"a": 1}, {"b": Int64(2)}]},
        expected={"a": 1, "b": Int64(2)},
        msg="Merging int and long values should succeed and preserve BSON types",
    ),
    ExpressionTestCase(
        "bson_infinity",
        expression={"$mergeObjects": [{"a": float("inf")}, {"b": float("-inf")}]},
        expected={"a": float("inf"), "b": float("-inf")},
        msg="Merging +Infinity and -Infinity should succeed and preserve values",
    ),
    ExpressionTestCase(
        "bson_minkey_maxkey",
        expression={"$mergeObjects": [{"a": MinKey()}, {"b": MaxKey()}]},
        expected={"a": MinKey(), "b": MaxKey()},
        msg="Merging MinKey and MaxKey should succeed and preserve BSON types",
    ),
    ExpressionTestCase(
        "bson_decimal128_date",
        expression={"$mergeObjects": [{"a": Decimal128("1.5")}, {"b": datetime(2024, 1, 1)}]},
        expected={"a": Decimal128("1.5"), "b": datetime(2024, 1, 1)},
        msg="Merging Decimal128 and Date should succeed and preserve BSON types",
    ),
    ExpressionTestCase(
        "bson_objectid_bindata",
        expression={
            "$mergeObjects": [{"a": ObjectId("000000000000000000000000")}, {"b": Binary(b"abc")}]
        },
        expected={"a": ObjectId("000000000000000000000000"), "b": b"abc"},
        msg="Merging ObjectId and BinData should succeed and preserve BSON types",
    ),
    ExpressionTestCase(
        "bson_regex_timestamp",
        expression={"$mergeObjects": [{"a": Regex("pattern")}, {"b": Timestamp(1, 1)}]},
        expected={"a": Regex("pattern"), "b": Timestamp(1, 1)},
        msg="Merging Regex and Timestamp should succeed and preserve BSON types",
    ),
    ExpressionTestCase(
        "bson_bool_array",
        expression={"$mergeObjects": [{"a": True}, {"b": [1, 2, 3]}]},
        expected={"a": True, "b": [1, 2, 3]},
        msg="Merging bool and array values should succeed and preserve types",
    ),
    ExpressionTestCase(
        "bson_zero_false_distinct",
        expression={"$mergeObjects": [{"a": 0}, {"b": False}]},
        expected={"a": 0, "b": False},
        msg="Merging 0 and false should succeed and preserve them as distinct values",
    ),
    # Field ordering
    ExpressionTestCase(
        "interleaved_conflicts",
        expression={"$mergeObjects": [{"a": 1, "b": 10}, {"b": 20, "c": 30}, {"a": 100, "c": 300}]},
        expected={"a": 100, "b": 20, "c": 300},
        msg="Interleaved conflicts should succeed with last value winning per key",
    ),
    ExpressionTestCase(
        "field_order_disjoint",
        expression={"$mergeObjects": [{"a": 1, "b": 2}, {"c": 3, "d": 4}]},
        expected={"a": 1, "b": 2, "c": 3, "d": 4},
        msg="Disjoint keys should succeed and preserve insertion order",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_mergeObjects_literal(collection, test):
    """Test $mergeObjects with literal expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


FIELD_REF_TESTS: list[ExpressionTestCase] = [
    # Missing field handling
    ExpressionTestCase(
        "missing_first",
        expression={"$mergeObjects": ["$missing", {"a": 1}]},
        doc={"x": 1},
        expected={"a": 1},
        msg="Missing field in first position should succeed and be treated as null",
    ),
    ExpressionTestCase(
        "missing_middle",
        expression={"$mergeObjects": [{"a": 1}, "$missing", {"b": 2}]},
        doc={"x": 1},
        expected={"a": 1, "b": 2},
        msg="Missing field in middle position should succeed and be treated as null",
    ),
    ExpressionTestCase(
        "all_missing",
        expression={"$mergeObjects": ["$missing1", "$missing2"]},
        doc={"x": 1},
        expected={},
        msg="All missing fields should succeed and return empty doc",
    ),
    # Expression type smoke
    ExpressionTestCase(
        "field_reference",
        expression={"$mergeObjects": ["$doc1", "$doc2"]},
        doc={"doc1": {"a": 1}, "doc2": {"b": 2}},
        expected={"a": 1, "b": 2},
        msg="Two field references to documents should succeed and merge",
    ),
    ExpressionTestCase(
        "object_expression",
        expression={"$mergeObjects": [{"a": "$val"}]},
        doc={"val": 42},
        expected={"a": 42},
        msg="Object expression with field ref should succeed and resolve value",
    ),
    # Field lookup
    ExpressionTestCase(
        "simple_field",
        expression={"$mergeObjects": ["$obj", {"b": 2}]},
        doc={"obj": {"a": 1}},
        expected={"a": 1, "b": 2},
        msg="Field reference to subdocument should succeed and merge with literal",
    ),
    ExpressionTestCase(
        "nested_field",
        expression={"$mergeObjects": ["$x.y", {"b": 2}]},
        doc={"x": {"y": {"a": 1}}},
        expected={"a": 1, "b": 2},
        msg="Nested field path lookup should succeed and merge with literal",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        expression={"$mergeObjects": ["$missing", {"a": 1}]},
        doc={"x": 1},
        expected={"a": 1},
        msg="Non-existent field should succeed and be treated as null",
    ),
    # Non-array syntax
    ExpressionTestCase(
        "non_array_field_ref",
        expression={"$mergeObjects": "$obj"},
        doc={"obj": {"a": 1, "b": 2}},
        expected={"a": 1, "b": 2},
        msg="Non-array syntax with field ref should succeed and pass through document",
    ),
    ExpressionTestCase(
        "non_array_null_field",
        expression={"$mergeObjects": "$obj"},
        doc={"obj": None},
        expected={},
        msg="Non-array syntax with null field should succeed and return empty doc",
    ),
    ExpressionTestCase(
        "non_array_missing_field",
        expression={"$mergeObjects": "$missing"},
        doc={"x": 1},
        expected={},
        msg="Non-array syntax with missing field should succeed and return empty doc",
    ),
    # Array of objects input
    ExpressionTestCase(
        "array_of_objects_non_array",
        expression={"$mergeObjects": "$arr"},
        doc={"arr": [{"a": 1}, {"b": 2}]},
        expected={"a": 1, "b": 2},
        msg="Array of objects via non-array syntax should succeed and merge sequentially",
    ),
    ExpressionTestCase(
        "array_of_objects_overlap",
        expression={"$mergeObjects": "$arr"},
        doc={"arr": [{"a": 1}, {"a": 2, "b": 3}]},
        expected={"a": 2, "b": 3},
        msg="Array of objects with overlapping keys should succeed with last value winning",
    ),
    ExpressionTestCase(
        "array_of_objects_array_syntax",
        expression={"$mergeObjects": ["$arr"]},
        doc={"arr": [{"a": 1}, {"b": 2}]},
        expected={"a": 1, "b": 2},
        msg="Array syntax with array-of-objects field should succeed and merge",
    ),
    # Single object passthrough
    ExpressionTestCase(
        "single_field_passthrough",
        expression={"$mergeObjects": ["$obj"]},
        doc={"obj": {"a": 1, "b": 2}},
        expected={"a": 1, "b": 2},
        msg="Single field reference should succeed and pass through document unchanged",
    ),
    # Multiple field references
    ExpressionTestCase(
        "two_field_refs",
        expression={"$mergeObjects": ["$obj1", "$obj2"]},
        doc={"obj1": {"a": 1}, "obj2": {"b": 2}},
        expected={"a": 1, "b": 2},
        msg="Two disjoint field references should succeed and merge all keys",
    ),
    ExpressionTestCase(
        "field_ref_with_null",
        expression={"$mergeObjects": ["$obj1", "$obj2"]},
        doc={"obj1": {"a": 1}, "obj2": None},
        expected={"a": 1},
        msg="Null field reference should succeed and be ignored",
    ),
    ExpressionTestCase(
        "three_inputs_overlap",
        expression={"$mergeObjects": ["$obj1", "$obj2", {"a": 99}]},
        doc={"obj1": {"a": 1}, "obj2": {"b": 2}},
        expected={"a": 99, "b": 2},
        msg="Three inputs with overlap should succeed with last value winning",
    ),
    # $$REMOVE as field value
    ExpressionTestCase(
        "remove_field_value",
        expression={"$mergeObjects": ["$obj", {"a": "$$REMOVE"}]},
        doc={"obj": {"a": 1, "b": 2}},
        expected={"a": 1, "b": 2},
        msg="$$REMOVE as field value should succeed: key omitted from literal, original preserved",
    ),
    # Array expression input
    ExpressionTestCase(
        "array_expression_input",
        expression={"$mergeObjects": [["$doc1", "$doc2"]]},
        doc={"doc1": {"a": 1}, "doc2": {"b": 2}},
        expected={"a": 1, "b": 2},
        msg="Nested array of field references should succeed and merge",
    ),
    # Composite array path
    ExpressionTestCase(
        "composite_array_path",
        expression={"$mergeObjects": "$a.b"},
        doc={"a": [{"b": {"x": 1}}, {"b": {"y": 2}}]},
        expected={"x": 1, "y": 2},
        msg="Composite array path should succeed and merge array of resolved objects",
    ),
    # Array index paths
    ExpressionTestCase(
        "array_index_on_object_key",
        expression={"$mergeObjects": ["$a.0", {"extra": 1}]},
        doc={"a": {"0": {"x": 1}}},
        expected={"x": 1, "extra": 1},
        msg="Numeric index on object should succeed and resolve to object key",
    ),
    ExpressionTestCase(
        "array_index_on_array",
        expression={"$mergeObjects": ["$a.0", {"extra": 1}]},
        doc={"a": [{"x": 1}, {"x": 2}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Numeric index on array should error with invalid type since it resolves to []",
    ),
    # $$ROOT and $$CURRENT
    ExpressionTestCase(
        "root_adds_field",
        expression={"$mergeObjects": ["$$ROOT", {"extra": 1}]},
        doc={"_id": 1, "a": 1},
        expected={"_id": 1, "a": 1, "extra": 1},
        msg="$$ROOT merged with literal should succeed and add new field",
    ),
    ExpressionTestCase(
        "root_overwrite",
        expression={"$mergeObjects": ["$$ROOT", {"a": 99}]},
        doc={"_id": 1, "a": 1},
        expected={"_id": 1, "a": 99},
        msg="Literal after $$ROOT should succeed and overwrite existing field",
    ),
    ExpressionTestCase(
        "literal_then_root",
        expression={"$mergeObjects": [{"a": 99, "b": 2}, "$$ROOT"]},
        doc={"_id": 1, "a": 1},
        expected={"a": 1, "b": 2, "_id": 1},
        msg="$$ROOT after literal should succeed and override literal values",
    ),
    ExpressionTestCase(
        "current_equivalence",
        expression={"$mergeObjects": ["$$CURRENT", {"extra": 1}]},
        doc={"_id": 1, "a": 1},
        expected={"_id": 1, "a": 1, "extra": 1},
        msg="$$CURRENT should succeed and behave equivalently to $$ROOT",
    ),
    ExpressionTestCase(
        "two_roots",
        expression={"$mergeObjects": ["$$ROOT", "$$ROOT"]},
        doc={"_id": 1, "a": 1},
        expected={"_id": 1, "a": 1},
        msg="Two $$ROOT references should succeed and deduplicate",
    ),
    ExpressionTestCase(
        "root_id_overwrite",
        expression={"$mergeObjects": ["$$ROOT", {"_id": "new"}]},
        doc={"_id": 1, "a": 1},
        expected={"_id": "new", "a": 1},
        msg="Literal _id after $$ROOT should succeed and overwrite _id",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_REF_TESTS))
def test_mergeObjects_field_ref(collection, test):
    """Test $mergeObjects with field references and inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result,
        expected=test.expected if test.error_code is None else None,
        error_code=test.error_code,
        msg=test.msg,
    )


def test_mergeObjects_large_many_fields(collection):
    """Test $mergeObjects with 50+ fields per document."""
    doc1 = {f"a{i}": i for i in range(50)}
    doc2 = {f"b{i}": i for i in range(50)}
    result = execute_expression(collection, {"$mergeObjects": [doc1, doc2]})
    expected = {**doc1, **doc2}
    assert_expression_result(
        result,
        expected=expected,
        msg="Merging two 50-field documents should succeed with all 100 fields",
    )


def test_mergeObjects_many_small_docs(collection):
    """Test $mergeObjects with 20+ small documents."""
    docs = [{f"k{i}": i} for i in range(20)]
    result = execute_expression(collection, {"$mergeObjects": docs})
    expected = {f"k{i}": i for i in range(20)}
    assert_expression_result(
        result, expected=expected, msg="Merging 20 small documents should succeed with all keys"
    )
