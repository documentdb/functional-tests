"""Tests for setFeatureCompatibilityVersion writeConcern field rejection (error cases).

Validates that writeConcern rejects non-object types with TYPE_MISMATCH_ERROR.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.setFeatureCompatibilityVersion_common import get_fcv

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [writeConcern Rejected]: setFeatureCompatibilityVersion rejects
# non-object writeConcern types.
WRITE_CONCERN_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": "majority",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as string",
    ),
    CommandTestCase(
        "int",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": 1,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as int",
    ),
    CommandTestCase(
        "bool",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": True,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as bool",
    ),
    CommandTestCase(
        "array",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": [{"w": 1}],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as array",
    ),
    CommandTestCase(
        "long",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": Int64(1),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as long",
    ),
    CommandTestCase(
        "double",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": 1.0,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as double",
    ),
    CommandTestCase(
        "decimal128",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": Decimal128("1"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as Decimal128",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_REJECTED_TESTS))
def test_setFeatureCompatibilityVersion_writeConcern_rejected(database_client, collection, test):
    """Test setFeatureCompatibilityVersion rejects non-object writeConcern types."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cmd["setFeatureCompatibilityVersion"] = get_fcv(collection)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
