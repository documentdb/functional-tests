"""Tests that $lookup concise syntax degrades to uncorrelated when the join fields are absent."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ALL_FOREIGN = [
    {"_id": 10, "ff": "a"},
    {"_id": 11, "ff": "b"},
    {"_id": 12, "ff": "c"},
]

# Property [Concise Degradation]: when localField and foreignField carry no
# usable field name, the equality constraint is dropped and every foreign
# document matches, so the pipeline runs uncorrelated against the whole
# foreign collection.
LOOKUP_CONCISE_DEGRADATION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "null_local_and_foreign_field_degrades_to_uncorrelated",
        foreign_docs=ALL_FOREIGN,
        docs=[{"_id": 1, "lf": "a"}, {"_id": 2, "lf": "b"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": None,
                    "foreignField": None,
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": "a", "joined": ALL_FOREIGN},
            {"_id": 2, "lf": "b", "joined": ALL_FOREIGN},
        ],
        msg="$lookup concise with null localField and foreignField should degrade "
        "to an uncorrelated subquery returning all foreign documents",
    ),
    LookupTestCase(
        "empty_string_local_and_foreign_field_degrades_to_uncorrelated",
        foreign_docs=ALL_FOREIGN,
        docs=[{"_id": 1, "lf": "a"}, {"_id": 2, "lf": "b"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "",
                    "foreignField": "",
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": "a", "joined": ALL_FOREIGN},
            {"_id": 2, "lf": "b", "joined": ALL_FOREIGN},
        ],
        msg="$lookup concise with empty string localField and foreignField should "
        "degrade to an uncorrelated subquery returning all foreign documents",
    ),
    LookupTestCase(
        "degraded_join_still_runs_pipeline_over_all_foreign",
        foreign_docs=[
            {"_id": 10, "val": 1},
            {"_id": 11, "val": 2},
            {"_id": 12, "val": 3},
        ],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": None,
                    "foreignField": None,
                    "pipeline": [{"$match": {"val": {"$gte": 2}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [{"_id": 11, "val": 2}, {"_id": 12, "val": 3}],
            }
        ],
        msg="$lookup concise with a dropped join constraint should still run the "
        "pipeline uncorrelated over every foreign document",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CONCISE_DEGRADATION_TESTS))
def test_lookup_concise_degradation(collection, test_case: LookupTestCase):
    """Test $lookup concise degradation to an uncorrelated subquery."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
