"""Tests for $listLocalSessions stage success behavior across valid argument shapes."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.lazy_payload import lazy
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Stage Argument Acceptance]: the no-filter shapes ({} and {allUsers: <bool>})
# are accepted.
LISTLOCALSESSIONS_ARGUMENT_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_document",
        pipeline=[{"$listLocalSessions": {}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should accept an empty document",
    ),
    StageTestCase(
        "all_users_true",
        pipeline=[{"$listLocalSessions": {"allUsers": True}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should accept allUsers: true",
    ),
    StageTestCase(
        "all_users_false",
        pipeline=[{"$listLocalSessions": {"allUsers": False}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should accept allUsers: false",
    ),
]

# Property [Null and Missing Behavior]: a null or absent users/allUsers field is treated
# as absent, and a null users element is silently skipped.
LISTLOCALSESSIONS_NULL_MISSING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "users_null",
        pipeline=[{"$listLocalSessions": {"users": None}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should treat a null users field as absent",
    ),
    StageTestCase(
        "all_users_null",
        pipeline=[{"$listLocalSessions": {"allUsers": None}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should treat a null allUsers field as absent",
    ),
    StageTestCase(
        "users_array_single_null",
        pipeline=[{"$listLocalSessions": {"users": [None]}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should silently skip a single null users element",
    ),
    StageTestCase(
        "users_array_element_then_null",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "db": "admin"}, None]}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should silently skip a null element following a "
        "well-formed element",
    ),
]

# Property [users Array and Element Handling]: an empty users array applies no filter
# and the empty-string principal is valid.
LISTLOCALSESSIONS_USERS_ARRAY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "users_empty_array",
        pipeline=[{"$listLocalSessions": {"users": []}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should accept an empty users array as no filter",
    ),
    StageTestCase(
        "users_empty_principal",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "", "db": ""}]}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should accept the empty-string principal",
    ),
]

# Property [Parameter Interactions]: users and allUsers coexist when the users filter is
# empty (after null-skipping) or absent, and allUsers: false never conflicts.
LISTLOCALSESSIONS_PARAMETER_INTERACTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "users_filter_all_users_false",
        pipeline=[
            {
                "$listLocalSessions": {
                    "users": [{"user": "nobody", "db": "admin"}],
                    "allUsers": False,
                }
            }
        ],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should accept a non-empty users filter with allUsers: false",
    ),
    StageTestCase(
        "empty_users_all_users_true",
        pipeline=[{"$listLocalSessions": {"users": [], "allUsers": True}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should accept an empty users array with allUsers: true "
        "without conflict",
    ),
    StageTestCase(
        "null_element_users_all_users_true",
        pipeline=[{"$listLocalSessions": {"users": [None], "allUsers": True}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should accept a users array that is empty after "
        "null-skipping with allUsers: true without conflict",
    ),
    StageTestCase(
        "users_null_all_users_true",
        pipeline=[{"$listLocalSessions": {"users": None, "allUsers": True}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should treat a null users field as absent with allUsers: true",
    ),
    StageTestCase(
        "users_null_all_users_null",
        pipeline=[{"$listLocalSessions": {"users": None, "allUsers": None}}],
        expected={"ok": Eq(1.0)},
        msg="$listLocalSessions should treat null users and null allUsers as absent, "
        "equivalent to an empty document",
    ),
]

# Property [users Filter Acceptance]: a well-formed {user, db} element is accepted and
# applied as a filter, so a principal owning no session yields no sessions.
LISTLOCALSESSIONS_USERS_FILTER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "users_well_formed_element",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "db": "admin"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should accept a well-formed users element and "
        "return no sessions for a non-existent principal",
    ),
]

# Property [users Array and Element Handling]: well-formed elements are accepted
# regardless of duplicates, array size, or sub-field key order.
LISTLOCALSESSIONS_USERS_ELEMENT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "users_duplicate_entries",
        pipeline=[
            {
                "$listLocalSessions": {
                    "users": [
                        {"user": "nobody", "db": "admin"},
                        {"user": "nobody", "db": "admin"},
                    ]
                }
            }
        ],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should accept duplicate identical elements without "
        "de-duplication error",
    ),
    StageTestCase(
        "users_large_array_10000",
        pipeline=lazy(
            lambda: [
                {
                    "$listLocalSessions": {
                        "users": [{"user": f"u{i}", "db": "admin"} for i in range(10_000)]
                    }
                }
            ]
        ),
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should accept a large users array",
    ),
    StageTestCase(
        "users_key_order_db_user",
        pipeline=[{"$listLocalSessions": {"users": [{"db": "admin", "user": "nobody"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should treat sub-field key order as irrelevant",
    ),
    StageTestCase(
        "users_whitespace_principal",
        pipeline=[{"$listLocalSessions": {"users": [{"user": " ", "db": " "}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should treat a whitespace principal as a distinct "
        "non-matching principal",
    ),
]

# Property [user Sub-field Content]: the user sub-field is matched as an opaque string
# with no interpretation, coercion, or length limit.
LISTLOCALSESSIONS_USER_CONTENT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "user_digits_only",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "12345", "db": "admin"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should keep a digits-only user as a literal string, "
        "not coerce it to a number",
    ),
    StageTestCase(
        "user_dollar_path",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "$x", "db": "admin"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should store a dollar-prefixed string as literal "
        "text, not a field path or variable reference",
    ),
    StageTestCase(
        "user_unicode",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "caf\u00e9\u4e2d", "db": "admin"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should accept multi-byte Unicode characters in user",
    ),
    StageTestCase(
        "user_embedded_null",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "a\x00b", "db": "admin"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should accept an embedded null character in user",
    ),
    StageTestCase(
        "user_long",
        pipeline=lazy(
            lambda: [{"$listLocalSessions": {"users": [{"user": "x" * 10_000, "db": "admin"}]}}]
        ),
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should accept a very long user with no "
        "operator-specific length limit",
    ),
]

# Property [db Sub-field Content]: the db sub-field is matched as an opaque string with
# no interpretation or coercion, including dot look-alikes that are not the ASCII dot.
LISTLOCALSESSIONS_DB_CONTENT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "db_digits_only",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "db": "12345"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should keep a digits-only db as a literal string, "
        "not coerce it to a number",
    ),
    StageTestCase(
        "db_dollar",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "db": "$"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should store a dollar sign as literal text in db",
    ),
    StageTestCase(
        "db_reserved_ascii",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "db": "<>:|?{}[]"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should accept reserved-looking ASCII characters in db",
    ),
    StageTestCase(
        "db_control_chars",
        # Control characters U+0001, U+0007, U+001F.
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "db": "\x01\x07\x1f"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should accept embedded control characters in db",
    ),
    StageTestCase(
        "db_unicode_whitespace",
        # NBSP U+00A0, en space U+2000, em space U+2003.
        pipeline=[
            {"$listLocalSessions": {"users": [{"user": "nobody", "db": "\u00a0\u2000\u2003"}]}}
        ],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should accept Unicode whitespace in db",
    ),
    StageTestCase(
        "db_fullwidth_full_stop",
        # Fullwidth full stop U+FF0E, a dot look-alike that is not the ASCII dot.
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "db": "\uff0e"}]}}],
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="$listLocalSessions should accept a dot look-alike that is not the ASCII dot in db",
    ),
]

LISTLOCALSESSIONS_SUCCESS_TESTS = (
    LISTLOCALSESSIONS_ARGUMENT_ACCEPTANCE_TESTS
    + LISTLOCALSESSIONS_NULL_MISSING_TESTS
    + LISTLOCALSESSIONS_USERS_ARRAY_TESTS
    + LISTLOCALSESSIONS_PARAMETER_INTERACTION_TESTS
    + LISTLOCALSESSIONS_USERS_FILTER_TESTS
    + LISTLOCALSESSIONS_USERS_ELEMENT_TESTS
    + LISTLOCALSESSIONS_USER_CONTENT_TESTS
    + LISTLOCALSESSIONS_DB_CONTENT_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LISTLOCALSESSIONS_SUCCESS_TESTS))
def test_listLocalSessions_success(collection: Collection, test_case: StageTestCase):
    """Test $listLocalSessions stage success cases against each case's expected result."""
    result = execute_command(
        collection,
        {"aggregate": 1, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg, raw_res=True)
