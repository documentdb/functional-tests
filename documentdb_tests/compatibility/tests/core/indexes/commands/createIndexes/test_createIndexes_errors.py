"""Tests for createIndexes error cases.

Validates error codes for invalid arguments, conflicting indexes,
unsupported options, and constraint violations.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CANNOT_CREATE_INDEX_ERROR,
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    DUPLICATE_KEY_ERROR,
    FAILED_TO_PARSE_ERROR,
    HASHED_COMPOUND_MULTIPLE_ERROR,
    HASHED_UNIQUE_NOT_SUPPORTED_ERROR,
    INDEX_KEY_SPECS_CONFLICT_ERROR,
    INDEX_OPTIONS_CONFLICT_ERROR,
    INVALID_INDEX_SPEC_OPTION_ERROR,
    INVALID_NAMESPACE_ERROR,
    INVALID_OPTIONS_ERROR,
    MISSING_FIELD_ERROR,
    PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
    SORT_COMPOUND_KEY_LIMIT_ERROR,
    TYPE_MISMATCH_ERROR,
    WILDCARD_STRING_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

SINGLE_COMMAND_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="empty_key_document",
        indexes=({"key": {}, "name": "empty_key"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Empty key should fail",
    ),
    IndexTestCase(
        id="empty_string_name",
        indexes=({"key": {"a": 1}, "name": ""},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Empty name should fail",
    ),
    IndexTestCase(
        id="non_string_name_integer",
        indexes=({"key": {"a": 1}, "name": 123},),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Non-string name should fail",
    ),
    IndexTestCase(
        id="unrecognized_index_option",
        indexes=({"key": {"a": 1}, "name": "a_1", "unknownOption": True},),
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="Unrecognized option should fail",
    ),
    IndexTestCase(
        id="duplicate_key_in_batch",
        indexes=(
            {"key": {"a": 1}, "name": "a_1_first"},
            {"key": {"a": 1}, "name": "a_1_second"},
        ),
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Duplicate key in batch should fail",
    ),
    IndexTestCase(
        id="unique_on_hashed",
        indexes=({"key": {"a": "hashed"}, "name": "a_hashed_unique", "unique": True},),
        error_code=HASHED_UNIQUE_NOT_SUPPORTED_ERROR,
        msg="Unique on hashed should fail",
    ),
    IndexTestCase(
        id="ttl_on_compound_index",
        indexes=({"key": {"a": 1, "b": 1}, "name": "ab_ttl", "expireAfterSeconds": 3600},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="TTL on compound should fail",
    ),
    IndexTestCase(
        id="ttl_on_id_field",
        indexes=({"key": {"_id": 1}, "name": "_id_ttl", "expireAfterSeconds": 3600},),
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="TTL on _id should fail",
    ),
    IndexTestCase(
        id="hidden_on_id_field",
        indexes=({"key": {"_id": 1}, "name": "_id_hidden", "hidden": True},),
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="Hidden on _id should fail",
    ),
    IndexTestCase(
        id="sparse_partial_combination",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_sp",
                "sparse": True,
                "partialFilterExpression": {"a": {"$exists": True}},
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Sparse + partial should fail",
    ),
    IndexTestCase(
        id="partial_non_document_type",
        indexes=({"key": {"a": 1}, "name": "a_partial_str", "partialFilterExpression": "invalid"},),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Non-document partial filter should fail",
    ),
    IndexTestCase(
        id="partial_with_nor",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_partial_nor",
                "partialFilterExpression": {"$nor": [{"a": 1}]},
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Partial filter with $nor should fail",
    ),
    IndexTestCase(
        id="partial_with_not",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_partial_not",
                "partialFilterExpression": {"a": {"$not": {"$gt": 5}}},
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Partial filter with $not should fail",
    ),
    IndexTestCase(
        id="collation_empty_object",
        indexes=({"key": {"a": 1}, "name": "a_empty_coll", "collation": {}},),
        error_code=BAD_VALUE_ERROR,
        msg="Empty collation should fail",
    ),
    IndexTestCase(
        id="collation_non_object",
        indexes=({"key": {"a": 1}, "name": "a_str_coll", "collation": "en"},),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Non-object collation should fail",
    ),
    IndexTestCase(
        id="collation_invalid_locale",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_bad_locale",
                "collation": {"locale": "invalid_locale_xyz"},
            },
        ),
        error_code=BAD_VALUE_ERROR,
        msg="Invalid locale should fail",
    ),
    IndexTestCase(
        id="text_with_non_simple_collation",
        indexes=({"key": {"a": "text"}, "name": "a_text_coll", "collation": {"locale": "en"}},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Text with non-simple collation should fail",
    ),
    IndexTestCase(
        id="text_weight_zero",
        indexes=({"key": {"a": "text"}, "name": "a_text_w0", "weights": {"a": 0}},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Weight 0 fails",
    ),
    IndexTestCase(
        id="text_only_one_per_collection",
        setup_indexes=[{"key": {"a": "text"}, "name": "a_text"}],
        indexes=({"key": {"b": "text"}, "name": "b_text"},),
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Second text index fails",
    ),
    IndexTestCase(
        id="text_different_key_same_name",
        setup_indexes=[{"key": {"a": "text"}, "name": "my_text"}],
        indexes=({"key": {"b": "text"}, "name": "my_text"},),
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Different key same name fails",
    ),
    IndexTestCase(
        id="compound_multiple_hashed",
        indexes=({"key": {"a": "hashed", "b": "hashed"}, "name": "ab_hashed"},),
        error_code=HASHED_COMPOUND_MULTIPLE_ERROR,
        msg="Multiple hashed fields fails",
    ),
    IndexTestCase(
        id="wildcard_direction_zero",
        indexes=({"key": {"$**": 0}, "name": "wc_0"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard direction 0 fails",
    ),
    IndexTestCase(
        id="wildcard_with_sparse",
        indexes=({"key": {"$**": 1}, "name": "wc_sparse", "sparse": True},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard with sparse fails",
    ),
    IndexTestCase(
        id="wildcard_with_unique",
        indexes=({"key": {"$**": 1}, "name": "wc_unique", "unique": True},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard with unique fails",
    ),
    IndexTestCase(
        id="wildcard_with_ttl",
        indexes=({"key": {"$**": 1}, "name": "wc_ttl", "expireAfterSeconds": 100},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard with TTL fails",
    ),
    IndexTestCase(
        id="compound_wildcard",
        indexes=({"key": {"$**": 1, "a": 1}, "name": "wc_compound"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Compound wildcard fails",
    ),
    IndexTestCase(
        id="wildcard_mixed_projection",
        indexes=({"key": {"$**": 1}, "name": "wc_mixed", "wildcardProjection": {"a": 1, "b": 0}},),
        error_code=PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
        msg="Mixed inclusion/exclusion projection fails",
    ),
    IndexTestCase(
        id="non_wildcard_with_projection",
        indexes=({"key": {"a": 1}, "name": "a_wc_proj", "wildcardProjection": {"b": 1}},),
        error_code=BAD_VALUE_ERROR,
        msg="Non-wildcard with wildcardProjection fails",
    ),
    IndexTestCase(
        id="wildcard_projection_non_object",
        indexes=({"key": {"$**": 1}, "name": "wc_str_proj", "wildcardProjection": "invalid"},),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Non-object wildcardProjection fails",
    ),
    IndexTestCase(
        id="subpath_wildcard_with_inclusion_projection",
        indexes=({"key": {"a.$**": 1}, "name": "a_wc_incl", "wildcardProjection": {"b": 1}},),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Subpath wildcard with inclusion projection fails",
    ),
    IndexTestCase(
        id="subpath_wildcard_with_exclusion_projection",
        indexes=({"key": {"a.$**": 1}, "name": "a_wc_excl", "wildcardProjection": {"b": 0}},),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Subpath wildcard with exclusion projection fails",
    ),
    IndexTestCase(
        id="key_direction_zero",
        indexes=({"key": {"a": 0}, "name": "a_0"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Direction 0 fails",
    ),
    IndexTestCase(
        id="unrecognized_string_type_abc",
        indexes=({"key": {"a": "abc"}, "name": "a_abc"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Unrecognized string type 'abc' fails",
    ),
    IndexTestCase(
        id="unrecognized_string_type_wildcard",
        indexes=({"key": {"a": "wildcard"}, "name": "a_wildcard"},),
        error_code=WILDCARD_STRING_TYPE_ERROR,
        msg="'wildcard' string type on regular field fails",
    ),
    IndexTestCase(
        id="compound_33_fields",
        indexes=(
            {
                "key": {f"f{i}": 1 for i in range(33)},
                "name": "_".join(f"f{i}_1" for i in range(33)),
            },
        ),
        error_code=SORT_COMPOUND_KEY_LIMIT_ERROR,
        msg="33 fields in compound key fails",
    ),
    IndexTestCase(
        id="empty_indexes_array",
        indexes=(),
        error_code=BAD_VALUE_ERROR,
        msg="Empty indexes array should fail",
    ),
    IndexTestCase(
        id="index_spec_missing_name",
        indexes=({"key": {"a": 1}},),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Missing name should fail",
    ),
    IndexTestCase(
        id="same_key_different_name",
        setup_indexes=[{"key": {"a": 1}, "name": "idx_a"}],
        indexes=({"key": {"a": 1}, "name": "idx_a_different"},),
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Same key different name should fail with code 85",
    ),
    IndexTestCase(
        id="different_key_same_name",
        setup_indexes=[{"key": {"a": 1}, "name": "idx_a"}],
        indexes=({"key": {"b": 1}, "name": "idx_a"},),
        error_code=INDEX_KEY_SPECS_CONFLICT_ERROR,
        msg="Different key same name should fail",
    ),
    IndexTestCase(
        id="different_direction_same_name",
        setup_indexes=[{"key": {"a": 1}, "name": "idx_a"}],
        indexes=({"key": {"a": -1}, "name": "idx_a"},),
        error_code=INDEX_KEY_SPECS_CONFLICT_ERROR,
        msg="Different direction same name should fail",
    ),
    IndexTestCase(
        id="name_conflicts_with_auto_generated",
        setup_indexes=[{"key": {"a": 1}, "name": "b_1"}],
        indexes=({"key": {"b": 1}, "name": "b_1"},),
        error_code=INDEX_KEY_SPECS_CONFLICT_ERROR,
        msg="Name conflicting with auto-generated should fail",
    ),
    IndexTestCase(
        id="unique_with_existing_duplicates",
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 1}),
        indexes=({"key": {"a": 1}, "name": "a_unique", "unique": True},),
        error_code=DUPLICATE_KEY_ERROR,
        msg="Unique with existing dups should fail",
    ),
    # TTL expireAfterSeconds type and range errors
    IndexTestCase(
        id="ttl_expire_string",
        indexes=({"key": {"a": 1}, "name": "a_ttl_str", "expireAfterSeconds": "3600"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="String expireAfterSeconds should fail",
    ),
    IndexTestCase(
        id="ttl_expire_object",
        indexes=({"key": {"a": 1}, "name": "a_ttl_obj", "expireAfterSeconds": {}},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Object expireAfterSeconds should fail",
    ),
    IndexTestCase(
        id="ttl_expire_null",
        indexes=({"key": {"a": 1}, "name": "a_ttl_null", "expireAfterSeconds": None},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Null expireAfterSeconds should fail",
    ),
    IndexTestCase(
        id="ttl_expire_boolean",
        indexes=({"key": {"a": 1}, "name": "a_ttl_bool", "expireAfterSeconds": True},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Boolean expireAfterSeconds should fail",
    ),
    IndexTestCase(
        id="ttl_expire_negative",
        indexes=({"key": {"a": 1}, "name": "a_ttl_neg", "expireAfterSeconds": -1},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Negative expireAfterSeconds should fail",
    ),
    IndexTestCase(
        id="ttl_expire_above_int32_max",
        indexes=({"key": {"a": 1}, "name": "a_ttl_big", "expireAfterSeconds": 2147483648},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="expireAfterSeconds above INT32_MAX should fail",
    ),
    # weights errors
    IndexTestCase(
        id="weights_on_non_text_index",
        indexes=({"key": {"a": 1}, "name": "a_weights", "weights": {"a": 1}},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Weights on non-text index should fail",
    ),
    IndexTestCase(
        id="text_weight_negative",
        indexes=({"key": {"a": "text"}, "name": "a_text_wneg", "weights": {"a": -1}},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Negative weight on text index should fail",
    ),
    # text index language errors
    IndexTestCase(
        id="text_invalid_default_language",
        indexes=({"key": {"a": "text"}, "name": "a_text_klingon", "default_language": "klingon"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Invalid default_language should fail",
    ),
    # text index language_override errors
    IndexTestCase(
        id="text_language_override_non_string",
        indexes=({"key": {"a": "text"}, "name": "a_text_lo_int", "language_override": 123},),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Non-string language_override should fail",
    ),
    IndexTestCase(
        id="text_language_override_empty",
        indexes=({"key": {"a": "text"}, "name": "a_text_lo_empty", "language_override": ""},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Empty language_override should fail",
    ),
    # 2dsphere errors
    IndexTestCase(
        id="2dsphere_version_zero",
        indexes=({"key": {"a": "2dsphere"}, "name": "a_2ds_v0", "2dsphereIndexVersion": 0},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="2dsphereIndexVersion 0 should fail",
    ),
    # 2d index errors
    IndexTestCase(
        id="2d_bits_zero",
        indexes=({"key": {"a": "2d"}, "name": "a_2d_b0", "bits": 0},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="2d bits 0 should fail",
    ),
    IndexTestCase(
        id="2d_bits_above_32",
        indexes=({"key": {"a": "2d"}, "name": "a_2d_b33", "bits": 33},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="2d bits 33 should fail",
    ),
    IndexTestCase(
        id="2d_min_equals_max",
        indexes=({"key": {"a": "2d"}, "name": "a_2d_eq", "min": 10, "max": 10},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="2d min == max should fail",
    ),
    IndexTestCase(
        id="2d_min_greater_than_max",
        indexes=({"key": {"a": "2d"}, "name": "a_2d_gt", "min": 100, "max": 10},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="2d min > max should fail",
    ),
    # Field name errors in key
    IndexTestCase(
        id="key_field_dollar_prefix",
        indexes=({"key": {"$a": 1}, "name": "dollar_a"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Field name starting with $ should fail",
    ),
    IndexTestCase(
        id="key_field_empty_path_segment",
        indexes=({"key": {"a..b": 1}, "name": "a_dotdot_b"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Field with empty path segment should fail",
    ),
    IndexTestCase(
        id="key_field_empty_string",
        indexes=({"key": {"": 1}, "name": "empty_field"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Empty string field name should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SINGLE_COMMAND_ERROR_TESTS))
def test_createIndexes_error(collection, test):
    """Test createIndexes error cases (parametrized)."""
    if test.doc:
        collection.insert_many(list(test.doc))
    if test.setup_indexes:
        execute_command(
            collection,
            {
                "createIndexes": collection.name,
                "indexes": list(test.setup_indexes),
            },
        )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": list(test.indexes),
        },
    )
    assertFailureCode(result, test.error_code, test.msg)


def test_createIndexes_empty_string_collection_name(collection):
    """Test createIndexes with empty string collection name fails."""
    result = execute_command(
        collection,
        {
            "createIndexes": "",
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertFailureCode(result, INVALID_NAMESPACE_ERROR, "Empty collection name should fail")


def test_createIndexes_non_string_collection_name_object(collection):
    """Test createIndexes with non-string collection name (object) fails."""
    result = execute_command(
        collection,
        {
            "createIndexes": {},
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertFailureCode(result, INVALID_NAMESPACE_ERROR, "Non-string collection name should fail")


def test_createIndexes_system_prefix_collection_name(collection):
    """Test createIndexes with 'system.' prefix collection name fails."""
    result = execute_command(
        collection,
        {
            "createIndexes": "system.test_col",
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertFailureCode(result, INVALID_NAMESPACE_ERROR, "system. prefix should fail")


def test_createIndexes_dollar_in_collection_name(collection):
    """Test createIndexes with '$' in collection name fails."""
    result = execute_command(
        collection,
        {
            "createIndexes": "test$col",
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertFailureCode(result, INVALID_NAMESPACE_ERROR, "$ in collection name should fail")


def test_createIndexes_indexes_non_array_object(collection):
    """Test createIndexes with indexes as object (not array) fails."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": {"key": {"a": 1}, "name": "a_1"},
        },
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, "Non-array indexes should fail")


