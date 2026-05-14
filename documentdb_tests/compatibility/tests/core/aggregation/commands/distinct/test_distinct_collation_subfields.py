"""Tests for distinct command collation sub-field validation and behavior."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Strictness: collation (locale)]: the locale sub-field is
# required and validates type and value.
DISTINCT_TYPE_STRICTNESS_COLLATION_LOCALE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_collation_locale_null",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": None},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="distinct should reject collation with null locale",
    ),
    *[
        CommandTestCase(
            f"type_collation_locale_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "collation": {"locale": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct should reject {tid} for collation locale",
        )
        for tid, val in [
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", ["en"]),
            ("object", {"name": "en"}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02")),
            ("regex", Regex("^en")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    *[
        CommandTestCase(
            f"type_collation_locale_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "collation": {"locale": v},
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"distinct should reject {tid} for collation locale",
        )
        for tid, val in [
            ("invalid", "invalid_locale_xyz"),
            ("wrong_case", "EN"),
        ]
    ],
]

# Property [Type Strictness: collation (strength)]: the strength sub-field
# validates type and range.
DISTINCT_TYPE_STRICTNESS_COLLATION_STRENGTH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_collation_strength_one_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept strength value 1 (lower boundary)",
    ),
    CommandTestCase(
        "type_collation_strength_five_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 5},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept strength value 5 (upper boundary)",
    ),
    CommandTestCase(
        "type_collation_strength_int32_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 3},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept int32 strength value 3",
    ),
    CommandTestCase(
        "type_collation_strength_int64_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": Int64(3)},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept Int64 strength value 3",
    ),
    CommandTestCase(
        "type_collation_strength_double_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 3.0},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept double strength value 3.0",
    ),
    CommandTestCase(
        "type_collation_strength_decimal128_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": Decimal128("3")},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept Decimal128 strength value 3",
    ),
    CommandTestCase(
        "type_collation_strength_null_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": None},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept null strength (treated as omitted)",
    ),
    CommandTestCase(
        "type_collation_strength_zero_invalid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 0},
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject strength value 0",
    ),
    CommandTestCase(
        "type_collation_strength_six_invalid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 6},
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject strength value 6",
    ),
    *[
        CommandTestCase(
            f"type_collation_strength_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "collation": {"locale": "en", "strength": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct should reject {tid} for collation strength",
        )
        for tid, val in [
            ("string", "one"),
            ("bool", True),
            ("array", [1]),
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

# Property [Type Strictness: collation (boolean sub-fields)]: the boolean
# sub-fields validate type strictly and have field-specific null handling.
DISTINCT_TYPE_STRICTNESS_COLLATION_BOOL_FIELDS_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"type_collation_{field}_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, f=field, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "collation": {"locale": "en", f: v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct should reject {tid} for collation {field}",
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
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, f=field: {
                "distinct": ctx.collection,
                "key": "x",
                "collation": {"locale": "en", f: None},
            },
            expected={"values": ["a"], "ok": 1.0},
            msg=f"distinct should accept null for collation {field} (treated as omitted)",
        )
        for field in ["caseLevel", "numericOrdering", "normalization"]
    ],
    CommandTestCase(
        "type_collation_backwards_null_rejected",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "backwards": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="distinct should reject null for collation backwards",
    ),
]

# Property [Type Strictness: collation (enum sub-fields)]: the string enum
# sub-fields validate type, value, and field-specific constraints.
DISTINCT_TYPE_STRICTNESS_COLLATION_ENUM_FIELDS_TESTS: list[CommandTestCase] = [
    # caseFirst valid values and constraints
    CommandTestCase(
        "type_collation_casefirst_lower_accepted",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "caseFirst": "lower", "strength": 3},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg='distinct should accept caseFirst "lower" with strength > 2',
    ),
    CommandTestCase(
        "type_collation_casefirst_with_strength_3",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "caseFirst": "upper", "strength": 3},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept caseFirst with strength > 2",
    ),
    CommandTestCase(
        "type_collation_casefirst_with_caselevel",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {
                "locale": "en",
                "caseFirst": "upper",
                "caseLevel": True,
            },
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept caseFirst with caseLevel=true",
    ),
    CommandTestCase(
        "type_collation_casefirst_off_always_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "caseFirst": "off", "strength": 1},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg='distinct should accept caseFirst "off" regardless of strength or caseLevel',
    ),
    CommandTestCase(
        "type_collation_casefirst_requires_caselevel_or_strength",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "caseFirst": "upper", "strength": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject caseFirst without caseLevel=true or strength > 2",
    ),
    # alternate valid values
    CommandTestCase(
        "type_collation_alternate_non_ignorable_accepted",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "alternate": "non-ignorable"},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg='distinct should accept alternate "non-ignorable"',
    ),
    CommandTestCase(
        "type_collation_alternate_shifted_accepted",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "alternate": "shifted"},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg='distinct should accept alternate "shifted"',
    ),
    # maxVariable valid values
    CommandTestCase(
        "type_collation_maxvariable_punct_accepted",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "maxVariable": "punct"},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg='distinct should accept maxVariable "punct"',
    ),
    CommandTestCase(
        "type_collation_maxvariable_space_accepted",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "maxVariable": "space"},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg='distinct should accept maxVariable "space"',
    ),
    # Null acceptance for all enum sub-fields
    *[
        CommandTestCase(
            f"type_collation_{field}_null_accepted",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, f=field: {
                "distinct": ctx.collection,
                "key": "x",
                "collation": {"locale": "en", f: None},
            },
            expected={"values": ["a"], "ok": 1.0},
            msg=f"distinct should accept null for collation {field} (treated as omitted)",
        )
        for field in ["caseFirst", "alternate", "maxVariable"]
    ],
    # Invalid string values (BadValue)
    *[
        CommandTestCase(
            f"type_collation_{field}_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, f=field, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "collation": {"locale": "en", f: v},
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"distinct should reject {tid} for collation {field}",
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
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, f=field, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "collation": {"locale": "en", f: v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct should reject {tid} for collation {field}",
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
DISTINCT_TYPE_STRICTNESS_COLLATION_UNKNOWN_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_collation_unknown_field",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="distinct should reject unknown fields in collation document",
    ),
]

# Property [Collation Behavior: numericOrdering]: numericOrdering=true causes
# numeric strings to be ordered by their numeric value rather than
# lexicographically, affecting both deduplication and result ordering.
DISTINCT_COLLATION_NUMERIC_ORDERING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_numericordering_true_ordering",
        docs=[
            {"_id": 1, "x": "10"},
            {"_id": 2, "x": "2"},
            {"_id": 3, "x": "1"},
            {"_id": 4, "x": "20"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected={"values": ["1", "2", "10", "20"], "ok": 1.0},
        msg="distinct with numericOrdering=true should order numeric strings numerically",
    ),
    CommandTestCase(
        "collation_numericordering_false_ordering",
        docs=[
            {"_id": 1, "x": "10"},
            {"_id": 2, "x": "2"},
            {"_id": 3, "x": "1"},
            {"_id": 4, "x": "20"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "numericOrdering": False},
        },
        expected={"values": ["1", "10", "2", "20"], "ok": 1.0},
        msg="distinct with numericOrdering=false should order strings lexicographically",
    ),
]

# Property [Collation Behavior: alternate]: alternate="shifted" causes
# punctuation and whitespace to be treated as equivalent at primary/secondary
# strength levels, collapsing them during deduplication.
DISTINCT_COLLATION_ALTERNATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_alternate_shifted_dedup",
        docs=[
            {"_id": 1, "x": "abc"},
            {"_id": 2, "x": "a-b-c"},
            {"_id": 3, "x": "a b c"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "alternate": "shifted", "strength": 1},
        },
        expected={"values": ["abc"], "ok": 1.0},
        msg="distinct with alternate=shifted should collapse punctuation/whitespace variants",
    ),
    CommandTestCase(
        "collation_alternate_non_ignorable_preserves",
        docs=[
            {"_id": 1, "x": "abc"},
            {"_id": 2, "x": "a-b-c"},
            {"_id": 3, "x": "a b c"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "alternate": "non-ignorable", "strength": 1},
        },
        expected={"values": ["a b c", "a-b-c", "abc"], "ok": 1.0},
        msg="distinct with alternate=non-ignorable should preserve punctuation distinctions",
    ),
]

# Property [Collation Behavior: maxVariable]: maxVariable controls which
# characters are ignored when alternate="shifted"; "space" ignores only
# whitespace, "punct" ignores both whitespace and punctuation.
DISTINCT_COLLATION_MAX_VARIABLE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_maxvariable_space",
        docs=[
            {"_id": 1, "x": "abc"},
            {"_id": 2, "x": "a bc"},
            {"_id": 3, "x": "a.bc"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "maxVariable": "space",
                "strength": 1,
            },
        },
        expected={"values": ["a.bc", "abc"], "ok": 1.0},
        msg="distinct with maxVariable=space should ignore only whitespace",
    ),
    CommandTestCase(
        "collation_maxvariable_punct",
        docs=[
            {"_id": 1, "x": "abc"},
            {"_id": 2, "x": "a bc"},
            {"_id": 3, "x": "a.bc"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "maxVariable": "punct",
                "strength": 1,
            },
        },
        expected={"values": ["abc"], "ok": 1.0},
        msg="distinct with maxVariable=punct should ignore whitespace and punctuation",
    ),
]

# Property [Collation Behavior: backwards]: backwards=true reverses the
# secondary (accent) comparison direction, affecting result ordering.
DISTINCT_COLLATION_BACKWARDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_backwards_true",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "cot\u00e9"},
            {"_id": 3, "x": "c\u00f4te"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 2, "backwards": True},
        },
        expected={"values": ["cote", "c\u00f4te", "cot\u00e9", "c\u00f4t\u00e9"], "ok": 1.0},
        msg="distinct with backwards=true should reverse accent comparison direction",
    ),
    CommandTestCase(
        "collation_backwards_false",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "cot\u00e9"},
            {"_id": 3, "x": "c\u00f4te"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 2, "backwards": False},
        },
        expected={"values": ["cote", "cot\u00e9", "c\u00f4te", "c\u00f4t\u00e9"], "ok": 1.0},
        msg="distinct with backwards=false should use normal accent comparison direction",
    ),
]

# Property [Collation Behavior: caseFirst]: caseFirst controls whether
# uppercase or lowercase sorts first at the tertiary level.
DISTINCT_COLLATION_CASEFIRST_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_casefirst_upper",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "caseFirst": "upper", "strength": 3},
        },
        expected={"values": ["A", "a", "B", "b"], "ok": 1.0},
        msg="distinct with caseFirst=upper should sort uppercase before lowercase",
    ),
    CommandTestCase(
        "collation_casefirst_lower",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "caseFirst": "lower", "strength": 3},
        },
        expected={"values": ["a", "A", "b", "B"], "ok": 1.0},
        msg="distinct with caseFirst=lower should sort lowercase before uppercase",
    ),
]

DISTINCT_COLLATION_SUBFIELD_TESTS: list[CommandTestCase] = (
    DISTINCT_TYPE_STRICTNESS_COLLATION_LOCALE_TESTS
    + DISTINCT_TYPE_STRICTNESS_COLLATION_STRENGTH_TESTS
    + DISTINCT_TYPE_STRICTNESS_COLLATION_BOOL_FIELDS_TESTS
    + DISTINCT_TYPE_STRICTNESS_COLLATION_ENUM_FIELDS_TESTS
    + DISTINCT_TYPE_STRICTNESS_COLLATION_UNKNOWN_FIELDS_TESTS
    + DISTINCT_COLLATION_NUMERIC_ORDERING_TESTS
    + DISTINCT_COLLATION_ALTERNATE_TESTS
    + DISTINCT_COLLATION_MAX_VARIABLE_TESTS
    + DISTINCT_COLLATION_BACKWARDS_TESTS
    + DISTINCT_COLLATION_CASEFIRST_BEHAVIOR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DISTINCT_COLLATION_SUBFIELD_TESTS))
def test_distinct_collation_subfields(
    database_client: Any, collection: Any, test: CommandTestCase
) -> None:
    """Test distinct command collation sub-field validation and behavior."""
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
