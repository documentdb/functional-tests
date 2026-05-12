"""Tests for $planCacheStats validation errors."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.bson_helpers import build_raw_bson_doc
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    NOT_FIRST_STAGE_ERROR,
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
    PLAN_CACHE_STATS_ALL_HOSTS_NOT_SHARDED_ERROR,
    PLAN_CACHE_STATS_COLLECTION_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import TimeseriesCollection

# Property [Duplicate allHosts Keys]: when duplicate allHosts keys are
# provided via an ordered document, the server rejects the document.
DUPLICATE_ALLHOSTS_KEYS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dup_allhosts_true_then_false",
        docs=[],
        pipeline=[
            {"$planCacheStats": build_raw_bson_doc([("allHosts", True), ("allHosts", False)])}
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="duplicate allHosts keys (True then False) should error",
    ),
    StageTestCase(
        "dup_allhosts_false_then_true",
        docs=[],
        pipeline=[
            {"$planCacheStats": build_raw_bson_doc([("allHosts", False), ("allHosts", True)])}
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="duplicate allHosts keys (False then True) should error",
    ),
    StageTestCase(
        "dup_allhosts_false_then_false",
        docs=[],
        pipeline=[
            {"$planCacheStats": build_raw_bson_doc([("allHosts", False), ("allHosts", False)])}
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="duplicate allHosts keys (False then False) should error",
    ),
]

# Property [Unrecognized Fields Error]: unknown fields in the
# $planCacheStats document are rejected with a FAILED_TO_PARSE_ERROR.
UNRECOGNIZED_FIELDS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unrecognized_single_unknown",
        docs=[],
        pipeline=[{"$planCacheStats": {"foo": 1}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="single unknown field should error",
    ),
    StageTestCase(
        "unrecognized_allhosts_plus_extra",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": False, "extra": 1}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="allHosts plus extra field should error",
    ),
    StageTestCase(
        "unrecognized_case_lowercase",
        docs=[],
        pipeline=[{"$planCacheStats": {"allhosts": True}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="'allhosts' (lowercase) should be rejected as unknown field",
    ),
    StageTestCase(
        "unrecognized_case_mixed",
        docs=[],
        pipeline=[{"$planCacheStats": {"AllHosts": True}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="'AllHosts' (mixed case) should be rejected as unknown field",
    ),
    StageTestCase(
        "unrecognized_case_upper",
        docs=[],
        pipeline=[{"$planCacheStats": {"ALLHOSTS": True}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="'ALLHOSTS' (uppercase) should be rejected as unknown field",
    ),
    StageTestCase(
        "unrecognized_unicode_zwsp",
        docs=[],
        pipeline=[{"$planCacheStats": {"all\u200bHosts": True}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="key with ZWSP unicode lookalike should be rejected",
    ),
    StageTestCase(
        "unrecognized_expression_literal",
        docs=[],
        pipeline=[{"$planCacheStats": {"$literal": {}}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="'$literal' expression-like field name should be rejected",
    ),
    StageTestCase(
        "unrecognized_expression_add",
        docs=[],
        pipeline=[{"$planCacheStats": {"$add": [1, 2]}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="'$add' expression-like field name should be rejected",
    ),
    StageTestCase(
        "unrecognized_dot_notation",
        docs=[],
        pipeline=[{"$planCacheStats": {"a.b": 1}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="dot-notation field name should be rejected",
    ),
    StageTestCase(
        "unrecognized_id_field",
        docs=[],
        pipeline=[{"$planCacheStats": {"_id": 1}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="'_id' field name should be rejected",
    ),
    StageTestCase(
        "unrecognized_empty_string",
        docs=[],
        pipeline=[{"$planCacheStats": {"": 1}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="empty string field name should be rejected",
    ),
    StageTestCase(
        "unrecognized_nested_document",
        docs=[],
        pipeline=[{"$planCacheStats": {"nested": {"key": "value"}}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="nested document field name should be rejected",
    ),
]

# Property [Extra Keys in Stage Document Error]: extra keys alongside
# $planCacheStats produce a PIPELINE_STAGE_EXTRA_FIELD_ERROR.
EXTRA_KEYS_IN_STAGE_DOCUMENT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "extra_key_string_value",
        docs=[],
        pipeline=[{"$planCacheStats": {}, "extra": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="extra key alongside $planCacheStats should error",
    ),
    StageTestCase(
        "extra_key_with_valid_allhosts",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": False}, "other": "x"}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="extra key alongside $planCacheStats with valid allHosts should error",
    ),
    StageTestCase(
        "extra_key_multiple",
        docs=[],
        pipeline=[{"$planCacheStats": {}, "a": 1, "b": 2}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="multiple extra keys alongside $planCacheStats should error",
    ),
]

# Property [Non-Existent Collection Error]: $planCacheStats on a non-existent
# collection produces an error.
NONEXISTENT_COLLECTION_DIRECT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nonexistent_direct",
        docs=None,
        pipeline=[{"$planCacheStats": {}}],
        error_code=PLAN_CACHE_STATS_COLLECTION_NOT_FOUND_ERROR,
        msg="$planCacheStats on non-existent collection should error",
    ),
]

# Property [Timeseries Collection Error]: $planCacheStats on a timeseries
# collection produces an error because pipeline rewriting prepends stages.
TIMESERIES_COLLECTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "timeseries_not_first_stage",
        target_collection=TimeseriesCollection(),
        docs=[],
        pipeline=[{"$planCacheStats": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$planCacheStats on timeseries collection should error",
    ),
]

# Property [allHosts True on Standalone/Replica Set Error]: allHosts: true on
# a standalone or replica set produces an error.
ALL_HOSTS_TRUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "allhosts_true_top_level",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": True}}],
        error_code=PLAN_CACHE_STATS_ALL_HOSTS_NOT_SHARDED_ERROR,
        msg="allHosts: true on standalone/replica set should error",
    ),
]

PLANCACHESTATS_VALIDATION_TESTS = (
    DUPLICATE_ALLHOSTS_KEYS_TESTS
    + UNRECOGNIZED_FIELDS_ERROR_TESTS
    + EXTRA_KEYS_IN_STAGE_DOCUMENT_ERROR_TESTS
    + NONEXISTENT_COLLECTION_DIRECT_TESTS
    + TIMESERIES_COLLECTION_ERROR_TESTS
    + ALL_HOSTS_TRUE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(PLANCACHESTATS_VALIDATION_TESTS))
def test_planCacheStats_validation(collection: Collection, test_case: StageTestCase):
    """Test $planCacheStats validation errors."""
    coll = populate_collection(collection, test_case)
    result = execute_command(
        coll,
        {
            "aggregate": coll.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
