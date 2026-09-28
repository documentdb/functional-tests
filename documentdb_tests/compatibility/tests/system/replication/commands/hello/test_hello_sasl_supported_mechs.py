"""Tests for hello command saslSupportedMechs parameter acceptance.

Validates valid usage, format edge cases, and accepted variations
for the saslSupportedMechs parameter.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.replication.utils.replication_test_case import (  # noqa: E501
    ReplicationTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [saslSupportedMechs Valid Usage]: hello accepts valid
# "db.user" format strings for saslSupportedMechs.
SASL_VALID_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "sasl_nonexistent_user",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": "admin.nonExistentUser",
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should succeed for non-existent user in saslSupportedMechs",
    ),
    ReplicationTestCase(
        "sasl_other_db_prefix",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": "otherdb.someuser",
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should accept non-admin database prefix in saslSupportedMechs",
    ),
]

# Property [saslSupportedMechs Format Edge Cases]: hello accepts
# borderline "db.user" format variations that still contain a dot.
SASL_FORMAT_EDGE_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "sasl_empty_db_component",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": ".noDatabase",
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should accept saslSupportedMechs with empty database component",
    ),
    ReplicationTestCase(
        "sasl_empty_username",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": "admin.",
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should accept saslSupportedMechs with empty username",
    ),
    ReplicationTestCase(
        "sasl_dot_only",
        command=lambda ctx: {"hello": 1, "saslSupportedMechs": "."},
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should accept dot-only saslSupportedMechs",
    ),
]

# Property [saslSupportedMechs Edge Cases]: hello handles edge cases
# in the "db.user" format string.
SASL_EDGE_CASE_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "sasl_dots_in_username",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": "admin.user.with.dots",
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should accept saslSupportedMechs with dots in username",
    ),
    ReplicationTestCase(
        "sasl_special_chars_in_db",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": "a]dmin.user",
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should accept saslSupportedMechs with special chars in db name",
    ),
    ReplicationTestCase(
        "sasl_long_username",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": "admin.a_very_long_username_that_exceeds_typical_lengths",
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should accept saslSupportedMechs with long username",
    ),
    ReplicationTestCase(
        "sasl_external_db",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": "$external.user",
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should accept $external database prefix in saslSupportedMechs",
    ),
]

HELLO_SASL_ALL_TESTS: list[ReplicationTestCase] = (
    SASL_VALID_TESTS + SASL_FORMAT_EDGE_TESTS + SASL_EDGE_CASE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(HELLO_SASL_ALL_TESTS))
def test_hello_sasl_supported_mechs(collection, test):
    """Test hello saslSupportedMechs parameter acceptance."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
