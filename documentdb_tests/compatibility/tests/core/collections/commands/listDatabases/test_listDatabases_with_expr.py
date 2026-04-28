"""
Tests for $expr in listDatabases command contexts.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_admin_command


def test_expr_in_list_databases(collection):
    """Test $expr in listDatabases filter."""
    collection.insert_one({"_id": 1})
    db_name = collection.database.name
    result = execute_admin_command(
        collection,
        {
            "listDatabases": 1,
            "filter": {"$expr": {"$eq": ["$name", db_name]}},
        },
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: db_name in [d["name"] for d in r.get("databases", [])],
    )
