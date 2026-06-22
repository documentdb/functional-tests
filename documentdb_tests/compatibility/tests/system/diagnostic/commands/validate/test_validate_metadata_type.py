"""Tests for validate command 'metadata' parameter type coercion.

Validates that the metadata parameter accepts all BSON types via coercion.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Type Coercion]: validate accepts all BSON types for the metadata parameter via coercion.
ACCEPTED_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_true",
        command={"metadata": True},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept bool true",
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"metadata": False},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept bool false",
    ),
    DiagnosticTestCase(
        "int32_1",
        command={"metadata": 1},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept int32 1 (coerces to true)",
    ),
    DiagnosticTestCase(
        "int32_0",
        command={"metadata": 0},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept int32 0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "double_1",
        command={"metadata": 1.0},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept double 1.0 (coerces to true)",
    ),
    DiagnosticTestCase(
        "double_0",
        command={"metadata": 0.0},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept double 0.0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "int64_1",
        command={"metadata": Int64(1)},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept Int64(1) (coerces to true)",
    ),
    DiagnosticTestCase(
        "int64_0",
        command={"metadata": Int64(0)},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept Int64(0) (coerces to false)",
    ),
    DiagnosticTestCase(
        "decimal128_1",
        command={"metadata": Decimal128("1")},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept Decimal128('1') (coerces to true)",
    ),
    DiagnosticTestCase(
        "decimal128_0",
        command={"metadata": Decimal128("0")},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept Decimal128('0') (coerces to false)",
    ),
    DiagnosticTestCase(
        "null",
        command={"metadata": None},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept null (treated as omitted/false)",
    ),
    DiagnosticTestCase(
        "string",
        command={"metadata": "true"},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept string (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "object",
        command={"metadata": {}},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept object (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "array",
        command={"metadata": []},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept array (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "binary",
        command={"metadata": Binary(b"")},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept Binary (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "objectid",
        command={"metadata": ObjectId()},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept ObjectId (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "datetime",
        command={"metadata": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept datetime (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "regex",
        command={"metadata": Regex(".*")},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept Regex (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"metadata": Timestamp(0, 0)},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept Timestamp (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "code",
        command={"metadata": Code("function(){}")},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept JavaScript Code (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "minkey",
        command={"metadata": MinKey()},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept MinKey (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "maxkey",
        command={"metadata": MaxKey()},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept MaxKey (coerces to truthy)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ACCEPTED_TYPE_TESTS))
def test_validate_metadata_accepted_types(collection, test):
    """Test that validate accepts all BSON types for the metadata parameter."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, **test.command},
    )
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
