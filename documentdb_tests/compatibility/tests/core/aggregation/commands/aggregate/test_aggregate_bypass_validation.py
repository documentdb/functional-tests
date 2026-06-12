"""Tests for aggregate command bypassDocumentValidation parameter."""

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    DOCUMENT_VALIDATION_FAILURE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import SiblingCollection
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT64_ZERO,
)

_BYPASS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name"],
        "properties": {"name": {"bsonType": "string"}},
    }
}

# Property [bypassDocumentValidation Acceptance]: valid
# bypassDocumentValidation values are accepted and control whether document
# validation is enforced.
AGGREGATE_BYPASS_VALIDATION_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bypass_true_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": True,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should silently accept bypassDocumentValidation=True without $out",
    ),
    CommandTestCase(
        "bypass_false_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": False,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should silently accept bypassDocumentValidation=False without $out",
    ),
    CommandTestCase(
        "bypass_null_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": None,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should silently accept bypassDocumentValidation=null without $out",
    ),
    CommandTestCase(
        "bypass_omitted_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should silently accept omitted bypassDocumentValidation without $out",
    ),
    CommandTestCase(
        "bypass_int32_1_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": 1,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept int32 1 for bypassDocumentValidation",
    ),
    CommandTestCase(
        "bypass_int32_0_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": 0,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept int32 0 for bypassDocumentValidation",
    ),
    CommandTestCase(
        "bypass_int64_1_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": Int64(1),
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Int64 1 for bypassDocumentValidation",
    ),
    CommandTestCase(
        "bypass_double_1_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": 1.0,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept double 1.0 for bypassDocumentValidation",
    ),
    CommandTestCase(
        "bypass_double_0_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": DOUBLE_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept double 0.0 for bypassDocumentValidation",
    ),
    CommandTestCase(
        "bypass_decimal128_1_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": Decimal128("1"),
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128('1') for bypassDocumentValidation",
    ),
    CommandTestCase(
        "bypass_decimal128_0_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": DECIMAL128_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128('0') for bypassDocumentValidation",
    ),
    *[
        CommandTestCase(
            f"bypass_{tid}_no_out",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "bypassDocumentValidation": v,
            },
            expected={"ok": Eq(1.0)},
            msg=f"aggregate should accept {tid} for bypassDocumentValidation",
        )
        for tid, val in [
            ("nan", FLOAT_NAN),
            ("neg_nan", FLOAT_NEGATIVE_NAN),
            ("decimal128_nan", DECIMAL128_NAN),
            ("decimal128_neg_nan", DECIMAL128_NEGATIVE_NAN),
            ("infinity", FLOAT_INFINITY),
            ("neg_infinity", FLOAT_NEGATIVE_INFINITY),
            ("decimal128_infinity", DECIMAL128_INFINITY),
            ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
        ]
    ],
    CommandTestCase(
        "bypass_neg_zero_double_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept -0.0 for bypassDocumentValidation",
    ),
    CommandTestCase(
        "bypass_neg_zero_decimal128_no_out",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128('-0') for bypassDocumentValidation",
    ),
    # Truthy values bypass validation with $out.
    CommandTestCase(
        "bypass_true_out",
        docs=[{"_id": 1, "no_name": True}],
        siblings=[
            SiblingCollection(suffix="_validated_target", validator=_BYPASS_VALIDATOR),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": f"{ctx.collection}_validated_target"}],
            "cursor": {},
            "bypassDocumentValidation": True,
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([]), "id": Eq(INT64_ZERO)},
        },
        msg="aggregate should bypass validation with True and $out",
    ),
    CommandTestCase(
        "bypass_int32_1_out",
        docs=[{"_id": 1, "no_name": True}],
        siblings=[
            SiblingCollection(suffix="_validated_target", validator=_BYPASS_VALIDATOR),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": f"{ctx.collection}_validated_target"}],
            "cursor": {},
            "bypassDocumentValidation": 1,
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([]), "id": Eq(INT64_ZERO)},
        },
        msg="aggregate should bypass validation with int32 1 and $out",
    ),
    *[
        CommandTestCase(
            f"bypass_{tid}_out",
            docs=[{"_id": 1, "no_name": True}],
            siblings=[
                SiblingCollection(suffix="_validated_target", validator=_BYPASS_VALIDATOR),
            ],
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [{"$out": f"{ctx.collection}_validated_target"}],
                "cursor": {},
                "bypassDocumentValidation": v,
            },
            expected={
                "ok": Eq(1.0),
                "cursor": {"firstBatch": Eq([]), "id": Eq(INT64_ZERO)},
            },
            msg=f"aggregate should bypass validation with {tid} (truthy) and $out",
        )
        for tid, val in [
            ("nan", FLOAT_NAN),
            ("neg_nan", FLOAT_NEGATIVE_NAN),
            ("decimal128_nan", DECIMAL128_NAN),
            ("decimal128_neg_nan", DECIMAL128_NEGATIVE_NAN),
            ("infinity", FLOAT_INFINITY),
            ("neg_infinity", FLOAT_NEGATIVE_INFINITY),
            ("decimal128_infinity", DECIMAL128_INFINITY),
            ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
        ]
    ],
    CommandTestCase(
        "bypass_true_merge",
        docs=[{"_id": 1, "no_name": True}],
        siblings=[
            SiblingCollection(suffix="_validated_target", validator=_BYPASS_VALIDATOR),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": f"{ctx.collection}_validated_target"}}],
            "cursor": {},
            "bypassDocumentValidation": True,
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([]), "id": Eq(INT64_ZERO)},
        },
        msg="aggregate should bypass validation with True and $merge",
    ),
]

