"""
Validation tests for $minN-array-element n argument.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import N_ARRAY_ELEMENT_NON_POSITIVE_N_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.aggregate


def test_minN_array_element_rejects_zero_n(collection):
    """Test $minN-array-element rejects n=0."""
    collection.insert_one({"_id": 1, "values": [1, 2]})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"minValues": {"$minN": {"n": 0, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    assertFailureCode(
        result,
        N_ARRAY_ELEMENT_NON_POSITIVE_N_ERROR,
        msg="$minN-array-element should reject n=0",
    )
