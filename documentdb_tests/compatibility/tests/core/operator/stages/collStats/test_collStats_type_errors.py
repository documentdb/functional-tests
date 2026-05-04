"""Tests for $collStats type validation errors."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, ObjectId, Regex, Timestamp
from bson.max_key import MaxKey
from bson.min_key import MinKey

from documentdb_tests.compatibility.tests.core.operator.stages.collStats.utils.collStats_helpers import (  # noqa: E501
    CollStatsTestCase,
)
from documentdb_tests.framework.error_codes import (
    COLLSTATS_ARG_NOT_OBJECT_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# All BSON types representable by pymongo.
_ALL_BSON_VALUES: list[tuple[Any, str]] = [
    ("string", "string"),
    (42, "int32"),
    (Int64(1), "int64"),
    (3.14, "double"),
    (True, "bool"),
    (None, "null"),
    ([1, 2], "array"),
    ({}, "object"),
    (Decimal128("1"), "decimal128"),
    (ObjectId(), "objectid"),
    (datetime(2024, 1, 1), "datetime"),
    (Timestamp(0, 0), "timestamp"),
    (Binary(b"x"), "binary"),
    (Regex(".*"), "regex"),
    (Code("function(){}"), "code"),
    (Code("function(){}", {}), "code_with_scope"),
    (MinKey(), "minkey"),
    (MaxKey(), "maxkey"),
]

# Property [histograms Sub-Field Type Strictness]: latencyStats.histograms
# accepts only boolean true or false - all non-boolean types produce
# TYPE_MISMATCH_ERROR, including null.
HISTOGRAMS_TYPE_ERROR_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        f"histograms_{case_id}",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"latencyStats": {"histograms": value}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"latencyStats.histograms={value!r} should be rejected as non-boolean",
    )
    for value, case_id in _ALL_BSON_VALUES
    if not isinstance(value, bool)
]

# Property [Sub-Option Type Validation Errors]: all non-document, non-null
# types for latencyStats, storageStats, count, or queryExecStats produce
# TYPE_MISMATCH_ERROR.
SUB_OPTION_TYPE_ERROR_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        f"{sub_option}_{type_id}",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {sub_option: value}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{sub_option!r}={value!r} should be rejected as non-document",
    )
    for sub_option in ["latencyStats", "storageStats", "count", "queryExecStats"]
    for value, type_id in _ALL_BSON_VALUES
    if value is not None and not isinstance(value, dict)
]

# Property [Stage Argument Type Validation]: all non-document BSON types as
# the $collStats argument produce COLLSTATS_ARG_NOT_OBJECT_ERROR.
STAGE_ARG_TYPE_ERROR_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        case_id,
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": value}],
        error_code=COLLSTATS_ARG_NOT_OBJECT_ERROR,
        msg=f"$collStats with {case_id!r} argument should be rejected as non-document",
    )
    for value, case_id in _ALL_BSON_VALUES
    if not isinstance(value, dict)
]

# Property [Stage Argument Expression Rejection]: expression-like objects as
# the $collStats argument produce UNRECOGNIZED_COMMAND_FIELD_ERROR.
STAGE_ARG_EXPRESSION_ERROR_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        case_id,
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": arg}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg=f"$collStats with {case_id!r} expression argument should be rejected",
    )
    for arg, case_id in [
        ({"$literal": {}}, "expression_literal"),
        ({"$add": [1, 2]}, "expression_add"),
    ]
]

COLLSTATS_TYPE_ERROR_TESTS: list[CollStatsTestCase] = (
    HISTOGRAMS_TYPE_ERROR_TESTS
    + SUB_OPTION_TYPE_ERROR_TESTS
    + STAGE_ARG_TYPE_ERROR_TESTS
    + STAGE_ARG_EXPRESSION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(COLLSTATS_TYPE_ERROR_TESTS))
def test_collStats_type_errors(database_client, collection, test):
    """Test $collStats type validation error properties."""
    coll = test.prepare(database_client, collection)
    result = execute_command(
        coll,
        {"aggregate": coll.name, "pipeline": test.pipeline, "cursor": {}},
    )
    test.assert_result(result)
