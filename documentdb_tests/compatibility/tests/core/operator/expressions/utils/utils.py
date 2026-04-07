"""
Utility functions for functional tests.

Provides helper functions for building and executing MongoDB aggregation
expressions and operators in test scenarios.
"""

from documentdb_tests.framework.assertions import assertExpected
from documentdb_tests.framework.error_codes import ErrorCode
from documentdb_tests.framework.executor import execute_command


def assertExprResult(result, expected, msg=None):
    """Assert expression result. Wraps success values in [{"result": val}] format."""
    if not isinstance(expected, ErrorCode):
        expected = [{"result": expected}]
    assertExpected(result, expected, msg)


def execute_expression(collection, expression):
    """
    Execute an aggregation expression against the collection.

    Projects the expression as "result" over whatever documents exist
    in the collection. Caller is responsible for inserting test data first.

    Args:
        collection: MongoDB collection object
        expression: The expression to evaluate (e.g., {"$divide": ["$a", "$b"]})

    Returns:
        Result from execute_command with structure:
        {"cursor": {"firstBatch": [{"result": <value>}]}}
    """
    return execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "result": expression}},
            ],
            "cursor": {},
        },
    )