def test_createIndexes_missing_indexes_field(collection):
    """Test createIndexes without indexes field fails."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
        },
    )
    assertFailureCode(result, MISSING_FIELD_ERROR, "Missing indexes field should fail")


def test_createIndexes_empty_index_spec_in_array(collection):
    """Test createIndexes with empty index spec object in array fails."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{}],
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR, "Empty index spec should fail")


def test_createIndexes_id_descending_fails(database_client):
    """Test creating descending index on _id fails (must be {_id: 1})."""
    coll = database_client["id_desc_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"_id": -1}, "name": "_id_neg1"}],
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR, "Descending _id should fail")
    coll.drop()


def test_createIndexes_on_view_fails(database_client):
    """Test createIndexes on a view fails."""
    coll = database_client["base_coll_view_test"]
    coll.drop()
    coll.insert_one({"_id": 1, "a": 1})
    database_client.command("create", "my_view_test", viewOn=coll.name, pipeline=[])
    view_coll = database_client["my_view_test"]
    result = execute_command(
        view_coll,
        {
            "createIndexes": view_coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertFailureCode(
        result, COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR, "createIndexes on view should fail"
    )
    database_client.drop_collection("my_view_test")
    coll.drop()


def test_createIndexes_duplicate_name_in_batch_new_collection(database_client):
    """Test duplicate name for different keys in same request on new collection fails."""
    coll = database_client["dup_name_batch_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [
                {"key": {"a": 1}, "name": "same_name"},
                {"key": {"b": 1}, "name": "same_name"},
            ],
        },
    )
    assertFailureCode(result, INDEX_KEY_SPECS_CONFLICT_ERROR, "Duplicate name in batch should fail")
    coll.drop()


