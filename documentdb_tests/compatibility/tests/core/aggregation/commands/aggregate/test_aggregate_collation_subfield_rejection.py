"""Tests for aggregate command collation sub-field rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

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

# Property [Collation Locale Rejection]: invalid types and values for the
# locale sub-field are rejected.
AGGREGATE_COLLATION_LOCALE_REJECTION_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"collation_reject_locale_type_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "collation": {"locale": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"aggregate should reject {tid} type for collation locale",
        )
        for tid, val in [
            ("int", 1),
            ("int64", Int64(1)),
            ("double", 1.0),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", ["en"]),
            ("document", {"a": 1}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"en")),
            ("regex", Regex("en")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "collation_reject_locale_null",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": None},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="aggregate should reject null locale as equivalent to missing",
    ),
    CommandTestCase(
        "collation_reject_missing_locale",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"strength": 1},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="aggregate should reject collation with missing locale field",
    ),
    CommandTestCase(
        "collation_reject_empty_locale",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject empty string locale",
    ),
    CommandTestCase(
        "collation_reject_invalid_locale",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "invalid_locale"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject invalid locale value",
    ),
    CommandTestCase(
        "collation_reject_underscore_fr_fr",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "fr_FR"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject underscore region code for locales that do not support it",
    ),
    CommandTestCase(
        "collation_reject_hyphen_locale",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en-US"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject hyphen separator in locale",
    ),
]

# Property [Collation Strength Rejection]: invalid types and out-of-range
# values for the strength sub-field are rejected.
AGGREGATE_COLLATION_STRENGTH_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_reject_strength_0",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 0},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject strength 0 as invalid enumeration value",
    ),
    CommandTestCase(
        "collation_reject_strength_6",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 6},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject strength value greater than 5",
    ),
    CommandTestCase(
        "collation_reject_strength_negative",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": -1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative strength value",
    ),
    CommandTestCase(
        "collation_reject_strength_string",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": "high"},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject string type for strength",
    ),
    CommandTestCase(
        "collation_reject_strength_bool",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean type for strength",
    ),
    CommandTestCase(
        "collation_reject_strength_array",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": [1]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array type for strength",
    ),
    CommandTestCase(
        "collation_reject_strength_nan",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": FLOAT_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject NaN strength as invalid enumeration value",
    ),
    CommandTestCase(
        "collation_reject_strength_neg_nan",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": FLOAT_NEGATIVE_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative NaN strength",
    ),
    CommandTestCase(
        "collation_reject_strength_decimal128_nan",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": DECIMAL128_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Decimal128 NaN strength",
    ),
    CommandTestCase(
        "collation_reject_strength_decimal128_neg_nan",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": DECIMAL128_NEGATIVE_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Decimal128 negative NaN strength",
    ),
    CommandTestCase(
        "collation_reject_strength_infinity",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": FLOAT_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject positive infinity strength",
    ),
    CommandTestCase(
        "collation_reject_strength_neg_infinity",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": FLOAT_NEGATIVE_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative infinity strength",
    ),
    CommandTestCase(
        "collation_reject_strength_decimal128_infinity",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": DECIMAL128_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Decimal128 infinity strength",
    ),
    CommandTestCase(
        "collation_reject_strength_decimal128_neg_infinity",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": DECIMAL128_NEGATIVE_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Decimal128 negative infinity strength",
    ),
]

# Property [Collation Other Sub-field Rejection]: invalid values for
# backwards, caseFirst, alternate, and maxVariable are rejected.
AGGREGATE_COLLATION_OTHER_SUBFIELD_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_reject_backwards_null",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject null for backwards (unique among boolean fields)",
    ),
    CommandTestCase(
        "collation_reject_casefirst_wrong_case",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "Upper"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject case-sensitive invalid caseFirst value",
    ),
    CommandTestCase(
        "collation_reject_alternate_invalid",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject invalid alternate value",
    ),
    CommandTestCase(
        "collation_reject_maxvariable_invalid",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject invalid maxVariable value",
    ),
]

# Property [Collation Unknown Field Rejection]: unrecognized fields in the
# collation document are rejected.
AGGREGATE_COLLATION_UNKNOWN_FIELD_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_reject_unknown_field",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject unknown fields in collation document",
    ),
    CommandTestCase(
        "collation_reject_unknown_field_case_sensitive",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "Strength": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject wrong-case field name as unknown field",
    ),
]

AGGREGATE_COLLATION_SUBFIELD_REJECTION_TESTS = (
    AGGREGATE_COLLATION_LOCALE_REJECTION_TESTS
    + AGGREGATE_COLLATION_STRENGTH_REJECTION_TESTS
    + AGGREGATE_COLLATION_OTHER_SUBFIELD_REJECTION_TESTS
    + AGGREGATE_COLLATION_UNKNOWN_FIELD_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_COLLATION_SUBFIELD_REJECTION_TESTS))
def test_aggregate_collation_subfield_rejection(database_client, collection, test):
    """Test aggregate collation sub-field rejection."""
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
