"""Tests for aggregate command let parameter rejection."""

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
from bson.son import SON

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    LET_FIELD_REFERENCE_IN_VALUE_ERROR,
    LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
    LET_SYSTEM_VARIABLE_OVERRIDE_ERROR,
    LET_UNDEFINED_VARIABLE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Let Rejection]: invalid let parameter types and variable
# definitions are rejected.
AGGREGATE_LET_REJECTION_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"let_reject_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "let": v,
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"aggregate should reject {tid} type for let parameter",
        )
        for tid, val in [
            ("string", "hello"),
            ("int", 42),
            ("bool", True),
            ("array", [1, 2]),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("binary", Binary(b"data")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "let_reject_empty_name",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject empty variable name in let",
    ),
    CommandTestCase(
        "let_reject_subsequent_exclamation",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"a!b": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject variable name with invalid subsequent character '!'",
    ),
    CommandTestCase(
        "let_reject_subsequent_dot",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"a.b": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject variable name with invalid subsequent character '.'",
    ),
    CommandTestCase(
        "let_reject_subsequent_hyphen",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"a-b": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject variable name with invalid subsequent character '-'",
    ),
    CommandTestCase(
        "let_reject_uppercase_first_char",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"Avar": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject variable name starting with ASCII uppercase",
    ),
    CommandTestCase(
        "let_reject_digit_first_char",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"1abc": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject variable name starting with digit",
    ),
    CommandTestCase(
        "let_reject_underscore_first_char",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"_abc": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject variable name starting with underscore",
    ),
    CommandTestCase(
        "let_reject_dollar_first_char",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"$abc": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject variable name starting with dollar sign",
    ),
    CommandTestCase(
        "let_reject_forward_reference",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$b"}}],
            "cursor": {},
            "let": SON([("a", "$$b"), ("b", 10)]),
        },
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="aggregate should reject forward references to later-defined let variables",
    ),
    CommandTestCase(
        "let_reject_field_reference",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"myVar": "$x"},
        },
        error_code=LET_FIELD_REFERENCE_IN_VALUE_ERROR,
        msg="aggregate should reject field references in let variable value expressions",
    ),
    CommandTestCase(
        "let_reject_now_in_value",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"myVar": "$$NOW"},
        },
        error_code=LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
        msg="aggregate should reject $$NOW in let variable value expressions",
    ),
    CommandTestCase(
        "let_reject_cluster_time_in_value",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"myVar": "$$CLUSTER_TIME"},
        },
        error_code=LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
        msg="aggregate should reject $$CLUSTER_TIME in let variable value expressions",
    ),
    CommandTestCase(
        "let_reject_override_now",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"NOW": 1},
        },
        error_code=LET_SYSTEM_VARIABLE_OVERRIDE_ERROR,
        msg="aggregate should reject overriding system variable NOW in let",
    ),
    CommandTestCase(
        "let_reject_override_cluster_time",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"CLUSTER_TIME": 1},
        },
        error_code=LET_SYSTEM_VARIABLE_OVERRIDE_ERROR,
        msg="aggregate should reject overriding system variable CLUSTER_TIME in let",
    ),
    CommandTestCase(
        "let_reject_override_root",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"ROOT": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject overriding system variable ROOT in let",
    ),
    CommandTestCase(
        "let_reject_override_remove",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"REMOVE": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject overriding system variable REMOVE in let",
    ),
    CommandTestCase(
        "let_reject_expr_error_propagates",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": {"myVar": {"$divide": [1, 0]}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should propagate expression errors in let values even if unused",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_LET_REJECTION_TESTS))
def test_aggregate_let_rejection(database_client, collection, test):
    """Test aggregate let parameter rejection."""
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
