"""Tests for $out stage - stage argument type errors, unknown field errors, null missing errors."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.bson_helpers import build_raw_bson_doc
from documentdb_tests.framework.error_codes import (
    DUPLICATE_FIELD_ERROR,
    INVALID_OPTIONS_ERROR,
    MISSING_FIELD_ERROR,
    OUT_ARGUMENT_TYPE_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null as Missing (Errors)]: null values for db, coll, and
# timeField are treated as missing rather than as type errors, and a null
# bucket parameter paired with a valid one produces an incomplete-pair
# error.
OUT_NULL_MISSING_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "null_db_missing",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": None, "coll": "target"}}],
        msg="$out should treat null db as missing, not as a type error",
        error_code=MISSING_FIELD_ERROR,
    ),
    OutTestCase(
        "null_coll_missing",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": None}}],
        msg="$out should treat null coll as missing, not as a type error",
        error_code=MISSING_FIELD_ERROR,
    ),
    OutTestCase(
        "null_time_field_missing",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": {"timeField": None}}}],
        msg="$out should treat null timeField as missing, not as a type error",
        error_code=MISSING_FIELD_ERROR,
    ),
    OutTestCase(
        "null_bucket_max_with_valid_rounding",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": None,
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg=(
            "$out should reject null bucketMaxSpanSeconds paired with valid"
            " bucketRoundingSeconds as an incomplete pair"
        ),
        error_code=INVALID_OPTIONS_ERROR,
    ),
    OutTestCase(
        "null_bucket_rounding_with_valid_max",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": 100,
                        "bucketRoundingSeconds": None,
                    },
                }
            }
        ],
        msg=(
            "$out should reject null bucketRoundingSeconds paired with valid"
            " bucketMaxSpanSeconds as an incomplete pair"
        ),
        error_code=INVALID_OPTIONS_ERROR,
    ),
]

# Property [Stage Argument Type Errors]: any type other than string or
# document produces a stage argument type error, including arrays regardless
# of contents, size, nesting, or element types.
OUT_STAGE_ARGUMENT_TYPE_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "arg_type_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$out": 42}],
        msg="$out should reject int32 argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$out": Int64(42)}],
        msg="$out should reject Int64 argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_float",
        docs=[{"_id": 1}],
        pipeline=[{"$out": 3.14}],
        msg="$out should reject float argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$out": Decimal128("99.9")}],
        msg="$out should reject Decimal128 argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$out": True}],
        msg="$out should reject boolean argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_null",
        docs=[{"_id": 1}],
        pipeline=[{"$out": None}],
        msg="$out should reject null argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$out": Binary(b"\x01")}],
        msg="$out should reject Binary argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$out": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$out should reject ObjectId argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$out": datetime(2024, 1, 1)}],
        msg="$out should reject datetime argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$out": Regex("abc")}],
        msg="$out should reject Regex argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$out": Timestamp(1, 1)}],
        msg="$out should reject Timestamp argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$out": MinKey()}],
        msg="$out should reject MinKey argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$out": MaxKey()}],
        msg="$out should reject MaxKey argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_code",
        docs=[{"_id": 1}],
        pipeline=[{"$out": Code("function() {}")}],
        msg="$out should reject Code argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_array_empty",
        docs=[{"_id": 1}],
        pipeline=[{"$out": []}],
        msg="$out should reject empty array argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_array_of_string",
        docs=[{"_id": 1}],
        pipeline=[{"$out": ["target"]}],
        msg="$out should reject array containing a string",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_array_of_document",
        docs=[{"_id": 1}],
        pipeline=[{"$out": [{"db": "test", "coll": "target"}]}],
        msg="$out should reject array containing a document",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_array_nested",
        docs=[{"_id": 1}],
        pipeline=[{"$out": [[1, 2]]}],
        msg="$out should reject nested array argument",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
    OutTestCase(
        "arg_type_array_mixed_types",
        docs=[{"_id": 1}],
        pipeline=[{"$out": [1, "a", None]}],
        msg="$out should reject array with mixed element types",
        error_code=OUT_ARGUMENT_TYPE_ERROR,
    ),
]

# Property [Document Form Unknown Fields]: any field other than db, coll,
# and timeseries in the document form is rejected as an unknown field, and
# field name matching is case-sensitive and whitespace-sensitive.
OUT_UNKNOWN_FIELD_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "unknown_field",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "extra": "x"}}],
        msg="$out should reject unknown field 'extra' in document form",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
    OutTestCase(
        "unknown_field_case_sensitive_db",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"Db": "test", "coll": "target"}}],
        msg="$out should reject 'Db' as unknown (case-sensitive)",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
    OutTestCase(
        "unknown_field_case_sensitive_coll",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "Coll": "target"}}],
        msg="$out should reject 'Coll' as unknown (case-sensitive)",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
    OutTestCase(
        "unknown_field_case_sensitive_timeseries",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "Timeseries": {"timeField": "ts"}}}],
        msg="$out should reject 'Timeseries' as unknown (case-sensitive)",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
    OutTestCase(
        "unknown_field_whitespace_sensitive_db",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db ": "test", "coll": "target"}}],
        msg="$out should reject 'db ' as unknown (whitespace-sensitive)",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
    OutTestCase(
        "unknown_field_whitespace_sensitive_coll",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", " coll": "target"}}],
        msg="$out should reject ' coll' as unknown (whitespace-sensitive)",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
    OutTestCase(
        "expression_like_object",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "$expr": {"$literal": 1}}}],
        msg="$out should treat expression-like objects as unknown fields",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
    OutTestCase(
        "expression_like_dollar_prefix",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "$merge": "x"}}],
        msg="$out should treat $-prefixed fields as unknown fields",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
]

# Property [Collection Name Validation Errors]: invalid collection names
# are rejected with the appropriate error code based on the violation type,
# with namespace errors taking precedence over illegal operation errors.

# Property [Document Form Duplicate Fields]: duplicate fields (db or coll
# appearing twice) in the document form produce a duplicate field error.
OUT_DUPLICATE_FIELD_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "duplicate_db_field",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": build_raw_bson_doc(
                    [
                        ("db", "test"),
                        ("coll", "target"),
                        ("db", "test"),
                    ]
                )
            }
        ],
        msg="$out should reject duplicate 'db' field in document form",
        error_code=DUPLICATE_FIELD_ERROR,
    ),
    OutTestCase(
        "duplicate_coll_field",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": build_raw_bson_doc(
                    [
                        ("db", "test"),
                        ("coll", "target"),
                        ("coll", "target"),
                    ]
                )
            }
        ],
        msg="$out should reject duplicate 'coll' field in document form",
        error_code=DUPLICATE_FIELD_ERROR,
    ),
]


OUT_STAGE_ARGUMENT_ERROR_TESTS = (
    OUT_NULL_MISSING_ERROR_TESTS
    + OUT_STAGE_ARGUMENT_TYPE_ERROR_TESTS
    + OUT_UNKNOWN_FIELD_ERROR_TESTS
    + OUT_DUPLICATE_FIELD_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_STAGE_ARGUMENT_ERROR_TESTS))
def test_out_error(collection, test_case: OutTestCase):
    """Test $out rejects invalid configurations with the expected error code."""
    populate_collection(collection, test_case)
    pipeline = test_case.pipeline
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
