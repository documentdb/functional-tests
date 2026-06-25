"""Tests for getClusterParameter response structure and value-type fidelity.

The top-level shape ({ok:1, clusterParameters: <array>}) is asserted in
test_getClusterParameter_argument_handling.py; this file covers element-level
structure and BSON-type fidelity: each element is an object keyed by ``_id``,
a single request isolates exactly the requested name, and parameter values
(nested documents, numbers, and clusterParameterTime) keep their BSON types
without coercion.
"""

import pytest
from bson import Decimal128, Int64, Timestamp

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq, Len

pytestmark = pytest.mark.admin

# Numeric BSON types that must survive a round trip without being coerced to
# string. bool is intentionally excluded (it is not a numeric value here).
_NUMERIC_TYPES = (int, float, Int64, Decimal128)


def test_getClusterParameter_each_element_is_object_with_string_id(collection):
    """Test every clusterParameters element is an object with a string _id."""
    params = execute_admin_command(collection, {"getClusterParameter": "*"})["clusterParameters"]
    summary = {
        "all_objects": all(isinstance(e, dict) for e in params),
        "all_ids_str": all(isinstance(e.get("_id"), str) for e in params),
    }
    assertProperties(
        {"summary": summary},
        {"summary": Eq({"all_objects": True, "all_ids_str": True})},
        msg="Every clusterParameters element should be an object with a string _id.",
        raw_res=True,
    )


def test_getClusterParameter_single_request_isolates_name(collection):
    """Test requesting one name returns exactly that name and no others."""
    name = execute_admin_command(collection, {"getClusterParameter": "*"})["clusterParameters"][0][
        "_id"
    ]
    result = execute_admin_command(collection, {"getClusterParameter": name})
    assertProperties(
        result,
        {"clusterParameters": Len(1), "clusterParameters.0._id": Eq(name)},
        msg=f"Requesting '{name}' should return exactly that name.",
        raw_res=True,
    )


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


def test_getClusterParameter_document_valued_parameter_preserves_nested_object(collection):
    """Test a document-valued parameter keeps its nested object structure."""
    params = execute_admin_command(collection, {"getClusterParameter": "*"})["clusterParameters"]
    nested_is_object = None
    for entry in params:
        for key, value in entry.items():
            if key != "_id" and isinstance(value, dict):
                nested_is_object = isinstance(value, dict)
                break
        if nested_is_object is not None:
            break
    if nested_is_object is None:
        pytest.skip("no document-valued cluster parameter on this deployment")
    assertProperties(
        {"nested_is_object": nested_is_object},
        {"nested_is_object": Eq(True)},
        msg="A document-valued parameter should preserve its nested object structure.",
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
