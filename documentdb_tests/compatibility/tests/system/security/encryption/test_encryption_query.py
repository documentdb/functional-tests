"""Tests for query and aggregation behavior against Queryable Encryption collections.

Verifies that a raw filter against an encrypted path, including a shape a real
client would never send such as a range comparison on an equality-only field, is
evaluated as an ordinary filter and never raises an encryption-specific error.
This repo has no client-side FLE driver, so query rewriting never happens.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.requires(queryable_encryption=True)


@pytest.fixture()
def qe_collection_seeded(qe_collection):
    """A qe_collection populated with two documents that both omit the encrypted field."""
    qe_collection.insert_many([{"_id": 1, "name": "a"}, {"_id": 2, "name": "b"}])
    return qe_collection


@pytest.mark.find
def test_encryption_find_equality_filter_returns_empty(qe_collection_seeded):
    """Test an equality filter on an encrypted field returns no matches, not an error."""
    result = execute_command(
        qe_collection_seeded, {"find": qe_collection_seeded.name, "filter": {"ssn": "123-45-6789"}}
    )
    assertResult(
        result,
        expected=[],
        msg="an equality filter on an encrypted field should return no matches"
        " when no document has that field set.",
    )


@pytest.mark.find
def test_encryption_find_range_operator_on_equality_field_no_error(qe_collection_seeded):
    """Test a range operator on an equality-only encrypted field executes without error."""
    result = execute_command(
        qe_collection_seeded, {"find": qe_collection_seeded.name, "filter": {"ssn": {"$gt": "a"}}}
    )
    assertResult(
        result,
        expected=[],
        msg="a range filter on an equality-only encrypted field should execute as an"
        " ordinary filter rather than raise a query-type error, since raw commands"
        " bypass client-side query rewriting.",
    )


@pytest.mark.find
def test_encryption_find_exists_false_matches_absent_field(qe_collection_seeded):
    """Test $exists:false on an encrypted field matches documents where it is absent."""
    result = execute_command(
        qe_collection_seeded,
        {
            "find": qe_collection_seeded.name,
            "filter": {"ssn": {"$exists": False}},
            "sort": {"_id": 1},
        },
    )
    assertResult(
        result,
        expected=[{"_id": 1, "name": "a"}, {"_id": 2, "name": "b"}],
        msg="$exists:false on an encrypted field should match documents where the field is absent.",
    )


@pytest.mark.aggregate
def test_encryption_aggregate_match_expr_on_encrypted_field(qe_collection_seeded):
    """Test $match+$expr referencing an encrypted field in aggregation."""
    result = execute_command(
        qe_collection_seeded,
        {
            "aggregate": qe_collection_seeded.name,
            "pipeline": [
                {"$match": {"$expr": {"$eq": [{"$type": "$ssn"}, "missing"]}}},
                {"$project": {"_id": 1}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=[{"_id": 1}, {"_id": 2}],
        msg="$match+$expr referencing an encrypted field should evaluate normally in aggregation.",
    )
