"""Tests for explain command error conditions.

Covers invalid verbosity strings, invalid and non-explainable explain field
values, and geospatial explain errors (hinting a non-geo index with
$nearSphere).
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_FOUND_ERROR,
    ILLEGAL_OPERATION_ERROR,
    NO_QUERY_EXECUTION_PLANS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin

EXPLAIN_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="invalid_verbosity",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "notAMode",
        },
        error_code=BAD_VALUE_ERROR,
        msg="invalid verbosity string should be BadValue",
    ),
    CommandTestCase(
        id="non_explainable_command",
        command=lambda ctx: {"explain": {"insert": ctx.collection, "documents": [{"_id": 1}]}},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="non-explainable command should error",
    ),
    CommandTestCase(
        id="empty_explain_document",
        command={"explain": {}},
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="empty explain document should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EXPLAIN_ERROR_TESTS))
def test_explain_error_cases(collection, test):
    """Test explain rejects invalid verbosity, non-explainable commands,
    and malformed explain fields.
    """
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.geospatial
def test_explain_find_nearSphere_hint_non_geo_index_fails(collection):
    """Test explain of a $nearSphere find hinting a non-geo index returns an error."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 1},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}, "a": 2},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 2]}, "a": 3},
        ]
    )
    collection.create_index([("a", 1)])
    near = {"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}}
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": near, "hint": {"a": 1}},
            "verbosity": "queryPlanner",
        },
    )
    assertFailureCode(
        result,
        NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="$nearSphere with a non-geo index hint should fail (no viable plan)",
    )
