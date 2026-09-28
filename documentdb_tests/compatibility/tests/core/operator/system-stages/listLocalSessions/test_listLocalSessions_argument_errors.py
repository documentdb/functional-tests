"""Tests for $listLocalSessions invalid-argument errors: types, fields, and mutual exclusion."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
    UNSUPPORTED_FORMAT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [Null and Missing Behavior (errors)]: a null stage argument is rejected
# as a non-object, and a present-but-null required sub-field is counted as missing.
LISTLOCALSESSIONS_NULL_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_stage_argument",
        pipeline=[{"$listLocalSessions": None}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should reject a null stage argument as a non-object",
    ),
    StageTestCase(
        "user_null",
        pipeline=[{"$listLocalSessions": {"users": [{"user": None, "db": "admin"}]}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$listLocalSessions should count a present-but-null user as missing",
    ),
    StageTestCase(
        "db_null",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "db": None}]}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$listLocalSessions should count a present-but-null db as missing",
    ),
]

# Property [Stage Argument Type Strictness (errors)]: a non-object stage argument is rejected.
LISTLOCALSESSIONS_ARGUMENT_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"argument_type_{tid}",
        pipeline=[{"$listLocalSessions": val}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$listLocalSessions should reject a {tid} stage argument as a non-object",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Stage Argument Array Rejection (errors)]: an array stage argument is rejected.
LISTLOCALSESSIONS_ARGUMENT_ARRAY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "argument_empty_array",
        pipeline=[{"$listLocalSessions": []}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should reject an empty array stage argument without unwrapping",
    ),
    StageTestCase(
        "argument_nonempty_array",
        pipeline=[{"$listLocalSessions": [{"user": "nobody", "db": "admin"}]}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should reject a non-empty array stage argument without unwrapping",
    ),
]

# Property [users Field Type Strictness (errors)]: a non-array users value is rejected,
# including an expression object.
LISTLOCALSESSIONS_USERS_TYPE_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"users_type_{tid}",
            pipeline=[{"$listLocalSessions": {"users": val}}],
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"$listLocalSessions should reject a {tid} users value as a non-array",
        )
        for tid, val in [
            ("string", "x"),
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
            ("bool", True),
            ("object", {"user": "nobody", "db": "admin"}),
            ("objectid", ObjectId("507f1f77bcf86cd799439011")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    StageTestCase(
        "users_expression_object",
        pipeline=[
            {"$listLocalSessions": {"users": {"$literal": [{"user": "nobody", "db": "admin"}]}}}
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should reject an expression object users value as a "
        "non-array, without unwrapping or expression evaluation",
    ),
]

# Property [users Element Type Strictness (errors)]: a non-object users element is
# rejected, including one following a valid element.
LISTLOCALSESSIONS_ELEMENT_TYPE_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"element_type_{tid}",
            pipeline=[{"$listLocalSessions": {"users": [val]}}],
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"$listLocalSessions should reject a {tid} users element as a non-object",
        )
        for tid, val in [
            ("string", "x"),
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
            ("bool", True),
            ("array", [1, 2]),
            ("objectid", ObjectId("507f1f77bcf86cd799439011")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    StageTestCase(
        "element_invalid_after_valid",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "db": "admin"}, "x"]}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should validate every element and reject a non-object "
        "element following a valid element",
    ),
]

# Property [user Sub-field Type Strictness (errors)]: a non-string user sub-field is
# rejected, including an expression object.
LISTLOCALSESSIONS_USER_TYPE_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"user_type_{tid}",
            pipeline=[{"$listLocalSessions": {"users": [{"user": val, "db": "admin"}]}}],
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"$listLocalSessions should reject a {tid} user sub-field as a non-string",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
            ("bool", True),
            ("array", ["nobody"]),
            ("object", {"a": 1}),
            ("objectid", ObjectId("507f1f77bcf86cd799439011")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    StageTestCase(
        "user_expression_object",
        pipeline=[{"$listLocalSessions": {"users": [{"user": {"$literal": "x"}, "db": "admin"}]}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should reject an expression object user sub-field as a "
        "non-string, without unwrapping or expression evaluation",
    ),
]

# Property [db Sub-field Type Strictness (errors)]: a non-string db sub-field is
# rejected, including an expression object.
LISTLOCALSESSIONS_DB_TYPE_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"db_type_{tid}",
            pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "db": val}]}}],
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"$listLocalSessions should reject a {tid} db sub-field as a non-string",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
            ("bool", True),
            ("array", ["admin"]),
            ("object", {"a": 1}),
            ("objectid", ObjectId("507f1f77bcf86cd799439011")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    StageTestCase(
        "db_expression_object",
        pipeline=[
            {"$listLocalSessions": {"users": [{"user": "nobody", "db": {"$concat": ["a", "b"]}}]}}
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should reject an expression object db sub-field as a "
        "non-string, without unwrapping or expression evaluation",
    ),
]

# Property [allUsers Type Strictness (errors)]: a non-boolean allUsers value is
# rejected, including an expression object.
LISTLOCALSESSIONS_ALLUSERS_TYPE_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"allusers_type_{tid}",
            pipeline=[{"$listLocalSessions": {"allUsers": val}}],
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"$listLocalSessions should reject a {tid} allUsers value as a non-boolean",
        )
        for tid, val in [
            ("int64", Int64(1)),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
            ("object", {"a": 1}),
            ("objectid", ObjectId("507f1f77bcf86cd799439011")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    StageTestCase(
        "allusers_expression_object",
        pipeline=[{"$listLocalSessions": {"allUsers": {"$literal": True}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should reject an expression object allUsers value as a "
        "non-boolean, without unwrapping or expression evaluation",
    ),
]

# Property [allUsers Coercion (errors)]: allUsers does not coerce numbers or strings
# to boolean.
LISTLOCALSESSIONS_ALLUSERS_COERCION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"allusers_coercion_{tid}",
        pipeline=[{"$listLocalSessions": {"allUsers": val}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$listLocalSessions should reject {tid} allUsers without coercion to boolean",
    )
    for tid, val in [
        ("zero", 0),
        ("one", 1),
        ("one_double", 1.0),
        ("two_and_half", 2.5),
        ("nan", FLOAT_NAN),
        ("infinity", FLOAT_INFINITY),
        ("empty_string", ""),
        ("string_true", "true"),
        ("string_false", "false"),
    ]
]

# Property [allUsers Array Rejection (errors)]: an array allUsers value is rejected.
LISTLOCALSESSIONS_ALLUSERS_ARRAY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "allusers_empty_array",
        pipeline=[{"$listLocalSessions": {"allUsers": []}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should reject an empty array allUsers value without unwrapping",
    ),
    StageTestCase(
        "allusers_single_element_array",
        pipeline=[{"$listLocalSessions": {"allUsers": [True]}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should reject a single-element array allUsers value "
        "without unwrapping",
    ),
    StageTestCase(
        "allusers_multi_element_array",
        pipeline=[{"$listLocalSessions": {"allUsers": [True, False]}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$listLocalSessions should reject a multi-element array allUsers value "
        "without unwrapping",
    ),
]

# Property [Required Sub-field Errors]: a non-null users element missing the user or db
# sub-field is rejected, including after a skipped null.
LISTLOCALSESSIONS_REQUIRED_SUBFIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "element_missing_user",
        pipeline=[{"$listLocalSessions": {"users": [{"db": "admin"}]}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$listLocalSessions should reject an element missing the required user sub-field",
    ),
    StageTestCase(
        "element_missing_db",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody"}]}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$listLocalSessions should reject an element missing the required db sub-field",
    ),
    StageTestCase(
        "element_empty",
        pipeline=[{"$listLocalSessions": {"users": [{}]}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$listLocalSessions should reject an empty element missing both required sub-fields",
    ),
    StageTestCase(
        "element_invalid_after_null",
        pipeline=[{"$listLocalSessions": {"users": [None, {"user": "nobody"}]}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$listLocalSessions should still validate a non-null element following a "
        "skipped null and reject it for a missing required sub-field",
    ),
]

# Property [Unknown Field Errors (Syntax Validation)]: an unrecognized field name is
# rejected; field names are matched case-sensitively at the top level and inside elements.
LISTLOCALSESSIONS_UNKNOWN_FIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unknown_top_level_field",
        pipeline=[{"$listLocalSessions": {"foo": 1}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject an unknown top-level field",
    ),
    StageTestCase(
        "unknown_top_level_field_with_valid",
        pipeline=[{"$listLocalSessions": {"foo": 1, "allUsers": None}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject an unknown top-level field even when a "
        "valid field is also present",
    ),
    StageTestCase(
        "top_level_allusers_lowercase",
        pipeline=[{"$listLocalSessions": {"allusers": True}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject a lowercase allUsers as an unknown field",
    ),
    StageTestCase(
        "top_level_allusers_capitalized",
        pipeline=[{"$listLocalSessions": {"AllUsers": True}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject a capitalized AllUsers as an unknown field",
    ),
    StageTestCase(
        "top_level_users_capitalized",
        pipeline=[{"$listLocalSessions": {"Users": []}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject a capitalized Users as an unknown field",
    ),
    StageTestCase(
        "top_level_users_uppercase",
        pipeline=[{"$listLocalSessions": {"USERS": []}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject an uppercase USERS as an unknown field",
    ),
    StageTestCase(
        "element_extra_subfield",
        pipeline=[
            {"$listLocalSessions": {"users": [{"user": "nobody", "db": "admin", "extra": 1}]}}
        ],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject an unknown sub-field inside a users element",
    ),
    StageTestCase(
        "element_user_capitalized",
        pipeline=[{"$listLocalSessions": {"users": [{"User": "nobody", "db": "admin"}]}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject a capitalized User sub-field as an unknown field",
    ),
    StageTestCase(
        "element_user_uppercase",
        pipeline=[{"$listLocalSessions": {"users": [{"USER": "nobody", "db": "admin"}]}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject an uppercase USER sub-field as an unknown field",
    ),
    StageTestCase(
        "element_db_capitalized",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "Db": "admin"}]}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject a capitalized Db sub-field as an unknown field",
    ),
    StageTestCase(
        "element_db_uppercase",
        pipeline=[{"$listLocalSessions": {"users": [{"user": "nobody", "DB": "admin"}]}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$listLocalSessions should reject an uppercase DB sub-field as an unknown field",
    ),
]

# Property [Mutual Exclusion Error]: a users array non-empty after null-skipping
# combined with allUsers: true is rejected.
LISTLOCALSESSIONS_MUTUAL_EXCLUSION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "users_element_with_all_users_true",
        pipeline=[
            {
                "$listLocalSessions": {
                    "users": [{"user": "nobody", "db": "admin"}],
                    "allUsers": True,
                }
            }
        ],
        error_code=UNSUPPORTED_FORMAT_ERROR,
        msg="$listLocalSessions should reject a non-empty users array combined with "
        "allUsers: true",
    ),
    StageTestCase(
        "users_null_then_element_with_all_users_true",
        # The array is non-empty only after the leading null element is skipped,
        # confirming the conflict is decided on the post-skip filter, not the raw
        # array length.
        pipeline=[
            {
                "$listLocalSessions": {
                    "users": [None, {"user": "nobody", "db": "admin"}],
                    "allUsers": True,
                }
            }
        ],
        error_code=UNSUPPORTED_FORMAT_ERROR,
        msg="$listLocalSessions should reject a users array that is non-empty after "
        "null-element skipping combined with allUsers: true",
    ),
]

LISTLOCALSESSIONS_ERROR_TESTS = (
    LISTLOCALSESSIONS_NULL_ERROR_TESTS
    + LISTLOCALSESSIONS_ARGUMENT_TYPE_ERROR_TESTS
    + LISTLOCALSESSIONS_ARGUMENT_ARRAY_ERROR_TESTS
    + LISTLOCALSESSIONS_USERS_TYPE_ERROR_TESTS
    + LISTLOCALSESSIONS_ELEMENT_TYPE_ERROR_TESTS
    + LISTLOCALSESSIONS_USER_TYPE_ERROR_TESTS
    + LISTLOCALSESSIONS_DB_TYPE_ERROR_TESTS
    + LISTLOCALSESSIONS_ALLUSERS_TYPE_ERROR_TESTS
    + LISTLOCALSESSIONS_ALLUSERS_COERCION_ERROR_TESTS
    + LISTLOCALSESSIONS_ALLUSERS_ARRAY_ERROR_TESTS
    + LISTLOCALSESSIONS_REQUIRED_SUBFIELD_ERROR_TESTS
    + LISTLOCALSESSIONS_UNKNOWN_FIELD_ERROR_TESTS
    + LISTLOCALSESSIONS_MUTUAL_EXCLUSION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LISTLOCALSESSIONS_ERROR_TESTS))
def test_listLocalSessions_error(collection: Collection, test_case: StageTestCase):
    """Test $listLocalSessions stage error cases."""
    result = execute_command(
        collection,
        {"aggregate": 1, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)  # type: ignore[arg-type]
