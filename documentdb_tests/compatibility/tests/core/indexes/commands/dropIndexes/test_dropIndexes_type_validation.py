"""
Tests for dropIndexes command — BSON type validation.

Covers invalid BSON types for collection name, index field, writeConcern
field type, and writeConcern field values.
"""

import pytest
from bson import Binary, Code, Decimal128, Int64, ObjectId, Regex, Timestamp
from bson.max_key import MaxKey
from bson.min_key import MinKey

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_NAMESPACE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

INVALID_COLLECTION_NAME_TYPES: list[IndexTestCase] = [
    IndexTestCase(
        "coll_name_int",
        invalid_input=123,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Integer collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_long",
        invalid_input=Int64(123),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Long collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_bool",
        invalid_input=True,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Boolean collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_double",
        invalid_input=1.5,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Double collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_decimal128",
        invalid_input=Decimal128("1.5"),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Decimal128 collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_null",
        invalid_input=None,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Null collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_object",
        invalid_input={"a": 1},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Object collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_array",
        invalid_input=[1, 2],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Array collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_objectId",
        invalid_input=ObjectId(),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="ObjectId collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_binData",
        invalid_input=Binary(b"\x00\x01"),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="BinData collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_regex",
        invalid_input=Regex(".*"),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Regex collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_javascript",
        invalid_input=Code("function(){}"),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="JavaScript collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_timestamp",
        invalid_input=Timestamp(0, 1),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Timestamp collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_minKey",
        invalid_input=MinKey(),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="MinKey collection name should fail with 73",
    ),
    IndexTestCase(
        "coll_name_maxKey",
        invalid_input=MaxKey(),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="MaxKey collection name should fail with 73",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_COLLECTION_NAME_TYPES))
def test_dropIndexes_invalid_collection_name_type(collection, test):
    """Test dropIndexes rejects non-string collection name types."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a")

    result = execute_command(collection, {"dropIndexes": test.invalid_input, "index": "*"})

    assertResult(result, error_code=test.error_code, msg=test.msg)


INVALID_INDEX_TYPES: list[IndexTestCase] = [
    IndexTestCase(
        "index_type_int",
        invalid_input=123,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Integer index should fail with 14",
    ),
    IndexTestCase(
        "index_type_long",
        invalid_input=Int64(123),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Long index should fail with 14",
    ),
    IndexTestCase(
        "index_type_bool",
        invalid_input=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Boolean index should fail with 14",
    ),
    IndexTestCase(
        "index_type_double",
        invalid_input=1.5,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Double index should fail with 14",
    ),
    IndexTestCase(
        "index_type_decimal128",
        invalid_input=Decimal128("1.5"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Decimal128 index should fail with 14",
    ),
    IndexTestCase(
        "index_type_null",
        invalid_input=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Null index should fail with 14",
    ),
    IndexTestCase(
        "index_type_objectId",
        invalid_input=ObjectId(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId index should fail with 14",
    ),
    IndexTestCase(
        "index_type_binData",
        invalid_input=Binary(b"\x00\x01"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="BinData index should fail with 14",
    ),
    IndexTestCase(
        "index_type_regex",
        invalid_input=Regex(".*"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex index should fail with 14",
    ),
    IndexTestCase(
        "index_type_javascript",
        invalid_input=Code("function(){}"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="JavaScript index should fail with 14",
    ),
    IndexTestCase(
        "index_type_timestamp",
        invalid_input=Timestamp(0, 1),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp index should fail with 14",
    ),
    IndexTestCase(
        "index_type_minKey",
        invalid_input=MinKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey index should fail with 14",
    ),
    IndexTestCase(
        "index_type_maxKey",
        invalid_input=MaxKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey index should fail with 14",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_INDEX_TYPES))
def test_dropIndexes_invalid_index_type(collection, test):
    """Test dropIndexes rejects invalid index field types."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a")

    result = execute_command(
        collection, {"dropIndexes": collection.name, "index": test.invalid_input}
    )

    assertResult(result, error_code=test.error_code, msg=test.msg)


INVALID_WRITE_CONCERN_TYPES: list[IndexTestCase] = [
    IndexTestCase(
        "wc_string",
        invalid_input="invalid",
        error_code=TYPE_MISMATCH_ERROR,
        msg="String writeConcern should fail with 14",
    ),
    IndexTestCase(
        "wc_int",
        invalid_input=123,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Integer writeConcern should fail with 14",
    ),
    IndexTestCase(
        "wc_bool",
        invalid_input=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Boolean writeConcern should fail with 14",
    ),
    IndexTestCase(
        "wc_array",
        invalid_input=[1, 2],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Array writeConcern should fail with 14",
    ),
    IndexTestCase(
        "wc_double",
        invalid_input=1.5,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Double writeConcern should fail with 14",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_WRITE_CONCERN_TYPES))
def test_dropIndexes_writeConcern_non_object(collection, test):
    """Test dropIndexes rejects non-object writeConcern types."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a")

    result = execute_command(
        collection,
        {
            "dropIndexes": collection.name,
            "index": "*",
            "writeConcern": test.invalid_input,
        },
    )

    assertResult(result, error_code=test.error_code, msg=test.msg)


INVALID_WRITE_CONCERN_VALUES: list[IndexTestCase] = [
    IndexTestCase(
        "w_invalid_string",
        write_concern={"w": "invalid"},
        error_code=BAD_VALUE_ERROR,
        msg="Invalid string w value should fail with BadValue",
    ),
    IndexTestCase(
        "w_negative",
        write_concern={"w": -1},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Negative w should fail with FailedToParse",
    ),
    IndexTestCase(
        "j_non_bool",
        write_concern={"j": "true"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Non-boolean j should fail with TypeMismatch",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_WRITE_CONCERN_VALUES))
def test_dropIndexes_writeConcern_invalid_values(collection, test):
    """Test dropIndexes rejects invalid writeConcern field values."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a")

    result = execute_command(
        collection,
        {
            "dropIndexes": collection.name,
            "index": "*",
            "writeConcern": test.write_concern,
        },
    )

    assertResult(result, error_code=test.error_code, msg=test.msg)
