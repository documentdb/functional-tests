"""Core behavior tests for setDefaultRWConcern."""

import pytest

from documentdb_tests.compatibility.tests.system.administration.utils.admin_test_case import (
    AdminTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gt

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]


CORE_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "set_both_defaults",
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "majority"},
            "defaultWriteConcern": {"w": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="Should succeed with both defaults",
    ),
    AdminTestCase(
        "round_trip_write_concern",
        setup_commands=({"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}},),
        command={"getDefaultRWConcern": 1},
        expected={"ok": Eq(1.0), "defaultWriteConcern": {"w": Eq(1), "wtimeout": Eq(0)}},
        msg="getDefaultRWConcern should reflect the configured write concern",
    ),
    AdminTestCase(
        "round_trip_read_concern",
        setup_commands=({"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "majority"}},),
        command={"getDefaultRWConcern": 1},
        expected={"ok": Eq(1.0), "defaultReadConcern": {"level": Eq("majority")}},
        msg="getDefaultRWConcern should reflect the configured read concern",
    ),
    AdminTestCase(
        "idempotent_write_concern",
        setup_commands=({"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}},),
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}},
        expected={"ok": Eq(1.0), "defaultWriteConcern": {"w": Eq(1), "wtimeout": Eq(0)}},
        msg="Second application should succeed with same value",
    ),
    AdminTestCase(
        "change_read_concern_level",
        setup_commands=({"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "local"}},),
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "majority"}},
        expected={"ok": Eq(1.0), "defaultReadConcern": {"level": Eq("majority")}},
        msg="Latest read concern level should win",
    ),
    AdminTestCase(
        "change_write_concern_value",
        setup_commands=({"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}},),
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": "majority"}},
        expected={"ok": Eq(1.0), "defaultWriteConcern": {"w": Eq("majority")}},
        msg="Should succeed changing write concern value",
    ),
    AdminTestCase(
        "observable_via_get",
        setup_commands=({"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}},),
        command={"getDefaultRWConcern": 1},
        expected={"defaultWriteConcernSource": Eq("global")},
        msg="Source should be 'global' after explicit set",
    ),
    AdminTestCase(
        "unset_read_concern_reverts_source_to_implicit",
        setup_commands=(
            {"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "majority"}},
            {"setDefaultRWConcern": 1, "defaultReadConcern": {}},
        ),
        command={"getDefaultRWConcern": 1},
        expected={"ok": Eq(1.0), "defaultReadConcernSource": Eq("implicit")},
        msg="unsetting the read concern with {} reverts its source from 'global' to 'implicit'",
    ),
    AdminTestCase(
        "set_read_concern_preserves_existing_write_concern",
        setup_commands=(
            {"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}},
            {"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "majority"}},
        ),
        command={"getDefaultRWConcern": 1},
        expected={
            "defaultWriteConcern": {"w": Eq(1), "wtimeout": Eq(0)},
            "defaultReadConcern": {"level": Eq("majority")},
        },
        msg="setting only the read concern leaves a previously-set write concern intact",
    ),
    AdminTestCase(
        "idempotent_read_concern",
        setup_commands=({"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "majority"}},),
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "majority"}},
        expected={"ok": Eq(1.0), "defaultReadConcern": {"level": Eq("majority")}},
        msg="re-applying the same read concern should succeed with the same value",
    ),
    AdminTestCase(
        "round_trip_write_concern_majority",
        setup_commands=({"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": "majority"}},),
        command={"getDefaultRWConcern": 1},
        expected={"ok": Eq(1.0), "defaultWriteConcern": {"w": Eq("majority"), "wtimeout": Eq(0)}},
        msg="getDefaultRWConcern should reflect a w:'majority' write concern",
    ),
    AdminTestCase(
        "round_trip_read_concern_available",
        setup_commands=({"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "available"}},),
        command={"getDefaultRWConcern": 1},
        expected={"ok": Eq(1.0), "defaultReadConcern": {"level": Eq("available")}},
        msg="getDefaultRWConcern should reflect an 'available' read concern",
    ),
    AdminTestCase(
        "round_trip_both_defaults",
        setup_commands=(
            {
                "setDefaultRWConcern": 1,
                "defaultReadConcern": {"level": "majority"},
                "defaultWriteConcern": {"w": 1},
            },
        ),
        command={"getDefaultRWConcern": 1},
        expected={
            "defaultReadConcern": {"level": Eq("majority")},
            "defaultWriteConcern": {"w": Eq(1), "wtimeout": Eq(0)},
        },
        msg="getDefaultRWConcern reflects both defaults set in a single call",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CORE_TESTS))
def test_setDefaultRWConcern_core(collection, test):
    """Run a setDefaultRWConcern core behavior case."""
    for setup in test.setup_commands:
        execute_admin_command(collection, setup)
    result = execute_admin_command(collection, test.command)
    assertResult(result, expected=test.expected, msg=test.msg, raw_res=True)


def test_setDefaultRWConcern_update_op_time_advances(collection):
    """Test that updateOpTime advances after a value-changing set."""
    execute_admin_command(collection, {"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}})
    before = execute_admin_command(collection, {"getDefaultRWConcern": 1})
    execute_admin_command(
        collection, {"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": "majority"}}
    )
    after = execute_admin_command(collection, {"getDefaultRWConcern": 1})
    assertResult(
        after,
        expected={"updateOpTime": Gt(before["updateOpTime"])},
        msg="updateOpTime should advance after a value-changing set",
        raw_res=True,
    )
