"""
$$CLUSTER_TIME error surfaces: unavailability by topology, and rejected
positions.

``count``/``distinct``/``listCollections``/``listDatabases`` reject the
variable even with a cluster clock present; a validator accepts it and
re-evaluates per write. Unavailability uses a distinct error from the generic
undefined-variable case. A few rejections stay next to their paired accept case
in other files.

Not covered here because the stage's own folder already rejects a system
variable in the same position with the same code: a $sort key, a $skip size and
an $unwind path. The $redact result check for a resolved value lives with the
other defined system variables in stages/redact/test_redact_validation.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
    assertSuccess,
)
from documentdb_tests.framework.error_codes import (
    BUCKET_AUTO_GRANULARITY_UNKNOWN_ERROR,
    BUCKET_BOUNDARIES_NOT_CONSTANT_ERROR,
    CANNOT_CREATE_INDEX_ERROR,
    CLUSTER_TIME_NOT_AVAILABLE_ERROR,
    DENSIFY_RANGE_BOUNDS_TYPE_ERROR,
    DOCUMENT_VALIDATION_FAILURE_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    INVALID_NAMESPACE_ERROR,
    LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
    LET_UNDEFINED_VARIABLE_ERROR,
    LIMIT_INVALID_ARGUMENT_ERROR,
    QUERY_FEATURE_NOT_ALLOWED,
    SAMPLE_SIZE_NOT_NUMERIC_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import TS_EPOCH, TS_MAX_UNSIGNED32

# The aggregate marker is applied per test rather than module-wide: count,
# distinct, listCollections, listDatabases and createIndexes below are not
# aggregations.
pytestmark = [pytest.mark.requires(cluster_time=True)]


REQUIRES_NO_CLUSTER_TIME = (pytest.mark.requires(cluster_time=False),)


# Property [Unavailable Without a Cluster Clock]: where the deployment has no
# logical cluster clock, every entry point fails with the same bespoke error.
CLUSTER_TIME_UNAVAILABLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="if_null_does_not_rescue",
        marks=REQUIRES_NO_CLUSTER_TIME,
        expression={"$ifNull": ["$$CLUSTER_TIME", "fallback"]},
        error_code=CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="$ifNull should not rescue an unavailable $$CLUSTER_TIME",
    ),
    ExpressionTestCase(
        id="undefined_variable_uses_a_different_code",
        marks=REQUIRES_NO_CLUSTER_TIME,
        expression="$$MADE_UP_VAR",
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="An unknown variable should fail with the undefined-variable error, "
        "not the cluster-time error",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(CLUSTER_TIME_UNAVAILABLE_TESTS))
def test_cluster_time_unavailable(collection, test: ExpressionTestCase):
    """Test referencing $$CLUSTER_TIME without a cluster clock is a hard error."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


