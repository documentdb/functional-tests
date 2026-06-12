"""Tests for aggregate command hint parameter rejection."""

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
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import SiblingCollection
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [Hint Type Rejection]: non-string, non-document BSON types for the
# hint field are rejected.
AGGREGATE_HINT_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_reject_null",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": None,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject null hint as invalid type",
    ),
    CommandTestCase(
        "hint_reject_bool",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": True,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject boolean hint",
    ),
    CommandTestCase(
        "hint_reject_int32",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}, "hint": 42},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject int32 hint",
    ),
    CommandTestCase(
        "hint_reject_int64",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": Int64(1),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject Int64 hint",
    ),
    CommandTestCase(
        "hint_reject_double",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": 3.14,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject double hint",
    ),
    CommandTestCase(
        "hint_reject_decimal128",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": Decimal128("1"),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject Decimal128 hint",
    ),
    CommandTestCase(
        "hint_reject_array",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": [1, 2],
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject array hint",
    ),
    CommandTestCase(
        "hint_reject_binary",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": Binary(b"hello"),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject Binary hint",
    ),
    CommandTestCase(
        "hint_reject_objectid",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": ObjectId(),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject ObjectId hint",
    ),
    CommandTestCase(
        "hint_reject_datetime",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject datetime hint",
    ),
    CommandTestCase(
        "hint_reject_timestamp",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": Timestamp(1, 1),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject Timestamp hint",
    ),
    CommandTestCase(
        "hint_reject_regex",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": Regex(".*"),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject Regex hint",
    ),
    CommandTestCase(
        "hint_reject_code",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": Code("function(){}"),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject Code hint",
    ),
    CommandTestCase(
        "hint_reject_code_with_scope",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": Code("function(){}", {"x": 1}),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject Code with scope hint",
    ),
    CommandTestCase(
        "hint_reject_minkey",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": MinKey(),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject MinKey hint",
    ),
    CommandTestCase(
        "hint_reject_maxkey",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": MaxKey(),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject MaxKey hint",
    ),
]

# Property [Hint String Value Rejection]: invalid string values for the hint
# field are rejected.
AGGREGATE_HINT_STRING_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_reject_empty_string",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}, "hint": ""},
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject empty string hint",
    ),
    CommandTestCase(
        "hint_reject_natural_string",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": "$natural",
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject $natural as a string hint",
    ),
]

# Property [Hint Direction Value Rejection]: invalid direction values in
# document hints are rejected.
AGGREGATE_HINT_DIRECTION_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_reject_direction_zero",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": 0},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject direction value 0 in document hint",
    ),
    CommandTestCase(
        "hint_reject_direction_two",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": 2},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject direction value 2 in document hint",
    ),
    CommandTestCase(
        "hint_reject_direction_fractional",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": 1.5},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject fractional direction value in document hint",
    ),
    CommandTestCase(
        "hint_reject_direction_bool",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": True},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject boolean direction value in document hint",
    ),
    CommandTestCase(
        "hint_reject_direction_null",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": None},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject null direction value in document hint",
    ),
    CommandTestCase(
        "hint_reject_direction_string",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": "asc"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject string direction value in document hint",
    ),
    CommandTestCase(
        "hint_reject_direction_nan",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": FLOAT_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject NaN direction value in document hint",
    ),
    CommandTestCase(
        "hint_reject_direction_neg_nan",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": FLOAT_NEGATIVE_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative NaN direction value in document hint",
    ),
    CommandTestCase(
        "hint_reject_direction_infinity",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": FLOAT_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Infinity direction value in document hint",
    ),
    CommandTestCase(
        "hint_reject_direction_neg_infinity",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"x": FLOAT_NEGATIVE_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative Infinity direction value in document hint",
    ),
    *[
        CommandTestCase(
            f"hint_reject_direction_{tid}",
            docs=[{"_id": 1, "x": 10}],
            indexes=[IndexModel([("x", 1)], name="x_1")],
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "hint": {"x": v},
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"aggregate should reject {tid} direction value in document hint",
        )
        for tid, val in [
            ("array", [1]),
            ("document", {"a": 1}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"data")),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
            ("decimal128_zero", DECIMAL128_ZERO),
            ("decimal128_two", Decimal128("2")),
            ("decimal128_nan", DECIMAL128_NAN),
            ("decimal128_neg_nan", DECIMAL128_NEGATIVE_NAN),
            ("decimal128_infinity", DECIMAL128_INFINITY),
            ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
        ]
    ],
    CommandTestCase(
        "hint_reject_natural_zero",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"$natural": 0},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject $natural with value 0",
    ),
    CommandTestCase(
        "hint_reject_natural_two",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"$natural": 2},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject $natural with value other than 1 or -1",
    ),
]

# Property [Hint Non-Matching Index Rejection]: hints referencing indexes that
# do not exist on the source collection are rejected.
AGGREGATE_HINT_NO_MATCH_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_reject_no_matching_string",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": "nonexistent_index_name",
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject string hint that does not match any index on the collection",
    ),
    CommandTestCase(
        "hint_reject_no_matching_doc",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"y": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject document hint that does not match any index on the collection",
    ),
    CommandTestCase(
        "hint_reject_nonexistent_index",
        docs=[{"_id": 1, "x": 10}],
        siblings=[
            SiblingCollection(
                suffix="_lookup_target",
                docs=[{"_id": 10, "x": 20}],
                indexes=[IndexModel([("x", 1)], name="x_idx")],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": f"{ctx.collection}_lookup_target",
                        "localField": "x",
                        "foreignField": "x",
                        "as": "joined",
                    }
                }
            ],
            "cursor": {},
            "hint": "x_idx",
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject hint for index that exists only on the lookup target",
    ),
]

# Property [Hint Stage Incompatibility]: certain pipeline stages are
# incompatible with specific hint values.
AGGREGATE_HINT_STAGE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_reject_text_index_doc",
        docs=[{"_id": 1, "x": 10, "content": "hello"}],
        indexes=[IndexModel([("content", "text")], name="text_idx")],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": {"content": "text"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject text index document hint as invalid direction",
    ),
    CommandTestCase(
        "hint_reject_text_with_hint",
        docs=[{"_id": 1, "x": 10, "content": "hello world"}],
        indexes=[
            IndexModel([("x", 1)], name="x_1"),
            IndexModel([("content", "text")], name="text_idx"),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"$text": {"$search": "hello"}}}],
            "cursor": {},
            "hint": "x_1",
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject $text combined with any non-empty hint",
    ),
    CommandTestCase(
        "hint_reject_geonear_natural",
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        indexes=[IndexModel([("loc", "2dsphere")])],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": [0, 0]},
                        "distanceField": "dist",
                    }
                }
            ],
            "cursor": {},
            "hint": {"$natural": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject $geoNear combined with $natural hint",
    ),
]

AGGREGATE_HINT_REJECTION_TESTS = (
    AGGREGATE_HINT_TYPE_REJECTION_TESTS
    + AGGREGATE_HINT_STRING_REJECTION_TESTS
    + AGGREGATE_HINT_DIRECTION_REJECTION_TESTS
    + AGGREGATE_HINT_NO_MATCH_REJECTION_TESTS
    + AGGREGATE_HINT_STAGE_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_HINT_REJECTION_TESTS))
def test_aggregate_hint_rejection(database_client, collection, test):
    """Test aggregate hint rejection."""
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
