"""
Tests projected output shape for the $elemMatch projection operator.
"""

from __future__ import annotations

import pytest
from bson import SON

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import OrderedKeys

# Property [Inclusion/Exclusion Mode]: $elemMatch adopts the inclusion or exclusion
# mode of its sibling projection fields, defaulting to inclusion when alone, and _id: 0
# is allowed in either mode.
ELEMMATCH_INCLUSION_EXCLUSION_MODE_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "mode_elemmatch_alone_inclusion",
        doc=[{"_id": 1, "arr": [1, 2, 3], "name": "Alice", "age": 30}],
        projection={"arr": {"$elemMatch": {"$gte": 2}}},
        expected=[{"_id": 1, "arr": [2]}],
        msg="$elemMatch alone should include only _id and the matched field",
    ),
    ProjectionTestCase(
        "mode_combined_with_inclusion",
        doc=[{"_id": 1, "arr": [1, 2, 3], "name": "Alice", "age": 30}],
        projection={"arr": {"$elemMatch": {"$gte": 2}}, "name": 1},
        expected=[{"_id": 1, "name": "Alice", "arr": [2]}],
        msg="$elemMatch combined with inclusion fields should operate in inclusion mode",
    ),
    ProjectionTestCase(
        "mode_combined_with_exclusion",
        doc=[{"_id": 1, "arr": [1, 2, 3], "name": "Alice", "city": "NYC"}],
        projection={"arr": {"$elemMatch": {"$gte": 2}}, "city": 0},
        expected=[{"_id": 1, "arr": [2], "name": "Alice"}],
        msg="$elemMatch combined with exclusion fields should operate in exclusion mode",
    ),
    ProjectionTestCase(
        "mode_id_zero_with_elemmatch_alone",
        doc=[{"_id": 1, "arr": [1, 2, 3], "name": "Alice"}],
        projection={"arr": {"$elemMatch": {"$gte": 2}}, "_id": 0},
        expected=[{"arr": [2]}],
        msg="$elemMatch should allow _id: 0 in inclusion mode",
    ),
    ProjectionTestCase(
        "mode_id_zero_with_exclusion",
        doc=[{"_id": 1, "arr": [1, 2, 3], "name": "Alice", "city": "NYC"}],
        projection={"arr": {"$elemMatch": {"$gte": 2}}, "_id": 0, "city": 0},
        expected=[{"arr": [2], "name": "Alice"}],
        msg="$elemMatch should allow _id: 0 in exclusion mode",
    ),
]

# Property [Multiple Projections]: multiple $elemMatch projections on different fields
# are each applied independently, selecting the first match within each field.
ELEMMATCH_MULTIPLE_FIELDS_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "multiple_fields_both_match",
        doc=[{"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30]}],
        projection={"a": {"$elemMatch": {"$gte": 2}}, "b": {"$elemMatch": {"$gte": 20}}},
        expected=[{"_id": 1, "a": [2], "b": [20]}],
        msg="$elemMatch should apply independently to each field when projected on multiple fields",
    ),
    ProjectionTestCase(
        "multiple_fields_one_omitted",
        doc=[{"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30]}],
        projection={"a": {"$elemMatch": {"$gte": 2}}, "b": {"$elemMatch": {"$gte": 99}}},
        expected=[{"_id": 1, "a": [2]}],
        msg="$elemMatch should omit only the non-matching field when projected on multiple fields",
    ),
]

# Property [Field Ordering - Inclusion Mode]: in inclusion mode, the fields included
# with field: 1 appear in document storage order and the $elemMatch field is appended
# after them.
ELEMMATCH_FIELD_ORDER_INCLUSION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "order_inclusion_elemmatch_appended_last",
        doc=[SON([("_id", 1), ("alpha", "a"), ("arr", [1, 2, 3]), ("beta", "b")])],
        projection=SON([("alpha", 1), ("arr", {"$elemMatch": {"$gte": 2}}), ("beta", 1)]),
        expected={"": OrderedKeys(["_id", "alpha", "beta", "arr"])},
        msg="$elemMatch field should appear after the fields included with field: 1",
    ),
    ProjectionTestCase(
        "order_inclusion_field_1_fields_in_storage_order",
        doc=[SON([("_id", 1), ("x", 10), ("arr", [1, 2, 3]), ("z", 30)])],
        projection=SON([("z", 1), ("arr", {"$elemMatch": {"$gte": 2}}), ("x", 1)]),
        expected={"": OrderedKeys(["_id", "x", "z", "arr"])},
        msg="field: 1 inclusions should appear in storage order not projection-spec order",
    ),
]

# Property [Field Ordering - Exclusion Mode]: in exclusion mode, the $elemMatch
# field retains its original document storage position.
ELEMMATCH_FIELD_ORDER_EXCLUSION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "order_exclusion_retains_storage_position",
        doc=[SON([("_id", 1), ("alpha", "a"), ("arr", [1, 2, 3]), ("beta", "b"), ("gamma", "c")])],
        projection=SON([("arr", {"$elemMatch": {"$gte": 2}}), ("gamma", 0)]),
        expected={"": OrderedKeys(["_id", "alpha", "arr", "beta"])},
        msg="$elemMatch field should retain its document storage position in exclusion mode",
    ),
    ProjectionTestCase(
        "order_exclusion_id_zero_retains_position",
        doc=[SON([("_id", 1), ("x", 10), ("arr", [1, 2, 3]), ("y", 20), ("z", 30)])],
        projection=SON([("_id", 0), ("arr", {"$elemMatch": {"$gte": 2}}), ("z", 0)]),
        expected={"": OrderedKeys(["x", "arr", "y"])},
        msg="$elemMatch field should retain its storage position in exclusion mode with _id: 0",
    ),
]

PROJECTION_OUTPUT_TESTS = (
    ELEMMATCH_INCLUSION_EXCLUSION_MODE_TESTS
    + ELEMMATCH_MULTIPLE_FIELDS_TESTS
    + ELEMMATCH_FIELD_ORDER_INCLUSION_TESTS
    + ELEMMATCH_FIELD_ORDER_EXCLUSION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PROJECTION_OUTPUT_TESTS))
def test_elemmatch_projection_output(collection, test):
    """Test $elemMatch projection output shape cases."""
    collection.insert_many(test.doc)
    cmd = {
        "find": collection.name,
        "projection": test.projection,
    }
    if test.filter is not None:
        cmd["filter"] = test.filter
    result = execute_command(collection, cmd)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
