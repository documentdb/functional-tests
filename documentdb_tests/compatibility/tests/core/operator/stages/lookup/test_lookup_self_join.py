"""Tests for $lookup self-join behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    LookupTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SELF = object()

# Property [Self-Join]: a collection can join to itself when from
# equals the source collection name, and null/missing matching works
# the same as with a foreign collection.
LOOKUP_SELF_JOIN_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "self_join_matches_own_documents",
        docs=[
            {"_id": 1, "lf": "a", "ff": "b"},
            {"_id": 2, "lf": "b", "ff": "a"},
            {"_id": 3, "lf": "c", "ff": "c"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": SELF,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "ff": "b",
                "joined": [{"_id": 2, "lf": "b", "ff": "a"}],
            },
            {
                "_id": 2,
                "lf": "b",
                "ff": "a",
                "joined": [{"_id": 1, "lf": "a", "ff": "b"}],
            },
            {
                "_id": 3,
                "lf": "c",
                "ff": "c",
                "joined": [{"_id": 3, "lf": "c", "ff": "c"}],
            },
        ],
        msg=(
            "$lookup should allow a collection to join to itself"
            " when from equals the source collection name"
        ),
    ),
    LookupTestCase(
        "self_join_same_local_foreign_field",
        docs=[
            {"_id": 1, "val": "a"},
            {"_id": 2, "val": "b"},
            {"_id": 3, "val": "a"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": SELF,
                    "localField": "val",
                    "foreignField": "val",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "val": "a",
                "joined": [{"_id": 1, "val": "a"}, {"_id": 3, "val": "a"}],
            },
            {
                "_id": 2,
                "val": "b",
                "joined": [{"_id": 2, "val": "b"}],
            },
            {
                "_id": 3,
                "val": "a",
                "joined": [{"_id": 1, "val": "a"}, {"_id": 3, "val": "a"}],
            },
        ],
        msg=(
            "$lookup self-join with the same localField and foreignField"
            " should match each document to itself and others with the same value"
        ),
    ),
    LookupTestCase(
        "self_join_null_missing_match",
        docs=[
            {"_id": 1, "lf": None, "ff": "x"},
            {"_id": 2, "ff": None},
            {"_id": 3, "lf": "x"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": SELF,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": None,
                "ff": "x",
                "joined": [
                    {"_id": 2, "ff": None},
                    {"_id": 3, "lf": "x"},
                ],
            },
            {
                "_id": 2,
                "ff": None,
                "joined": [
                    {"_id": 2, "ff": None},
                    {"_id": 3, "lf": "x"},
                ],
            },
            {
                "_id": 3,
                "lf": "x",
                "joined": [{"_id": 1, "lf": None, "ff": "x"}],
            },
        ],
        msg=(
            "$lookup self-join should match null/missing documents"
            " the same as with a foreign collection"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_SELF_JOIN_TESTS))
def test_lookup_self_join(collection, test_case: LookupTestCase):
    """Test $lookup self-join behavior."""
    collection.database.create_collection(collection.name)
    collection.insert_many(test_case.docs)
    lookup_spec = dict(test_case.pipeline[0]["$lookup"])
    lookup_spec["from"] = collection.name
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$lookup": lookup_spec}],
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
    )
