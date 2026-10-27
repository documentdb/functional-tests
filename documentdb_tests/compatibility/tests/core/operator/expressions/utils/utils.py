"""
Utility functions for functional tests.

Provides helper functions for building and executing MongoDB aggregation
expressions and operators in test scenarios.
"""

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.lazy_payload import materialize


def build_nested_expr(value, operator, depth):
    """
    Build nested operator expression.

    Creates a nested structure where an operator is applied multiple times.
    For example, with operator="abs" and depth=2, creates: {$abs: {$abs: value}}

    Args:
        value: The innermost value to wrap
        operator: The operator name (without $ prefix)
        depth: Number of times to nest the operator

    Returns:
        dict: Nested operator expression

    Example:
        >>> build_nested_expr(5, "abs", 2)
        {'$abs': {'$abs': 5}}
    """
    expr = value
    for _ in range(depth):
        expr = {f"${operator}": expr}
    return expr


def execute_project(collection, project):
    """
    Execute a projection with literal input values.

    Evaluates the projection against a single empty document. The document is
    inserted into the collection and the pipeline runs over that collection,
    rather than synthesizing the row with a ``$documents`` stage. This keeps the
    helper free of any dependency on ``$documents`` support while producing the
    same single-row input the projection sees.

    Note: the inserted document carries an auto-generated ``_id``, so the input
    row is ``{_id: <ObjectId>}`` rather than the field-less row ``$documents:
    [{}]`` produces. Literal expressions and references to any other (missing)
    field behave identically, and the output projection excludes ``_id``; but an
    expression that reads ``$_id``, ``$$ROOT``, or ``$$CURRENT`` sees that id and
    will diverge. Callers that need a truly field-less input (e.g. ``$$ROOT`` must
    be ``{}``) or exactly one row over a pre-populated collection must shape their
    own pipeline instead of using this helper.

    Args:
        collection: MongoDB collection object
        project: Fields to project. Do not include _id; the function always
            excludes it to keep test assertions free of auto-generated values.

    Returns:
        Result from execute_command

    Example:
        >>> execute_project(collection, {"sum": {"$add": [1, 2]}})
        # Returns result with {"sum": 3} in firstBatch
    """
    collection.insert_one({})
    return execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {**materialize(project), "_id": 0}},
            ],
            "cursor": {},
        },
    )


def execute_project_with_insert(collection, document, project):
    """
    Execute a projection with values from an inserted document.

    Args:
        collection: MongoDB collection object
        document: Document to insert
        project: Fields to project. Do not include _id; the function always
            excludes it to keep test assertions free of auto-generated values.

    Returns:
        Result from execute_command

    Example:
        >>> execute_project_with_insert(
        ...     collection,
        ...     {"a": 10, "b": 3},
        ...     {"quotient": {"$divide": ["$a", "$b"]}}
        ... )
        # Returns result with {"quotient": 3.33...} in firstBatch
    """
    collection.insert_one(materialize(document) or {})
    return execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {**materialize(project), "_id": 0}},
            ],
            "cursor": {},
        },
    )


def execute_expression(collection, expression):
    """
    Execute an aggregation expression against a single empty document.

    Evaluates an expression against an empty document. The document is inserted
    into the collection and the pipeline runs over that collection, rather than
    synthesizing the row with a ``$documents`` stage. This keeps the helper free
    of any dependency on ``$documents`` support while producing the same
    single-row input the expression is evaluated against. Useful for testing
    expressions with literal values; references to fields other than ``_id``
    resolve to missing, just as they would against a ``$documents: [{}]`` row.

    Note: the inserted document carries an auto-generated ``_id``, so the input
    row is ``{_id: <ObjectId>}`` rather than the field-less row ``$documents:
    [{}]`` produces. Literal expressions and references to any other (missing)
    field are unaffected, and the output projection excludes ``_id``; but an
    expression that reads ``$_id``, ``$$ROOT``, or ``$$CURRENT`` sees that id and
    will diverge. Callers that need a truly field-less input (e.g. ``$$ROOT`` must
    be ``{}``) or exactly one row over a pre-populated collection must shape their
    own pipeline instead of using this helper.

    Args:
        collection: MongoDB collection object
        expression: The expression to evaluate (e.g., {"$add": [1, 2]})

    Returns:
        Result from execute_command with structure:
        {"cursor": {"firstBatch": [{"result": <value>}]}}

    Example:
        >>> execute_expression(collection, {"$add": [1, 2]})
        # Returns result with {"result": 3} in firstBatch
    """
    collection.insert_one({})
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


def execute_expression_with_insert(collection, expression, document):
    """
    Execute an aggregation expression with values from an inserted document.

    Inserts a document into the collection, then evaluates the expression
    via $project. Useful for testing expressions with field references.

    Args:
        collection: MongoDB collection object
        expression: The expression to evaluate (e.g., {"$divide": ["$a", "$b"]})
        document: Document to insert (e.g., {"a": 10, "b": 2})

    Returns:
        Result from execute_command with structure:
        {"cursor": {"firstBatch": [{"result": <value>}]}}
    """
    collection.insert_one(materialize(document) or {})
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


def assert_expression_result(result, expected=None, error_code=None, msg=None, ignore_order=False):
    """
    Assert the result of an execute_expression* call.

    Wraps assertResult to handle the {"result": value} projection shape
    produced by execute_expression and execute_expression_with_insert.

    Args:
        result: Result from execute_expression or execute_expression_with_insert
        expected: Expected scalar value (wrapped into [{"result": expected}])
        error_code: Expected error code (for error cases)
        msg: Custom assertion message (optional)
        ignore_order: If True, sort list results before comparison
    """
    assertResult(
        result,
        expected=[{"result": expected}] if error_code is None else None,
        error_code=error_code,
        msg=msg,
        ignore_order_in=["result"] if ignore_order else None,
    )
