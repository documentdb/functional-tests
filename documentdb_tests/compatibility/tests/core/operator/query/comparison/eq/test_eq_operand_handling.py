"""
Tests for $eq operand handling.

Covers $eq treating its operand as a literal BSON value (never an operator
expression or field reference), $eq rejected as a top-level operator, and
equivalence of the explicit {$eq: v} and implicit {a: v} query forms.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

LITERAL_OPERAND_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="dollar_prefixed_string_is_literal",
        filter={"a": {"$eq": "$other"}},
        doc=[{"_id": 1, "a": "$other"}, {"_id": 2, "a": "literal"}],
        expected=[{"_id": 1, "a": "$other"}],
        msg="$eq with a $-prefixed string matches the literal string, not a field reference",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_OPERAND_TESTS))
def test_eq_literal_operand(collection, test):
    """Parametrized test for $eq literal-operand safety."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


def test_eq_at_query_root_errors(collection):
    """Test $eq as a top-level operator (no field) fails with BAD_VALUE."""
    collection.insert_many([{"_id": 1, "a": 1}])
    result = execute_command(collection, {"find": collection.name, "filter": {"$eq": 5}})
    assertFailureCode(
        result,
        BAD_VALUE_ERROR,
        msg="$eq at query root is an unknown top-level operator",
    )


# (id, docs, value, expected) — the explicit {a: {$eq: value}} and implicit
# {a: value} forms must both return `expected` for any non-regex value. Each form
# is asserted independently (one assertion per test) against the same expected set,
# which establishes that the two forms are equivalent.
IMPLICIT_EQUIVALENCE_CASES = [
    ("scalar_int", [{"_id": 1, "a": 1}, {"_id": 2, "a": 2}], 1, [{"_id": 1, "a": 1}]),
    ("string", [{"_id": 1, "a": "x"}, {"_id": 2, "a": "y"}], "x", [{"_id": 1, "a": "x"}]),
    ("bool", [{"_id": 1, "a": True}, {"_id": 2, "a": False}], True, [{"_id": 1, "a": True}]),
    (
        "null_and_missing",
        [{"_id": 1, "a": None}, {"_id": 2}, {"_id": 3, "a": 1}],
        None,
        [{"_id": 1, "a": None}, {"_id": 2}],
    ),
    (
        "array_exact",
        [{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [1, 2, 3]}],
        [1, 2],
        [{"_id": 1, "a": [1, 2]}],
    ),
    (
        "embedded_document",
        [{"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}],
        {"b": 1},
        [{"_id": 1, "a": {"b": 1}}],
    ),
]


def _equivalence_params():
    params = []
    for case_id, docs, value, expected in IMPLICIT_EQUIVALENCE_CASES:
        params.append(pytest.param({"a": {"$eq": value}}, docs, expected, id=f"{case_id}_explicit"))
        params.append(pytest.param({"a": value}, docs, expected, id=f"{case_id}_implicit"))
    return params


@pytest.mark.parametrize("filter, docs, expected", _equivalence_params())
def test_eq_implicit_form_equivalence(collection, filter, docs, expected):
    """Explicit {a: {$eq: v}} and implicit {a: v} forms return the same result set."""
    collection.insert_many(docs)
    result = execute_command(collection, {"find": collection.name, "filter": filter})
    assertSuccess(
        result,
        expected,
        ignore_doc_order=True,
        msg="explicit $eq and implicit-equality forms must return identical results",
    )
