"""Tests for aggregate command collation caseFirst sub-field rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [caseFirst Constraint Validation]: caseFirst "upper" or "lower"
# requires either caseLevel:true or strength > 2; otherwise BAD_VALUE_ERROR is
# produced. caseFirst "off" is always valid regardless of strength or caseLevel.
COLLATION_CASEFIRST_CONSTRAINT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "casefirst_upper_strength1_no_caselevel_error",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 1,
                "caseFirst": "upper",
                "caseLevel": False,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject caseFirst upper with strength 1 and caseLevel false",
    ),
    CommandTestCase(
        "casefirst_upper_strength2_no_caselevel_error",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 2,
                "caseFirst": "upper",
                "caseLevel": False,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject caseFirst upper with strength 2 and caseLevel false",
    ),
    CommandTestCase(
        "casefirst_lower_strength1_no_caselevel_error",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 1,
                "caseFirst": "lower",
                "caseLevel": False,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject caseFirst lower with strength 1 and caseLevel false",
    ),
    CommandTestCase(
        "casefirst_lower_strength2_no_caselevel_error",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 2,
                "caseFirst": "lower",
                "caseLevel": False,
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject caseFirst lower with strength 2 and caseLevel false",
    ),
    CommandTestCase(
        "casefirst_upper_strength3_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3, "caseFirst": "upper"},
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="aggregate should accept caseFirst upper with strength 3",
    ),
    CommandTestCase(
        "casefirst_lower_strength4_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 4, "caseFirst": "lower"},
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="aggregate should accept caseFirst lower with strength 4",
    ),
    CommandTestCase(
        "casefirst_upper_strength1_caselevel_true_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 1,
                "caseFirst": "upper",
                "caseLevel": True,
            },
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="aggregate should accept caseFirst upper with caseLevel true",
    ),
    CommandTestCase(
        "casefirst_lower_strength2_caselevel_true_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 2,
                "caseFirst": "lower",
                "caseLevel": True,
            },
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="aggregate should accept caseFirst lower with caseLevel true",
    ),
    CommandTestCase(
        "casefirst_off_strength1_no_caselevel_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 1,
                "caseFirst": "off",
                "caseLevel": False,
            },
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="aggregate should accept caseFirst off regardless of strength or caseLevel",
    ),
]

# Property [caseFirst Type Strictness]: non-string types for caseFirst produce
# TYPE_MISMATCH_ERROR, and invalid string values produce BAD_VALUE_ERROR.
COLLATION_CASEFIRST_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "casefirst_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": 1},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int32 caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": ["upper"]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": {"value": "upper"}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject object caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": Binary(b"x")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject CodeWithScope caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey caseFirst",
    ),
    CommandTestCase(
        "casefirst_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey caseFirst",
    ),
    CommandTestCase(
        "casefirst_invalid_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject empty string caseFirst",
    ),
    CommandTestCase(
        "casefirst_invalid_wrong_case_Upper",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "Upper"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject wrong-case caseFirst Upper",
    ),
    CommandTestCase(
        "casefirst_invalid_wrong_case_Lower",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "Lower"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject wrong-case caseFirst Lower",
    ),
    CommandTestCase(
        "casefirst_invalid_wrong_case_OFF",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "OFF"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject wrong-case caseFirst OFF",
    ),
    CommandTestCase(
        "casefirst_invalid_nonsense",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject nonsense caseFirst value",
    ),
]

COLLATION_CASEFIRST_ERROR_TESTS: list[CommandTestCase] = (
    COLLATION_CASEFIRST_CONSTRAINT_TESTS + COLLATION_CASEFIRST_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_CASEFIRST_ERROR_TESTS))
def test_aggregate_collation_casefirst_rejection(database_client, collection, test):
    """Test aggregate command collation sub-field rejection."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
