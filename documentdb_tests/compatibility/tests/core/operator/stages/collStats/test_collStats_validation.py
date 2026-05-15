"""Tests for $collStats argument validation and error precedence."""

from __future__ import annotations

import pytest
from bson.son import SON

from documentdb_tests.compatibility.tests.core.operator.stages.collStats.utils.collStats_helpers import (  # noqa: E501
    CollStatsTestCase,
)
from documentdb_tests.framework.bson_helpers import build_raw_bson_doc
from documentdb_tests.framework.error_codes import (
    COLLSTATS_NON_EMPTY_OPTION_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, NotExists
from documentdb_tests.framework.target_collection import ViewCollection

# Property [Multiple Options - Order Independence]: the ordering of sub-options
# in the argument document has no effect on which sections appear or their
# values.
ORDER_INDEPENDENCE_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "ordering_lscq",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$collStats": SON(
                    [
                        ("latencyStats", {}),
                        ("storageStats", {}),
                        ("count", {}),
                        ("queryExecStats", {}),
                    ]
                )
            }
        ],
        checks={
            "latencyStats": Exists(),
            "storageStats": Exists(),
            "count": Eq(1),
            "queryExecStats": Exists(),
        },
        msg="sub-option ordering should not affect output",
    ),
    CollStatsTestCase(
        "ordering_qcsl",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$collStats": SON(
                    [
                        ("queryExecStats", {}),
                        ("count", {}),
                        ("storageStats", {}),
                        ("latencyStats", {}),
                    ]
                )
            }
        ],
        checks={
            "latencyStats": Exists(),
            "storageStats": Exists(),
            "count": Eq(1),
            "queryExecStats": Exists(),
        },
        msg="sub-option ordering should not affect output",
    ),
    CollStatsTestCase(
        "ordering_clqs",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$collStats": SON(
                    [
                        ("count", {}),
                        ("latencyStats", {}),
                        ("queryExecStats", {}),
                        ("storageStats", {}),
                    ]
                )
            }
        ],
        checks={
            "latencyStats": Exists(),
            "storageStats": Exists(),
            "count": Eq(1),
            "queryExecStats": Exists(),
        },
        msg="sub-option ordering should not affect output",
    ),
]

# Property [Multiple Options - Duplicate Keys]: when duplicate keys are present
# in the argument document, the option is enabled if any occurrence has a
# non-null value, regardless of key ordering.
DUPLICATE_KEY_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "count_null_then_enabled",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": build_raw_bson_doc([("count", None), ("count", {})])}],
        checks={"count": Exists()},
        msg="duplicate keys (null then enabled) should enable count",
    ),
    CollStatsTestCase(
        "count_enabled_then_null",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": build_raw_bson_doc([("count", {}), ("count", None)])}],
        checks={"count": Exists()},
        msg="duplicate keys (enabled then null) should enable count",
    ),
    CollStatsTestCase(
        "storageStats_null_then_enabled",
        docs=[{"_id": 1}],
        pipeline=[
            {"$collStats": build_raw_bson_doc([("storageStats", None), ("storageStats", {})])}
        ],
        checks={"storageStats": Exists()},
        msg="duplicate keys (null then enabled) should enable storageStats",
    ),
    CollStatsTestCase(
        "storageStats_enabled_then_null",
        docs=[{"_id": 1}],
        pipeline=[
            {"$collStats": build_raw_bson_doc([("storageStats", {}), ("storageStats", None)])}
        ],
        checks={"storageStats": Exists()},
        msg="duplicate keys (enabled then null) should enable storageStats",
    ),
    CollStatsTestCase(
        "latencyStats_null_then_enabled",
        docs=[{"_id": 1}],
        pipeline=[
            {"$collStats": build_raw_bson_doc([("latencyStats", None), ("latencyStats", {})])}
        ],
        checks={"latencyStats": Exists()},
        msg="duplicate keys (null then enabled) should enable latencyStats",
    ),
    CollStatsTestCase(
        "latencyStats_enabled_then_null",
        docs=[{"_id": 1}],
        pipeline=[
            {"$collStats": build_raw_bson_doc([("latencyStats", {}), ("latencyStats", None)])}
        ],
        checks={"latencyStats": Exists()},
        msg="duplicate keys (enabled then null) should enable latencyStats",
    ),
    CollStatsTestCase(
        "queryExecStats_null_then_enabled",
        docs=[{"_id": 1}],
        pipeline=[
            {"$collStats": build_raw_bson_doc([("queryExecStats", None), ("queryExecStats", {})])}
        ],
        checks={"queryExecStats": Exists()},
        msg="duplicate keys (null then enabled) should enable queryExecStats",
    ),
    CollStatsTestCase(
        "queryExecStats_enabled_then_null",
        docs=[{"_id": 1}],
        pipeline=[
            {"$collStats": build_raw_bson_doc([("queryExecStats", {}), ("queryExecStats", None)])}
        ],
        checks={"queryExecStats": Exists()},
        msg="duplicate keys (enabled then null) should enable queryExecStats",
    ),
]

