"""
$$NOW error and rejection cases: malformed variable names, command surfaces that
reject it outright, and positions requiring a literal, a field name, or a numeric
value rather than an expression (literal-only stage parameters, partial-filter
index, TTL expiry, $redact). Validator rejection lives alongside its accept-path
sibling in test_now_write_paths.py instead.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BUCKET_AUTO_GRANULARITY_UNKNOWN_ERROR,
    BUCKET_BOUNDARIES_NOT_CONSTANT_ERROR,
    CANNOT_CREATE_INDEX_ERROR,
    DENSIFY_RANGE_BOUNDS_TYPE_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    INVALID_NAMESPACE_ERROR,
    LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
    LET_UNDEFINED_VARIABLE_ERROR,
    LIMIT_INVALID_ARGUMENT_ERROR,
    QUERY_FEATURE_NOT_ALLOWED,
    REDACT_NON_SENTINEL_ERROR,
    SAMPLE_SIZE_NOT_NUMERIC_ERROR,
    SKIP_INVALID_ARGUMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

NOW_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="now_lowercase_is_undefined_variable",
        expression={"$type": "$$now"},
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$$now should fail as an undefined user variable rather than resolve to $$NOW",
    ),
    ExpressionTestCase(
        id="now_lowercase_does_not_resolve_to_missing",
        expression="$$now",
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$$now should error rather than silently evaluate to missing",
    ),
]


@pytest.mark.aggregate  # count/distinct/listCollections/listDatabases below aren't aggregations
@pytest.mark.parametrize("test", pytest_params(NOW_ERROR_TESTS))
def test_now_naming_errors(collection, test: ExpressionTestCase):
    """$$NOW naming edge cases and malformed variable references are rejected."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


def test_now_in_count_expr_is_unavailable(collection):
    """Test $$NOW is rejected in a count query as an unavailable builtin variable."""
    collection.insert_many(
        [{"_id": 1, "d": datetime(2000, 1, 1)}, {"_id": 2, "d": datetime(2100, 1, 1)}]
    )
    result = execute_command(
        collection,
        {"count": collection.name, "query": {"$expr": {"$lt": ["$d", "$$NOW"]}}},
    )
    assertFailureCode(
        result,
        LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
        msg="count should reject $$NOW as an unavailable builtin variable",
    )


def test_now_in_distinct_expr_is_unavailable(collection):
    """Test $$NOW is rejected in a distinct query as an unavailable builtin variable."""
    collection.insert_many(
        [
            {"_id": 1, "d": datetime(2000, 1, 1), "g": "a"},
            {"_id": 2, "d": datetime(2100, 1, 1), "g": "b"},
        ]
    )
    result = execute_command(
        collection,
        {
            "distinct": collection.name,
            "key": "g",
            "query": {"$expr": {"$lt": ["$d", "$$NOW"]}},
        },
    )
    assertFailureCode(
        result,
        LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
        msg="distinct should reject $$NOW as an unavailable builtin variable",
    )


