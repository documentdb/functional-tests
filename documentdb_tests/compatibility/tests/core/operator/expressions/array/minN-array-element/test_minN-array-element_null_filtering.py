"""
Compatibility tests for $minN-array-element null filtering behavior.

Tests that $minN-array-element filters null values when n exceeds the number of
available non-null values.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.aggregate, pytest.mark.smoke]


def test_minN_array_element_filters_null_values_when_n_exceeds_available_values(collection):
    """Test $minN-array-element filters null values when n exceeds available values."""
    collection.insert_many(
        [
            {"_id": 1, "values": [None, 8, 2, None, 5]},
            {"_id": 2, "values": [None]},
            {"_id": 3, "values": []},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"minValues": {"$minN": {"n": 5, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "minValues": [2, 5, 8]},
        {"_id": 2, "minValues": []},
        {"_id": 3, "minValues": []},
    ]
    assertSuccess(
        result,
        expected,
        msg="$minN-array-element should filter null values when n exceeds available values",
    )
