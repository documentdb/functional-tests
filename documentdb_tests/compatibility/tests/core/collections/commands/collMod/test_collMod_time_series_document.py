"""Tests for collMod time series document acceptance and rejection."""

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
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    TimeseriesCollection,
    ViewCollection,
)

# Property [Timeseries Document Acceptance]: on a time series collection the
# `timeseries` document is accepted, with the empty document and null both
# treated as no-ops.
COLLMOD_TS_DOC_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_document",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "timeseries": {}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an empty timeseries document as a no-op",
    ),
    CommandTestCase(
        "null_document",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "timeseries": None},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null timeseries document as a no-op",
    ),
]

# Property [Timeseries Type Rejection]: a non-object timeseries value is
# rejected with a TypeMismatch error, and an array is not unwrapped into a
# document.
COLLMOD_TS_DOC_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"doc_type_{tid}",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "timeseries": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} timeseries value as the wrong type",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [{"granularity": "seconds"}]),
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

# Property [Timeseries Unknown Sub-Field Rejection]: an unrecognized sub-field
# inside the timeseries document is rejected, including the creation-only
# timeField and metaField sub-fields that are not modifiable through collMod.
COLLMOD_TS_DOC_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"unknown_{fid}",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx, sub=subdoc: {"collMod": ctx.collection, "timeseries": sub},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg=f"collMod should reject an unknown {fid} sub-field in the timeseries document",
    )
    for fid, subdoc in [
        ("arbitrary", {"bogus": 1}),
        ("time_field", {"timeField": "ts"}),
        ("meta_field", {"metaField": "meta"}),
    ]
]

# Property [Timeseries Unsupported Target Rejection]: applying the timeseries
# document to a non-time-series collection (regular, capped, clustered, or view)
# is rejected because the option is only supported on time series collections.
COLLMOD_TS_DOC_TARGET_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "doc_target_regular",
        docs=[{"_id": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "timeseries": {}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a timeseries document on a regular collection",
    ),
    CommandTestCase(
        "target_capped",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "timeseries": {}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a timeseries document on a capped collection",
    ),
    CommandTestCase(
        "target_clustered",
        target_collection=ClusteredCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "timeseries": {}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a timeseries document on a clustered collection",
    ),
    CommandTestCase(
        "doc_target_view",
        target_collection=ViewCollection(options={"pipeline": []}),
        docs=[{"_id": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "timeseries": {}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a timeseries document on a view",
    ),
]

COLLMOD_TS_DOCUMENT_TESTS: list[CommandTestCase] = (
    COLLMOD_TS_DOC_SUCCESS_TESTS
    + COLLMOD_TS_DOC_TYPE_ERROR_TESTS
    + COLLMOD_TS_DOC_UNKNOWN_FIELD_ERROR_TESTS
    + COLLMOD_TS_DOC_TARGET_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_TS_DOCUMENT_TESTS))
def test_collMod_time_series_document(database_client, collection, test):
    """Test collMod time series document acceptance and rejection."""
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
