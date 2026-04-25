"""
Tests for $expr argument shapes and expression evaluation.

Covers valid argument forms (field references, comparison expressions,
deeply nested operators), system variables ($$ROOT, $$CURRENT, $$NOW, $literal),
computed result truthiness, and constant expression evaluation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="field_ref_truthy",
        doc=[{"_id": 1, "a": 5}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": 5}],
        msg="non-zero field value is truthy",
    ),
    QueryTestCase(
        id="field_ref_falsy",
        doc=[{"_id": 1, "a": 0}],
        filter={"$expr": "$a"},
        expected=[],
        msg="zero field value is falsy",
    ),
    QueryTestCase(
        id="field_ref_missing",
        doc=[{"_id": 1, "b": 1}],
        filter={"$expr": "$a"},
        expected=[],
        msg="missing field is falsy",
    ),
    QueryTestCase(
        id="comparison_two_fields",
        doc=[{"_id": 1, "a": 5, "b": 3}, {"_id": 2, "a": 1, "b": 3}],
        filter={"$expr": {"$gt": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": 5, "b": 3}],
        msg="$expr with comparison expression",
    ),
    QueryTestCase(
        id="deeply_nested_operators",
        doc=[{"_id": 1, "a": 4.5}, {"_id": 2, "a": 1.2}],
        filter={"$expr": {"$gt": [{"$add": [1, {"$abs": {"$ceil": "$a"}}]}, 5]}},
        expected=[{"_id": 1, "a": 4.5}],
        msg="$expr with deeply nested expression operators",
    ),
    QueryTestCase(
        id="system_var_root",
        doc=[{"_id": 1, "a": 1}],
        filter={"$expr": {"$eq": [{"$type": "$$ROOT"}, "object"]}},
        expected=[{"_id": 1, "a": 1}],
        msg="$expr with $$ROOT system variable",
    ),
    QueryTestCase(
        id="system_var_current",
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": -1}],
        filter={"$expr": {"$gt": ["$$CURRENT.a", 0]}},
        expected=[{"_id": 1, "a": 5}],
        msg="$expr with $$CURRENT system variable",
    ),
    QueryTestCase(
        id="system_var_now",
        doc=[{"_id": 1, "a": 1}],
        filter={"$expr": {"$eq": [{"$type": "$$NOW"}, "date"]}},
        expected=[{"_id": 1, "a": 1}],
        msg="$expr with $$NOW system variable returns a date",
    ),
    QueryTestCase(
        id="literal_dollar_string",
        doc=[{"_id": 1, "a": "$hello"}, {"_id": 2, "a": "world"}],
        filter={"$expr": {"$eq": [{"$literal": "$hello"}, "$a"]}},
        expected=[{"_id": 1, "a": "$hello"}],
        msg="$expr with $literal preserving dollar-prefixed string",
    ),
    QueryTestCase(
        id="computed_zero_falsy",
        doc=[{"_id": 1, "arr": [0]}],
        filter={"$expr": {"$arrayElemAt": ["$arr", 0]}},
        expected=[],
        msg="computed zero from $arrayElemAt is falsy",
    ),
    QueryTestCase(
        id="computed_missing_falsy",
        doc=[{"_id": 1, "arr": []}],
        filter={"$expr": {"$arrayElemAt": ["$arr", 0]}},
        expected=[],
        msg="$arrayElemAt on empty array returns missing (falsy)",
    ),
    QueryTestCase(
        id="constant_eq_true",
        doc=[{"_id": 1, "a": 1}],
        filter={"$expr": {"$eq": [1, 1]}},
        expected=[{"_id": 1, "a": 1}],
        msg="$expr evaluates constant expression — always true",
    ),
    QueryTestCase(
        id="constant_add_truthy",
        doc=[{"_id": 1, "a": 1}],
        filter={"$expr": {"$add": [1, 2]}},
        expected=[{"_id": 1, "a": 1}],
        msg="$expr truthiness on computed non-zero result",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_expr_argument_handling(collection, test):
    """Test $expr argument shapes and expression evaluation."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