def test_createIndexes_reserved_name_id_on_non_id_key(database_client):
    """Test creating index with name '_id_' on a non-_id key fails."""
    coll = database_client["reserved_id_name_test"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "_id_"}],
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR, "Reserved name _id_ on non-_id key should fail")
    coll.drop()


def test_createIndexes_unique_multiple_null_values_fails(collection):
    """Test unique index with multiple null values fails on insert."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_unique", "unique": True}],
        },
    )
    collection.insert_one({"_id": 1, "a": None})
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 2, "a": None}],
        },
    )
    assertFailureCode(result, DUPLICATE_KEY_ERROR, "Duplicate null should fail")


def test_createIndexes_unique_missing_field_duplicates_fails(collection):
    """Test unique index with multiple documents missing indexed field fails."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_unique", "unique": True}],
        },
    )
    collection.insert_one({"_id": 1, "b": 1})
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 2, "b": 2}],
        },
    )
    assertFailureCode(result, DUPLICATE_KEY_ERROR, "Duplicate missing field should fail")


def test_createIndexes_65th_index_fails(database_client):
    """Test creating 65th index (including _id) fails."""
    coll = database_client["exceed_idx_limit_test"]
    coll.drop()
    indexes = [{"key": {f"f{i}": 1}, "name": f"f{i}_1"} for i in range(63)]
    execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": indexes,
        },
    )
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"extra": 1}, "name": "extra_1"}],
        },
    )
    assertFailureCode(result, CANNOT_CREATE_INDEX_ERROR, "65th index should fail")
    coll.drop()


def test_createIndexes_batch_exceeding_limit_fails(database_client):
    """Test creating multiple indexes in one command that would exceed 64 limit fails."""
    coll = database_client["batch_exceed_limit_test"]
    coll.drop()
    indexes = [{"key": {f"f{i}": 1}, "name": f"f{i}_1"} for i in range(64)]
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": indexes,
        },
    )
    assertFailureCode(result, CANNOT_CREATE_INDEX_ERROR, "Batch exceeding 64 should fail")
    coll.drop()