# Property [Unknown Sub-Fields - Rejection]: latencyStats rejects unknown
# sub-fields with UNRECOGNIZED_COMMAND_FIELD_ERROR, while count and
# queryExecStats reject any non-empty document with
# COLLSTATS_NON_EMPTY_OPTION_ERROR.
UNKNOWN_SUBFIELD_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "storageStats_plain_unknown",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"unknownField": 1}}}],
        checks={"storageStats.scaleFactor": Eq(1)},
        msg="storageStats should silently ignore unknown fields",
    ),
    CollStatsTestCase(
        "storageStats_expression_like_add",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"$add": [1, 2]}}}],
        checks={"storageStats.scaleFactor": Eq(1)},
        msg="storageStats should silently ignore expression-like keys",
    ),
    CollStatsTestCase(
        "storageStats_expression_like_literal",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"$literal": {}}}}],
        checks={"storageStats.scaleFactor": Eq(1)},
        msg="storageStats should silently ignore $literal key",
    ),
    CollStatsTestCase(
        "latencyStats_unknown",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"latencyStats": {"unknownField": 1}}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="latencyStats should reject unknown sub-fields",
    ),
    CollStatsTestCase(
        "count_unknown",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"count": {"unknownField": 1}}}],
        error_code=COLLSTATS_NON_EMPTY_OPTION_ERROR,
        msg="count should reject non-empty document",
    ),
    CollStatsTestCase(
        "queryExecStats_unknown",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"queryExecStats": {"unknownField": 1}}}],
        error_code=COLLSTATS_NON_EMPTY_OPTION_ERROR,
        msg="queryExecStats should reject non-empty document",
    ),
]

# Property [Error Precedence]: validation errors are prioritized by category
# before collection context. Type errors and non-empty-option errors fire
# before view or namespace-not-found errors. When multiple sub-option
# validation errors exist in the same document, the first field in document
# order determines which error is reported.
ERROR_PRECEDENCE_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "type_error_over_view",
        target_collection=ViewCollection(),
        pipeline=[{"$collStats": {"storageStats": "bad"}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="type error should fire before view error",
    ),
    CollStatsTestCase(
        "non_empty_count_over_view",
        target_collection=ViewCollection(),
        pipeline=[{"$collStats": {"count": {"x": 1}}}],
        error_code=COLLSTATS_NON_EMPTY_OPTION_ERROR,
        msg="non-empty count error should fire before view error",
    ),
    CollStatsTestCase(
        "type_error_over_nonexistent",
        pipeline=[{"$collStats": {"count": "bad"}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="type error should fire before non-existent error",
    ),
    CollStatsTestCase(
        "non_empty_count_over_nonexistent",
        pipeline=[{"$collStats": {"count": {"x": 1}}}],
        error_code=COLLSTATS_NON_EMPTY_OPTION_ERROR,
        msg="non-empty count error should fire before non-existent error",
    ),
    CollStatsTestCase(
        "latencyStats_error_first",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"latencyStats": {"unknownField": 1}, "count": {"x": 1}}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="first invalid field (latencyStats) should determine the error",
    ),
    CollStatsTestCase(
        "count_error_first",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"count": {"x": 1}, "latencyStats": {"unknownField": 1}}}],
        error_code=COLLSTATS_NON_EMPTY_OPTION_ERROR,
        msg="first invalid field (count) should determine the error",
    ),
]

# Property [Null Sub-Option Equivalence]: setting any top-level sub-option to
# null is equivalent to omitting it - the corresponding section is absent from
# the output and only the base fields (ns, host, localTime) are returned.
NULL_SUB_OPTION_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "latencyStats_null_equivalent_to_omitted",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"latencyStats": None}}],
        checks={"latencyStats": NotExists()},
        msg="'latencyStats'=null should produce only base fields",
    ),
    CollStatsTestCase(
        "storageStats_null_equivalent_to_omitted",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": None}}],
        checks={"storageStats": NotExists()},
        msg="'storageStats'=null should produce only base fields",
    ),
    CollStatsTestCase(
        "count_null_equivalent_to_omitted",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"count": None}}],
        checks={"count": NotExists()},
        msg="'count'=null should produce only base fields",
    ),
    CollStatsTestCase(
        "queryExecStats_null_equivalent_to_omitted",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"queryExecStats": None}}],
        checks={"queryExecStats": NotExists()},
        msg="'queryExecStats'=null should produce only base fields",
    ),
]

# Property [Sub-Option Case Sensitivity]: sub-option keys are case-sensitive.
# Wrong-cased variants produce UNRECOGNIZED_COMMAND_FIELD_ERROR.
CASE_SENSITIVITY_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        f"{key}_wrong_case",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {key: {}}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg=f"{key!r} should be rejected as unrecognized",
    )
    for key in [
        "LatencyStats",
        "latencystats",
        "StorageStats",
        "storagestats",
        "Count",
        "COUNT",
        "QueryExecStats",
        "queryexecstats",
    ]
]

COLLSTATS_VALIDATION_TESTS: list[CollStatsTestCase] = (
    ORDER_INDEPENDENCE_TESTS
    + DUPLICATE_KEY_TESTS
    + UNKNOWN_SUBFIELD_TESTS
    + ERROR_PRECEDENCE_TESTS
    + NULL_SUB_OPTION_TESTS
    + CASE_SENSITIVITY_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(COLLSTATS_VALIDATION_TESTS))
def test_collStats_validation(database_client, collection, test):
    """Test $collStats argument validation and error precedence properties."""
    coll = test.prepare(database_client, collection)
    result = execute_command(
        coll, {"aggregate": coll.name, "pipeline": test.pipeline, "cursor": {}}
    )
    test.assert_result(result)
