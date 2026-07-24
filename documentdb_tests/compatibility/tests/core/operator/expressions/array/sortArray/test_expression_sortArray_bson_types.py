"""
BSON type and mixed type sorting tests for $sortArray expression.

Tests sorting arrays containing various BSON types (by value and by document
field), mixed types (lexicographic BSON ordering, including cross-type object
and array elements), numeric boundary values, documents with missing sort
fields, special values (Decimal128 NaN, numeric equivalence, negative zero,
Unicode codepoint order), and valid sortBy type variants (int/double/int64/
decimal128, 1 and -1).
"""

from datetime import datetime, timezone
from uuid import UUID

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
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Literal-path parity]: representative cases from each group below
# also run through the literal-value path (not just via inserted documents),
# and are appended to ALL_TESTS below so they also get insert coverage.
LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="sort_int64_asc",
        expression={
            "$sortArray": {
                "input": {"$literal": [Int64(30), Int64(10), Int64(20)]},
                "sortBy": 1,
            }
        },
        expected=[Int64(10), Int64(20), Int64(30)],
        msg="Should sort Int64 values ascending",
    ),
    ExpressionTestCase(
        id="mixed_numbers_and_strings_asc",
        expression={
            "$sortArray": {
                "input": {"$literal": [20, 4, "Gratis", 6, 21, 5]},
                "sortBy": 1,
            }
        },
        expected=[4, 5, 6, 20, 21, "Gratis"],
        msg="Should sort numbers before strings",
    ),
    ExpressionTestCase(
        id="int32_boundaries",
        expression={
            "$sortArray": {
                "input": {"$literal": [0, INT32_MAX, INT32_MIN]},
                "sortBy": 1,
            }
        },
        expected=[INT32_MIN, 0, INT32_MAX],
        msg="Should sort INT32 boundary values correctly",
    ),
    ExpressionTestCase(
        id="sort_docs_by_int64_field",
        expression={
            "$sortArray": {
                "input": {"$literal": [{"v": Int64(30)}, {"v": Int64(10)}, {"v": Int64(20)}]},
                "sortBy": {"v": 1},
            }
        },
        expected=[{"v": Int64(10)}, {"v": Int64(20)}, {"v": Int64(30)}],
        msg="Should sort documents by Int64 field ascending",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_sortArray_bson_literal(collection, test):
    """Test $sortArray BSON types with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [BSON type ordering by value]: each BSON value type sorts
# correctly within its own type — Int64/Decimal128/datetime/ObjectId/bool/
# Timestamp/Binary(+subtype)/Regex/UUID — with values compared meaningfully
# rather than by memory/insertion order.
BSON_VALUE_SORT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="sort_int64_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Int64(30), Int64(10), Int64(20)]},
        expected=[Int64(10), Int64(20), Int64(30)],
        msg="Should sort Int64 values ascending",
    ),
    ExpressionTestCase(
        id="sort_decimal128_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Decimal128("3.14"), Decimal128("1.5"), Decimal128("2.7")]},
        expected=[Decimal128("1.5"), Decimal128("2.7"), Decimal128("3.14")],
        msg="Should sort Decimal128 values ascending",
    ),
    ExpressionTestCase(
        id="sort_datetime_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={
            "arr": [
                datetime(2024, 3, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 2, 1, tzinfo=timezone.utc),
            ]
        },
        expected=[
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 2, 1, tzinfo=timezone.utc),
            datetime(2024, 3, 1, tzinfo=timezone.utc),
        ],
        msg="Should sort datetime values ascending",
    ),
    ExpressionTestCase(
        id="sort_objectid_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={
            "arr": [
                ObjectId("000000000000000000000003"),
                ObjectId("000000000000000000000001"),
                ObjectId("000000000000000000000002"),
            ]
        },
        expected=[
            ObjectId("000000000000000000000001"),
            ObjectId("000000000000000000000002"),
            ObjectId("000000000000000000000003"),
        ],
        msg="Should sort ObjectId values ascending",
    ),
    ExpressionTestCase(
        id="sort_bool_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [True, False, True, False]},
        expected=[False, False, True, True],
        msg="Should sort booleans ascending (false < true)",
    ),
    ExpressionTestCase(
        id="sort_timestamp_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Timestamp(3, 0), Timestamp(1, 0), Timestamp(2, 0)]},
        expected=[Timestamp(1, 0), Timestamp(2, 0), Timestamp(3, 0)],
        msg="Should sort Timestamp values ascending",
    ),
    ExpressionTestCase(
        id="sort_binary_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Binary(b"\x03"), Binary(b"\x01"), Binary(b"\x02")]},
        expected=[b"\x01", b"\x02", b"\x03"],
        msg="Should sort Binary values ascending",
    ),
    ExpressionTestCase(
        id="sort_binary_subtype_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Binary(b"\x03", 128), Binary(b"\x01", 128), Binary(b"\x02", 128)]},
        expected=[Binary(b"\x01", 128), Binary(b"\x02", 128), Binary(b"\x03", 128)],
        msg="Should sort Binary with subtype preserved ascending",
    ),
    ExpressionTestCase(
        id="sort_regex_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Regex("c.*"), Regex("a.*"), Regex("b.*")]},
        expected=[Regex("a.*"), Regex("b.*"), Regex("c.*")],
        msg="Should sort Regex values ascending by pattern",
    ),
    ExpressionTestCase(
        id="sort_uuid_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={
            "arr": [
                Binary.from_uuid(UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")),
                Binary.from_uuid(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
                Binary.from_uuid(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
            ]
        },
        expected=[
            Binary.from_uuid(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
            Binary.from_uuid(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
            Binary.from_uuid(UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")),
        ],
        msg="Should sort UUID binary values ascending",
    ),
]

# Property [Canonical cross-type ordering]: when an array mixes multiple BSON
# types, elements sort by the canonical BSON type order first, then by value
# within a type. Per docs, whole-array sort is lexicographic.
# BSON order: MinKey < null < numbers < string < object < array <
#             binary < objectId < bool < date < timestamp < regex < MaxKey
MIXED_TYPE_SORT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="mixed_numbers_and_strings_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [20, 4, "Gratis", 6, 21, 5]},
        expected=[4, 5, 6, 20, 21, "Gratis"],
        msg="Should sort numbers before strings",
    ),
    ExpressionTestCase(
        id="mixed_bool_and_numbers_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [True, 1, False, 0]},
        expected=[0, 1, False, True],
        msg="Should sort numbers before booleans",
    ),
    ExpressionTestCase(
        id="mixed_minkey_maxkey_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [MaxKey(), 1, MinKey(), "a"]},
        expected=[MinKey(), 1, "a", MaxKey()],
        msg="MinKey should sort first and MaxKey last per BSON ordering",
    ),
    ExpressionTestCase(
        id="mixed_binary_regex_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Regex("x"), Binary(b"\x01"), ObjectId("000000000000000000000001"), True]},
        expected=[b"\x01", ObjectId("000000000000000000000001"), True, Regex("x")],
        msg="Should follow BSON order: binary < objectId < bool < regex",
    ),
    ExpressionTestCase(
        id="cross_type_number_string_object_array_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [1, [1], {"a": 1}, "1"]},
        expected=[1, "1", {"a": 1}, [1]],
        msg="Canonical type order ascending: numbers < strings < objects < arrays",
    ),
    ExpressionTestCase(
        id="cross_type_number_string_object_array_desc",
        expression={"$sortArray": {"input": "$arr", "sortBy": -1}},
        doc={"arr": [1, [1], {"a": 1}, "1"]},
        expected=[[1], {"a": 1}, "1", 1],
        msg="Canonical type order descending: arrays < objects < strings < numbers",
    ),
    ExpressionTestCase(
        id="array_of_arrays_elementwise",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [[2], [1], [1, 2]]},
        expected=[[1], [1, 2], [2]],
        msg="Array elements sorted element-wise (prefix sorts before longer) — manual B13",
    ),
]

# Property [Missing sort field]: documents or scalars without the specified
# sortBy field sort as equal to each other (per docs), whether some or all
# elements lack the field.
MISSING_FIELD_SORT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="docs_some_missing_field",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": 1}}},
        doc={"arr": [{"a": 3}, {"b": 1}, {"a": 1}]},
        expected=[{"b": 1}, {"a": 1}, {"a": 3}],
        msg="Documents missing sort field should sort before those with it",
    ),
    ExpressionTestCase(
        id="docs_all_missing_field",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": 1}}},
        doc={"arr": [{"b": 3}, {"b": 1}, {"b": 2}]},
        expected=[{"b": 3}, {"b": 1}, {"b": 2}],
        msg="All documents missing sort field should maintain relative order",
    ),
]

# Property [Numeric boundary values]: min/max/±Infinity values for each
# numeric BSON type sort correctly at the extremes, without overflow or
# precision loss affecting order.
BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int32_boundaries",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [0, INT32_MAX, INT32_MIN]},
        expected=[INT32_MIN, 0, INT32_MAX],
        msg="Should sort INT32 boundary values correctly",
    ),
    ExpressionTestCase(
        id="int64_boundaries",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Int64(0), INT64_MAX, INT64_MIN]},
        expected=[INT64_MIN, Int64(0), INT64_MAX],
        msg="Should sort INT64 boundary values correctly",
    ),
    ExpressionTestCase(
        id="infinity_values",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [FLOAT_INFINITY, 0, FLOAT_NEGATIVE_INFINITY]},
        expected=[FLOAT_NEGATIVE_INFINITY, 0, FLOAT_INFINITY],
        msg="Should sort infinity values correctly",
    ),
    ExpressionTestCase(
        id="decimal128_infinity",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [DECIMAL128_INFINITY, Decimal128("0"), DECIMAL128_NEGATIVE_INFINITY]},
        expected=[DECIMAL128_NEGATIVE_INFINITY, Decimal128("0"), DECIMAL128_INFINITY],
        msg="Should sort Decimal128 infinity values correctly",
    ),
]

# Property [Sort by typed field]: sorting by a named document field works
# correctly across every BSON field-value type, including mixed numeric
# types within the same field.
BSON_FIELD_SORT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="sort_docs_by_int64_field",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"v": 1}}},
        doc={"arr": [{"v": Int64(30)}, {"v": Int64(10)}, {"v": Int64(20)}]},
        expected=[{"v": Int64(10)}, {"v": Int64(20)}, {"v": Int64(30)}],
        msg="Should sort documents by Int64 field ascending",
    ),
    ExpressionTestCase(
        id="sort_docs_by_decimal128_field",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"v": 1}}},
        doc={"arr": [{"v": Decimal128("3")}, {"v": Decimal128("1")}, {"v": Decimal128("2")}]},
        expected=[{"v": Decimal128("1")}, {"v": Decimal128("2")}, {"v": Decimal128("3")}],
        msg="Should sort documents by Decimal128 field ascending",
    ),
    ExpressionTestCase(
        id="sort_docs_by_datetime_field",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"v": 1}}},
        doc={
            "arr": [
                {"v": datetime(2024, 3, 1, tzinfo=timezone.utc)},
                {"v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
                {"v": datetime(2024, 2, 1, tzinfo=timezone.utc)},
            ]
        },
        expected=[
            {"v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2024, 2, 1, tzinfo=timezone.utc)},
            {"v": datetime(2024, 3, 1, tzinfo=timezone.utc)},
        ],
        msg="Should sort documents by datetime field ascending",
    ),
    ExpressionTestCase(
        id="sort_docs_by_cross_numeric_types",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"v": 1}}},
        doc={"arr": [{"v": Decimal128("2.5")}, {"v": 1}, {"v": Int64(3)}, {"v": 1.5}]},
        expected=[{"v": 1}, {"v": 1.5}, {"v": Decimal128("2.5")}, {"v": Int64(3)}],
        msg="Should sort documents with mixed numeric field types",
    ),
    ExpressionTestCase(
        id="sort_docs_by_binary_field",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"v": 1}}},
        doc={"arr": [{"v": Binary(b"\x03")}, {"v": Binary(b"\x01")}, {"v": Binary(b"\x02")}]},
        expected=[{"v": b"\x01"}, {"v": b"\x02"}, {"v": b"\x03"}],
        msg="Should sort documents by Binary field ascending",
    ),
    ExpressionTestCase(
        id="sort_docs_by_binary_subtype_field",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"v": 1}}},
        doc={
            "arr": [
                {"v": Binary(b"\x03", 128)},
                {"v": Binary(b"\x01", 128)},
                {"v": Binary(b"\x02", 128)},
            ]
        },
        expected=[
            {"v": Binary(b"\x01", 128)},
            {"v": Binary(b"\x02", 128)},
            {"v": Binary(b"\x03", 128)},
        ],
        msg="Should sort documents by Binary field with subtype preserved",
    ),
    ExpressionTestCase(
        id="sort_docs_by_regex_field",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"v": 1}}},
        doc={"arr": [{"v": Regex("c.*")}, {"v": Regex("a.*")}, {"v": Regex("b.*")}]},
        expected=[{"v": Regex("a.*")}, {"v": Regex("b.*")}, {"v": Regex("c.*")}],
        msg="Should sort documents by Regex field ascending",
    ),
    ExpressionTestCase(
        id="sort_docs_by_minkey_maxkey_field",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"v": 1}}},
        doc={"arr": [{"v": MaxKey()}, {"v": 1}, {"v": MinKey()}]},
        expected=[{"v": MinKey()}, {"v": 1}, {"v": MaxKey()}],
        msg="Should sort documents with MinKey before and MaxKey after all other types",
    ),
    ExpressionTestCase(
        id="sort_docs_by_uuid_field",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"v": 1}}},
        doc={
            "arr": [
                {"v": Binary.from_uuid(UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"))},
                {"v": Binary.from_uuid(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))},
                {"v": Binary.from_uuid(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))},
            ]
        },
        expected=[
            {"v": Binary.from_uuid(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))},
            {"v": Binary.from_uuid(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))},
            {"v": Binary.from_uuid(UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"))},
        ],
        msg="Should sort documents by UUID binary field ascending",
    ),
]

# Property [Special numeric/string values]: Decimal128 NaN sorts first,
# numerically-equivalent cross-type values (including all-zero variants)
# compare equal and preserve stable order, high-precision Decimal128 values
# remain distinguishable, and strings sort by Unicode codepoint.
SPECIAL_VALUE_SORT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nan_decimal128_ascending",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Decimal128("3"), DECIMAL128_NAN, Decimal128("1")]},
        expected=[DECIMAL128_NAN, Decimal128("1"), Decimal128("3")],
        msg="Decimal128 NaN should sort first",
    ),
    ExpressionTestCase(
        id="numeric_equivalence_value",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Int64(2), 1, Decimal128("3"), 2.0]},
        expected=[1, Int64(2), 2.0, Decimal128("3")],
        msg="Numerically equivalent values sort together",
    ),
    ExpressionTestCase(
        id="decimal128_high_precision",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={
            "arr": [
                Decimal128("1.000000000000000000000000000000002"),
                Decimal128("1.000000000000000000000000000000001"),
            ]
        },
        expected=[
            Decimal128("1.000000000000000000000000000000001"),
            Decimal128("1.000000000000000000000000000000002"),
        ],
        msg="Should distinguish high-precision Decimal128 values",
    ),
    ExpressionTestCase(
        id="negative_zero_double",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [1, DOUBLE_NEGATIVE_ZERO, -1]},
        expected=[-1, DOUBLE_NEGATIVE_ZERO, 1],
        msg="Negative zero sorts with zero",
    ),
    ExpressionTestCase(
        id="cross_type_zero_equivalence",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [Decimal128("0"), DOUBLE_NEGATIVE_ZERO, Int64(0)]},
        expected=[Decimal128("0"), DOUBLE_NEGATIVE_ZERO, Int64(0)],
        msg="All-zero values across Decimal128/double/Int64 compare equal and"
        " keep stable (input) order",
    ),
    ExpressionTestCase(
        id="unicode_codepoint",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": ["é", "a", "z"]},
        expected=["a", "z", "é"],
        msg="Should sort by Unicode codepoint",
    ),
]

# Property [Valid sortBy type variants]: sortBy accepts any numeric BSON type
# whose value is exactly 1 or -1 (int, double, Int64, Decimal128), not just a
# plain int literal.
VALID_BSON_SORTBY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="sortby_int_1",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="sortBy int 1 should sort ascending",
    ),
    ExpressionTestCase(
        id="sortby_int_neg1",
        expression={"$sortArray": {"input": "$arr", "sortBy": -1}},
        doc={"arr": [3, 1, 2]},
        expected=[3, 2, 1],
        msg="sortBy int -1 should sort descending",
    ),
    ExpressionTestCase(
        id="sortby_double_1",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1.0}},
        doc={"arr": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="sortBy 1.0 should sort ascending",
    ),
    ExpressionTestCase(
        id="sortby_double_neg1",
        expression={"$sortArray": {"input": "$arr", "sortBy": -1.0}},
        doc={"arr": [3, 1, 2]},
        expected=[3, 2, 1],
        msg="sortBy -1.0 should sort descending",
    ),
    ExpressionTestCase(
        id="sortby_int64_1",
        expression={"$sortArray": {"input": "$arr", "sortBy": Int64(1)}},
        doc={"arr": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="sortBy Int64(1) should sort ascending",
    ),
    ExpressionTestCase(
        id="sortby_int64_neg1",
        expression={"$sortArray": {"input": "$arr", "sortBy": Int64(-1)}},
        doc={"arr": [3, 1, 2]},
        expected=[3, 2, 1],
        msg="sortBy Int64(-1) should sort descending",
    ),
    ExpressionTestCase(
        id="sortby_decimal128_1",
        expression={"$sortArray": {"input": "$arr", "sortBy": Decimal128("1")}},
        doc={"arr": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="sortBy Decimal128('1') should sort ascending",
    ),
    ExpressionTestCase(
        id="sortby_decimal128_neg1",
        expression={"$sortArray": {"input": "$arr", "sortBy": Decimal128("-1")}},
        doc={"arr": [3, 1, 2]},
        expected=[3, 2, 1],
        msg="sortBy Decimal128('-1') should sort descending",
    ),
]

ALL_TESTS = (
    BSON_VALUE_SORT_TESTS
    + MIXED_TYPE_SORT_TESTS
    + MISSING_FIELD_SORT_TESTS
    + BOUNDARY_TESTS
    + BSON_FIELD_SORT_TESTS
    + SPECIAL_VALUE_SORT_TESTS
    + VALID_BSON_SORTBY_TESTS
    + LITERAL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_sortArray_bson_insert(collection, test):
    """Test $sortArray BSON types with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