@pytest.mark.collection_mgmt
def test_now_in_list_collections_expr_is_unavailable(collection):
    """Test $$NOW is rejected in a listCollections filter as an unavailable builtin variable."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "listCollections": 1,
            "filter": {"$expr": {"$lt": [{"$toDate": 0}, "$$NOW"]}},
        },
    )
    assertFailureCode(
        result,
        LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
        msg="listCollections should reject $$NOW as an unavailable builtin variable",
    )


@pytest.mark.admin
def test_now_in_list_databases_expr_is_unavailable(collection):
    """Test $$NOW is rejected in a listDatabases filter as an unavailable builtin variable."""
    result = execute_admin_command(
        collection,
        {
            "listDatabases": 1,
            "filter": {"$expr": {"$lt": [{"$toDate": 0}, "$$NOW"]}},
        },
    )
    assertFailureCode(
        result,
        LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
        msg="listDatabases should reject $$NOW as an unavailable builtin variable",
    )


@dataclass(frozen=True)
class RejectedPipelineCase(BaseTestCase):
    """A pipeline that should be rejected because a stage parameter requires a
    literal, a field name, or a numeric value rather than an expression."""

    pipeline: Optional[list[dict[str, Any]]] = None
    error_code: int = 0


# Stage parameters that take a field name or a literal rather than an expression. A
# variable reference there is rejected by the stage's own parser, so the code is the
# stage's parameter error rather than a shared one.
LITERAL_ONLY_STAGE_CASES: list[RejectedPipelineCase] = [
    RejectedPipelineCase(
        id="sort_key",
        pipeline=[{"$sort": {"$$NOW": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$sort should reject $$NOW as a sort key",
    ),
    RejectedPipelineCase(
        id="limit_size",
        pipeline=[{"$limit": "$$NOW"}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject $$NOW as its size",
    ),
    RejectedPipelineCase(
        id="skip_size",
        pipeline=[{"$skip": "$$NOW"}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject $$NOW as its size",
    ),
    RejectedPipelineCase(
        id="sample_size",
        pipeline=[{"$sample": {"size": "$$NOW"}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject $$NOW as its size",
    ),
    RejectedPipelineCase(
        id="unwind_path",
        pipeline=[{"$unwind": "$$NOW"}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unwind should reject $$NOW as a field path",
    ),
    RejectedPipelineCase(
        id="bucket_boundaries",
        pipeline=[{"$bucket": {"groupBy": "$v", "boundaries": ["$$NOW", 10], "default": "other"}}],
        error_code=BUCKET_BOUNDARIES_NOT_CONSTANT_ERROR,
        msg="$bucket should reject $$NOW as a boundary",
    ),
    RejectedPipelineCase(
        id="bucket_auto_granularity",
        pipeline=[{"$bucketAuto": {"groupBy": "$v", "buckets": 1, "granularity": "$$NOW"}}],
        error_code=BUCKET_AUTO_GRANULARITY_UNKNOWN_ERROR,
        msg="$bucketAuto should reject $$NOW as its granularity",
    ),
    RejectedPipelineCase(
        id="densify_range_bounds",
        pipeline=[{"$densify": {"field": "v", "range": {"step": 1, "bounds": ["$$NOW", 10]}}}],
        error_code=DENSIFY_RANGE_BOUNDS_TYPE_ERROR,
        msg="$densify should reject $$NOW as a range bound",
    ),
    RejectedPipelineCase(
        id="fill_sort_by",
        pipeline=[{"$fill": {"sortBy": {"$$NOW": 1}, "output": {"v": {"method": "linear"}}}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$fill should reject $$NOW as a sortBy key",
    ),
    RejectedPipelineCase(
        id="out_namespace",
        pipeline=[{"$out": {"db": "$$NOW", "coll": "target"}}],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$out should reject $$NOW as its target database",
    ),
    RejectedPipelineCase(
        id="merge_namespace",
        pipeline=[{"$merge": {"into": {"db": "$$NOW", "coll": "target"}}}],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$merge should reject $$NOW as its target database",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(LITERAL_ONLY_STAGE_CASES))
def test_now_rejected_in_literal_only_stage_parameter(collection, test: RejectedPipelineCase):
    """Test stage parameters requiring a literal reject a $$NOW reference."""
    collection.insert_one({"_id": 1, "v": 1})

    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}}
    )

    assertFailureCode(result, test.error_code, msg=test.msg)


@pytest.mark.index
def test_now_rejected_in_a_partial_filter_expression(collection):
    """Test a partial index filter referencing $$NOW is rejected at create time."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"ts": 1},
                    "name": "now_partial",
                    "partialFilterExpression": {"$expr": {"$lte": ["$ts", "$$NOW"]}},
                }
            ],
        },
    )

    assertFailureCode(
        result,
        QUERY_FEATURE_NOT_ALLOWED,
        msg="A partial index filter should reject a $$NOW reference",
    )


@pytest.mark.index
def test_now_rejected_as_expire_after_seconds(collection):
    """Test a TTL index cannot take $$NOW as its expiry value."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"ts": 1}, "name": "now_ttl", "expireAfterSeconds": "$$NOW"}],
        },
    )

    assertFailureCode(
        result,
        CANNOT_CREATE_INDEX_ERROR,
        msg="A TTL expiry accepts no expressions, so the variable cannot be smuggled in",
    )


@pytest.mark.aggregate
def test_now_rejected_as_a_redact_result(collection):
    """Test $redact rejects $$NOW as its returned value."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$redact": "$$NOW"}], "cursor": {}},
    )

    assertFailureCode(
        result,
        REDACT_NON_SENTINEL_ERROR,
        msg="$redact should only accept its own three control variables as a result",
    )
