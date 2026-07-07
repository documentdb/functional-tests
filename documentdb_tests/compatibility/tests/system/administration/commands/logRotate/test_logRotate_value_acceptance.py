"""Tests for logRotate acceptance of specific scalar values.

Covers values the shared BSON-type harness does not sample: boolean `false`, `0`,
and negative integers/longs (it only feeds `True` and `INT32_MAX`/`INT64_MAX`).
Each rotation goes through `execute_admin_with_retry_command`, which retries past the
transient FileRenameFailed so the test can assert a clean success.
"""

import pytest
from bson.int64 import Int64

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.error_codes import FILE_RENAME_FAILED_ERROR
from documentdb_tests.framework.executor import execute_admin_with_retry_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def test_logRotate_value_bool_false_accepted(collection):
    """Test logRotate accepts boolean false (the BSON sample only covers true)."""
    result = execute_admin_with_retry_command(
        collection, {"logRotate": False}, retry_code=FILE_RENAME_FAILED_ERROR
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="logRotate value should accept boolean false")


@pytest.mark.parametrize(
    "value",
    [0, -1, Int64(-5)],
    ids=["zero", "negative_int", "negative_long"],
)
def test_logRotate_value_zero_and_negative_accepted(collection, value):
    """Test logRotate accepts 0 and negative integers (BSON samples only cover max values)."""
    result = execute_admin_with_retry_command(
        collection, {"logRotate": value}, retry_code=FILE_RENAME_FAILED_ERROR
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg=f"logRotate value should accept {value!r}")
