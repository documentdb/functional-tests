"""Aggregation $group stage tests - grouping equivalence rules."""

from __future__ import annotations

import pytest
from bson import SON, Binary, Decimal128, Int64, Regex

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
    INT64_ZERO,
)

# Property [Numeric Grouping Equivalence]: numeric types with the same
# mathematical value (int32, Int64, double, Decimal128) group together into one
# group, and Decimal128 values differing only in trailing zeros are equivalent.
GROUP_NUMERIC_EQUIVALENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="int32_int64_double_decimal128_same_value",
        docs=[
            {"_id": 1, "v": 1},
            {"_id": 2, "v": Int64(1)},
            {"_id": 3, "v": 1.0},
            {"_id": 4, "v": Decimal128("1")},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": 1, "ids": [1, 2, 3, 4]}],
        msg="int32, Int64, double, and Decimal128 of the same value should group together",
    ),
    StageTestCase(
        id="decimal128_trailing_zeros",
        docs=[
            {"_id": 1, "v": Decimal128("1")},
            {"_id": 2, "v": DECIMAL128_TRAILING_ZERO},
            {"_id": 3, "v": Decimal128("1.00")},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": Decimal128("1"), "ids": [1, 2, 3]}],
        msg="Decimal128 values differing only in trailing zeros should group together",
    ),
]

# Property [Numeric Group _id Type]: the output _id type for a numeric group
# is the type of the first document encountered in that group.
GROUP_NUMERIC_ID_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="numeric_group_id_type_is_first_doc_type",
        docs=[
            {"_id": 1, "v": Int64(1)},
            {"_id": 2, "v": 1},
            {"_id": 3, "v": 1.0},
            {"_id": 4, "v": Decimal128("1")},
        ],
        pipeline=[
            {"$group": {"_id": "$v", "count": {"$sum": 1}}},
            {"$project": {"id_type": {"$type": "$_id"}}},
        ],
        expected=[{"_id": Int64(1), "id_type": "long"}],
        msg="Output _id type should be the type of the first document encountered",
    ),
]

# Property [Zero Variant Equivalence]: all zero representations (-0.0, 0.0,
# int32(0), Int64(0), Decimal128("0"), Decimal128("-0")) produce one group.
GROUP_ZERO_EQUIVALENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="all_zero_variants_group_together",
        docs=[
            {"_id": 1, "v": DOUBLE_NEGATIVE_ZERO},
            {"_id": 2, "v": DOUBLE_ZERO},
            {"_id": 3, "v": 0},
            {"_id": 4, "v": INT64_ZERO},
            {"_id": 5, "v": DECIMAL128_ZERO},
            {"_id": 6, "v": DECIMAL128_NEGATIVE_ZERO},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": DOUBLE_NEGATIVE_ZERO, "ids": [1, 2, 3, 4, 5, 6]}],
        msg="All zero variants should produce one group",
    ),
]

# Property [Infinity Equivalence]: positive infinity from float and Decimal128
# group together, and negative infinity from float and Decimal128 group
# together.
GROUP_INFINITY_EQUIVALENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="positive_infinity_variants",
        docs=[
            {"_id": 1, "v": FLOAT_INFINITY},
            {"_id": 2, "v": DECIMAL128_INFINITY},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": FLOAT_INFINITY, "ids": [1, 2]}],
        msg="float inf and Decimal128 Infinity should group together",
    ),
    StageTestCase(
        id="negative_infinity_variants",
        docs=[
            {"_id": 1, "v": FLOAT_NEGATIVE_INFINITY},
            {"_id": 2, "v": DECIMAL128_NEGATIVE_INFINITY},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": FLOAT_NEGATIVE_INFINITY, "ids": [1, 2]}],
        msg="float -inf and Decimal128 -Infinity should group together",
    ),
]

# Property [Boolean vs Numeric Distinction]: boolean values do not group with
# their numeric equivalents - True and 1 produce separate groups, as do False
# and 0.
GROUP_BOOL_NUMERIC_DISTINCTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="true_not_equal_to_one",
        docs=[
            {"_id": 1, "v": True},
            {"_id": 2, "v": 1},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": True, "ids": [1]},
            {"_id": 1, "ids": [2]},
        ],
        msg="True and 1 should produce separate groups",
    ),
    StageTestCase(
        id="false_not_equal_to_zero",
        docs=[
            {"_id": 1, "v": False},
            {"_id": 2, "v": 0},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": False, "ids": [1]},
            {"_id": 0, "ids": [2]},
        ],
        msg="False and 0 should produce separate groups",
    ),
]

# Property [String Comparison Strictness]: string grouping is case-sensitive,
# does not apply Unicode normalization, and treats null bytes as significant.
GROUP_STRING_COMPARISON_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="case_sensitive_strings",
        docs=[
            {"_id": 1, "v": "a"},
            {"_id": 2, "v": "A"},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": "A", "ids": [2]},
            {"_id": "a", "ids": [1]},
        ],
        msg="String comparison should be case-sensitive",
    ),
    StageTestCase(
        id="no_unicode_normalization",
        docs=[
            {"_id": 1, "v": "\u00e9"},
            {"_id": 2, "v": "e\u0301"},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": "\u00e9", "ids": [1]},
            {"_id": "e\u0301", "ids": [2]},
        ],
        msg="Precomposed and decomposed Unicode forms should produce separate groups",
    ),
    StageTestCase(
        id="null_bytes_significant",
        docs=[
            {"_id": 1, "v": "a\x00b"},
            {"_id": 2, "v": "a"},
            {"_id": 3, "v": "ab"},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": "a", "ids": [2]},
            {"_id": "a\x00b", "ids": [1]},
            {"_id": "ab", "ids": [3]},
        ],
        msg="Null bytes should be significant in string grouping",
    ),
]

