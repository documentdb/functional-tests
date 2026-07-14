"""Tests for setClusterParameter command core behavior.

Validates set/get round-trip, idempotent re-application, last-write-wins
semantics, reset to default, clusterParameterTime advancement, null resetting a
scalar field to its default, parameter independence, and accepted argument forms.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.system.administration.utils.admin_test_case import (
    AdminTestCase,
)
from documentdb_tests.framework.assertions import (
    assertProperties,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gt

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]

PARAM_NAME = "changeStreamOptions"
DEFAULT_VALUE = {"preAndPostImages": {"expireAfterSeconds": "off"}}
ALT_VALUE_1 = {"preAndPostImages": {"expireAfterSeconds": 7200}}
ALT_VALUE_2 = {"preAndPostImages": {"expireAfterSeconds": 3600}}


def _set_param(collection, value):
    """Set the cluster parameter."""
    return execute_admin_command(collection, {"setClusterParameter": {PARAM_NAME: value}})


def _restore(collection):
    """Restore default."""
    execute_admin_command(collection, {"setClusterParameter": {PARAM_NAME: DEFAULT_VALUE}})


CORE_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "set_valid_parameter_alt1",
        command={"setClusterParameter": {PARAM_NAME: ALT_VALUE_1}},
        expected={"ok": Eq(1.0)},
        msg="Setting a valid cluster parameter (alt1) should return ok:1",
    ),
    AdminTestCase(
        "set_valid_parameter_alt2",
        command={"setClusterParameter": {PARAM_NAME: ALT_VALUE_2}},
        expected={"ok": Eq(1.0)},
        msg="Setting a valid cluster parameter (alt2) should return ok:1",
    ),
    AdminTestCase(
        "unrecognized_top_level_field_ignored",
        command={"setClusterParameter": {PARAM_NAME: ALT_VALUE_1}, "unknownField": 1},
        expected={"ok": Eq(1.0)},
        msg="Unrecognized top-level field should be ignored",
    ),
    AdminTestCase(
        "maxTimeMS_accepted",
        command={"setClusterParameter": {PARAM_NAME: ALT_VALUE_1}, "maxTimeMS": 30000},
        expected={"ok": Eq(1.0)},
        msg="maxTimeMS should be accepted",
    ),
    AdminTestCase(
        "empty_subdocument_changeStreams_noop",
        command={"setClusterParameter": {"changeStreams": {}}},
        expected={"ok": Eq(1.0)},
        msg="Empty sub-document for changeStreams is accepted as a no-op",
    ),
    AdminTestCase(
        "changeStreamOptions_expireAfterSeconds_off_accepted",
        command={
            "setClusterParameter": {PARAM_NAME: {"preAndPostImages": {"expireAfterSeconds": "off"}}}
        },
        expected={"ok": Eq(1.0)},
        msg="changeStreamOptions.expireAfterSeconds accepts the string 'off'",
    ),
    AdminTestCase(
        "changeStreamOptions_expireAfterSeconds_numeric_accepted",
        command={
            "setClusterParameter": {PARAM_NAME: {"preAndPostImages": {"expireAfterSeconds": 7200}}}
        },
        expected={"ok": Eq(1.0)},
        msg="changeStreamOptions.expireAfterSeconds accepts a numeric value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CORE_TESTS))
def test_setClusterParameter_core(collection, test):
    """Test setClusterParameter core success cases."""
    try:
        result = execute_admin_command(collection, test.command)
        assertResult(result, expected=test.expected, msg=test.msg, raw_res=True)
    finally:
        _restore(collection)


def test_setClusterParameter_round_trip(collection):
    """Test setClusterParameter value is reported back unchanged by getClusterParameter."""
    try:
        _set_param(collection, ALT_VALUE_1)
        result = execute_admin_command(collection, {"getClusterParameter": PARAM_NAME})
        assertSuccessPartial(
            result,
            {"clusterParameters": [{"preAndPostImages": {"expireAfterSeconds": Int64(7200)}}]},
            msg="getClusterParameter should report the value just written",
        )
    finally:
        _restore(collection)


def test_setClusterParameter_round_trip_pauseMigrations(collection):
    """Test pauseMigrationsDuringMultiUpdates round-trips through getClusterParameter unchanged."""
    try:
        execute_admin_command(
            collection,
            {"setClusterParameter": {"pauseMigrationsDuringMultiUpdates": {"enabled": True}}},
        )
        result = execute_admin_command(
            collection, {"getClusterParameter": "pauseMigrationsDuringMultiUpdates"}
        )
        assertSuccessPartial(
            result,
            {"clusterParameters": [{"enabled": True}]},
            msg="getClusterParameter should report the value just written",
        )
    finally:
        execute_admin_command(
            collection,
            {"setClusterParameter": {"pauseMigrationsDuringMultiUpdates": {"enabled": False}}},
        )


def test_setClusterParameter_idempotent(collection):
    """Test re-applying a parameter's current value leaves it unchanged (no-op)."""
    try:
        _set_param(collection, ALT_VALUE_1)
        _set_param(collection, ALT_VALUE_1)
        result = execute_admin_command(collection, {"getClusterParameter": PARAM_NAME})
        assertSuccessPartial(
            result,
            {"clusterParameters": [{"preAndPostImages": {"expireAfterSeconds": Int64(7200)}}]},
            msg="Value should remain unchanged after re-applying the same value",
        )
    finally:
        _restore(collection)


