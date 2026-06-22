"""Tests for validate command option combinations and error conditions.

Validates valid and invalid option combinations, repair/fixMultikey specifics,
and unrecognized field handling.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Valid Combinations]: validate succeeds with valid option combinations.
VALID_COMBINATION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "all_defaults_explicit",
        command={"full": False, "repair": False, "metadata": False, "checkBSONConformance": False},
        checks={"ok": Eq(1.0)},
        msg="validate should succeed with all options set to false explicitly",
    ),
    DiagnosticTestCase(
        "full_true",
        command={"full": True},
        checks={"ok": Eq(1.0)},
        msg="validate with full: true should succeed",
    ),
    DiagnosticTestCase(
        "checkBSONConformance_true",
        command={"checkBSONConformance": True},
        checks={"ok": Eq(1.0)},
        msg="validate with checkBSONConformance: true should succeed",
    ),
    DiagnosticTestCase(
        "full_and_checkBSONConformance",
        command={"full": True, "checkBSONConformance": True},
        checks={"ok": Eq(1.0)},
        msg="validate with full: true and checkBSONConformance: true should succeed",
    ),
    DiagnosticTestCase(
        "metadata_true",
        command={"metadata": True},
        checks={"ok": Eq(1.0)},
        msg="validate with metadata: true should succeed",
    ),
    DiagnosticTestCase(
        "fixMultikey_true_alone",
        command={"fixMultikey": True},
        checks={"ok": Eq(1.0)},
        msg="validate with fixMultikey: true alone should succeed",
    ),
    DiagnosticTestCase(
        "repair_true_alone",
        command={"repair": True},
        checks={"ok": Eq(1.0)},
        msg="validate with repair: true alone should succeed",
    ),
    DiagnosticTestCase(
        "repair_true_with_fixMultikey",
        command={"repair": True, "fixMultikey": True},
        checks={"ok": Eq(1.0)},
        msg="validate with repair: true and fixMultikey: true should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_COMBINATION_TESTS))
def test_validate_valid_option_combinations(collection, test):
    """Test that validate succeeds with valid option combinations."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"validate": collection.name, **test.command})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


# Property [Invalid Combinations]: validate rejects incompatible option combinations.
INVALID_COMBINATION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "metadata_with_full",
        command={"metadata": True, "full": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="validate should error with metadata: true and full: true",
    ),
    DiagnosticTestCase(
        "metadata_with_repair",
        command={"metadata": True, "repair": True, "fixMultikey": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="validate should error with metadata: true and repair: true",
    ),
    DiagnosticTestCase(
        "metadata_with_checkBSONConformance",
        command={"metadata": True, "checkBSONConformance": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="validate should error with metadata: true and checkBSONConformance: true",
    ),
    DiagnosticTestCase(
        "checkBSONConformance_with_repair",
        command={"checkBSONConformance": True, "repair": True, "fixMultikey": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="validate should error with checkBSONConformance: true and repair: true",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_COMBINATION_TESTS))
def test_validate_invalid_option_combinations(collection, test):
    """Test that validate errors on invalid option combinations."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"validate": collection.name, **test.command})
    assertFailureCode(result, test.error_code, msg=test.msg)
