"""Tests for aggregate command collation alternate and maxVariable sub-field rejection."""

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

# Property [Alternate and MaxVariable Type and Value Errors]: non-string types
# for alternate or maxVariable produce TYPE_MISMATCH_ERROR, and invalid string
# values produce BAD_VALUE_ERROR.
COLLATION_ALTERNATE_MAXVARIABLE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "alternate_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": 1},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int32 alternate",
    ),
    CommandTestCase(
        "alternate_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 alternate",
    ),
    CommandTestCase(
        "alternate_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double alternate",
    ),
    CommandTestCase(
        "alternate_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 alternate",
    ),
    CommandTestCase(
        "alternate_type_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean alternate",
    ),
    CommandTestCase(
        "alternate_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": ["shifted"]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array alternate",
    ),
    CommandTestCase(
        "alternate_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": {"value": "shifted"}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject object alternate",
    ),
    CommandTestCase(
        "alternate_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId alternate",
    ),
    CommandTestCase(
        "alternate_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime alternate",
    ),
    CommandTestCase(
        "alternate_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp alternate",
    ),
    CommandTestCase(
        "alternate_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": Binary(b"x")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary alternate",
    ),
    CommandTestCase(
        "alternate_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex alternate",
    ),
    CommandTestCase(
        "alternate_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code alternate",
    ),
    CommandTestCase(
        "alternate_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject CodeWithScope alternate",
    ),
    CommandTestCase(
        "alternate_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey alternate",
    ),
    CommandTestCase(
        "alternate_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey alternate",
    ),
    CommandTestCase(
        "alternate_invalid_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject empty string alternate",
    ),
    CommandTestCase(
        "alternate_invalid_wrong_case_Shifted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": "Shifted"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject wrong-case alternate Shifted",
    ),
    CommandTestCase(
        "alternate_invalid_wrong_case_NON_IGNORABLE",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": "Non-Ignorable"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject wrong-case alternate Non-Ignorable",
    ),
    CommandTestCase(
        "alternate_invalid_nonsense",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "alternate": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject nonsense alternate value",
    ),
    CommandTestCase(
        "maxvariable_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": 1},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int32 maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": ["punct"]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": {"value": "punct"}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject object maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {
                "locale": "en",
                "maxVariable": datetime(2021, 1, 1, tzinfo=timezone.utc),
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": Binary(b"x")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject CodeWithScope maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey maxVariable",
    ),
    CommandTestCase(
        "maxvariable_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey maxVariable",
    ),
    CommandTestCase(
        "maxvariable_invalid_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject empty string maxVariable",
    ),
    CommandTestCase(
        "maxvariable_invalid_wrong_case_Punct",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": "Punct"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject wrong-case maxVariable Punct",
    ),
    CommandTestCase(
        "maxvariable_invalid_wrong_case_Space",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": "Space"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject wrong-case maxVariable Space",
    ),
    CommandTestCase(
        "maxvariable_invalid_nonsense",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "maxVariable": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject nonsense maxVariable value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_ALTERNATE_MAXVARIABLE_TYPE_ERROR_TESTS))
def test_aggregate_collation_alternate_rejection(database_client, collection, test):
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