def test_setClusterParameter_set_then_reset(collection):
    """Test setClusterParameter resetting a parameter restores its default value."""
    try:
        _set_param(collection, ALT_VALUE_1)
        _set_param(collection, DEFAULT_VALUE)
        result = execute_admin_command(collection, {"getClusterParameter": PARAM_NAME})
        assertSuccessPartial(
            result,
            {"clusterParameters": [{"preAndPostImages": {"expireAfterSeconds": "off"}}]},
            msg="Parameter should read back as its default after reset",
        )
    finally:
        _restore(collection)


def test_setClusterParameter_last_write_wins(collection):
    """Test two sequential setClusterParameter calls — last write wins."""
    try:
        _set_param(collection, ALT_VALUE_1)
        _set_param(collection, ALT_VALUE_2)
        result = execute_admin_command(collection, {"getClusterParameter": PARAM_NAME})
        assertSuccessPartial(
            result,
            {"clusterParameters": [{"preAndPostImages": {"expireAfterSeconds": Int64(3600)}}]},
            msg="Last write should win",
        )
    finally:
        _restore(collection)


@pytest.mark.requires(cluster_admin=True)
def test_setClusterParameter_advances_cluster_parameter_time(collection):
    """Test setClusterParameter advances clusterParameterTime when the value changes."""
    _restore(collection)
    before = execute_admin_command(collection, {"getClusterParameter": PARAM_NAME})
    t0 = before["clusterParameters"][0]["clusterParameterTime"]

    try:
        _set_param(collection, ALT_VALUE_1)

        result = execute_admin_command(collection, {"getClusterParameter": PARAM_NAME})
        assertProperties(
            result,
            {"clusterParameters.0.clusterParameterTime": Gt(t0)},
            msg="clusterParameterTime should advance after a value-changing set",
            raw_res=True,
        )
    finally:
        _restore(collection)


def _assert_null_resets_field(collection, param, field, non_default, default):
    """Set a scalar field to a non-default, then null it, and assert it reset to default."""
    try:
        execute_admin_command(collection, {"setClusterParameter": {param: {field: non_default}}})
        execute_admin_command(collection, {"setClusterParameter": {param: {field: None}}})
        result = execute_admin_command(collection, {"getClusterParameter": param})
        assertSuccessPartial(
            result,
            {"clusterParameters": [{field: default}]},
            msg=f"null for {param}.{field} should reset to default",
        )
    finally:
        execute_admin_command(collection, {"setClusterParameter": {param: {field: default}}})


def test_setClusterParameter_null_resets_changeStreams_expireAfterSeconds(collection):
    """Test null on changeStreams.expireAfterSeconds resets it to its default."""
    _assert_null_resets_field(collection, "changeStreams", "expireAfterSeconds", 5000, Int64(3600))


def test_setClusterParameter_null_resets_pauseMigrations_enabled(collection):
    """Test null on pauseMigrationsDuringMultiUpdates.enabled resets it to its default."""
    _assert_null_resets_field(
        collection, "pauseMigrationsDuringMultiUpdates", "enabled", True, False
    )


def test_setClusterParameter_independent_parameters_do_not_interfere(collection):
    """Test setting one parameter does not clobber the value of another."""
    try:
        _set_param(collection, ALT_VALUE_1)
        execute_admin_command(
            collection, {"setClusterParameter": {"changeStreams": {"expireAfterSeconds": 5000}}}
        )
        result = execute_admin_command(
            collection, {"getClusterParameter": [PARAM_NAME, "changeStreams"]}
        )
        assertSuccessPartial(
            result,
            {
                "clusterParameters": [
                    {"preAndPostImages": {"expireAfterSeconds": Int64(7200)}},
                    {"expireAfterSeconds": Int64(5000)},
                ]
            },
            msg="Each parameter should retain its own value after setting the other",
        )
    finally:
        _restore(collection)
        # This test also mutates changeStreams, which _restore (changeStreamOptions only)
        # does not cover — restore it explicitly so it doesn't leak into later tests.
        execute_admin_command(
            collection, {"setClusterParameter": {"changeStreams": {"expireAfterSeconds": 3600}}}
        )
