"""Tests for getClusterParameter response structure and value-type fidelity.

Verifies the shape and BSON types of the success response:
clusterParameters is an array, each element has _id equal to the
requested name, ok is 1, and single-name requests are isolated.
Also validates BSON type fidelity (clusterParameterTime, numeric values).

Categories: #4 (response structure), #17
"""

import pytest
from bson import Decimal128, Int64, Timestamp

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq, IsType, Len

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"

# Numeric BSON types that must survive a round trip without being coerced to
# string. bool is intentionally excluded (it is not a numeric value here).
_NUMERIC_TYPES = (int, float, Int64, Decimal128)


# ---------------------------------------------------------------------------
# §4  Response shape
# ---------------------------------------------------------------------------


def test_getClusterParameter_response_has_ok_1(collection):
    """Test success response includes ok:1."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertProperties(result, {"ok": Eq(1.0)}, msg="Response ok should be 1.0", raw_res=True)


def test_getClusterParameter_response_clusterParameters_is_array(collection):
    """Test success response contains 'clusterParameters' field of type array."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertProperties(
        result,
        {"clusterParameters": IsType("array")},
        msg="clusterParameters should be an array",
        raw_res=True,
    )


def test_getClusterParameter_single_name_length_is_one(collection):
    """Test single-name request returns exactly one element in clusterParameters."""
    result = execute_admin_command(collection, {"getClusterParameter": _VALID_PARAM})
    assertProperties(
        result,
        {"clusterParameters": Len(1)},
        msg="Single-name request should return exactly one element",
        raw_res=True,
    )


def test_getClusterParameter_element_has_id_field(collection):
    """Test the clusterParameters element has a string '_id' field."""
    result = execute_admin_command(collection, {"getClusterParameter": _VALID_PARAM})
    assertProperties(
        result,
        {"clusterParameters.0._id": IsType("string")},
        msg="_id field should be a string",
        raw_res=True,
    )


def test_getClusterParameter_single_name_id_matches_request(collection):
    """Test requesting one name returns element with _id equal to requested name."""
    result = execute_admin_command(collection, {"getClusterParameter": _VALID_PARAM})
    assertProperties(
        result,
        {"clusterParameters.0._id": Eq(_VALID_PARAM)},
        msg=f"_id should equal requested name '{_VALID_PARAM}'",
        raw_res=True,
    )


def test_getClusterParameter_element_has_nested_value_field(collection):
    """Test document-valued parameter has a nested value sub-document."""
    result = execute_admin_command(collection, {"getClusterParameter": _VALID_PARAM})
    assertProperties(
        result,
        {"clusterParameters.0.preAndPostImages": IsType("object")},
        msg="changeStreamOptions should contain 'preAndPostImages' sub-document",
        raw_res=True,
    )


def test_getClusterParameter_element_is_object_type(collection):
    """Test the first clusterParameters element is a document (object type)."""
    result = execute_admin_command(collection, {"getClusterParameter": _VALID_PARAM})
    assertProperties(
        result,
        {"clusterParameters.0": IsType("object")},
        msg="clusterParameters element should be an object",
        raw_res=True,
    )


# ---------------------------------------------------------------------------
# §17  Value type fidelity
# ---------------------------------------------------------------------------


def test_getClusterParameter_clusterParameterTime_is_timestamp_when_present(collection):
    """Test any clusterParameterTime field is a BSON Timestamp."""
    params = execute_admin_command(collection, {"getClusterParameter": "*"})["clusterParameters"]
    times = [e["clusterParameterTime"] for e in params if "clusterParameterTime" in e]
    if not times:
        pytest.skip("no parameter on this deployment carries clusterParameterTime")
    all_timestamps = all(isinstance(t, Timestamp) for t in times)
    assertProperties(
        {"all_timestamps": all_timestamps},
        {"all_timestamps": Eq(True)},
        msg="clusterParameterTime should be a BSON Timestamp.",
        raw_res=True,
    )


def test_getClusterParameter_numeric_value_not_coerced(collection):
    """Test numeric parameter values keep a numeric BSON type (not stringified)."""
    params = execute_admin_command(collection, {"getClusterParameter": "*"})["clusterParameters"]

    def first_numeric_type(value):
        if isinstance(value, bool):
            return None
        if isinstance(value, _NUMERIC_TYPES):
            return type(value).__name__
        if isinstance(value, dict):
            for v in value.values():
                found = first_numeric_type(v)
                if found:
                    return found
        return None

    numeric_type = None
    for entry in params:
        for key, value in entry.items():
            if key == "_id":
                continue
            numeric_type = first_numeric_type(value)
            if numeric_type:
                break
        if numeric_type:
            break
    if numeric_type is None:
        pytest.skip("no numeric-valued cluster parameter on this deployment")
    is_numeric_type = numeric_type in {"int", "float", "Int64", "Decimal128"}
    assertProperties(
        {"is_numeric_type": is_numeric_type},
        {"is_numeric_type": Eq(True)},
        msg=f"Numeric parameter value kept numeric BSON type '{numeric_type}' (not coerced).",
        raw_res=True,
    )