# Property [bypassDocumentValidation Validation Enforcement]: when falsy with
# $out or $merge, invalid documents cause a document validation failure.
AGGREGATE_BYPASS_VALIDATION_ENFORCEMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bypass_false_out_invalid",
        docs=[{"_id": 1, "no_name": True}],
        siblings=[
            SiblingCollection(suffix="_validated_target", validator=_BYPASS_VALIDATOR),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": f"{ctx.collection}_validated_target"}],
            "cursor": {},
            "bypassDocumentValidation": False,
        },
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="aggregate should reject invalid documents with bypassDocumentValidation=False and $out",  # noqa: E501
    ),
    CommandTestCase(
        "bypass_false_merge_invalid",
        docs=[{"_id": 1, "no_name": True}],
        siblings=[
            SiblingCollection(suffix="_validated_target", validator=_BYPASS_VALIDATOR),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": f"{ctx.collection}_validated_target"}}],
            "cursor": {},
            "bypassDocumentValidation": False,
        },
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="aggregate should reject invalid documents with bypassDocumentValidation=False and $merge",  # noqa: E501
    ),
    CommandTestCase(
        "bypass_int32_0_out_invalid",
        docs=[{"_id": 1, "no_name": True}],
        siblings=[
            SiblingCollection(suffix="_validated_target", validator=_BYPASS_VALIDATOR),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": f"{ctx.collection}_validated_target"}],
            "cursor": {},
            "bypassDocumentValidation": 0,
        },
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="aggregate should enforce validation with bypassDocumentValidation=0 and $out",
    ),
    CommandTestCase(
        "bypass_double_neg_zero_out_invalid",
        docs=[{"_id": 1, "no_name": True}],
        siblings=[
            SiblingCollection(suffix="_validated_target", validator=_BYPASS_VALIDATOR),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": f"{ctx.collection}_validated_target"}],
            "cursor": {},
            "bypassDocumentValidation": DOUBLE_NEGATIVE_ZERO,
        },
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="aggregate should enforce validation with bypassDocumentValidation=-0.0 and $out",
    ),
    CommandTestCase(
        "bypass_decimal128_0_out_invalid",
        docs=[{"_id": 1, "no_name": True}],
        siblings=[
            SiblingCollection(suffix="_validated_target", validator=_BYPASS_VALIDATOR),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": f"{ctx.collection}_validated_target"}],
            "cursor": {},
            "bypassDocumentValidation": DECIMAL128_ZERO,
        },
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="aggregate should enforce validation with bypassDocumentValidation=Decimal128('0') and $out",  # noqa: E501
    ),
]

# Property [bypassDocumentValidation Rejection]: all non-boolean, non-numeric
# BSON types produce a type mismatch error.
AGGREGATE_BYPASS_VALIDATION_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"bypass_reject_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "bypassDocumentValidation": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"aggregate should reject {tid} for bypassDocumentValidation",
    )
    for tid, val in [
        ("string", "hello"),
        ("array", [1, 2]),
        ("document", {"a": 1}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex(".*")),
        ("binary", Binary(b"hello")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

AGGREGATE_BYPASS_VALIDATION_TESTS = (
    AGGREGATE_BYPASS_VALIDATION_ACCEPTANCE_TESTS
    + AGGREGATE_BYPASS_VALIDATION_ENFORCEMENT_TESTS
    + AGGREGATE_BYPASS_VALIDATION_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_BYPASS_VALIDATION_TESTS))
def test_aggregate_bypass_validation(database_client, collection, test):
    """Test aggregate bypassDocumentValidation acceptance and rejection."""
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
