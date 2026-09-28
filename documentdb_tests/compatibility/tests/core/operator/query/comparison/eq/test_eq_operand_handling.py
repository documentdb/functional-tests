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

# Property [Implicit Form Equivalence]: for any non-regex operand, the explicit
# {a: {$eq: v}} and implicit {a: v} query forms return identical results. Each
# base case has an "_explicit" and "_implicit" QueryTestCase variant.
IMPLICIT_EQUIVALENCE_CASES: list[QueryTestCase] = [
    QueryTestCase(
        id="scalar_int_explicit",
        filter={"a": {"$eq": 1}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 1, "a": 1}],
        msg="explicit $eq matches an equal int",
    ),
    QueryTestCase(
        id="scalar_int_implicit",
        filter={"a": 1},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 1, "a": 1}],
        msg="implicit equality matches an equal int",
    ),
    QueryTestCase(
        id="string_explicit",
        filter={"a": {"$eq": "x"}},
        doc=[{"_id": 1, "a": "x"}, {"_id": 2, "a": "y"}],
        expected=[{"_id": 1, "a": "x"}],
        msg="explicit $eq matches an equal string",
    ),
    QueryTestCase(
        id="string_implicit",
        filter={"a": "x"},
        doc=[{"_id": 1, "a": "x"}, {"_id": 2, "a": "y"}],
        expected=[{"_id": 1, "a": "x"}],
        msg="implicit equality matches an equal string",
    ),
    QueryTestCase(
        id="bool_explicit",
        filter={"a": {"$eq": True}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": False}],
        expected=[{"_id": 1, "a": True}],
        msg="explicit $eq matches an equal bool",
    ),
    QueryTestCase(
        id="bool_implicit",
        filter={"a": True},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": False}],
        expected=[{"_id": 1, "a": True}],
        msg="implicit equality matches an equal bool",
    ),
    QueryTestCase(
        id="null_and_missing_explicit",
        filter={"a": {"$eq": None}},
        doc=[{"_id": 1, "a": None}, {"_id": 2}, {"_id": 3, "a": 1}],
        expected=[{"_id": 1, "a": None}, {"_id": 2}],
        msg="explicit $eq matches both null and missing",
    ),
    QueryTestCase(
        id="null_and_missing_implicit",
        filter={"a": None},
        doc=[{"_id": 1, "a": None}, {"_id": 2}, {"_id": 3, "a": 1}],
        expected=[{"_id": 1, "a": None}, {"_id": 2}],
        msg="implicit equality matches both null and missing",
    ),
    QueryTestCase(
        id="array_exact_explicit",
        filter={"a": {"$eq": [1, 2]}},
        doc=[{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="explicit $eq matches an exact array",
    ),
    QueryTestCase(
        id="array_exact_implicit",
        filter={"a": [1, 2]},
        doc=[{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="implicit equality matches an exact array",
    ),
    QueryTestCase(
        id="embedded_document_explicit",
        filter={"a": {"$eq": {"b": 1}}},
        doc=[{"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}],
        expected=[{"_id": 1, "a": {"b": 1}}],
        msg="explicit $eq matches an exact embedded document",
    ),
    QueryTestCase(
        id="embedded_document_implicit",
        filter={"a": {"b": 1}},
        doc=[{"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}],
        expected=[{"_id": 1, "a": {"b": 1}}],
        msg="implicit equality matches an exact embedded document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(IMPLICIT_EQUIVALENCE_CASES))
def test_eq_implicit_form_equivalence(collection, test):
    """Explicit {a: {$eq: v}} and implicit {a: v} forms return the same result set."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


# Property [Literal Operand]: $eq treats its operand as a literal BSON value —
# a $-prefixed string is matched literally, never resolved as a field reference.
def test_eq_literal_operand(collection):
    """$eq with a $-prefixed string matches the literal string, not a field reference."""
    collection.insert_many([{"_id": 1, "a": "$other"}, {"_id": 2, "a": "literal"}])
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": {"$eq": "$other"}}}
    )
    assertSuccess(
        result,
        [{"_id": 1, "a": "$other"}],
        msg="$eq with a $-prefixed string matches the literal string, not a field reference",
        ignore_doc_order=True,
    )


# Property [Root Operator Rejection]: $eq is not a top-level query operator and
# is rejected with BAD_VALUE when used without a field.
def test_eq_at_query_root_errors(collection):
    """Test $eq as a top-level operator (no field) fails with BAD_VALUE."""
    collection.insert_many([{"_id": 1, "a": 1}])
    result = execute_command(collection, {"find": collection.name, "filter": {"$eq": 5}})
    assertFailureCode(
        result,
        BAD_VALUE_ERROR,
        msg="$eq at query root is an unknown top-level operator",
    )
