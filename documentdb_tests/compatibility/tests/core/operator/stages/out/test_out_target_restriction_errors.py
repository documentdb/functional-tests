"""Tests for $out stage - target collection restriction errors."""

from __future__ import annotations

from datetime import datetime

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
    assertSuccess,
)
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    DOCUMENT_VALIDATION_FAILURE_ERROR,
    DUPLICATE_KEY_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
    OUT_CAPPED_COLLECTION_ERROR,
    OUT_TIMESERIES_COLLECTION_TYPE_ERROR,
    OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Target Collection Restriction Errors]: $out rejects writing to
# capped collections and views, and writing to a view with timeseries options
# produces a timeseries collection type error instead of the view-specific
# error.
OUT_TARGET_RESTRICTION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "capped_target",
        docs=[{"_id": 1, "value": 10}],
        target_coll="capped_out_target",
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_capped_out_target"),
            c.database.create_collection(
                f"{c.name}_capped_out_target", capped=True, size=1_048_576
            ),
        ),
        msg="$out should reject writing to a capped collection",
        error_code=OUT_CAPPED_COLLECTION_ERROR,
    ),
    OutTestCase(
        "view_target",
        docs=[{"_id": 1, "value": 10}],
        target_coll="view_out_target",
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_view_out_target"),
            c.database.command(
                {"create": f"{c.name}_view_out_target", "viewOn": c.name, "pipeline": []}
            ),
        ),
        msg="$out should reject writing to a view",
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    ),
    OutTestCase(
        "view_ts_target",
        docs=[{"_id": 1, "value": 10}],
        target_coll="view_ts_out_target",
        out_spec={"timeseries": {"timeField": "ts"}},
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_view_ts_out_target"),
            c.database.command(
                {"create": f"{c.name}_view_ts_out_target", "viewOn": c.name, "pipeline": []}
            ),
        ),
        msg=(
            "$out to a view with timeseries options should produce a timeseries"
            " collection type error, not the view-specific error"
        ),
        error_code=OUT_TIMESERIES_COLLECTION_TYPE_ERROR,
    ),
]

# Property [Timeseries Existing Collection Errors]: writing with timeseries
# options to an existing regular collection produces a timeseries collection
# type error, and writing with mismatched timeseries options to an existing
# time series collection produces a timeseries options mismatch error
# regardless of which option differs.
OUT_TIMESERIES_EXISTING_COLLECTION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_to_regular",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_to_regular_target",
        out_spec={"timeseries": {"timeField": "ts"}},
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_ts_to_regular_target"),
            c.database.create_collection(f"{c.name}_ts_to_regular_target"),
        ),
        msg=(
            "$out with timeseries options to an existing regular collection"
            " should produce a timeseries collection type error"
        ),
        error_code=OUT_TIMESERIES_COLLECTION_TYPE_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_different_time_field",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={"timeseries": {"timeField": "other"}},
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_ts_mismatch_target"),
            c.database.command(
                {"create": f"{c.name}_ts_mismatch_target", "timeseries": {"timeField": "ts"}}
            ),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_meta_field_present_vs_absent",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={"timeseries": {"timeField": "ts", "metaField": "m"}},
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_ts_mismatch_target"),
            c.database.command(
                {"create": f"{c.name}_ts_mismatch_target", "timeseries": {"timeField": "ts"}}
            ),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_different_meta_field",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={"timeseries": {"timeField": "ts", "metaField": "other"}},
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_ts_mismatch_target"),
            c.database.command(
                {
                    "create": f"{c.name}_ts_mismatch_target",
                    "timeseries": {"timeField": "ts", "metaField": "m"},
                }
            ),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_different_granularity",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={"timeseries": {"timeField": "ts", "granularity": "hours"}},
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_ts_mismatch_target"),
            c.database.command(
                {
                    "create": f"{c.name}_ts_mismatch_target",
                    "timeseries": {"timeField": "ts", "granularity": "seconds"},
                }
            ),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_granularity_vs_bucket_options",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={"timeseries": {"timeField": "ts", "granularity": "hours"}},
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_ts_mismatch_target"),
            c.database.command(
                {
                    "create": f"{c.name}_ts_mismatch_target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": 100,
                        "bucketRoundingSeconds": 100,
                    },
                }
            ),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_different_bucket_values",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 200,
                "bucketRoundingSeconds": 200,
            }
        },
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_ts_mismatch_target"),
            c.database.command(
                {
                    "create": f"{c.name}_ts_mismatch_target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": 100,
                        "bucketRoundingSeconds": 100,
                    },
                }
            ),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
]

