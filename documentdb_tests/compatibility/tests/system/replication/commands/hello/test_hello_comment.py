"""Tests for hello command comment parameter, combined parameters,
and unrecognized fields.

Validates that the comment parameter accepts all BSON types, that
combined parameters work together, and that unrecognized fields are
handled correctly.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64, ObjectId

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

# Property [Comment Type Acceptance]: the comment parameter accepts all
# BSON types without error.
HELLO_COMMENT_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        f"comment_{tid}",
        command=lambda ctx, v=val: {"hello": 1, "comment": v},
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg=f"hello should accept {tid} as comment value",
    )
    for tid, val in [
        ("string", "a log comment"),
        ("int32", 42),
        ("double", 3.14),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("object", {"key": "val"}),
        ("array", [1, "two", 3]),
        ("int64", Int64(999)),
        ("decimal128", Decimal128("1.5")),
        ("objectid", ObjectId()),
    ]
]

# Property [Combined Parameters]: hello accepts saslSupportedMechs and
# comment together or individually.
HELLO_COMBINED_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "combined_both_params",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": "admin.testuser",
            "comment": "both params",
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should accept both saslSupportedMechs and comment",
    ),
    ReplicationTestCase(
        "combined_comment_only",
        command=lambda ctx: {"hello": 1, "comment": "only comment"},
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should succeed with only comment parameter",
    ),
    ReplicationTestCase(
        "combined_sasl_only",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": "admin.testuser",
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should succeed with only saslSupportedMechs parameter",
    ),
]

# Property [Unrecognized Field Handling]: hello silently ignores
# unrecognized fields.
HELLO_UNRECOGNIZED_FIELD_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "unrecognized_single_field",
        command=lambda ctx: {"hello": 1, "unknownField": "value"},
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should ignore unrecognized field",
    ),
    ReplicationTestCase(
        "unrecognized_multiple_fields",
        command=lambda ctx: {
            "hello": 1,
            "unknownField1": 1,
            "unknownField2": 2,
        },
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should ignore multiple unrecognized fields",
    ),
]

HELLO_COMMENT_ALL_TESTS: list[ReplicationTestCase] = (
    HELLO_COMMENT_TESTS + HELLO_COMBINED_TESTS + HELLO_UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(HELLO_COMMENT_ALL_TESTS))
def test_hello_comment(collection, test):
    """Test hello comment parameter, combined parameters, and unrecognized fields."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
