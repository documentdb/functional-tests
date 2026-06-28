"""Tests for $currentOp operand validation, type coercion, and error behavior."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [Operand Type Errors]: an operand that is not a BSON object produces
# a TypeMismatch error, and a literal array operand is never unwrapped into an
# argument list (it is rejected like any other non-object type).
CURRENTOP_OPERAND_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"operand_type_{tid}",
        pipeline=[{"$currentOp": value}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$currentOp should reject a {tid} operand",
    )
    for tid, value in [
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
        ("array_empty", []),
        ("array_string", ["a"]),
        ("array_options_doc", [{"allUsers": True}]),
    ]
]

# Property [Field Type Errors]: each documented boolean field and the
# undocumented truncateOps field rejects every non-boolean BSON type with a
# TypeMismatch error.
CURRENTOP_FIELD_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"field_type_{field_name}_{tid}",
        pipeline=[{"$currentOp": {field_name: value}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$currentOp should reject a {tid} value for the {field_name} field",
    )
    for field_name in (
        "allUsers",
        "idleConnections",
        "idleCursors",
        "idleSessions",
        "localOps",
        "targetAllNodes",
        "truncateOps",
    )
    for tid, value in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("string", "x"),
        ("array", [1]),
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
]

# Property [Field Numeric Non-Coercion]: no numeric field value is coerced to a
# boolean; integer zero/one, whole-number and signed-zero doubles, NaN, and
# infinities are all rejected.
CURRENTOP_FIELD_NUMERIC_COERCION_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"field_numeric_{field_name}_{nid}",
        pipeline=[{"$currentOp": {field_name: value}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$currentOp should not coerce numeric {nid} to a boolean for the {field_name} field",
    )
    for field_name in ("allUsers", "idleConnections")
    for nid, value in [
        ("int_zero", 0),
        ("double_one", 1.0),
        ("double_zero", DOUBLE_ZERO),
        ("nan", FLOAT_NAN),
        ("inf", FLOAT_INFINITY),
    ]
]

# Property [Field String Non-Coercion]: no string field value is coerced to a
# boolean; "true", "false", and the empty string are all rejected.
CURRENTOP_FIELD_STRING_COERCION_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"field_string_{field_name}_{sid}",
        pipeline=[{"$currentOp": {field_name: value}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$currentOp should not coerce string {sid} to a boolean for the {field_name} field",
    )
    for field_name in ("allUsers", "idleConnections")
    for sid, value in [
        ("true", "true"),
        ("false", "false"),
        ("empty", ""),
    ]
]

# Property [Field Array Non-Unwrapping]: an array field value is rejected and
# never unwrapped into a boolean, regardless of its contents.
CURRENTOP_FIELD_ARRAY_COERCION_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"field_array_{field_name}_{aid}",
        pipeline=[{"$currentOp": {field_name: value}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$currentOp should reject an array ({aid}) for the {field_name} field",
    )
    for field_name in ("allUsers", "idleConnections")
    for aid, value in [
        ("empty", []),
        ("single_true", [True]),
        ("nested", [[True]]),
    ]
]

# Property [Field Expression Non-Evaluation]: a field value is not evaluated as
# an aggregation expression; expression documents and field-path strings are
# rejected by their literal BSON type.
CURRENTOP_FIELD_EXPRESSION_COERCION_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"field_expr_{field_name}_{eid}",
        pipeline=[{"$currentOp": {field_name: value}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$currentOp should not evaluate {eid} as an expression for the {field_name} field",
    )
    for field_name in ("allUsers", "idleConnections")
    for eid, value in [
        ("literal", {"$literal": True}),
        ("toBool", {"$toBool": 1}),
        ("and", {"$and": []}),
        ("field_path", "$active"),
        ("root_var", "$$ROOT"),
    ]
]

# Property [Null Value Errors]: a null operand is rejected with a TypeMismatch
# error rather than treated as a valid default form, and any field set to
# literal null is rejected rather than falling back to that field's default.
CURRENTOP_NULL_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "operand_null",
        pipeline=[{"$currentOp": None}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$currentOp should reject a null operand",
    ),
    *(
        StageTestCase(
            f"field_null_{field_name}",
            pipeline=[{"$currentOp": {field_name: None}}],
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"$currentOp should reject a null value for the {field_name} field",
        )
        for field_name in (
            "allUsers",
            "idleConnections",
            "idleCursors",
            "idleSessions",
            "localOps",
            "targetAllNodes",
            "truncateOps",
        )
    ),
]

# Property [Unknown Field Errors]: any field name not in the recognized set,
# including wrong-case variants of valid fields and the empty name, produces an
# IDLUnknownField error regardless of the field's value type.
CURRENTOP_UNKNOWN_FIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"unknown_field_{tid}",
        pipeline=[{"$currentOp": {name: value}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg=f"$currentOp should reject unrecognized field {tid}",
    )
    for tid, name, value in [
        ("plain", "foo", 1),
        ("valid_looking_option", "comment", "x"),
        ("case_variant", "AllUsers", True),
        ("dollar_prefixed", "$db", "admin"),
        ("empty_name", "", True),
    ]
]

# Property [Operand and Default Behavior]: a well-formed operand of optional
# boolean options is accepted and the stage returns ok:1.
CURRENTOP_OPERAND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_operand",
        pipeline=[{"$currentOp": {}}],
        expected={"ok": Eq(1.0)},
        msg="$currentOp should accept an empty operand and use all default values",
    ),
    *(
        StageTestCase(
            f"field_{field_name}_{str(value).lower()}",
            pipeline=[{"$currentOp": {field_name: value}}],
            expected={"ok": Eq(1.0)},
            msg=f"$currentOp should accept {field_name} set to {str(value).lower()}",
        )
        for field_name in (
            "allUsers",
            "idleConnections",
            "idleCursors",
            "idleSessions",
            "localOps",
            "truncateOps",
        )
        for value in (True, False)
    ),
    StageTestCase(
        "field_targetAllNodes_false",
        pipeline=[{"$currentOp": {"targetAllNodes": False}}],
        expected={"ok": Eq(1.0)},
        msg="$currentOp should accept targetAllNodes set to false",
    ),
    StageTestCase(
        "combo_all_documented_true",
        pipeline=[
            {
                "$currentOp": {
                    "allUsers": True,
                    "idleConnections": True,
                    "idleCursors": True,
                    "idleSessions": True,
                    "localOps": True,
                    "targetAllNodes": False,
                }
            }
        ],
        expected={"ok": Eq(1.0)},
        msg="$currentOp should accept all documented fields combined in one operand",
    ),
    StageTestCase(
        "combo_all_documented_false",
        pipeline=[
            {
                "$currentOp": {
                    "allUsers": False,
                    "idleConnections": False,
                    "idleCursors": False,
                    "idleSessions": False,
                    "localOps": False,
                    "targetAllNodes": False,
                }
            }
        ],
        expected={"ok": Eq(1.0)},
        msg="$currentOp should accept all documented fields set to false in one operand",
    ),
    StageTestCase(
        "combo_truncateOps_allUsers",
        pipeline=[{"$currentOp": {"truncateOps": True, "allUsers": True}}],
        expected={"ok": Eq(1.0)},
        msg="$currentOp should accept truncateOps combined with a documented field",
    ),
]

# Property [Sharded-Only Errors]: targetAllNodes:true is rejected on a
# non-sharded deployment with a FailedToParse error, and localOps:true combined
# with targetAllNodes:true is rejected with a FailedToParse error for the
# undocumented mutual exclusion.
CURRENTOP_SHARDED_ONLY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sharded_target_all_nodes_true",
        pipeline=[{"$currentOp": {"targetAllNodes": True}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$currentOp should reject targetAllNodes:true on a non-sharded deployment",
    ),
    StageTestCase(
        "sharded_local_ops_and_target_all_nodes_true",
        pipeline=[{"$currentOp": {"localOps": True, "targetAllNodes": True}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$currentOp should reject localOps:true combined with targetAllNodes:true",
    ),
]

CURRENTOP_ERROR_TESTS: list[StageTestCase] = (
    CURRENTOP_OPERAND_TYPE_ERROR_TESTS
    + CURRENTOP_FIELD_TYPE_ERROR_TESTS
    + CURRENTOP_FIELD_NUMERIC_COERCION_TESTS
    + CURRENTOP_FIELD_STRING_COERCION_TESTS
    + CURRENTOP_FIELD_ARRAY_COERCION_TESTS
    + CURRENTOP_FIELD_EXPRESSION_COERCION_TESTS
    + CURRENTOP_NULL_VALUE_ERROR_TESTS
    + CURRENTOP_UNKNOWN_FIELD_ERROR_TESTS
    + CURRENTOP_SHARDED_ONLY_ERROR_TESTS
)

CURRENTOP_OPERAND_AND_ERROR_TESTS: list[StageTestCase] = (
    CURRENTOP_OPERAND_TESTS + CURRENTOP_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CURRENTOP_OPERAND_AND_ERROR_TESTS))
def test_currentOp_operand(collection, test_case: StageTestCase):
    """Test $currentOp accepts well-formed operands and rejects invalid ones."""
    result = execute_admin_command(
        collection,
        {"aggregate": 1, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
