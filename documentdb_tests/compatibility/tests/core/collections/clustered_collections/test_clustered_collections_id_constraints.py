"""Tests for _id field constraints specific to clustered collections."""

from __future__ import annotations

import pytest
from bson import Binary

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    CLUSTERED_INFINITY_DUPLICATE_ERROR,
    CLUSTERED_NAN_DUPLICATE_ERROR,
    CLUSTERED_RECORD_ID_SIZE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.test_constants import (
    CLUSTERED_RECORD_ID_LIMIT_BYTES,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

from .utils.clustered_utils import create_clustered


# Property [RecordId Size Limit]: clustered collections enforce a maximum _id
# size that regular collections do not have.
@pytest.mark.collection_mgmt
def test_record_id_size_limit_exceeded(collection):
    """Test _id exceeding the RecordId size limit is rejected."""
    name = create_clustered(collection)
    # String _id overhead is 2 bytes (type byte + null terminator in KeyString encoding).
    large_id = "x" * (CLUSTERED_RECORD_ID_LIMIT_BYTES - 2 + 1)
    result = execute_command(
        collection,
        {"insert": name, "documents": [{"_id": large_id}]},
    )
    assertResult(
        result,
        error_code=CLUSTERED_RECORD_ID_SIZE_ERROR,
        msg="should reject _id exceeding the RecordId size limit",
    )


# Property [RecordId Size Limit Boundary]: a string _id at exactly the maximum
# allowed length succeeds.
@pytest.mark.collection_mgmt
def test_record_id_size_limit_boundary(collection):
    """Test _id at exactly the RecordId size limit succeeds."""
    name = create_clustered(collection)
    # String _id overhead is 2 bytes (type byte + null terminator in KeyString encoding).
    max_id = "x" * (CLUSTERED_RECORD_ID_LIMIT_BYTES - 2)
    result = execute_command(
        collection,
        {"insert": name, "documents": [{"_id": max_id}]},
    )
    assertSuccessPartial(
        result, {"n": 1, "ok": 1.0}, msg="should accept _id at exactly the RecordId limit"
    )


# Property [NaN Duplicate Error Code]: duplicate NaN _id (any NaN variant)
# produces a clustered-specific error code different from regular collections.
@pytest.mark.collection_mgmt
@pytest.mark.parametrize(
    "first,second",
    [
        pytest.param(FLOAT_NAN, FLOAT_NAN, id="float_nan"),
        pytest.param(FLOAT_NEGATIVE_NAN, FLOAT_NEGATIVE_NAN, id="float_neg_nan"),
        pytest.param(DECIMAL128_NAN, DECIMAL128_NAN, id="decimal128_nan"),
        pytest.param(DECIMAL128_NEGATIVE_NAN, DECIMAL128_NEGATIVE_NAN, id="decimal128_neg_nan"),
        pytest.param(FLOAT_NAN, DECIMAL128_NAN, id="float_nan_then_decimal128_nan"),
        pytest.param(
            FLOAT_NEGATIVE_NAN, DECIMAL128_NEGATIVE_NAN, id="float_neg_nan_then_decimal128_neg_nan"
        ),
    ],
)
def test_nan_duplicate_clustered_error(collection, first, second):
    """Test NaN duplicate _id produces clustered-specific error."""
    name = create_clustered(collection)
    db = collection.database
    db[name].insert_one({"_id": first})
    result = execute_command(
        collection,
        {"insert": name, "documents": [{"_id": second}]},
    )
    assertResult(
        result,
        error_code=CLUSTERED_NAN_DUPLICATE_ERROR,
        msg="NaN duplicate should produce clustered-specific error",
    )


# Property [Infinity Duplicate Error Code]: duplicate Infinity _id (any Infinity
# variant) produces a clustered-specific error code different from regular
# collections.
@pytest.mark.collection_mgmt
@pytest.mark.parametrize(
    "first,second",
    [
        pytest.param(FLOAT_INFINITY, FLOAT_INFINITY, id="float_inf"),
        pytest.param(FLOAT_NEGATIVE_INFINITY, FLOAT_NEGATIVE_INFINITY, id="float_neg_inf"),
        pytest.param(DECIMAL128_INFINITY, DECIMAL128_INFINITY, id="decimal128_inf"),
        pytest.param(
            DECIMAL128_NEGATIVE_INFINITY, DECIMAL128_NEGATIVE_INFINITY, id="decimal128_neg_inf"
        ),
        pytest.param(FLOAT_INFINITY, DECIMAL128_INFINITY, id="float_inf_then_decimal128_inf"),
        pytest.param(
            FLOAT_NEGATIVE_INFINITY,
            DECIMAL128_NEGATIVE_INFINITY,
            id="float_neg_inf_then_decimal128_neg_inf",
        ),
    ],
)
def test_infinity_duplicate_clustered_error(collection, first, second):
    """Test Infinity duplicate _id produces clustered-specific error."""
    name = create_clustered(collection)
    db = collection.database
    db[name].insert_one({"_id": first})
    result = execute_command(
        collection,
        {"insert": name, "documents": [{"_id": second}]},
    )
    assertResult(
        result,
        error_code=CLUSTERED_INFINITY_DUPLICATE_ERROR,
        msg="Infinity duplicate should produce clustered-specific error",
    )


# Property [Binary _id RecordId Boundary]: Binary _id has 7 bytes overhead in
# the RecordId encoding; at exactly the limit it succeeds, one byte over fails.
@pytest.mark.collection_mgmt
def test_binary_id_record_id_boundary(collection):
    """Test Binary _id at exactly RecordId limit succeeds."""
    name = create_clustered(collection)
    # Binary _id overhead is 7 bytes.
    max_binary = Binary(b"x" * (CLUSTERED_RECORD_ID_LIMIT_BYTES - 7))
    result = execute_command(
        collection,
        {"insert": name, "documents": [{"_id": max_binary}]},
    )
    assertSuccessPartial(
        result, {"n": 1, "ok": 1.0}, msg="should accept Binary _id at exactly the RecordId limit"
    )


# Property [Binary _id RecordId Exceeded]: Binary _id exceeding the RecordId
# limit produces the clustered-specific size error.
@pytest.mark.collection_mgmt
def test_binary_id_record_id_exceeded(collection):
    """Test Binary _id exceeding RecordId limit is rejected."""
    name = create_clustered(collection)
    # Binary _id overhead is 7 bytes.
    large_binary = Binary(b"x" * (CLUSTERED_RECORD_ID_LIMIT_BYTES - 7 + 1))
    result = execute_command(
        collection,
        {"insert": name, "documents": [{"_id": large_binary}]},
    )
    assertResult(
        result,
        error_code=CLUSTERED_RECORD_ID_SIZE_ERROR,
        msg="should reject Binary _id exceeding RecordId limit",
    )


# Property [Multi-Byte String RecordId Limit]: the RecordId size limit applies
# to UTF-8 byte length, not character count.
@pytest.mark.collection_mgmt
def test_multibyte_string_record_id_limit(collection):
    """Test RecordId limit applies to byte length for multi-byte strings."""
    name = create_clustered(collection)
    # Each 3-byte UTF-8 character (e.g. U+4E00) counts as 3 bytes.
    # String overhead is 2 bytes. Use chars that fill exactly to the limit.
    max_chars = (CLUSTERED_RECORD_ID_LIMIT_BYTES - 2) // 3
    max_id = "\u4e00" * max_chars
    result = execute_command(
        collection,
        {"insert": name, "documents": [{"_id": max_id}]},
    )
    assertSuccessPartial(
        result, {"n": 1, "ok": 1.0}, msg="should accept multi-byte string _id within byte limit"
    )