# Property [Index Constraint Errors]: unique index violations (including
# compound unique indexes) and duplicate _id values in the output produce a
# duplicate key error, and when a unique index violation occurs writing to a
# nonexistent target, the target collection is not created.
OUT_INDEX_CONSTRAINT_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "idx_unique",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 1}],
        target_coll="idx_unique_target",
        setup=lambda c: (
            c.database[f"{c.name}_idx_unique_target"].insert_many(
                [{"_id": 90, "x": 90}, {"_id": 91, "x": 91}]
            ),
            c.database[f"{c.name}_idx_unique_target"].create_index("x", unique=True),
        ),
        msg="$out should produce a duplicate key error on unique index violation",
        error_code=DUPLICATE_KEY_ERROR,
    ),
    OutTestCase(
        "idx_compound",
        docs=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1, "b": 2}],
        target_coll="idx_compound_target",
        setup=lambda c: (
            c.database[f"{c.name}_idx_compound_target"].insert_one({"_id": 99, "a": 99, "b": 99}),
            c.database[f"{c.name}_idx_compound_target"].create_index(
                [("a", 1), ("b", 1)], unique=True
            ),
        ),
        msg="$out should produce a duplicate key error on compound unique index violation",
        error_code=DUPLICATE_KEY_ERROR,
    ),
    OutTestCase(
        "idx_dup_id",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        target_coll="idx_dup_id_target",
        pipeline=[
            {"$unset": "_id"},
            {"$addFields": {"_id": "same"}},
        ],
        msg="$out should produce a duplicate key error when output contains duplicate _id values",
        error_code=DUPLICATE_KEY_ERROR,
    ),
]

# Property [Read Concern Errors]: linearizable read concern with $out
# produces an invalid options error.
OUT_READ_CONCERN_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "rc_linearizable",
        docs=[{"_id": 1, "value": 10}],
        target_coll="rc_linearizable_target",
        msg="$out should reject linearizable read concern",
        error_code=INVALID_OPTIONS_ERROR,
    ),
]


OUT_TARGET_RESTRICTION_TESTS = (
    OUT_TARGET_RESTRICTION_ERROR_TESTS
    + OUT_TIMESERIES_EXISTING_COLLECTION_ERROR_TESTS
    + OUT_INDEX_CONSTRAINT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TARGET_RESTRICTION_TESTS))