# Property [Regex Flag Distinction]: regex values with the same pattern but
# different flags produce separate groups.
GROUP_REGEX_FLAG_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="regex_different_flags_separate",
        docs=[
            {"_id": 1, "v": Regex("abc", "i")},
            {"_id": 2, "v": Regex("abc", "m")},
            {"_id": 3, "v": Regex("abc", "i")},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": Regex("abc", "i"), "ids": [1, 3]},
            {"_id": Regex("abc", "m"), "ids": [2]},
        ],
        msg="Regex with same pattern but different flags should produce separate groups",
    ),
]

# Property [Binary Subtype Distinction]: binary values with the same data but
# different subtypes produce separate groups.
GROUP_BINARY_SUBTYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="binary_different_subtypes_separate",
        docs=[
            {"_id": 1, "v": Binary(b"hello", 0)},
            {"_id": 2, "v": Binary(b"hello", 5)},
            {"_id": 3, "v": Binary(b"hello", 0)},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": b"hello", "ids": [1, 3]},
            {"_id": Binary(b"hello", 5), "ids": [2]},
        ],
        msg="Binary with same data but different subtypes should produce separate groups",
    ),
]

# Property [Compound _id Field Order]: in a compound _id, field order matters
# for grouping - documents with the same fields in different order produce
# separate groups.
GROUP_COMPOUND_FIELD_ORDER_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="compound_id_field_order_matters",
        docs=[
            {"_id": 1, "v": SON([("a", 1), ("b", 2)])},
            {"_id": 2, "v": SON([("b", 2), ("a", 1)])},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": {"a": 1, "b": 2}, "ids": [1]},
            {"_id": {"b": 2, "a": 1}, "ids": [2]},
        ],
        msg="Compound _id with different field order should produce separate groups",
    ),
]

# Property [Array Grouping Equivalence]: numeric equivalence applies within
# arrays, boolean vs numeric distinction applies within arrays, and array
# element order matters for grouping.
GROUP_ARRAY_EQUIVALENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="array_numeric_equivalence",
        docs=[
            {"_id": 1, "v": [1]},
            {"_id": 2, "v": [Int64(1)]},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": [1], "ids": [1, 2]}],
        msg="Arrays with numerically equivalent elements should group together",
    ),
    StageTestCase(
        id="array_bool_vs_numeric_distinct",
        docs=[
            {"_id": 1, "v": [True]},
            {"_id": 2, "v": [1]},
            {"_id": 3, "v": [False]},
            {"_id": 4, "v": [0]},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": [0], "ids": [4]},
            {"_id": [1], "ids": [2]},
            {"_id": [False], "ids": [3]},
            {"_id": [True], "ids": [1]},
        ],
        msg="[True] and [1], [False] and [0] should produce separate groups",
    ),
    StageTestCase(
        id="array_element_order_matters",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": [2, 1]},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": [1, 2], "ids": [1]},
            {"_id": [2, 1], "ids": [2]},
        ],
        msg="Arrays with different element order should produce separate groups",
    ),
]

# Property [IEEE 754 Precision Boundary]: when a double cannot exactly
# represent an Int64 value, they form separate groups; a double that rounds to
# a representable value groups with the integer matching that rounded value.
GROUP_IEEE754_PRECISION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="double_int64_precision_loss_separate",
        docs=[
            {"_id": 1, "v": DOUBLE_FROM_INT64_MAX},
            {"_id": 2, "v": INT64_MAX},
        ],
        pipeline=[{"$group": {"_id": "$v", "count": {"$sum": 1}}}],
        expected=[
            {"_id": INT64_MAX, "count": 1},
            {"_id": DOUBLE_FROM_INT64_MAX, "count": 1},
        ],
        msg="Double that cannot exactly represent Int64 max should form a separate group",
    ),
    StageTestCase(
        id="double_rounds_to_nearest_groups_with_int",
        docs=[
            {"_id": 1, "v": float(DOUBLE_MAX_SAFE_INTEGER + 1)},
            {"_id": 2, "v": Int64(DOUBLE_MAX_SAFE_INTEGER)},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": float(DOUBLE_MAX_SAFE_INTEGER), "ids": [1, 2]}],
        msg=(
            "Double that rounds to nearest representable value should group"
            " with the matching integer"
        ),
    ),
]

GROUP_GROUPING_EQUIVALENCE_TESTS = (
    GROUP_NUMERIC_EQUIVALENCE_TESTS
    + GROUP_NUMERIC_ID_TYPE_TESTS
    + GROUP_ZERO_EQUIVALENCE_TESTS
    + GROUP_INFINITY_EQUIVALENCE_TESTS
    + GROUP_BOOL_NUMERIC_DISTINCTION_TESTS
    + GROUP_STRING_COMPARISON_TESTS
    + GROUP_REGEX_FLAG_TESTS
    + GROUP_BINARY_SUBTYPE_TESTS
    + GROUP_COMPOUND_FIELD_ORDER_TESTS
    + GROUP_ARRAY_EQUIVALENCE_TESTS
    + GROUP_IEEE754_PRECISION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_GROUPING_EQUIVALENCE_TESTS))
def test_group_equivalence(collection, test_case: StageTestCase):
    """Test $group stage - grouping equivalence."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
