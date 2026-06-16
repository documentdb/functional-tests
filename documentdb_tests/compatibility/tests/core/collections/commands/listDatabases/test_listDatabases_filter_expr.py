"""Tests for listDatabases filter $expr expression support."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Eq, Len

# Property [Filter $expr Expression Support]: $expr in the filter
# supports aggregation expression operators with one representative
# per category: comparison, arithmetic, string, array, set,
# conditional, type, conversion, date, variable, and miscellaneous.
FILTER_EXPR_SUPPORT_TESTS: list[CommandTestCase] = [
    # Comparison.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$eq": ["$name", "admin"]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $eq should match by name",
        id="expr_eq",
    ),
    # Arithmetic.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$gt": [{"$add": ["$sizeOnDisk", 1]}, 0]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $add should compute sum on sizeOnDisk",
        id="expr_add",
    ),
    # String.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$eq": [{"$concat": ["$name", "_x"]}, "admin_x"]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $concat should build and compare strings",
        id="expr_concat",
    ),
    # Regex.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$regexMatch": {"input": "$name", "regex": "^ad"}}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $regexMatch should match patterns",
        id="expr_regex_match",
    ),
    # Array.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$eq": [{"$size": {"$range": [0, 5]}}, 5]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $size and $range should work on arrays",
        id="expr_array",
    ),
    # Set.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$setEquals": [[1, 2], [2, 1]]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $setEquals should compare sets",
        id="expr_set_equals",
    ),
    # Conditional.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$cond": [{"$eq": ["$name", "admin"]}, True, False]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $cond should evaluate conditional branches",
        id="expr_cond",
    ),
    # Type.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$eq": [{"$type": "$name"}, "string"]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $type should return the BSON type name",
        id="expr_type",
    ),
    # Conversion.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$eq": [{"$toString": 1}, "1"]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $toString should convert to string",
        id="expr_to_string",
    ),
    # Date.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {
                "$expr": {"$gt": [{"$year": {"$toDate": "2024-01-15"}}, 0]},
            },
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $year should extract year from date",
        id="expr_year",
    ),
    # Variable.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$eq": ["$$CURRENT.name", "admin"]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$$CURRENT should reference the current document in $expr",
        id="expr_current",
    ),
    # $let.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {
                "$expr": {
                    "$let": {
                        "vars": {"target": "admin"},
                        "in": {"$eq": ["$name", "$$target"]},
                    }
                }
            },
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$let with user-defined variables should work in $expr",
        id="expr_let",
    ),
    # $literal.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$expr": {"$eq": [{"$literal": "$name"}, "$name"]}},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="$literal string should not equal the resolved field value",
        id="expr_literal_vs_field",
    ),
    # Miscellaneous.
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {
                "$expr": {
                    "$eq": [
                        {"$type": {"$mergeObjects": [{"a": 1}, {"b": 2}]}},
                        "object",
                    ],
                },
            },
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$expr with $mergeObjects should merge documents",
        id="expr_merge_objects",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(FILTER_EXPR_SUPPORT_TESTS))
def test_listDatabases_filter_expr(collection, test):
    """Test listDatabases filter $expr expression support."""
    ctx = CommandContext.from_collection(collection)
    collection.database.create_collection(collection.name)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
