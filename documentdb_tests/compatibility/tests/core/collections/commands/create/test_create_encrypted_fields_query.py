"""Tests for the create command encrypted fields query validation behavior."""

from uuid import uuid4

import pytest
from bson import Binary, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    ENCRYPTED_FIELD_EMPTY_QUERIES_ERROR,
    ENCRYPTED_FIELD_INVALID_QUERY_COMBO_ERROR,
    ENCRYPTED_FIELD_MAX_QUERY_TYPES_ERROR,
    ENCRYPTED_FIELD_MISSING_CASE_SENSITIVE_ERROR,
    ENCRYPTED_FIELD_MISSING_DIACRITIC_SENSITIVE_ERROR,
    ENCRYPTED_FIELD_MISSING_STR_MAX_QUERY_LENGTH_ERROR,
    ENCRYPTED_FIELD_MISSING_STR_MIN_QUERY_LENGTH_ERROR,
    ENCRYPTED_FIELD_RANGE_MIN_MAX_ERROR,
    ENCRYPTED_FIELD_RANGE_MIN_MAX_TYPE_ERROR,
    ENCRYPTED_FIELD_RANGE_TYPE_ERROR,
    ENCRYPTED_FIELD_STR_LENGTH_ERROR,
    ENCRYPTED_FIELD_TEXT_SEARCH_TYPE_ERROR,
    ENCRYPTED_FIELD_TRIM_FACTOR_OUT_OF_RANGE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    INT64_ZERO,
)

