"""
Tests for update command let variables.

Validates command-level let, statement-level c field, and variable
usage in query filters and pipeline updates.
"""

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import UPDATE_C_FIELD_REQUIRES_PIPELINE_ERROR
from documentdb_tests.framework.executor import execute_command


def test_update_let_variable_in_expr_query(collection):
    """Test command-level let variable accessed via $expr in query."""
    collection.insert_many([{"_id": 1, "x": 5}, {"_id": 2, "x": 10}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"$expr": {"$eq": ["$x", "$$target"]}},
                    "u": {"$set": {"found": True}},
                }
            ],
            "let": {"target": 5},
        },
    )
    assertSuccess(result, {"ok": 1.0, "n": 1, "nModified": 1}, raw_res=True)


def test_update_let_variable_in_pipeline(collection):
    """Test command-level let variable in pipeline update."""
    collection.insert_one({"_id": 1, "x": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": [{"$set": {"val": "$$myVar"}}],
                }
            ],
            "let": {"myVar": "hello"},
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "x": 1, "val": "hello"}])


def test_update_c_field_variables_in_pipeline(collection):
    """Test statement-level c field defines variables accessible in pipeline stages."""
    collection.insert_one({"_id": 1, "x": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": [{"$set": {"result": "$$localVar"}}],
                    "c": {"localVar": 42},
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "x": 1, "result": 42}])


def test_update_c_field_with_non_pipeline_u_errors(collection):
    """Test c field with non-pipeline u (operator doc) errors."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"x": 2}},
                    "c": {"myVar": 1},
                }
            ],
        },
    )
    assertFailureCode(result, UPDATE_C_FIELD_REQUIRES_PIPELINE_ERROR)


def test_update_let_empty_document_no_error(collection):
    """Test let with empty document {} does not error."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 2}}}],
            "let": {},
        },
    )
    assertSuccess(result, {"ok": 1.0, "n": 1, "nModified": 1}, raw_res=True)
