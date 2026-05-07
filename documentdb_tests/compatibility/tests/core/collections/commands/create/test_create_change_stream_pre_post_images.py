"""Tests for the create command changeStreamPreAndPostImages parameter."""

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
    INVALID_OPTIONS_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [ChangeStreamPreAndPostImages Acceptance]: enabled:true succeeds on
# regular, capped, and clustered collections; enabled:false is a no-op; null
# top-level is treated as omitted.
CREATE_CSPI_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="enabled_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        expected={"ok": 1.0},
        msg="enabled:true on regular collection should succeed",
    ),
    CommandTestCase(
        id="enabled_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "changeStreamPreAndPostImages": {"enabled": False},
        },
        expected={"ok": 1.0},
        msg="enabled:false is a no-op and should succeed",
    ),
    CommandTestCase(
        id="null_top_level",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "changeStreamPreAndPostImages": None,
        },
        expected={"ok": 1.0},
        msg="null top-level is treated as omitted",
    ),
]

# Property [ChangeStreamPreAndPostImages Compatibility]: the option is
# compatible with capped, clustered, validator, collation, and storageEngine.
CREATE_CSPI_COMPATIBILITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="compatible_with_capped",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        expected={"ok": 1.0},
        msg="Compatible with capped collections",
    ),
    CommandTestCase(
        id="compatible_with_clustered",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        expected={"ok": 1.0},
        msg="Compatible with clustered collections",
    ),
    CommandTestCase(
        id="compatible_with_validator",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$exists": True}},
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        expected={"ok": 1.0},
        msg="Compatible with validator",
    ),
    CommandTestCase(
        id="compatible_with_collation",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en"},
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        expected={"ok": 1.0},
        msg="Compatible with collation",
    ),
    CommandTestCase(
        id="compatible_with_storage_engine",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "storageEngine": {"wiredTiger": {"configString": ""}},
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        expected={"ok": 1.0},
        msg="Compatible with storageEngine",
    ),
    CommandTestCase(
        id="view_with_enabled_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "changeStreamPreAndPostImages": {"enabled": False},
        },
        expected={"ok": 1.0},
        msg="view + enabled:false should succeed (only enabled:true errors)",
    ),
]

# Property [ChangeStreamPreAndPostImages Top-Level Type Strictness]: non-document
# types for the top-level field produce TYPE_MISMATCH_ERROR.
CREATE_CSPI_TOP_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"non_document_{tid}",
        command=lambda ctx, v=val, t=tid: {
            "create": f"{ctx.collection}_custom",
            "changeStreamPreAndPostImages": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{tid} type should fail",
    )
    for tid, val in [
        ("string", "yes"),
        ("int", 1),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1]),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [ChangeStreamPreAndPostImages Enabled Field Validation]: missing or
# null enabled produces MISSING_FIELD_ERROR; non-bool enabled produces
# TYPE_MISMATCH_ERROR; unknown sub-fields produce UNRECOGNIZED_COMMAND_FIELD_ERROR.
CREATE_CSPI_ENABLED_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="missing_enabled",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "changeStreamPreAndPostImages": {},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="missing enabled field should fail",
    ),
    CommandTestCase(
        id="enabled_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "changeStreamPreAndPostImages": {"enabled": None},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="enabled:null is treated as missing",
    ),
    *[
        CommandTestCase(
            id=f"enabled_non_bool_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "changeStreamPreAndPostImages": {"enabled": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"non-bool enabled ({tid}) should fail",
        )
        for tid, val in [
            ("string", "yes"),
            ("int", 1),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("array", [1]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        id="unknown_sub_field",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "changeStreamPreAndPostImages": {"enabled": True, "extra": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="unknown fields in document should fail",
    ),
]

# Property [ChangeStreamPreAndPostImages Collection Type Restriction]: views
# with enabled:true and timeseries with any value produce INVALID_OPTIONS_ERROR.
CREATE_CSPI_COLLECTION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="view_enabled_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="view + enabled:true should fail",
    ),
    CommandTestCase(
        id="timeseries_enabled_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="timeseries + enabled:true should fail",
    ),
    CommandTestCase(
        id="timeseries_enabled_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "changeStreamPreAndPostImages": {"enabled": False},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="timeseries + enabled:false should also fail",
    ),
]

CREATE_CSPI_TESTS: list[CommandTestCase] = (
    CREATE_CSPI_ACCEPTANCE_TESTS
    + CREATE_CSPI_COMPATIBILITY_TESTS
    + CREATE_CSPI_TOP_LEVEL_TYPE_ERROR_TESTS
    + CREATE_CSPI_ENABLED_FIELD_ERROR_TESTS
    + CREATE_CSPI_COLLECTION_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_CSPI_TESTS))
def test_create_change_stream_pre_post_images(database_client, collection, test):
    """Test create command change stream pre post images behavior."""
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