# Property [EncryptedFields Query Validation]: invalid query specifications
# in encrypted field definitions produce errors.
CREATE_ENCRYPTED_FIELDS_QUERY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="ef_err_queries_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "queries": None,
                    }
                ]
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="queries:null should fail (NOT treated as omitted)",
    ),
    CommandTestCase(
        id="ef_err_empty_queries_array",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "queries": [],
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_EMPTY_QUERIES_ERROR,
        msg="empty queries array should fail",
    ),
    CommandTestCase(
        id="ef_err_invalid_query_type",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {"queryType": "invalid"},
                    }
                ]
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="invalid queryType value should fail",
    ),
    CommandTestCase(
        id="ef_err_suffix_preview_non_string_bsontype",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {
                            "queryType": "suffixPreview",
                            "strMinQueryLength": 1,
                            "strMaxQueryLength": 10,
                            "caseSensitive": True,
                            "diacriticSensitive": True,
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_TEXT_SEARCH_TYPE_ERROR,
        msg="suffixPreview requires string bsonType",
    ),
    CommandTestCase(
        id="ef_err_prefix_preview_non_string_bsontype",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {
                            "queryType": "prefixPreview",
                            "strMinQueryLength": 1,
                            "strMaxQueryLength": 10,
                            "caseSensitive": True,
                            "diacriticSensitive": True,
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_TEXT_SEARCH_TYPE_ERROR,
        msg="prefixPreview requires string bsonType",
    ),
    CommandTestCase(
        id="ef_err_suffix_preview_missing_str_min_query_length",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {
                            "queryType": "suffixPreview",
                            "strMaxQueryLength": 10,
                            "caseSensitive": True,
                            "diacriticSensitive": True,
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_MISSING_STR_MIN_QUERY_LENGTH_ERROR,
        msg="suffixPreview without strMinQueryLength should fail",
    ),
    CommandTestCase(
        id="ef_err_suffix_preview_missing_str_max_query_length",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {
                            "queryType": "suffixPreview",
                            "strMinQueryLength": 1,
                            "caseSensitive": True,
                            "diacriticSensitive": True,
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_MISSING_STR_MAX_QUERY_LENGTH_ERROR,
        msg="suffixPreview without strMaxQueryLength should fail",
    ),
    CommandTestCase(
        id="ef_err_suffix_preview_missing_case_sensitive",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {
                            "queryType": "suffixPreview",
                            "strMinQueryLength": 1,
                            "strMaxQueryLength": 10,
                            "diacriticSensitive": True,
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_MISSING_CASE_SENSITIVE_ERROR,
        msg="suffixPreview without caseSensitive should fail",
    ),
    CommandTestCase(
        id="ef_err_suffix_preview_missing_diacritic_sensitive",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {
                            "queryType": "suffixPreview",
                            "strMinQueryLength": 1,
                            "strMaxQueryLength": 10,
                            "caseSensitive": True,
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_MISSING_DIACRITIC_SENSITIVE_ERROR,
        msg="suffixPreview without diacriticSensitive should fail",
    ),
    CommandTestCase(
        id="ef_err_prefix_preview_missing_all_subfields",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {
                            "queryType": "prefixPreview",
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_MISSING_STR_MIN_QUERY_LENGTH_ERROR,
        msg="prefixPreview without any required sub-fields should fail",
    ),
    CommandTestCase(
        id="ef_err_str_min_query_length_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {
                            "queryType": "suffixPreview",
                            "strMinQueryLength": 0,
                            "strMaxQueryLength": 10,
                            "caseSensitive": True,
                            "diacriticSensitive": True,
                        },
                    }
                ]
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="strMinQueryLength must be > 0",
    ),
    CommandTestCase(
        id="ef_err_str_max_query_length_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {
                            "queryType": "suffixPreview",
                            "strMinQueryLength": 1,
                            "strMaxQueryLength": 0,
                            "caseSensitive": True,
                            "diacriticSensitive": True,
                        },
                    }
                ]
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="strMaxQueryLength must be > 0",
    ),
    CommandTestCase(
        id="ef_err_str_min_greater_than_max",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {
                            "queryType": "suffixPreview",
                            "strMinQueryLength": 20,
                            "strMaxQueryLength": 10,
                            "caseSensitive": True,
                            "diacriticSensitive": True,
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_STR_LENGTH_ERROR,
        msg="strMinQueryLength > strMaxQueryLength should fail",
    ),
    CommandTestCase(
        id="ef_err_case_sensitive_non_bool",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {
                            "queryType": "suffixPreview",
                            "strMinQueryLength": 1,
                            "strMaxQueryLength": 10,
                            "caseSensitive": "yes",
                            "diacriticSensitive": True,
                        },
                    }
                ]
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="caseSensitive must be bool",
    ),
    CommandTestCase(
        id="ef_err_diacritic_sensitive_non_bool",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {
                            "queryType": "suffixPreview",
                            "strMinQueryLength": 1,
                            "strMaxQueryLength": 10,
                            "caseSensitive": True,
                            "diacriticSensitive": 1,
                        },
                    }
                ]
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="diacriticSensitive must be bool",
    ),
    CommandTestCase(
        id="ef_err_invalid_query_combo_equality_range",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": [
                            {"queryType": "equality"},
                            {"queryType": "range"},
                        ],
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_INVALID_QUERY_COMBO_ERROR,
        msg="equality+range combo is not allowed",
    ),
    CommandTestCase(
        id="ef_err_max_query_types_exceeded",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": [
                            {
                                "queryType": "suffixPreview",
                                "strMinQueryLength": 1,
                                "strMaxQueryLength": 10,
                                "caseSensitive": True,
                                "diacriticSensitive": True,
                            },
                            {
                                "queryType": "prefixPreview",
                                "strMinQueryLength": 1,
                                "strMaxQueryLength": 10,
                                "caseSensitive": True,
                                "diacriticSensitive": True,
                            },
                            {"queryType": "equality"},
                        ],
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_MAX_QUERY_TYPES_ERROR,
        msg="more than 2 query types per field should fail",
    ),
    CommandTestCase(
        id="ef_err_sparsity_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {"queryType": "range", "sparsity": 0},
                    }
                ]
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="sparsity must be >= 1",
    ),
    CommandTestCase(
        id="ef_err_sparsity_fractional",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {"queryType": "range", "sparsity": 1.5},
                    }
                ]
            },
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="sparsity must be integer, not fractional",
    ),
    CommandTestCase(
        id="ef_err_trim_factor_too_large",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {"queryType": "range", "trimFactor": 1000000},
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_TRIM_FACTOR_OUT_OF_RANGE_ERROR,
        msg="trimFactor must be less than the bit width of the field type",
        marks=(pytest.mark.replica_set,),
    ),
    CommandTestCase(
        id="ef_err_contention_fractional",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {"queryType": "range", "contention": 0.5},
                    }
                ]
            },
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="contention must be integer, not fractional",
    ),
    CommandTestCase(
        id="ef_err_range_string_bsontype",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "string",
                        "queries": {"queryType": "range"},
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_RANGE_TYPE_ERROR,
        msg="range queryType requires numeric/date bsonType",
    ),
    CommandTestCase(
        id="ef_err_range_min_greater_than_max",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {
                            "queryType": "range",
                            "min": 10,
                            "max": 5,
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_RANGE_MIN_MAX_ERROR,
        msg="range min >= max should fail",
    ),
    CommandTestCase(
        id="ef_err_range_min_equal_max",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {
                            "queryType": "range",
                            "min": 5,
                            "max": 5,
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_RANGE_MIN_MAX_ERROR,
        msg="range min == max should fail",
    ),
    CommandTestCase(
        id="ef_err_range_min_type_mismatch",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {
                            "queryType": "range",
                            "min": INT64_ZERO,
                            "max": Int64(100),
                        },
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_RANGE_MIN_MAX_TYPE_ERROR,
        msg="range min/max type must exactly match bsonType",
    ),
    CommandTestCase(
        id="ef_err_trim_factor_negative",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {"queryType": "range", "trimFactor": -1},
                    }
                ]
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="trimFactor must be >= 0",
    ),
    CommandTestCase(
        id="ef_err_contention_negative",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "num",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "int",
                        "queries": {"queryType": "range", "contention": -1},
                    }
                ]
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="contention must be >= 0",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_ENCRYPTED_FIELDS_QUERY_ERROR_TESTS))
def test_create_encrypted_fields_query(database_client, collection, test):
    """Test create command encrypted fields query validation behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
