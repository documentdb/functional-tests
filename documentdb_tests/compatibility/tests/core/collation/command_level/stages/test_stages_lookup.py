"""Tests for collation interaction with $lookup stage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.collation.utils.collation_view_mismatch import (
    SECONDARY,
    ViewMismatchTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


@dataclass(frozen=True)
class LookupCollationTestCase(LookupTestCase):
    """Test case for $lookup with optional command-level collation."""

    command_collation: dict[str, Any] | None = None


# Property [Lookup Equality Join Collation]: collation affects join comparison
# in equality-based $lookup so that collation-equal strings match across
# localField and foreignField.
COLLATION_LOOKUP_EQUALITY_TESTS: list[LookupCollationTestCase] = [
    LookupCollationTestCase(
        "lookup_equality_strength1_case_insensitive",
        docs=[{"_id": 1, "product": "Apple"}, {"_id": 2, "product": "banana"}],
        foreign_docs=[{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Banana"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "product",
                    "foreignField": "name",
                    "as": "matched",
                }
            },
            {"$sort": {"_id": 1}},
        ],
        command_collation={"locale": "en", "strength": 1},
        expected=[
            {"_id": 1, "product": "Apple", "matched": [{"_id": 1, "name": "apple"}]},
            {"_id": 2, "product": "banana", "matched": [{"_id": 2, "name": "Banana"}]},
        ],
        msg="$lookup equality join with strength 1 should match case-insensitively",
    ),
    LookupCollationTestCase(
        "lookup_equality_no_collation_binary",
        docs=[{"_id": 1, "product": "Apple"}, {"_id": 2, "product": "banana"}],
        foreign_docs=[{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Banana"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "product",
                    "foreignField": "name",
                    "as": "matched",
                }
            },
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": 1, "product": "Apple", "matched": []},
            {"_id": 2, "product": "banana", "matched": []},
        ],
        msg="$lookup equality join without collation should use binary comparison",
    ),
]

# Property [Lookup Pipeline Collation Propagation]: collation propagates into
# the pipeline form of $lookup so that sub-pipeline expressions inherit
# command-level collation.
COLLATION_LOOKUP_PIPELINE_TESTS: list[LookupCollationTestCase] = [
    LookupCollationTestCase(
        "lookup_pipeline_strength1_case_insensitive",
        docs=[{"_id": 1, "product": "Apple"}, {"_id": 2, "product": "banana"}],
        foreign_docs=[{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Banana"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"prod": "$product"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$name", "$$prod"]}}},
                    ],
                    "as": "matched",
                }
            },
            {"$sort": {"_id": 1}},
        ],
        command_collation={"locale": "en", "strength": 1},
        expected=[
            {"_id": 1, "product": "Apple", "matched": [{"_id": 1, "name": "apple"}]},
            {"_id": 2, "product": "banana", "matched": [{"_id": 2, "name": "Banana"}]},
        ],
        msg="$lookup pipeline form with strength 1 should inherit collation",
    ),
    LookupCollationTestCase(
        "lookup_pipeline_no_collation_binary",
        docs=[{"_id": 1, "product": "Apple"}, {"_id": 2, "product": "banana"}],
        foreign_docs=[{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Banana"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"prod": "$product"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$name", "$$prod"]}}},
                    ],
                    "as": "matched",
                }
            },
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": 1, "product": "Apple", "matched": []},
            {"_id": 2, "product": "banana", "matched": []},
        ],
        msg="$lookup pipeline form without collation should use binary comparison",
    ),
]

COLLATION_LOOKUP_TESTS: list[LookupCollationTestCase] = (
    COLLATION_LOOKUP_EQUALITY_TESTS + COLLATION_LOOKUP_PIPELINE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(COLLATION_LOOKUP_TESTS))
def test_collation_aggregate_lookup(collection, test_case: LookupCollationTestCase):
    """Test collation affects $lookup join comparison."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        if test_case.command_collation is not None:
            command["collation"] = test_case.command_collation
        result = execute_command(collection, command)
        assertResult(result, expected=test_case.expected, msg=test_case.msg)


# Property [Lookup View Collation Mismatch]: $lookup from a collection or view
# to a view with mismatched collation produces OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
# while matching collation or lookup to a base collection succeeds.
COLLATION_LOOKUP_VIEW_TESTS: list[ViewMismatchTestCase] = [
    ViewMismatchTestCase(
        "lookup_collection_to_view_mismatched",
        docs=[{"_id": 1, "product": "Apple"}, {"_id": 2, "product": "banana"}],
        secondary_docs=[{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Banana"}],
        pipeline=[
            {
                "$lookup": {
                    "from": SECONDARY,
                    "localField": "product",
                    "foreignField": "name",
                    "as": "matched",
                }
            },
            {"$sort": {"_id": 1}},
        ],
        secondary_view_collation={"locale": "fr", "strength": 2},
        command_collation={"locale": "en", "strength": 1},
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$lookup from collection to view with mismatched collation should error",
    ),
    ViewMismatchTestCase(
        "lookup_view_to_view_different_collation",
        docs=[{"_id": 1, "product": "Apple"}, {"_id": 2, "product": "banana"}],
        secondary_docs=[{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Banana"}],
        pipeline=[
            {
                "$lookup": {
                    "from": SECONDARY,
                    "localField": "product",
                    "foreignField": "name",
                    "as": "matched",
                }
            },
            {"$sort": {"_id": 1}},
        ],
        secondary_view_collation={"locale": "fr", "strength": 2},
        source_view_collation={"locale": "en", "strength": 1},
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$lookup from view to view with different collation should error",
    ),
    ViewMismatchTestCase(
        "lookup_collection_to_view_matching",
        docs=[{"_id": 1, "product": "Apple"}, {"_id": 2, "product": "banana"}],
        secondary_docs=[{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Banana"}],
        pipeline=[
            {
                "$lookup": {
                    "from": SECONDARY,
                    "localField": "product",
                    "foreignField": "name",
                    "as": "matched",
                }
            },
            {"$sort": {"_id": 1}},
        ],
        secondary_view_collation={"locale": "en", "strength": 1},
        command_collation={"locale": "en", "strength": 1},
        expected=[
            {"_id": 1, "product": "Apple", "matched": [{"_id": 1, "name": "apple"}]},
            {"_id": 2, "product": "banana", "matched": [{"_id": 2, "name": "Banana"}]},
        ],
        msg="$lookup from collection to view with matching collation should succeed",
    ),
    ViewMismatchTestCase(
        "lookup_view_to_base_collection",
        docs=[{"_id": 1, "product": "Apple"}, {"_id": 2, "product": "banana"}],
        secondary_docs=[{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Banana"}],
        pipeline=[
            {
                "$lookup": {
                    "from": SECONDARY,
                    "localField": "product",
                    "foreignField": "name",
                    "as": "matched",
                }
            },
            {"$sort": {"_id": 1}},
        ],
        source_view_collation={"locale": "en", "strength": 1},
        expected=[
            {"_id": 1, "product": "Apple", "matched": [{"_id": 1, "name": "apple"}]},
            {"_id": 2, "product": "banana", "matched": [{"_id": 2, "name": "Banana"}]},
        ],
        msg="$lookup from view to base collection should succeed",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(COLLATION_LOOKUP_VIEW_TESTS))
def test_collation_aggregate_lookup_view(database_client, collection, test_case):
    """Test $lookup collation mismatch behavior with views."""
    collection = test_case.prepare(database_client, collection)
    result = execute_command(collection, test_case.build_command(collection))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