# Stage parameters that take a field name or a literal rather than an
# expression. A variable reference there is rejected by the stage's own parser,
# so the code is the stage's parameter error rather than a shared one. A $sort
# key, a $skip size and an $unwind path are omitted: those folders already
# reject a system-variable reference (or a bare $$ token) in the same position
# with the same code.
LITERAL_ONLY_STAGE_CASES: list[StageTestCase] = [
    StageTestCase(
        "limit_size",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$limit": "$$CLUSTER_TIME"}],
        error_code=LIMIT_INVALID_ARGUMENT_ERROR,
        msg="$limit should reject a $$CLUSTER_TIME reference as its size",
    ),
    StageTestCase(
        "sample_size",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sample": {"size": "$$CLUSTER_TIME"}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should reject a $$CLUSTER_TIME reference as its size",
    ),
    StageTestCase(
        "bucket_boundaries",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": ["$$CLUSTER_TIME", 10],
                    "default": "other",
                }
            }
        ],
        error_code=BUCKET_BOUNDARIES_NOT_CONSTANT_ERROR,
        msg="$bucket should reject a $$CLUSTER_TIME reference in its boundaries",
    ),
    StageTestCase(
        "bucket_auto_granularity",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[
            {"$bucketAuto": {"groupBy": "$v", "buckets": 1, "granularity": "$$CLUSTER_TIME"}}
        ],
        error_code=BUCKET_AUTO_GRANULARITY_UNKNOWN_ERROR,
        msg="$bucketAuto should reject a $$CLUSTER_TIME reference as its granularity",
    ),
    StageTestCase(
        "densify_range_bounds",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[
            {
                "$densify": {
                    "field": "v",
                    "range": {"step": 1, "bounds": ["$$CLUSTER_TIME", 10]},
                }
            }
        ],
        error_code=DENSIFY_RANGE_BOUNDS_TYPE_ERROR,
        msg="$densify should reject a $$CLUSTER_TIME reference in its range bounds",
    ),
    StageTestCase(
        "fill_sort_by",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[
            {"$fill": {"sortBy": {"$$CLUSTER_TIME": 1}, "output": {"v": {"method": "linear"}}}}
        ],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$fill should reject a $$CLUSTER_TIME reference as a sort key",
    ),
    StageTestCase(
        "out_namespace",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$out": {"db": "$$CLUSTER_TIME", "coll": "target"}}],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$out should reject a $$CLUSTER_TIME reference in its target namespace",
    ),
    StageTestCase(
        "merge_namespace",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$merge": {"into": {"db": "$$CLUSTER_TIME", "coll": "target"}}}],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$merge should reject a $$CLUSTER_TIME reference in its target namespace",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LITERAL_ONLY_STAGE_CASES))
def test_cluster_time_rejected_in_literal_only_stage_parameter(
    collection, test_case: StageTestCase
):
    """Test stage parameters requiring a literal reject a $$CLUSTER_TIME reference."""
    populate_collection(collection, test_case)

    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}}
    )

    assertResult(
        result,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


@pytest.mark.aggregate
@pytest.mark.requires(cluster_time=False)
def test_cluster_time_unavailable_fails_on_empty_collection(collection):
    """Test the unavailability error fires at parse time on a collection with no documents."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$addFields": {"t": "$$CLUSTER_TIME"}}],
            "cursor": {},
        },
    )

    assertFailureCode(
        result,
        CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="The unavailability error should fire at parse time, not per document",
    )


@pytest.mark.requires(cluster_time=False)
@pytest.mark.find
def test_cluster_time_unavailable_in_find_expr(collection):
    """Test a find filter referencing $$CLUSTER_TIME fails without a cluster clock."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"$expr": {"$gt": ["$$CLUSTER_TIME", None]}}},
    )

    assertFailureCode(
        result,
        CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="A find filter referencing $$CLUSTER_TIME should fail without a cluster clock",
    )


@pytest.mark.requires(cluster_time=False)
@pytest.mark.update
def test_cluster_time_unavailable_in_update_pipeline(collection):
    """Test a pipeline-form update referencing $$CLUSTER_TIME fails without a cluster clock."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": [{"$addFields": {"t": "$$CLUSTER_TIME"}}], "multi": True}],
        },
    )

    assertFailureCode(
        result,
        CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="A pipeline-form update referencing $$CLUSTER_TIME should fail",
    )


@pytest.mark.requires(cluster_time=False)
@pytest.mark.update
def test_cluster_time_unavailable_update_applies_no_writes(collection):
    """Test a failed pipeline-form update leaves every document unmodified."""
    collection.insert_many([{"_id": 1}, {"_id": 2}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": [{"$addFields": {"t": "$$CLUSTER_TIME"}}], "multi": True}],
        },
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"t": {"$exists": True}}}
    )

    assertSuccess(
        result,
        [],
        msg="A failed $$CLUSTER_TIME update should not partially apply writes",
    )


@pytest.mark.requires(cluster_time=False)
@pytest.mark.update
def test_cluster_time_unavailable_in_find_and_modify_pipeline(collection):
    """Test findAndModify with a $$CLUSTER_TIME pipeline fails without a cluster clock."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": [{"$addFields": {"t": "$$CLUSTER_TIME"}}],
        },
    )

    assertFailureCode(
        result,
        CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="findAndModify with a $$CLUSTER_TIME pipeline should fail",
    )


