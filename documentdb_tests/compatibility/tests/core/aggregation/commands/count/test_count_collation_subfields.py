"""Tests for count command collation sub-field validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [Type Strictness: collation (strength)]: the strength sub-field
# validates type and range.
COUNT_TYPE_STRICTNESS_COLLATION_STRENGTH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_collation_strength_int32_valid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": 3},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept int32 strength value 3",
    ),
    CommandTestCase(
        "type_collation_strength_int64_valid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": Int64(3)},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept Int64 strength value 3",
    ),
    CommandTestCase(
        "type_collation_strength_double_valid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": 3.0},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept whole-number double strength value",
    ),
    CommandTestCase(
        "type_collation_strength_decimal128_valid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": Decimal128("3")},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept Decimal128 strength value 3",
    ),
    CommandTestCase(
        "type_collation_strength_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": None},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept null for strength (treated as default)",
    ),
    CommandTestCase(
        "type_collation_strength_fractional_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": 2.5},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept fractional double 2.5 for strength (floor to 2)",
    ),
    CommandTestCase(
        "type_collation_strength_one_min_valid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept strength 1 (minimum valid value)",
    ),
    CommandTestCase(
        "type_collation_strength_five_max_valid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": 5},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept strength 5 (maximum valid value)",
    ),
    CommandTestCase(
        "type_collation_strength_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": 0},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject strength 0",
    ),
    CommandTestCase(
        "type_collation_strength_six",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": 6},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject strength 6 (above max)",
    ),
    CommandTestCase(
        "type_collation_strength_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": -1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject negative strength value",
    ),
    CommandTestCase(
        "type_collation_strength_fractional_floor_to_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": 0.9},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject strength 0.9 (floor to 0, then invalid)",
    ),
    CommandTestCase(
        "type_collation_strength_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": FLOAT_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject NaN for strength (coerces to 0, then invalid)",
    ),
    CommandTestCase(
        "type_collation_strength_neg_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": FLOAT_NEGATIVE_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject -NaN double for strength",
    ),
    CommandTestCase(
        "type_collation_strength_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": DECIMAL128_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject NaN Decimal128 for strength",
    ),
    CommandTestCase(
        "type_collation_strength_decimal128_neg_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": DECIMAL128_NEGATIVE_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject -NaN Decimal128 for strength",
    ),
    CommandTestCase(
        "type_collation_strength_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": FLOAT_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject Infinity for strength (coerces to int32 max, then invalid)",
    ),
    CommandTestCase(
        "type_collation_strength_neg_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": FLOAT_NEGATIVE_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject -Infinity double for strength",
    ),
    CommandTestCase(
        "type_collation_strength_decimal128_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": DECIMAL128_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject Infinity Decimal128 for strength",
    ),
    CommandTestCase(
        "type_collation_strength_decimal128_neg_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": DECIMAL128_NEGATIVE_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject -Infinity Decimal128 for strength",
    ),
    *[
        CommandTestCase(
            f"type_collation_strength_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "count": ctx.collection,
                "collation": {"locale": "en", "strength": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"count should reject {tid} for collation strength",
        )
        for tid, val in [
            ("string", "3"),
            ("bool", True),
            ("array", [3]),
            ("object", {"v": 3}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02")),
            ("regex", Regex("^abc")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [Type Strictness: collation (boolean sub-fields)]: the boolean
# sub-fields validate type strictly and have field-specific null handling.
COUNT_TYPE_STRICTNESS_COLLATION_BOOL_FIELDS_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"type_collation_{field}_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, f=field, v=val: {
                "count": ctx.collection,
                "collation": {"locale": "en", f: v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"count should reject {tid} for collation {field}",
        )
        for field in ["caseLevel", "numericOrdering", "backwards", "normalization"]
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.0),
            ("decimal128", Decimal128("1")),
            ("string", "true"),
            ("array", [True]),
            ("object", {"a": True}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02")),
            ("regex", Regex("^abc")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    # Null handling: caseLevel, numericOrdering, normalization accept null;
    # backwards rejects null.
    *[
        CommandTestCase(
            f"type_collation_{field}_null_accepted",
            docs=[{"_id": 1}],
            command=lambda ctx, f=field: {
                "count": ctx.collection,
                "collation": {"locale": "en", f: None},
            },
            expected={"n": 1, "ok": 1.0},
            msg=f"count should accept null for collation {field} (treated as omitted)",
        )
        for field in ["caseLevel", "numericOrdering", "normalization"]
    ],
    CommandTestCase(
        "type_collation_backwards_null_rejected",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "backwards": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject null for collation backwards",
    ),
]

# Property [Type Strictness: collation (enum sub-fields)]: the string enum
# sub-fields validate type, value, and field-specific constraints.
COUNT_TYPE_STRICTNESS_COLLATION_ENUM_FIELDS_TESTS: list[CommandTestCase] = [
    # caseFirst valid values and constraints
    CommandTestCase(
        "type_collation_casefirst_lower_accepted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "caseFirst": "lower", "strength": 3},
        },
        expected={"n": 1, "ok": 1.0},
        msg='count should accept caseFirst "lower" with strength > 2',
    ),
    CommandTestCase(
        "type_collation_casefirst_with_strength_3",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "caseFirst": "upper", "strength": 3},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept caseFirst with strength > 2",
    ),
    CommandTestCase(
        "type_collation_casefirst_with_caselevel",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {
                "locale": "en",
                "caseFirst": "upper",
                "caseLevel": True,
            },
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept caseFirst with caseLevel=true",
    ),
    CommandTestCase(
        "type_collation_casefirst_off_always_valid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "caseFirst": "off", "strength": 1},
        },
        expected={"n": 1, "ok": 1.0},
        msg='count should accept caseFirst "off" regardless of strength or caseLevel',
    ),
    CommandTestCase(
        "type_collation_casefirst_requires_caselevel_or_strength",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "caseFirst": "upper", "strength": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject caseFirst without caseLevel=true or strength > 2",
    ),
    # alternate valid values
    CommandTestCase(
        "type_collation_alternate_non_ignorable_accepted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "alternate": "non-ignorable"},
        },
        expected={"n": 1, "ok": 1.0},
        msg='count should accept alternate "non-ignorable"',
    ),
    CommandTestCase(
        "type_collation_alternate_shifted_accepted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "alternate": "shifted"},
        },
        expected={"n": 1, "ok": 1.0},
        msg='count should accept alternate "shifted"',
    ),
    # maxVariable valid values
    CommandTestCase(
        "type_collation_maxvariable_punct_accepted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "maxVariable": "punct"},
        },
        expected={"n": 1, "ok": 1.0},
        msg='count should accept maxVariable "punct"',
    ),
    CommandTestCase(
        "type_collation_maxvariable_space_accepted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "maxVariable": "space"},
        },
        expected={"n": 1, "ok": 1.0},
        msg='count should accept maxVariable "space"',
    ),
    # Null acceptance for all enum sub-fields
    *[
        CommandTestCase(
            f"type_collation_{field}_null_accepted",
            docs=[{"_id": 1}],
            command=lambda ctx, f=field: {
                "count": ctx.collection,
                "collation": {"locale": "en", f: None},
            },
            expected={"n": 1, "ok": 1.0},
            msg=f"count should accept null for collation {field} (treated as omitted)",
        )
        for field in ["caseFirst", "alternate", "maxVariable"]
    ],
    # Invalid string values (BadValue)
    *[
        CommandTestCase(
            f"type_collation_{field}_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, f=field, v=val: {
                "count": ctx.collection,
                "collation": {"locale": "en", f: v},
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"count should reject {tid} for collation {field}",
        )
        for field, tid, val in [
            ("caseFirst", "invalid", "invalid"),
            ("caseFirst", "empty", ""),
            ("caseFirst", "wrong_case", "Upper"),
            ("alternate", "invalid", "invalid"),
            ("alternate", "empty", ""),
            ("alternate", "wrong_case", "Shifted"),
            ("maxVariable", "invalid", "invalid"),
            ("maxVariable", "empty", ""),
            ("maxVariable", "wrong_case", "Punct"),
        ]
    ],
    # Non-string type rejection (TypeMismatch) for all enum sub-fields
    *[
        CommandTestCase(
            f"type_collation_{field}_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, f=field, v=val: {
                "count": ctx.collection,
                "collation": {"locale": "en", f: v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"count should reject {tid} for collation {field}",
        )
        for field in ["caseFirst", "alternate", "maxVariable"]
        for tid, val in [
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1, 2]),
            ("object", {"a": 1}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02")),
            ("regex", Regex("^abc")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [Type Strictness: collation (unknown fields)]: unknown fields in the
# collation document produce an UnrecognizedCommandField error.
COUNT_TYPE_STRICTNESS_COLLATION_UNKNOWN_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_collation_unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="count should reject unknown fields in collation document",
    ),
]

# Property [Collation Behavior: numericOrdering]: numericOrdering=true causes
# numeric strings to be compared by their numeric value rather than
# lexicographically.
COUNT_COLLATION_NUMERIC_ORDERING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_numericordering_true",
        docs=[{"_id": 1, "s": "2"}, {"_id": 2, "s": "10"}, {"_id": 3, "s": "1"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$gt": "2"}},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count with numericOrdering=true should compare '10' > '2' numerically",
    ),
    CommandTestCase(
        "collation_numericordering_false",
        docs=[{"_id": 1, "s": "2"}, {"_id": 2, "s": "10"}, {"_id": 3, "s": "1"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$gt": "2"}},
            "collation": {"locale": "en", "numericOrdering": False},
        },
        expected={"n": 0, "ok": 1.0},
        msg="count with numericOrdering=false should compare '10' < '2' lexicographically",
    ),
]

# Property [Collation Behavior: alternate]: alternate="shifted" causes
# punctuation and whitespace to be ignored at primary/secondary strength levels.
COUNT_COLLATION_ALTERNATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_alternate_shifted_ignores_punctuation",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "a-b-c"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": "abc"},
            "collation": {"locale": "en", "alternate": "shifted", "strength": 1},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with alternate=shifted should ignore punctuation at strength 1",
    ),
    CommandTestCase(
        "collation_alternate_non_ignorable_respects_punctuation",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "a-b-c"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": "abc"},
            "collation": {"locale": "en", "alternate": "non-ignorable", "strength": 1},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count with alternate=non-ignorable should respect punctuation",
    ),
]

# Property [Collation Behavior: maxVariable]: maxVariable controls which
# characters are ignored when alternate="shifted"; "space" ignores only
# whitespace, "punct" ignores both whitespace and punctuation.
COUNT_COLLATION_MAX_VARIABLE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_maxvariable_space",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "a bc"}, {"_id": 3, "s": "a.bc"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": "abc"},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "maxVariable": "space",
                "strength": 1,
            },
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with maxVariable=space should ignore only whitespace",
    ),
    CommandTestCase(
        "collation_maxvariable_punct",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "a bc"}, {"_id": 3, "s": "a.bc"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": "abc"},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "maxVariable": "punct",
                "strength": 1,
            },
        },
        expected={"n": 3, "ok": 1.0},
        msg="count with maxVariable=punct should ignore whitespace and punctuation",
    ),
]

# Property [Collation Behavior: backwards]: backwards=true reverses the
# secondary (accent) comparison direction.
COUNT_COLLATION_BACKWARDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_backwards_true",
        docs=[
            {"_id": 1, "s": "cote"},
            {"_id": 2, "s": "cot\u00e9"},
            {"_id": 3, "s": "c\u00f4te"},
            {"_id": 4, "s": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$gt": "cot\u00e9"}},
            "collation": {"locale": "en", "strength": 2, "backwards": True},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count with backwards=true should reverse accent comparison direction",
    ),
    CommandTestCase(
        "collation_backwards_false",
        docs=[
            {"_id": 1, "s": "cote"},
            {"_id": 2, "s": "cot\u00e9"},
            {"_id": 3, "s": "c\u00f4te"},
            {"_id": 4, "s": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$gt": "cot\u00e9"}},
            "collation": {"locale": "en", "strength": 2, "backwards": False},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with backwards=false should use normal accent comparison direction",
    ),
]

# Property [Collation Behavior: caseFirst]: caseFirst controls whether
# uppercase or lowercase sorts first at the tertiary level.
COUNT_COLLATION_CASEFIRST_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_casefirst_upper",
        docs=[{"_id": 1, "s": "a"}, {"_id": 2, "s": "A"}, {"_id": 3, "s": "b"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$gt": "A"}},
            "collation": {"locale": "en", "caseFirst": "upper", "strength": 3},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with caseFirst=upper should sort uppercase before lowercase",
    ),
    CommandTestCase(
        "collation_casefirst_lower",
        docs=[{"_id": 1, "s": "a"}, {"_id": 2, "s": "A"}, {"_id": 3, "s": "b"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$gt": "A"}},
            "collation": {"locale": "en", "caseFirst": "lower", "strength": 3},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count with caseFirst=lower should sort lowercase before uppercase",
    ),
]

COUNT_COLLATION_SUBFIELD_TESTS: list[CommandTestCase] = (
    COUNT_TYPE_STRICTNESS_COLLATION_STRENGTH_TESTS
    + COUNT_TYPE_STRICTNESS_COLLATION_BOOL_FIELDS_TESTS
    + COUNT_TYPE_STRICTNESS_COLLATION_ENUM_FIELDS_TESTS
    + COUNT_TYPE_STRICTNESS_COLLATION_UNKNOWN_FIELDS_TESTS
    + COUNT_COLLATION_NUMERIC_ORDERING_TESTS
    + COUNT_COLLATION_ALTERNATE_TESTS
    + COUNT_COLLATION_MAX_VARIABLE_TESTS
    + COUNT_COLLATION_BACKWARDS_TESTS
    + COUNT_COLLATION_CASEFIRST_BEHAVIOR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_COLLATION_SUBFIELD_TESTS))
def test_count_collation_subfields(database_client, collection, test):
    """Test count command collation sub-field validation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
