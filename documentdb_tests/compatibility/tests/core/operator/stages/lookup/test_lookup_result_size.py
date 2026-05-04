"""Tests for $lookup large result sets and document size limits."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Large Result Sets]: joining many matching documents succeeds
# and the joined array can exceed 16MB when fully materialized to the
# client.
LOOKUP_LARGE_RESULT_SET_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "join_1000_matching_documents",
        docs=[{"_id": 1, "lf": "m"}],
        foreign_docs=[{"_id": i, "ff": "m"} for i in range(1_000)],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            },
            {"$project": {"joined_count": {"$size": "$joined"}}},
        ],
        expected=[{"_id": 1, "joined_count": 1_000}],
        msg="$lookup should successfully join 1000 matching documents",
    ),
    LookupTestCase(
        "joined_array_exceeds_16mb",
        docs=[{"_id": 1, "lf": "m"}],
        foreign_docs=[{"_id": i, "ff": "m", "data": "x" * 1_000_000} for i in range(20)],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            },
            {"$project": {"joined_count": {"$size": "$joined"}}},
        ],
        expected=[{"_id": 1, "joined_count": 20}],
        msg="$lookup should produce a joined array that exceeds 16MB",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_LARGE_RESULT_SET_TESTS))
def test_lookup_large_result_sets(collection, test_case: LookupTestCase):
    """Test $lookup with large result sets."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
