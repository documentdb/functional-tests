"""
Utility functions for functional tests.

Provides helper functions for building and executing MongoDB aggregation
expressions and operators in test scenarios.
"""

from documentdb_tests.framework.executor import execute_command


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
    return execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {"$project": {**project, "_id": 0}},
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
    collection.insert_one(document)
    return execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {**project, "_id": 0}},
            ],
            "cursor": {},
        },
    )


def execute_expression(collection, expression):
    """
    Execute an aggregation expression using $documents stage.

    Evaluates an expression against an empty document using the $documents
    stage. Useful for testing expressions with literal values.

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
    return execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
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
    collection.insert_one(document)
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
