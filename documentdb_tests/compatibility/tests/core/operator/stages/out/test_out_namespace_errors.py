"""Tests for $out stage - namespace and pipeline position errors."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_NAMESPACE_ERROR,
    LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    OUT_NOT_LAST_STAGE_ERROR,
    OUT_RESTRICTED_DATABASE_ERROR,
    OUT_SPECIAL_COLLECTION_ERROR,
    UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Collection Name Validation Errors]: invalid collection names
# are rejected with the appropriate error code based on the violation type,
# with namespace errors taking precedence over illegal operation errors.
OUT_COLLECTION_NAME_VALIDATION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "coll_empty_string",
        docs=[{"_id": 1}],
        pipeline=[{"$out": ""}],
        msg="$out should reject empty string collection name as invalid namespace",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "coll_null_byte",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "test\x00coll"}],
        msg="$out should reject collection name containing null byte as invalid namespace",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "coll_leading_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$out": ".leading"}],
        msg="$out should reject collection name with leading dot as invalid namespace",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "coll_system_prefix",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "system.test"}],
        msg="$out should reject system. prefix collection name as a special collection",
        error_code=OUT_SPECIAL_COLLECTION_ERROR,
    ),
    OutTestCase(
        "coll_system_buckets_prefix",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "system.buckets.test"}],
        msg="$out should reject system.buckets. prefix as a special collection",
        error_code=OUT_SPECIAL_COLLECTION_ERROR,
    ),
    OutTestCase(
        "coll_dollar_prefix",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "$name"}],
        msg="$out should reject dollar-prefixed collection name as illegal operation",
        error_code=ILLEGAL_OPERATION_ERROR,
    ),
    OutTestCase(
        "coll_double_dollar_prefix",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "$$name"}],
        msg="$out should reject double-dollar-prefixed collection name as illegal operation",
        error_code=ILLEGAL_OPERATION_ERROR,
    ),
    OutTestCase(
        "coll_bare_dollar",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "$"}],
        msg="$out should reject bare dollar collection name as illegal operation",
        error_code=ILLEGAL_OPERATION_ERROR,
    ),
    OutTestCase(
        "coll_bare_double_dollar",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "$$"}],
        msg="$out should reject bare double-dollar collection name as illegal operation",
        error_code=ILLEGAL_OPERATION_ERROR,
    ),
    OutTestCase(
        "coll_namespace_exceeds_255_bytes",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "a" * 255}],
        msg="$out should reject namespace exceeding 255 bytes as illegal operation",
        error_code=ILLEGAL_OPERATION_ERROR,
    ),
]

# Property [Database Name Validation Errors]: invalid database names
# containing dots, slashes, backslashes, ASCII spaces, null bytes, dollar
# prefixes, or empty strings are rejected as invalid namespaces.
OUT_DATABASE_NAME_VALIDATION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "db_empty_string",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "", "coll": "target"}}],
        msg="$out should reject empty string database name",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_leading_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": ".leading", "coll": "target"}}],
        msg="$out should reject database name with leading dot",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_middle_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "a.b", "coll": "target"}}],
        msg="$out should reject database name with middle dot",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_trailing_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "trailing.", "coll": "target"}}],
        msg="$out should reject database name with trailing dot",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_dollar_prefix",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "$name", "coll": "target"}}],
        msg="$out should reject dollar-prefixed database name",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_bare_dollar",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "$", "coll": "target"}}],
        msg="$out should reject bare dollar database name",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_bare_double_dollar",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "$$", "coll": "target"}}],
        msg="$out should reject bare double-dollar database name",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_null_byte",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test\x00db", "coll": "target"}}],
        msg="$out should reject database name containing null byte",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_slash",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "a/b", "coll": "target"}}],
        msg="$out should reject database name containing slash",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_backslash",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "a\\b", "coll": "target"}}],
        msg="$out should reject database name containing backslash",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_ascii_space",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": " ", "coll": "target"}}],
        msg="$out should reject database name that is a single ASCII space",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
    OutTestCase(
        "db_ascii_space_mixed",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "a b", "coll": "target"}}],
        msg="$out should reject database name containing an ASCII space",
        error_code=INVALID_NAMESPACE_ERROR,
    ),
]

# Property [Restricted Database Errors]: writing to the reserved system
# databases (admin, config, local) produces a restricted database error.
OUT_RESTRICTED_DATABASE_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "restricted_db_admin",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "admin", "coll": "target"}}],
        msg="$out should reject writing to the admin database",
        error_code=OUT_RESTRICTED_DATABASE_ERROR,
    ),
    OutTestCase(
        "restricted_db_config",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "config", "coll": "target"}}],
        msg="$out should reject writing to the config database",
        error_code=OUT_RESTRICTED_DATABASE_ERROR,
    ),
    OutTestCase(
        "restricted_db_local",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "local", "coll": "target"}}],
        msg="$out should reject writing to the local database",
        error_code=OUT_RESTRICTED_DATABASE_ERROR,
    ),
]

# Property [Pipeline Position Errors]: $out must be the last stage in a
# pipeline - placing it before another stage, duplicating it, or combining
# it with $merge in either order produces a pipeline position error.
OUT_PIPELINE_POSITION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "out_not_last_stage",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "target"}, {"$match": {"_id": 1}}],
        msg="$out not as the last stage should produce a pipeline position error",
        error_code=OUT_NOT_LAST_STAGE_ERROR,
    ),
    OutTestCase(
        "two_out_stages",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "target1"}, {"$out": "target2"}],
        msg="Two $out stages in the same pipeline should produce a pipeline position error",
        error_code=OUT_NOT_LAST_STAGE_ERROR,
    ),
    OutTestCase(
        "out_then_merge",
        docs=[{"_id": 1}],
        pipeline=[{"$out": "target"}, {"$merge": {"into": "target2"}}],
        msg="$out followed by $merge should produce a pipeline position error",
        error_code=OUT_NOT_LAST_STAGE_ERROR,
    ),
    OutTestCase(
        "merge_then_out",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": "target"}}, {"$out": "target2"}],
        msg="$merge followed by $out should produce a pipeline position error",
        error_code=OUT_NOT_LAST_STAGE_ERROR,
    ),
]

# Property [Nested Pipeline Restriction Errors]: $out is not allowed inside
# nested pipelines ($lookup, $facet, $unionWith) or in view definitions, and
# the innermost nesting restriction applies when stages are nested.
OUT_NESTED_PIPELINE_RESTRICTION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "out_inside_lookup",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$lookup": {
                    "from": "other",
                    "pipeline": [{"$out": "target"}],
                    "as": "result",
                }
            }
        ],
        msg="$out inside a $lookup nested pipeline should be rejected",
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    ),
    OutTestCase(
        "out_inside_facet",
        docs=[{"_id": 1}],
        pipeline=[{"$facet": {"branch": [{"$out": "target"}]}}],
        msg="$out inside a $facet nested pipeline should be rejected",
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
    ),
    OutTestCase(
        "out_inside_union_with",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$unionWith": {
                    "coll": "other",
                    "pipeline": [{"$out": "target"}],
                }
            }
        ],
        msg="$out inside a $unionWith nested pipeline should be rejected",
        error_code=UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    ),
    OutTestCase(
        "out_inside_lookup_inside_facet",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$facet": {
                    "branch": [
                        {
                            "$lookup": {
                                "from": "other",
                                "pipeline": [{"$out": "target"}],
                                "as": "r",
                            }
                        }
                    ]
                }
            }
        ],
        msg=(
            "$out nested inside $lookup inside $facet should produce the"
            " innermost nesting error ($lookup restriction)"
        ),
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    ),
]

# Property [Timeseries Field Type Errors]: all timeseries sub-fields reject
# non-accepted types with a type mismatch error - timeseries accepts only
# object, timeField/metaField/granularity accept only string, and


OUT_NAMESPACE_ERROR_TESTS = (
    OUT_COLLECTION_NAME_VALIDATION_ERROR_TESTS
    + OUT_DATABASE_NAME_VALIDATION_ERROR_TESTS
    + OUT_RESTRICTED_DATABASE_ERROR_TESTS
    + OUT_PIPELINE_POSITION_ERROR_TESTS
    + OUT_NESTED_PIPELINE_RESTRICTION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_NAMESPACE_ERROR_TESTS))
def test_out_error(collection, test_case: OutTestCase):
    """Test $out rejects invalid configurations with the expected error code."""
    populate_collection(collection, test_case)
    pipeline = test_case.pipeline
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
