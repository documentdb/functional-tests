"""Tests for aggregate command collation sub-field acceptance."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import DECIMAL128_TWO_AND_HALF

# Property [Collation Sub-field Acceptance]: collation sub-fields accept
# their documented types and values.
AGGREGATE_COLLATION_SUBFIELD_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_locale_case_sensitive",
        docs=[{"_id": 1, "name": "abc"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en"},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])}},
        msg="aggregate should accept lowercase locale (case-sensitive, no trimming)",
    ),
    CommandTestCase(
        "collation_locale_underscore_en_us",
        docs=[{"_id": 1, "name": "abc"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en_US"},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])}},
        msg="aggregate should accept underscore region code en_US",
    ),
    CommandTestCase(
        "collation_locale_underscore_zh_hant",
        docs=[{"_id": 1, "name": "abc"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "zh_Hant"},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])}},
        msg="aggregate should accept underscore region code zh_Hant",
    ),
    CommandTestCase(
        "collation_strength_int32",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}])},
        },
        msg="aggregate should accept int32 strength in range 1-5",
    ),
    CommandTestCase(
        "collation_strength_int64",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": Int64(2)},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}])},
        },
        msg="aggregate should accept Int64 strength",
    ),
    CommandTestCase(
        "collation_strength_double",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2.0},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}])},
        },
        msg="aggregate should accept double strength",
    ),
    CommandTestCase(
        "collation_strength_decimal128",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": Decimal128("2")},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}])},
        },
        msg="aggregate should accept Decimal128 strength",
    ),
    CommandTestCase(
        "collation_strength_null",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": None},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])},
        },
        msg="aggregate should accept null strength and use default (tertiary)",
    ),
    CommandTestCase(
        "collation_strength_double_truncate",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1.5},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}])},
        },
        msg="aggregate should truncate double strength 1.5 toward zero to 1",
    ),
    CommandTestCase(
        "collation_strength_decimal128_bankers",
        docs=[{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": DECIMAL128_TWO_AND_HALF},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}, {"_id": 2, "name": "ABC"}])},
        },
        msg="aggregate should round Decimal128 strength 2.5 to 2 via banker's rounding",
    ),
    *[
        CommandTestCase(
            f"collation_{field.lower()}_{label}",
            docs=[{"_id": 1, "name": "abc"}],
            command=lambda ctx, f=field, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"name": "abc"}}],
                "cursor": {},
                "collation": {"locale": "en", f: v},
            },
            expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])}},
            msg=f"aggregate should accept {field} {label}",
        )
        for field, label, val in [
            ("caseLevel", "true", True),
            ("caseLevel", "false", False),
            ("caseLevel", "null", None),
            ("numericOrdering", "true", True),
            ("numericOrdering", "false", False),
            ("numericOrdering", "null", None),
            ("normalization", "true", True),
            ("normalization", "false", False),
            ("normalization", "null", None),
            ("caseFirst", "upper", "upper"),
            ("caseFirst", "lower", "lower"),
            ("caseFirst", "off", "off"),
            ("caseFirst", "null", None),
            ("alternate", "non_ignorable", "non-ignorable"),
            ("alternate", "shifted", "shifted"),
            ("alternate", "null", None),
            ("maxVariable", "punct", "punct"),
            ("maxVariable", "space", "space"),
            ("maxVariable", "null", None),
        ]
    ],
    CommandTestCase(
        "collation_backwards_true",
        docs=[{"_id": 1, "name": "abc"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en", "backwards": True},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])}},
        msg="aggregate should accept backwards True",
    ),
    CommandTestCase(
        "collation_backwards_false",
        docs=[{"_id": 1, "name": "abc"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en", "backwards": False},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "name": "abc"}])}},
        msg="aggregate should accept backwards False",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_COLLATION_SUBFIELD_ACCEPTANCE_TESTS))
def test_aggregate_collation_subfield_acceptance(database_client, collection, test):
    """Test aggregate collation sub-field acceptance."""
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