@pytest.mark.aggregate
@pytest.mark.requires(cluster_time=False)
def test_cluster_time_unavailable_in_explain(collection):
    """Test explain of a pipeline referencing $$CLUSTER_TIME fails without a cluster clock."""
    result = execute_command(
        collection,
        {
            "explain": {
                "aggregate": collection.name,
                "pipeline": [{"$addFields": {"t": "$$CLUSTER_TIME"}}],
                "cursor": {},
            },
            "verbosity": "queryPlanner",
        },
    )

    assertFailureCode(
        result,
        CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="explain should surface the unavailability error rather than validating the pipeline",
    )


@pytest.mark.aggregate
@pytest.mark.requires(cluster_time=False)
def test_cluster_time_unavailable_error_is_not_swallowed_by_a_view(collection):
    """Test querying a view whose pipeline references $$CLUSTER_TIME surfaces an error."""
    database = collection.database
    collection.insert_one({"_id": 1})
    database.command(
        {
            "create": f"{collection.name}_unavailable_view",
            "viewOn": collection.name,
            "pipeline": [{"$addFields": {"t": "$$CLUSTER_TIME"}}],
        }
    )

    result = execute_command(
        collection,
        {"aggregate": f"{collection.name}_unavailable_view", "pipeline": [], "cursor": {}},
    )

    assertFailureCode(
        result,
        CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="A view referencing $$CLUSTER_TIME should surface the unavailability error",
    )


@pytest.mark.aggregate
@pytest.mark.requires(cluster_time=False)
def test_now_still_resolves_where_cluster_time_is_unavailable(collection):
    """Test $$NOW resolves in the same pipeline shape that $$CLUSTER_TIME rejects."""
    result = execute_expression(collection, {"$type": "$$NOW"})
    assert_expression_result(
        result,
        expected="date",
        msg="$$NOW should resolve where $$CLUSTER_TIME is unavailable, isolating the failure",
    )


@pytest.mark.index
def test_cluster_time_rejected_in_a_partial_filter_expression(collection):
    """Test a partial index filter referencing $$CLUSTER_TIME is rejected."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"ts": 1},
                    "name": "cluster_time_partial",
                    "partialFilterExpression": {"$expr": {"$lte": ["$ts", "$$CLUSTER_TIME"]}},
                }
            ],
        },
    )

    assertFailureCode(
        result,
        QUERY_FEATURE_NOT_ALLOWED,
        msg="A partial index filter should reject a $$CLUSTER_TIME reference",
    )


@pytest.mark.index
def test_cluster_time_rejected_as_expire_after_seconds(collection):
    """Test a TTL index cannot take $$CLUSTER_TIME as its expiry value."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"ts": 1},
                    "name": "cluster_time_ttl",
                    "expireAfterSeconds": "$$CLUSTER_TIME",
                }
            ],
        },
    )

    assertFailureCode(
        result,
        CANNOT_CREATE_INDEX_ERROR,
        msg="A TTL expiry accepts no expressions, so the variable cannot be smuggled in",
    )


def test_cluster_time_rejected_in_a_count_expr_filter(collection):
    """Test the count command rejects $$CLUSTER_TIME in its query."""
    collection.insert_many([{"_id": 1}, {"_id": 2}])

    result = execute_command(
        collection,
        {"count": collection.name, "query": {"$expr": {"$gt": ["$$CLUSTER_TIME", None]}}},
    )

    assertFailureCode(
        result,
        LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
        msg="count does not expose the runtime constants, so the variable is unavailable there",
    )


def test_cluster_time_rejected_in_a_distinct_expr_filter(collection):
    """Test the distinct command rejects $$CLUSTER_TIME in its query."""
    collection.insert_many([{"_id": 1, "g": "a"}, {"_id": 2, "g": "b"}])

    result = execute_command(
        collection,
        {
            "distinct": collection.name,
            "key": "g",
            "query": {"$expr": {"$gt": ["$$CLUSTER_TIME", None]}},
        },
    )

    assertFailureCode(
        result,
        LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
        msg="distinct does not expose the runtime constants, so the variable is unavailable there",
    )


