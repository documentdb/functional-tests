"""Tests for $listClusterCatalog argument and field validation errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.listClusterCatalog.utils.listClusterCatalog_helpers import (  # noqa: E501
    ListClusterCatalogTestCase,
    StageContext,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_NAMESPACE_ERROR,
    INVALID_OPTIONS_ERROR,
    LIST_CLUSTER_CATALOG_COLLECTION_ERROR,
    LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
    NOT_FIRST_STAGE_ERROR,
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_TRAILING_ZERO

# Property [Stage Argument Type Errors]: a non-document argument to
# $listClusterCatalog produces a non-object error for all non-document
# BSON types.
ARG_TYPE_ERROR_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="arg_null",
        pipeline=[{"$listClusterCatalog": None}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject null argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_bool",
        pipeline=[{"$listClusterCatalog": True}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject boolean argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_int32",
        pipeline=[{"$listClusterCatalog": 42}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject int32 argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_int64",
        pipeline=[{"$listClusterCatalog": Int64(42)}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject int64 argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_double",
        pipeline=[{"$listClusterCatalog": 3.14}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject double argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_decimal128",
        pipeline=[{"$listClusterCatalog": DECIMAL128_TRAILING_ZERO}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject Decimal128 argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_string",
        pipeline=[{"$listClusterCatalog": "hello"}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject string argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_array",
        pipeline=[{"$listClusterCatalog": [1, 2]}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject array argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_objectid",
        pipeline=[{"$listClusterCatalog": ObjectId()}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject ObjectId argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_datetime",
        pipeline=[{"$listClusterCatalog": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject datetime argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_timestamp",
        pipeline=[{"$listClusterCatalog": Timestamp(1, 1)}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject Timestamp argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_binary",
        pipeline=[{"$listClusterCatalog": Binary(b"\x01")}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject Binary argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_regex",
        pipeline=[{"$listClusterCatalog": Regex("^abc")}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject Regex argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_code",
        pipeline=[{"$listClusterCatalog": Code("function(){}")}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject Code argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_code_with_scope",
        pipeline=[{"$listClusterCatalog": Code("function(){}", {"x": 1})}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject CodeWithScope argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_minkey",
        pipeline=[{"$listClusterCatalog": MinKey()}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject MinKey argument",
    ),
    ListClusterCatalogTestCase(
        id="arg_maxkey",
        pipeline=[{"$listClusterCatalog": MaxKey()}],
        error_code=LIST_CLUSTER_CATALOG_NON_OBJECT_ERROR,
        msg="$listClusterCatalog should reject MaxKey argument",
    ),
]

# Property [Field Type Strictness - shards]: the shards field accepts only
# boolean true or false; all non-boolean BSON types produce a type mismatch error.
SHARDS_TYPE_ERROR_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="shards_null",
        pipeline=[{"$listClusterCatalog": {"shards": None}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: null should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_int32",
        pipeline=[{"$listClusterCatalog": {"shards": 1}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: int32 should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_int64",
        pipeline=[{"$listClusterCatalog": {"shards": Int64(1)}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: int64 should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_double",
        pipeline=[{"$listClusterCatalog": {"shards": 1.0}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: double should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_string",
        pipeline=[{"$listClusterCatalog": {"shards": "true"}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: string should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_array",
        pipeline=[{"$listClusterCatalog": {"shards": [True]}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: array should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_object",
        pipeline=[{"$listClusterCatalog": {"shards": {"$literal": True}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: expression-like object should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_decimal128",
        pipeline=[{"$listClusterCatalog": {"shards": Decimal128("1")}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: Decimal128 should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_objectid",
        pipeline=[{"$listClusterCatalog": {"shards": ObjectId()}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: ObjectId should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_datetime",
        pipeline=[{"$listClusterCatalog": {"shards": datetime(2024, 1, 1, tzinfo=timezone.utc)}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: datetime should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_binary",
        pipeline=[{"$listClusterCatalog": {"shards": Binary(b"\x01")}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: Binary should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_regex",
        pipeline=[{"$listClusterCatalog": {"shards": Regex("^a")}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: Regex should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_code",
        pipeline=[{"$listClusterCatalog": {"shards": Code("function(){}")}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: Code should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_code_with_scope",
        pipeline=[{"$listClusterCatalog": {"shards": Code("function(){}", {"x": 1})}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: CodeWithScope should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_timestamp",
        pipeline=[{"$listClusterCatalog": {"shards": Timestamp(1, 1)}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: Timestamp should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_minkey",
        pipeline=[{"$listClusterCatalog": {"shards": MinKey()}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: MinKey should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="shards_maxkey",
        pipeline=[{"$listClusterCatalog": {"shards": MaxKey()}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="shards: MaxKey should produce type mismatch error",
    ),
]

# Property [Field Type Strictness - balancingConfiguration]: the
# balancingConfiguration field accepts only boolean true or false; all
# non-boolean BSON types produce a type mismatch error.
BALANCING_CONFIG_TYPE_ERROR_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="bc_null",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": None}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: null should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_int32",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": 1}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: int32 should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_int64",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": Int64(1)}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: int64 should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_double",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": 1.0}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: double should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_string",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": "true"}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: string should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_array",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": [True]}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: array should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_object",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": {"$literal": True}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: expression-like object should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_decimal128",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": Decimal128("1")}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: Decimal128 should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_objectid",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": ObjectId()}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: ObjectId should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_datetime",
        pipeline=[
            {
                "$listClusterCatalog": {
                    "balancingConfiguration": datetime(2024, 1, 1, tzinfo=timezone.utc)
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: datetime should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_binary",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": Binary(b"\x01")}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: Binary should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_regex",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": Regex("^a")}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: Regex should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_code",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": Code("function(){}")}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: Code should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_code_with_scope",
        pipeline=[
            {"$listClusterCatalog": {"balancingConfiguration": Code("function(){}", {"x": 1})}}
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: CodeWithScope should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_timestamp",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": Timestamp(1, 1)}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: Timestamp should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_minkey",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": MinKey()}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: MinKey should produce type mismatch error",
    ),
    ListClusterCatalogTestCase(
        id="bc_maxkey",
        pipeline=[{"$listClusterCatalog": {"balancingConfiguration": MaxKey()}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="balancingConfiguration: MaxKey should produce type mismatch error",
    ),
]

# Property [Unknown Fields]: unrecognized or incorrectly-cased field names
# in the stage argument produce an unrecognized field error.
UNKNOWN_FIELD_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="unknown_field",
        pipeline=[{"$listClusterCatalog": {"unknownField": True}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown field should produce an unrecognized field error",
    ),
    ListClusterCatalogTestCase(
        id="expression_key",
        pipeline=[{"$listClusterCatalog": {"$literal": True}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Expression-like key should be treated as unknown field",
    ),
    ListClusterCatalogTestCase(
        id="shards_uppercase",
        pipeline=[{"$listClusterCatalog": {"Shards": True}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Shards (capitalized) should be treated as unknown field",
    ),
    ListClusterCatalogTestCase(
        id="shards_all_caps",
        pipeline=[{"$listClusterCatalog": {"SHARDS": True}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="SHARDS (all caps) should be treated as unknown field",
    ),
    ListClusterCatalogTestCase(
        id="bc_uppercase",
        pipeline=[{"$listClusterCatalog": {"BalancingConfiguration": True}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="BalancingConfiguration (capitalized) should be treated as unknown field",
    ),
]

# Property [Pipeline Position]: $listClusterCatalog must be the first
# stage; placing it after any other stage produces an error.
PIPELINE_POSITION_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="after_match",
        pipeline=[{"$match": {}}, {"$listClusterCatalog": {}}],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$listClusterCatalog after $match should produce an invalid namespace error",
    ),
    ListClusterCatalogTestCase(
        id="two_stages",
        pipeline=[{"$listClusterCatalog": {}}, {"$listClusterCatalog": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="Two $listClusterCatalog stages should produce a pipeline position error",
    ),
]

# Property [Must Run on Database]: running the stage on a collection
# (collection.aggregate) instead of db.aggregate produces a collection-level error.
MUST_RUN_ON_DB_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="must_run_on_database",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$listClusterCatalog": {}}],
            "cursor": {},
        },
        error_code=LIST_CLUSTER_CATALOG_COLLECTION_ERROR,
        msg="$listClusterCatalog on a collection should produce a collection-level error",
    ),
]

# Property [Stage Document Extra Keys]: extra keys alongside
# $listClusterCatalog in the stage document produce an extra field error.
EXTRA_KEY_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="extra_keys_in_stage_doc",
        pipeline=[{"$listClusterCatalog": {}, "$match": {}}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="Extra keys alongside $listClusterCatalog should produce an extra field error",
    ),
]

# Property [readConcern Errors]: readConcern levels other than local
# produce an invalid options error.
READ_CONCERN_ERROR_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id=f"readConcern_{level}",
        command={
            "aggregate": 1,
            "pipeline": [{"$listClusterCatalog": {}}],
            "cursor": {},
            "readConcern": {"level": level},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"readConcern {level!r} should produce an invalid options error",
    )
    for level in ("majority", "linearizable", "available", "snapshot")
]

VALIDATION_TESTS: list[ListClusterCatalogTestCase] = (
    ARG_TYPE_ERROR_TESTS
    + SHARDS_TYPE_ERROR_TESTS
    + BALANCING_CONFIG_TYPE_ERROR_TESTS
    + UNKNOWN_FIELD_TESTS
    + PIPELINE_POSITION_TESTS
    + MUST_RUN_ON_DB_TESTS
    + EXTRA_KEY_TESTS
    + READ_CONCERN_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(VALIDATION_TESTS))
def test_listClusterCatalog_validation(collection: Collection, test: ListClusterCatalogTestCase):
    """Test $listClusterCatalog argument validation and error handling."""
    test.prepare(collection.database, collection)
    ctx = StageContext.from_collection(collection)
    result = execute_command(collection, test.build_command(collection, ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)
