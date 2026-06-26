"""Tests for setFeatureCompatibilityVersion confirm field type coercion (error cases).

Validates that the confirm field treats falsy values as false and rejects
non-numeric, non-bool types.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FCV_CONFIRM_REQUIRED_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.setFeatureCompatibilityVersion_common import get_fcv

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Confirm Rejected]: confirm field treats falsy values as false
# and rejects non-numeric, non-bool types.
CONFIRM_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "int_0",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": 0},
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=0 as false",
    ),
    CommandTestCase(
        "double_0",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": 0.0,
        },
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=0.0 as false",
    ),
    CommandTestCase(
        "long_0",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": Int64(0),
        },
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=Int64(0) as false",
    ),
    CommandTestCase(
        "decimal_0",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": Decimal128("0"),
        },
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=Decimal128('0') as false",
    ),
    CommandTestCase(
        "null",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": None,
        },
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=null as not-true",
    ),
    CommandTestCase(
        "negative_zero",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": -0.0,
        },
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=-0.0 as false",
    ),
    CommandTestCase(
        "string_type",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": "true",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject confirm as string type",
    ),
    CommandTestCase(
        "object_type",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": {"a": 1},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject confirm as object type",
    ),
    CommandTestCase(
        "array_type",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": [True],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject confirm as array type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONFIRM_REJECTED_TESTS))
def test_setFeatureCompatibilityVersion_confirm_rejected(database_client, collection, test):
    """Test setFeatureCompatibilityVersion rejects invalid confirm values."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    current = get_fcv(collection)
    other = "8.0" if current != "8.0" else "8.2"
    cmd = test.build_command(ctx)
    cmd["setFeatureCompatibilityVersion"] = other
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