@pytest.mark.collection_mgmt
def test_cluster_time_rejected_in_a_list_collections_expr_filter(collection):
    """Test listCollections rejects $$CLUSTER_TIME in its filter."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "listCollections": 1,
            "filter": {"$expr": {"$gt": ["$$CLUSTER_TIME", None]}},
        },
    )

    assertFailureCode(
        result,
        LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
        msg="listCollections does not expose the runtime constants, "
        "so the variable is unavailable there",
    )


@pytest.mark.admin
def test_cluster_time_rejected_in_a_list_databases_expr_filter(collection):
    """Test listDatabases rejects $$CLUSTER_TIME in its filter."""
    result = execute_admin_command(
        collection,
        {
            "listDatabases": 1,
            "filter": {"$expr": {"$gt": ["$$CLUSTER_TIME", None]}},
        },
    )

    assertFailureCode(
        result,
        LET_SYSTEM_VARIABLE_IN_VALUE_ERROR,
        msg="listDatabases does not expose the runtime constants, "
        "so the variable is unavailable there",
    )


@pytest.mark.collection_mgmt
def test_cluster_time_in_a_collection_validator_is_accepted(collection):
    """Test a collection validator referencing $$CLUSTER_TIME is accepted at create time."""
    database = collection.database

    result = execute_command(
        collection,
        {
            "create": f"{collection.name}_validated",
            "validator": {"$expr": {"$lte": ["$ts", "$$CLUSTER_TIME"]}},
        },
    )
    database.drop_collection(f"{collection.name}_validated")

    assertSuccess(
        result,
        {"ok": 1.0},
        raw_res=True,
        msg="A validator referencing $$CLUSTER_TIME is accepted rather than rejected",
    )


@pytest.mark.collection_mgmt
@pytest.mark.insert
def test_cluster_time_in_a_collection_validator_is_evaluated_per_write(collection):
    """Test a $$CLUSTER_TIME validator rejects a document whose timestamp is in the future."""
    database = collection.database
    database.command(
        {
            "create": f"{collection.name}_validated",
            "validator": {"$expr": {"$lte": ["$ts", "$$CLUSTER_TIME"]}},
        }
    )

    result = execute_command(
        collection,
        {
            "insert": f"{collection.name}_validated",
            "documents": [{"_id": 1, "ts": TS_MAX_UNSIGNED32}],
        },
    )
    database.drop_collection(f"{collection.name}_validated")

    assertFailureCode(
        result,
        DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="A $$CLUSTER_TIME validator should be evaluated against each written document",
    )


@pytest.mark.collection_mgmt
@pytest.mark.insert
def test_cluster_time_in_a_collection_validator_accepts_a_conforming_document(collection):
    """Test a $$CLUSTER_TIME validator accepts a document satisfying the constraint at write time.

    This is the accept half that distinguishes "evaluated fresh per write" from
    "always rejects everything". The reject half is
    ``test_cluster_time_in_a_collection_validator_is_evaluated_per_write`` above.
    """
    database = collection.database
    database.command(
        {
            "create": f"{collection.name}_validated",
            "validator": {"$expr": {"$lte": ["$ts", "$$CLUSTER_TIME"]}},
        }
    )

    result = execute_command(
        collection,
        {
            "insert": f"{collection.name}_validated",
            "documents": [{"_id": 1, "ts": TS_EPOCH}],
        },
    )
    database.drop_collection(f"{collection.name}_validated")

    assertSuccess(
        result,
        {"n": 1, "ok": 1.0},
        raw_res=True,
        msg="A document whose timestamp is in the past should pass the $$CLUSTER_TIME validator",
    )


@pytest.mark.aggregate
@pytest.mark.requires(cluster_time=False)
def test_cluster_time_in_a_redact_result_without_a_cluster_clock(collection):
    """Test the unavailability error precedes the $redact result check.

    The with-a-clock half, where $redact rejects the resolved value as a
    non-sentinel, lives with the other defined system variables in
    ``stages/redact/test_redact_validation.py``.
    """
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$redact": "$$CLUSTER_TIME"}], "cursor": {}},
    )

    assertFailureCode(
        result,
        CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="Without a cluster clock the variable fails before $redact validates its result",
    )