def test_out_target_restriction_error(collection, test_case: OutTestCase):
    """Test $out rejects invalid target configurations with the expected error code."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    pipeline = list(test_case.pipeline or []) + [test_case.build_out_stage(collection)]
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_READ_CONCERN_ERROR_TESTS))
def test_out_read_concern_error(collection, test_case: OutTestCase):
    """Test $out rejects invalid read concern levels."""
    populate_collection(collection, test_case)
    pipeline = [test_case.build_out_stage(collection)]
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


# Property [Nested Pipeline Restriction - View Definition]: $out in a view
# definition is rejected.
OUT_VIEW_DEFINITION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "view_def_out",
        docs=[{"_id": 1, "value": 10}],
        target_coll="view_def_target",
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$out in a view definition should produce an invalid view pipeline error",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_VIEW_DEFINITION_ERROR_TESTS))
def test_out_in_view_definition_error(collection, test_case: OutTestCase):
    """Test $out in a view definition is rejected."""
    populate_collection(collection, test_case)
    pipeline = [test_case.build_out_stage(collection)]
    result = execute_command(
        collection,
        {
            "create": f"{collection.name}_bad_view",
            "viewOn": collection.name,
            "pipeline": pipeline,
        },
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


# Property [Schema Validation Errors]: when the target collection has
# validationAction set to error and an invalid document is produced, the
# write fails with a document validation failure error and the pre-existing
# collection is unchanged.
OUT_SCHEMA_VALIDATION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "schema_val_err",
        docs=[{"_id": 1, "value": "not_a_number"}],
        target_coll="schema_val_error_target",
        setup=lambda c: (
            c.database.drop_collection(f"{c.name}_schema_val_error_target"),
            c.database.command(
                {
                    "create": f"{c.name}_schema_val_error_target",
                    "validator": {
                        "$jsonSchema": {
                            "bsonType": "object",
                            "required": ["value"],
                            "properties": {"value": {"bsonType": "int"}},
                        }
                    },
                    "validationAction": "error",
                }
            ),
            c.database[f"{c.name}_schema_val_error_target"].insert_one({"_id": 99, "value": 42}),
        ),
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        expected=[{"_id": 99, "value": 42}],
        msg="$out should fail with document validation failure when validationAction is error",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_SCHEMA_VALIDATION_ERROR_TESTS))
def test_out_schema_validation_error(collection, test_case):
    """Test $out fails with document validation failure when validationAction is error."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    pipeline = [test_case.build_out_stage(collection)]
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_SCHEMA_VALIDATION_ERROR_TESTS))
def test_out_schema_validation_error_unchanged(collection, test_case: OutTestCase):
    """Test $out schema validation failure leaves the pre-existing collection unchanged."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    pipeline = [test_case.build_out_stage(collection)]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    target = test_case.resolve_target_coll(collection)
    result = execute_command(
        collection,
        {"find": target, "filter": {}, "projection": {"_id": 1, "value": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Transaction Errors]: using $out inside a transaction produces
# an error.
OUT_TRANSACTION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "transaction_out",
        docs=[{"_id": 1, "value": 10}],
        target_coll="txn_target",
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="$out inside a transaction should produce an error",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TRANSACTION_ERROR_TESTS))
def test_out_transaction_error(collection, test_case: OutTestCase):
    """Test $out inside a transaction produces an error."""
    populate_collection(collection, test_case)
    pipeline = [test_case.build_out_stage(collection)]
    # Verify the pipeline works outside a transaction first.
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    command = {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}}
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        try:
            result = collection.database.command(command, session=session)
        except Exception as e:
            result = e
        finally:
            session.abort_transaction()
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


# Property [Byte-Based Namespace Limit]: the namespace length limit (255
# bytes) is byte-based, not character-based - multi-byte characters consume
# more of the limit per character than single-byte characters.
OUT_BYTE_NAMESPACE_LIMIT_TESTS: list[OutTestCase] = [
    OutTestCase(
        "byte_limit",
        docs=[{"_id": 1}],
        error_code=ILLEGAL_OPERATION_ERROR,
        msg=(
            "$out should reject a collection name that exceeds 255 namespace bytes"
            " even though the character count is within the single-byte limit"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_BYTE_NAMESPACE_LIMIT_TESTS))
def test_out_byte_based_namespace_limit(collection, test_case: OutTestCase):
    """Test $out namespace limit is byte-based, not character-based."""
    populate_collection(collection, test_case)
    db_name = collection.database.name
    # Namespace = db_name + "." + coll_name; limit is 255 bytes.
    prefix_bytes = len(db_name.encode("utf-8")) + 1
    max_coll_bytes = 255 - prefix_bytes
    # CJK character U+4E2D is 3 bytes in UTF-8. Use enough CJK characters
    # to exceed the byte limit while staying under the character count that
    # would fit with single-byte characters.
    cjk_char_count = (max_coll_bytes // 3) + 1
    cjk_name = "\u4e2d" * cjk_char_count
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": cjk_name}], "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
