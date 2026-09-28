"""Tests for getParameter command core behavior."""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NotExists

pytestmark = pytest.mark.admin


SINGLE_PARAM_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "int_42_with_named_param",
        command={"getParameter": 42, "logLevel": 1},
        checks={"ok": Eq(1.0), "logLevel": Exists()},
        msg="Should return parameter value with any integer",
    ),
    DiagnosticTestCase(
        "int_0_with_named_param",
        command={"getParameter": 0, "logLevel": 1},
        checks={"ok": Eq(1.0), "logLevel": Exists()},
        msg="Should return parameter value with integer 0 (value is ignored)",
    ),
    DiagnosticTestCase(
        "negative_int_with_named_param",
        command={"getParameter": -1, "logLevel": 1},
        checks={"ok": Eq(1.0), "logLevel": Exists()},
        msg="Should return parameter value with negative integer",
    ),
    DiagnosticTestCase(
        "multiple_named_params",
        command={"getParameter": 1, "logLevel": 1, "quiet": 1},
        checks={"ok": Eq(1.0), "logLevel": Exists(), "quiet": Exists()},
        msg="Should return all named parameters requested in one command",
    ),
    DiagnosticTestCase(
        "empty_doc_with_named_param",
        command={"getParameter": {}, "logLevel": 1},
        checks={"ok": Eq(1.0), "logLevel": Exists()},
        msg="Empty document with a named parameter should be accepted (behaves like int form)",
    ),
]


SHOW_DETAILS_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "showDetails_true_returns_detail_fields",
        command={"getParameter": {"showDetails": True}, "logLevel": 1},
        checks={
            "ok": Eq(1.0),
            "logLevel": Exists(),
            "logLevel.value": Exists(),
            "logLevel.settableAtRuntime": Eq(True),
            "logLevel.settableAtStartup": IsType("bool"),
        },
        msg="showDetails:true should return value, settableAtRuntime, settableAtStartup",
    ),
    DiagnosticTestCase(
        "showDetails_true_allParameters",
        command={"getParameter": {"showDetails": True, "allParameters": True}},
        checks={
            "ok": Eq(1.0),
            "logLevel.value": Exists(),
            "logLevel.settableAtRuntime": IsType("bool"),
            "logLevel.settableAtStartup": IsType("bool"),
        },
        msg="showDetails with allParameters should return details for all",
    ),
]


SET_AT_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "setAt_startup",
        command={"getParameter": {"allParameters": True, "setAt": "startup"}},
        checks={"ok": Eq(1.0)},
        msg="setAt:'startup' with allParameters should succeed",
    ),
    DiagnosticTestCase(
        "setAt_runtime",
        command={"getParameter": {"allParameters": True, "setAt": "runtime"}},
        checks={"ok": Eq(1.0)},
        msg="setAt:'runtime' with allParameters should succeed",
    ),
]


