"""Tests for validate command repair and fixMultikey options.

Validates type coercion for repair and fixMultikey parameters and verifies
repairMode values for different repair configurations.
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

# Property [Type Coercion]: validate accepts all BSON types for the repair parameter via coercion.
REPAIR_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_true",
        command={"repair": True},
        checks={"ok": Eq(1.0)},
        msg="repair should accept bool true",
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"repair": False},
        checks={"ok": Eq(1.0)},
        msg="repair should accept bool false",
    ),
    DiagnosticTestCase(
        "int32_1",
        command={"repair": 1},
        checks={"ok": Eq(1.0)},
        msg="repair should accept int32 1 (coerces to true)",
    ),
    DiagnosticTestCase(
        "int32_0",
        command={"repair": 0},
        checks={"ok": Eq(1.0)},
        msg="repair should accept int32 0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "double_1",
        command={"repair": 1.0},
        checks={"ok": Eq(1.0)},
        msg="repair should accept double 1.0 (coerces to true)",
    ),
    DiagnosticTestCase(
        "double_0",
        command={"repair": 0.0},
        checks={"ok": Eq(1.0)},
        msg="repair should accept double 0.0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "int64_1",
        command={"repair": Int64(1)},
        checks={"ok": Eq(1.0)},
        msg="repair should accept Int64(1) (coerces to true)",
    ),
    DiagnosticTestCase(
        "int64_0",
        command={"repair": Int64(0)},
        checks={"ok": Eq(1.0)},
        msg="repair should accept Int64(0) (coerces to false)",
    ),
    DiagnosticTestCase(
        "decimal128_1",
        command={"repair": Decimal128("1")},
        checks={"ok": Eq(1.0)},
        msg="repair should accept Decimal128('1') (coerces to true)",
    ),
    DiagnosticTestCase(
        "decimal128_0",
        command={"repair": Decimal128("0")},
        checks={"ok": Eq(1.0)},
        msg="repair should accept Decimal128('0') (coerces to false)",
    ),
    DiagnosticTestCase(
        "null",
        command={"repair": None},
        checks={"ok": Eq(1.0)},
        msg="repair should accept null (treated as omitted/false)",
    ),
    DiagnosticTestCase(
        "string",
        command={"repair": "true"},
        checks={"ok": Eq(1.0)},
        msg="repair should accept string (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "object",
        command={"repair": {}},
        checks={"ok": Eq(1.0)},
        msg="repair should accept object (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "array",
        command={"repair": []},
        checks={"ok": Eq(1.0)},
        msg="repair should accept array (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "binary",
        command={"repair": Binary(b"")},
        checks={"ok": Eq(1.0)},
        msg="repair should accept Binary (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "objectid",
        command={"repair": ObjectId()},
        checks={"ok": Eq(1.0)},
        msg="repair should accept ObjectId (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "datetime",
        command={"repair": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        checks={"ok": Eq(1.0)},
        msg="repair should accept datetime (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "regex",
        command={"repair": Regex(".*")},
        checks={"ok": Eq(1.0)},
        msg="repair should accept Regex (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"repair": Timestamp(0, 0)},
        checks={"ok": Eq(1.0)},
        msg="repair should accept Timestamp (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "code",
        command={"repair": Code("function(){}")},
        checks={"ok": Eq(1.0)},
        msg="repair should accept JavaScript Code (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "minkey",
        command={"repair": MinKey()},
        checks={"ok": Eq(1.0)},
        msg="repair should accept MinKey (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "maxkey",
        command={"repair": MaxKey()},
        checks={"ok": Eq(1.0)},
        msg="repair should accept MaxKey (coerces to truthy)",
    ),
]


# Property [Type Coercion]: validate accepts all BSON types for the fixMultikey parameter.
FIXMULTIKEY_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_true",
        command={"fixMultikey": True},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept bool true",
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"fixMultikey": False},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept bool false",
    ),
    DiagnosticTestCase(
        "int32_1",
        command={"fixMultikey": 1},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept int32 1 (coerces to true)",
    ),
    DiagnosticTestCase(
        "int32_0",
        command={"fixMultikey": 0},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept int32 0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "double_1",
        command={"fixMultikey": 1.0},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept double 1.0 (coerces to true)",
    ),
    DiagnosticTestCase(
        "double_0",
        command={"fixMultikey": 0.0},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept double 0.0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "int64_1",
        command={"fixMultikey": Int64(1)},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept Int64(1) (coerces to true)",
    ),
    DiagnosticTestCase(
        "int64_0",
        command={"fixMultikey": Int64(0)},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept Int64(0) (coerces to false)",
    ),
    DiagnosticTestCase(
        "decimal128_1",
        command={"fixMultikey": Decimal128("1")},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept Decimal128('1') (coerces to true)",
    ),
    DiagnosticTestCase(
        "decimal128_0",
        command={"fixMultikey": Decimal128("0")},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept Decimal128('0') (coerces to false)",
    ),
    DiagnosticTestCase(
        "null",
        command={"fixMultikey": None},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept null (treated as omitted/false)",
    ),
    DiagnosticTestCase(
        "string",
        command={"fixMultikey": "true"},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept string (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "object",
        command={"fixMultikey": {}},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept object (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "array",
        command={"fixMultikey": []},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept array (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "binary",
        command={"fixMultikey": Binary(b"")},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept Binary (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "objectid",
        command={"fixMultikey": ObjectId()},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept ObjectId (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "datetime",
        command={"fixMultikey": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept datetime (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "regex",
        command={"fixMultikey": Regex(".*")},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept Regex (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"fixMultikey": Timestamp(0, 0)},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept Timestamp (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "code",
        command={"fixMultikey": Code("function(){}")},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept JavaScript Code (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "minkey",
        command={"fixMultikey": MinKey()},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept MinKey (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "maxkey",
        command={"fixMultikey": MaxKey()},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept MaxKey (coerces to truthy)",
    ),
]


# Property [Repair Mode]: validate returns correct repairMode for different configurations.
REPAIR_MODE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "no_repair_mode_none",
        command={},
        checks={"ok": Eq(1.0), "repairMode": Eq("None"), "repaired": Eq(False)},
        msg="validate should return repairMode: 'None' with no repair options",
    ),
    DiagnosticTestCase(
        "repair_and_fixMultikey_mode_fix_errors",
        command={"repair": True, "fixMultikey": True},
        checks={"ok": Eq(1.0), "repairMode": Eq("FixErrors"), "repaired": Eq(False)},
        msg="validate with repair+fixMultikey should return repairMode: 'FixErrors'",
    ),
    DiagnosticTestCase(
        "fixMultikey_alone_mode_adjust",
        command={"fixMultikey": True},
        checks={"ok": Eq(1.0), "repairMode": Eq("AdjustMultikey"), "repaired": Eq(False)},
        msg="validate with fixMultikey alone should return repairMode: 'AdjustMultikey'",
    ),
    DiagnosticTestCase(
        "repair_alone_mode_fix_errors",
        command={"repair": True},
        checks={"ok": Eq(1.0), "repairMode": Eq("FixErrors"), "repaired": Eq(False)},
        msg="validate with repair alone should return repairMode: 'FixErrors'",
    ),
]


REPAIR_AND_FIXMULTIKEY_TESTS = REPAIR_TYPE_TESTS + FIXMULTIKEY_TYPE_TESTS + REPAIR_MODE_TESTS


@pytest.mark.parametrize("test", pytest_params(REPAIR_AND_FIXMULTIKEY_TESTS))
def test_validate_repair_and_fixMultikey(collection, test):
    """Test repair/fixMultikey type coercion and repairMode values."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, **test.command},
    )
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
