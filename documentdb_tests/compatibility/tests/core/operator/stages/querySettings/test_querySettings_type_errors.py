"""Tests for $querySettings stage argument and showDebugQueryShape type errors."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    QUERYSETTINGS_NON_DOCUMENT_ARG_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
    DOUBLE_ZERO,
    INT64_ZERO,
)

# Property [Stage Argument Type Errors]: a non-document value as the stage
# argument is rejected with QUERYSETTINGS_NON_DOCUMENT_ARG_ERROR.
QUERYSETTINGS_STAGE_ARG_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"stage_arg_type_{tid}",
        pipeline=[{"$querySettings": val}],
        error_code=QUERYSETTINGS_NON_DOCUMENT_ARG_ERROR,
        msg=f"$querySettings should reject {tid} as the stage argument",
    )
    for tid, val in [
        ("null", None),
        ("string", "hello"),
        ("int32", 42),
        ("int64", INT64_ZERO),
        ("double", DOUBLE_ZERO),
        ("decimal128", DECIMAL128_ZERO),
        ("bool", True),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1)),
        ("timestamp", Timestamp(0, 0)),
        ("binary", Binary(b"x")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("array_with_config", [{"showDebugQueryShape": True}]),
    ]
]

# Property [showDebugQueryShape BSON Type Strictness]: a non-boolean BSON
# type as showDebugQueryShape is rejected with TYPE_MISMATCH_ERROR.
QUERYSETTINGS_DEBUG_SHAPE_BSON_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"debug_shape_bson_{tid}",
        pipeline=[{"$querySettings": {"showDebugQueryShape": val}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$querySettings should reject {tid} as showDebugQueryShape",
    )
    for tid, val in [
        ("null", None),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 42.0),
        ("decimal128", Decimal128("42")),
        ("string", "hello"),
        ("object", {"k": "v"}),
        ("array", ["x"]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1)),
        ("timestamp", Timestamp(0, 0)),
        ("binary", Binary(b"x")),
        ("binary_uuid", Binary(uuid.uuid4().bytes, subtype=4)),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [showDebugQueryShape Coercion Strictness]: a non-boolean value
# is not coerced to a boolean via truthy/falsy semantics or expression
# evaluation for showDebugQueryShape; each is rejected with
# TYPE_MISMATCH_ERROR.
QUERYSETTINGS_DEBUG_SHAPE_COERCION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"debug_shape_coerce_{tid}",
        pipeline=[{"$querySettings": {"showDebugQueryShape": val}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$querySettings should reject {tid} as showDebugQueryShape",
    )
    for tid, val in [
        ("int32_zero", 0),
        ("int32_one", 1),
        ("int64_zero", INT64_ZERO),
        ("double_zero", DOUBLE_ZERO),
        ("double_one", 1.0),
        ("decimal128_zero", DECIMAL128_ZERO),
        ("string_true", "true"),
        ("string_false", "false"),
        ("object_arbitrary", {"a": 1}),
        ("expr_literal_true", {"$literal": True}),
        ("expr_to_bool", {"$toBool": 1}),
        ("expr_eq", {"$eq": [1, 1]}),
        ("array_empty", []),
        ("array_single_true", [True]),
        ("array_single_none", [None]),
        ("array_nested", [[True]]),
        ("array_two_bools", [True, False]),
    ]
]

QUERYSETTINGS_TYPE_ERROR_TESTS = (
    QUERYSETTINGS_STAGE_ARG_TYPE_ERROR_TESTS
    + QUERYSETTINGS_DEBUG_SHAPE_BSON_TYPE_ERROR_TESTS
    + QUERYSETTINGS_DEBUG_SHAPE_COERCION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(QUERYSETTINGS_TYPE_ERROR_TESTS))
def test_querySettings_type_errors(collection: Collection, test_case: StageTestCase):
    """Test $querySettings stage-argument and showDebugQueryShape type errors."""
    result = execute_admin_command(
        collection,
        {"aggregate": 1, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