PARAM_DATA_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "param_with_int_value",
        command={"getParameter": 1, "logLevel": 1},
        checks={"ok": Eq(1.0), "logLevel": IsType("int")},
        msg="Should retrieve parameter with integer value",
    ),
    DiagnosticTestCase(
        "param_with_bool_value",
        command={"getParameter": 1, "allowDiskUseByDefault": 1},
        checks={"ok": Eq(1.0), "allowDiskUseByDefault": IsType("bool")},
        msg="Should retrieve parameter with boolean value",
    ),
    DiagnosticTestCase(
        "param_with_string_value",
        command={"getParameter": 1, "ShardingTaskExecutorPoolReplicaSetMatching": 1},
        checks={"ok": Eq(1.0), "ShardingTaskExecutorPoolReplicaSetMatching": IsType("string")},
        msg="Should retrieve parameter with string value",
    ),
    DiagnosticTestCase(
        "param_with_document_value",
        command={"getParameter": 1, "featureCompatibilityVersion": 1},
        checks={"ok": Eq(1.0), "featureCompatibilityVersion": IsType("object")},
        msg="Should retrieve parameter with document value",
    ),
    DiagnosticTestCase(
        "param_with_array_value",
        command={"getParameter": 1, "authenticationMechanisms": 1},
        checks={"ok": Eq(1.0), "authenticationMechanisms": IsType("array")},
        msg="Should retrieve parameter with array value",
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(SINGLE_PARAM_TESTS + SHOW_DETAILS_TESTS + SET_AT_TESTS + PARAM_DATA_TYPE_TESTS),
)
def test_getParameter_success_cases(collection, test):
    """Test getParameter success cases: retrieval, showDetails, setAt, and value types."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_getParameter_allParameters_true(collection):
    """Test getParameter with {allParameters: true} returns all parameters."""
    result = execute_admin_command(collection, {"getParameter": {"allParameters": True}})
    assertProperties(
        result,
        {"ok": Eq(1.0), "logLevel": Exists()},
        msg="Should return ok:1 and parameters",
        raw_res=True,
    )


def test_getParameter_star_and_allParameters_consistent(collection):
    """Test all parameters returned by '*' are also returned by {allParameters: true}."""
    star_result = execute_admin_command(collection, {"getParameter": "*"})
    all_result = execute_admin_command(collection, {"getParameter": {"allParameters": True}})
    star_keys = set(star_result.keys()) - {"ok"}
    all_keys = set(all_result.keys()) - {"ok"}
    missing = star_keys - all_keys
    assertSuccess(
        {"ok": 1.0, "missing": []},
        {"ok": 1.0, "missing": list(missing)},
        raw_res=True,
        msg="Keys from '*' should all appear in allParameters",
    )


def test_getParameter_showDetails_false(collection):
    """Test {showDetails: false} returns parameter value without detail fields."""
    result = execute_admin_command(
        collection, {"getParameter": {"showDetails": False}, "logLevel": 1}
    )
    assertProperties(
        result,
        {
            "ok": Eq(1.0),
            "logLevel": Exists(),
            "logLevel.value": NotExists(),
            "logLevel.settableAtRuntime": NotExists(),
            "logLevel.settableAtStartup": NotExists(),
        },
        msg="showDetails:false should return the plain value without detail fields",
        raw_res=True,
    )


def test_getParameter_setAt_without_allParameters_succeeds(collection):
    """Test setAt without allParameters succeeds (setAt is ignored for single param)."""
    result = execute_admin_command(
        collection, {"getParameter": {"setAt": "startup"}, "logLevel": 1}
    )
    assertProperties(
        result,
        {"ok": Eq(1.0), "logLevel": Exists()},
        msg="setAt without allParameters should succeed",
        raw_res=True,
    )


def test_getParameter_star_response_has_multiple_params(collection):
    """Test '*' response contains multiple parameter fields."""
    result = execute_admin_command(collection, {"getParameter": "*"})
    param_keys = set(result.keys()) - {"ok"}
    assertSuccess(
        {"ok": 1.0, "has_logLevel": True, "has_multiple_params": True},
        {
            "ok": 1.0,
            "has_logLevel": "logLevel" in param_keys,
            "has_multiple_params": len(param_keys) > 1,
        },
        raw_res=True,
        msg=f"Star should return multiple params including logLevel, got {len(param_keys)}",
    )


def test_getParameter_single_matches_star(collection):
    """Test parameter value from single retrieval matches value in '*' response."""
    single = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    star = execute_admin_command(collection, {"getParameter": "*"})
    assertSuccess(
        {"ok": 1.0, "logLevel": single["logLevel"]},
        {"ok": 1.0, "logLevel": star["logLevel"]},
        raw_res=True,
        msg="Single retrieval should match star value",
    )


@pytest.mark.no_parallel
def test_getParameter_reflects_setParameter_change(collection):
    """Test getParameter returns updated value after setParameter modifies a runtime parameter."""
    try:
        execute_admin_command(collection, {"setParameter": 1, "logLevel": 2})
        result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
        assertProperties(
            result, {"logLevel": Eq(2)}, msg="Should reflect setParameter change", raw_res=True
        )
    finally:
        execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_getParameter_known_startup_only_param(collection):
    """Test retrieval of a known startup-only parameter (KeysRotationIntervalSec)."""
    result = execute_admin_command(
        collection, {"getParameter": {"showDetails": True}, "KeysRotationIntervalSec": 1}
    )
    assertProperties(
        result,
        {
            "KeysRotationIntervalSec.settableAtRuntime": Eq(False),
            "KeysRotationIntervalSec.settableAtStartup": Eq(True),
        },
        msg="Startup-only param should have settableAtRuntime:false",
        raw_res=True,
    )


def test_getParameter_fully_immutable_param(collection):
    """Test a fully-immutable parameter has both settability flags false."""
    result = execute_admin_command(
        collection, {"getParameter": {"showDetails": True}, "authSchemaVersion": 1}
    )
    assertProperties(
        result,
        {
            "authSchemaVersion.settableAtRuntime": Eq(False),
            "authSchemaVersion.settableAtStartup": Eq(False),
        },
        msg="Fully-immutable param should have both settability flags false",
        raw_res=True,
    )


def test_getParameter_setAt_filters_result_count(collection):
    """Test setAt actually narrows the result set."""
    all_keys = set(execute_admin_command(collection, {"getParameter": {"allParameters": True}}))
    runtime_keys = set(
        execute_admin_command(
            collection, {"getParameter": {"allParameters": True, "setAt": "runtime"}}
        )
    )
    startup_keys = set(
        execute_admin_command(
            collection, {"getParameter": {"allParameters": True, "setAt": "startup"}}
        )
    )
    n_all = len(all_keys - {"ok"})
    assertSuccess(
        {"ok": 1.0, "runtime_filtered": True, "startup_filtered": True},
        {
            "ok": 1.0,
            "runtime_filtered": len(runtime_keys - {"ok"}) < n_all,
            "startup_filtered": len(startup_keys - {"ok"}) < n_all,
        },
        raw_res=True,
        msg="setAt:'runtime' and setAt:'startup' should each return fewer params than unfiltered",
    )


def test_getParameter_setAt_buckets_startup_only_param(collection):
    """Test setAt routes a startup-only param to the correct bucket."""
    runtime_keys = set(
        execute_admin_command(
            collection, {"getParameter": {"allParameters": True, "setAt": "runtime"}}
        )
    )
    startup_keys = set(
        execute_admin_command(
            collection, {"getParameter": {"allParameters": True, "setAt": "startup"}}
        )
    )
    assertSuccess(
        {"ok": 1.0, "in_runtime": False, "in_startup": True},
        {
            "ok": 1.0,
            "in_runtime": "KeysRotationIntervalSec" in runtime_keys,
            "in_startup": "KeysRotationIntervalSec" in startup_keys,
        },
        raw_res=True,
        msg="Startup-only param should appear only under setAt:'startup'",
    )


def test_getParameter_allParameters_with_named_param_returns_all(collection):
    """Test {allParameters: true} with a named param returns the same keys as allParameters."""
    all_only = execute_admin_command(collection, {"getParameter": {"allParameters": True}})
    with_named = execute_admin_command(
        collection, {"getParameter": {"allParameters": True}, "logLevel": 1}
    )
    all_only_keys = set(all_only.keys()) - {"ok"}
    with_named_keys = set(with_named.keys()) - {"ok"}
    assertSuccess(
        {"key_diff": []},
        {"key_diff": sorted(all_only_keys ^ with_named_keys)},
        raw_res=True,
        msg="allParameters with a named param should return the same keys as allParameters alone",
    )


def test_getParameter_allParameters_with_named_param_not_filtered(collection):
    """Test {allParameters: true} with a named param is not narrowed to just that param."""
    result = execute_admin_command(
        collection, {"getParameter": {"allParameters": True}, "logLevel": 1}
    )
    param_keys = set(result.keys()) - {"ok"}
    assertSuccess(
        {"has_logLevel": True, "has_other_params": True},
        {
            "has_logLevel": "logLevel" in param_keys,
            "has_other_params": len(param_keys) > 1,
        },
        raw_res=True,
        msg="allParameters with a named param should still return all params, not just logLevel",
    )
