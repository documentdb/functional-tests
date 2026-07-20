"""Tests for fsync command-envelope field handling.

Covers comment acceptance, generic envelope options, unknown-field rejection,
and apiStrict rejection.
"""

from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    API_STRICT_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    NotExists,
)
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

pytestmark = pytest.mark.no_parallel


# Property [Comment Acceptance]: comment accepts any BSON value and is not echoed
# in the response.
FSYNC_COMMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        command={"fsync": 1, "comment": val},
        expected={
            "ok": Eq(1.0),
            "numFiles": Eq(1),
            "lockCount": NotExists(),
            "comment": NotExists(),
        },
        msg=f"fsync should accept a {tid} comment value and not echo it in the response",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(7)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "audit note"),
        ("object", {"a": 1}),
        ("array", [1, 2, 3]),
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

# Property [Generic Command Options Accepted]: generic command-envelope options
# ($readPreference, maxTimeMS, apiVersion) are accepted and ignored, leaving the
# no-lock flush response unchanged. Their semantics are owned elsewhere; this
# only confirms fsync accepts the syntax.
FSYNC_GENERIC_OPTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "generic_read_preference",
        command={"fsync": 1, "$readPreference": {"mode": "secondary"}},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should accept a $readPreference option and perform a no-lock flush",
    ),
    CommandTestCase(
        "generic_max_time_ms",
        command={"fsync": 1, "maxTimeMS": 5_000},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should accept an int maxTimeMS option and perform a no-lock flush",
    ),
    CommandTestCase(
        "generic_max_time_ms_float",
        command={"fsync": 1, "maxTimeMS": 5_000.0},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should accept a float maxTimeMS option and perform a no-lock flush",
    ),
    CommandTestCase(
        "generic_api_version",
        command={"fsync": 1, "apiVersion": "1"},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should accept apiVersion 1 alone and perform a no-lock flush",
    ),
]

# Property [Unknown Field and Field-Name Case Sensitivity]: an unrecognized
# top-level field, including case variants of known field names, produces an
# unrecognized-field error.
FSYNC_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field",
        command={"fsync": 1, "bogus": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="fsync should reject an unknown top-level command field with an "
        "unrecognized-field error",
    ),
    CommandTestCase(
        "case_variant_lock",
        command={"fsync": 1, "Lock": True},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="fsync should reject a case variant of a known command field name "
        "with an unrecognized-field error",
    ),
    CommandTestCase(
        "timeout_missing_millis_suffix",
        command={"fsync": 1, "fsyncLockAcquisitionTimeout": 90_000},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="fsync should reject fsyncLockAcquisitionTimeout, which is missing the "
        "Millis suffix, as an unknown field",
    ),
]

# Property [Unsupported Stable API]: apiStrict under API Version 1 is rejected
# rather than silently ignored.
FSYNC_API_STRICT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "envelope_api_strict",
        command={"fsync": 1, "apiVersion": "1", "apiStrict": True},
        error_code=API_STRICT_ERROR,
        msg="fsync should reject apiStrict under API Version 1 with an APIStrictError",
    ),
]

FSYNC_COMMAND_ENVELOPE_TESTS: list[CommandTestCase] = (
    FSYNC_COMMENT_TESTS
    + FSYNC_GENERIC_OPTION_TESTS
    + FSYNC_UNKNOWN_FIELD_ERROR_TESTS
    + FSYNC_API_STRICT_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(FSYNC_COMMAND_ENVELOPE_TESTS))
def test_fsync_command_envelope_cases(collection, test):
    """Test fsync command-envelope option acceptance and rejection cases."""
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
