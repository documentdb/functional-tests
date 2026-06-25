"""Tests for collMod dryRun behavior."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    CANNOT_CONVERT_INDEX_TO_UNIQUE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, NotExists
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_ZERO,
)

# Property [dryRun Truthy Checks Without Converting]: a bool true or any numeric
# type that coerces to true (any nonzero value, including negatives, NaN, and
# Infinity) runs the unique conversion as a dry run, validating without
# converting, so the result omits the unique_new echo that an actual conversion
# would produce.
COLLMOD_DRY_RUN_TRUTHY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"truthy_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1", prepareUnique=True)],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": True},
            "dryRun": v,
        },
        expected={"ok": Eq(1.0), "unique_new": NotExists(), "unique_old": NotExists()},
        msg=f"collMod should treat a {tid} dryRun as a dry run that checks without converting",
    )
    for tid, val in [
        ("bool_true", True),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("int32_negative", -1),
        ("double_negative", -2.0),
        ("decimal128_negative", Decimal128("-1")),
        ("float_nan", FLOAT_NAN),
        ("decimal128_nan", DECIMAL128_NAN),
        ("float_infinity", FLOAT_INFINITY),
        ("decimal128_infinity", DECIMAL128_INFINITY),
        ("float_negative_infinity", FLOAT_NEGATIVE_INFINITY),
        ("decimal128_negative_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [dryRun Falsy Performs Conversion]: a bool false, any numeric zero
# (including negative zero), or null disables dry run, so the unique conversion
# is actually performed and the result echoes unique_new true.
COLLMOD_DRY_RUN_FALSY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"falsy_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1", prepareUnique=True)],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": True},
            "dryRun": v,
        },
        expected={"ok": Eq(1.0), "unique_new": Eq(True)},
        msg=f"collMod should treat a {tid} dryRun as disabled and perform the conversion",
    )
    for tid, val in [
        ("bool_false", False),
        ("int32_zero", 0),
        ("int64_zero", INT64_ZERO),
        ("double_zero", DOUBLE_ZERO),
        ("double_negative_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_zero", DECIMAL128_ZERO),
        ("decimal128_negative_zero", DECIMAL128_NEGATIVE_ZERO),
        ("null", None),
    ]
]

# Property [dryRun Falsy Accepted Without A Unique Conversion]: a falsy dryRun
# (bool false, numeric zero, or null) is accepted with ok:1.0 even when no unique
# conversion is present (whether paired with a non-unique modification such as
# hidden, which still applies, or with no index modification at all), unlike a
# truthy dryRun, which requires a unique conversion.
COLLMOD_DRY_RUN_FALSY_NO_CONVERSION_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"falsy_no_conversion_hidden_{tid}",
            indexes=[IndexModel([("a", 1)], name="a_1")],
            docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
            command=lambda ctx, v=val: {
                "collMod": ctx.collection,
                "index": {"name": "a_1", "hidden": True},
                "dryRun": v,
            },
            expected={"ok": Eq(1.0), "hidden_old": Eq(False), "hidden_new": Eq(True)},
            msg=f"collMod should accept a {tid} dryRun on a non-unique modification and apply it",
        )
        for tid, val in [
            ("bool_false", False),
            ("int32_zero", 0),
            ("null", None),
        ]
    ],
    *[
        CommandTestCase(
            f"falsy_no_conversion_no_index_{tid}",
            indexes=[IndexModel([("a", 1)], name="a_1")],
            docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
            command=lambda ctx, v=val: {
                "collMod": ctx.collection,
                "dryRun": v,
            },
            expected={"ok": Eq(1.0)},
            msg=f"collMod should accept a {tid} dryRun with no index modification present",
        )
        for tid, val in [
            ("bool_false", False),
            ("int32_zero", 0),
        ]
    ],
]

COLLMOD_DRY_RUN_SUCCESS_TESTS: list[CommandTestCase] = (
    COLLMOD_DRY_RUN_TRUTHY_TESTS
    + COLLMOD_DRY_RUN_FALSY_TESTS
    + COLLMOD_DRY_RUN_FALSY_NO_CONVERSION_TESTS
)

# Property [dryRun Type Rejection]: a dryRun value that is neither a bool nor a
# numeric type is rejected as a type mismatch, since only bool and numeric
# values can be coerced to the dry-run flag.
COLLMOD_DRY_RUN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1", prepareUnique=True)],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": True},
            "dryRun": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} dryRun value as a type mismatch",
    )
    for tid, val in [
        ("string", "yes"),
        ("array", [True]),
        ("object", {"x": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [dryRun Truthy Requires A Unique Conversion]: a truthy dryRun with no
# index modification, or with an index modification that is not a unique
# conversion (an identify-only index or a non-unique change such as hidden), is
# rejected as an invalid option because dry run mode validates a pending unique
# conversion and has nothing to check otherwise.
COLLMOD_DRY_RUN_REQUIRES_CONVERSION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "no_index_modification",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx: {"collMod": ctx.collection, "dryRun": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a truthy dryRun with no index modification as an "
        "invalid option",
    ),
    CommandTestCase(
        "identify_only_index",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1"},
            "dryRun": True,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a truthy dryRun with an identify-only index as an "
        "invalid option",
    ),
    CommandTestCase(
        "non_unique_modification",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": True},
            "dryRun": True,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a truthy dryRun with a non-unique index "
        "modification as an invalid option",
    ),
]

# Property [dryRun Truthy Reports Conversion Violations]: a truthy dryRun on a
# unique conversion of an index whose documents contain duplicate values is
# rejected because the conversion would violate uniqueness, reported without
# converting.
COLLMOD_DRY_RUN_DUPLICATE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unique_conversion_with_duplicates",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        # Documents that share a value on the indexed field so a unique
        # conversion has a violation to report.
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 1}],
        setup=lambda coll: execute_command(
            coll,
            {"collMod": coll.name, "index": {"name": "a_1", "prepareUnique": True}},
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": True},
            "dryRun": True,
        },
        error_code=CANNOT_CONVERT_INDEX_TO_UNIQUE_ERROR,
        msg="collMod should reject a dry-run unique conversion that has duplicate "
        "values without converting",
    ),
]

COLLMOD_DRY_RUN_ERROR_TESTS: list[CommandTestCase] = (
    COLLMOD_DRY_RUN_TYPE_ERROR_TESTS
    + COLLMOD_DRY_RUN_REQUIRES_CONVERSION_ERROR_TESTS
    + COLLMOD_DRY_RUN_DUPLICATE_ERROR_TESTS
)

COLLMOD_DRY_RUN_TESTS: list[CommandTestCase] = (
    COLLMOD_DRY_RUN_SUCCESS_TESTS + COLLMOD_DRY_RUN_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_DRY_RUN_TESTS))
def test_collMod_dry_run(database_client, collection, test):
    """Test collMod dryRun behavior."""
    collection = test.prepare(database_client, collection)
    if test.setup:
        test.setup(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
