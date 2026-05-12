"""Tests for $indexStats pipeline position requirements."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [First Stage]: $indexStats succeeds when it is the first stage
# in a pipeline.
FIRST_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="first_stage_succeeds",
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": "_id_"}},
            {"$project": {"_id": 0, "name": 1}},
        ],
        expected=[{"name": "_id_"}],
        msg="$indexStats as the first stage should succeed",
    ),
    StageTestCase(
        id="all_indexes_returned",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", -1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$project": {"_id": 0, "name": 1, "key": 1}},
            {"$sort": {"name": 1}},
        ],
        expected=[
            {"name": "_id_", "key": {"_id": 1}},
            {"name": "a_1", "key": {"a": 1}},
            {"name": "b_-1", "key": {"b": -1}},
        ],
        msg="All indexes should be returned with correct names and keys",
    ),
]

# Property [Not First Position]: $indexStats must be the first stage in a
# pipeline.
NOT_FIRST_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="after_match",
        docs=[],
        pipeline=[{"$match": {}}, {"$indexStats": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$indexStats after $match should fail",
    ),
    StageTestCase(
        id="after_project",
        docs=[],
        pipeline=[{"$project": {"a": 1}}, {"$indexStats": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$indexStats after $project should fail",
    ),
    StageTestCase(
        id="after_add_fields",
        docs=[],
        pipeline=[{"$addFields": {"a": 1}}, {"$indexStats": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$indexStats after $addFields should fail",
    ),
    StageTestCase(
        id="after_limit",
        docs=[],
        pipeline=[{"$limit": 1}, {"$indexStats": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$indexStats after $limit should fail",
    ),
    StageTestCase(
        id="after_unwind",
        docs=[],
        pipeline=[{"$unwind": "$a"}, {"$indexStats": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$indexStats after $unwind should fail",
    ),
    StageTestCase(
        id="two_index_stats",
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$indexStats": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="Second $indexStats in same pipeline should fail",
    ),
    StageTestCase(
        id="coll_stats_then_index_stats",
        docs=[],
        pipeline=[{"$collStats": {"count": {}}}, {"$indexStats": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$indexStats after $collStats should fail",
    ),
    StageTestCase(
        id="index_stats_then_coll_stats",
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$collStats": {"count": {}}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$collStats after $indexStats should fail",
    ),
]

# Property [Facet Restriction]: $indexStats is not allowed inside $facet.
FACET_RESTRICTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="inside_facet",
        docs=[],
        pipeline=[{"$facet": {"a": [{"$indexStats": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$indexStats inside $facet should be disallowed",
    ),
]

# Property [Match Filtering]: $match after $indexStats filters index
# documents by field values.
MATCH_FILTERING_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="match_by_name",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", -1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": "a_1"}},
            {"$project": {"_id": 0, "name": 1}},
        ],
        expected=[{"name": "a_1"}],
        msg="$match should filter indexStats output by name",
    ),
    StageTestCase(
        id="match_by_key_field",
        indexes=[IndexModel([("x", 1)]), IndexModel([("y", -1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"key.y": -1}},
            {"$project": {"_id": 0, "name": 1}},
        ],
        expected=[{"name": "y_-1"}],
        msg="$match should filter by nested key field",
    ),
    StageTestCase(
        id="match_no_results",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": "nonexistent"}},
            {"$project": {"_id": 0, "name": 1}},
        ],
        expected=[],
        msg="$match with no matching index should return empty",
    ),
    StageTestCase(
        id="match_regex",
        indexes=[IndexModel([("field_one", 1)]), IndexModel([("field_two", -1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": {"$regex": "^field_"}}},
            {"$project": {"_id": 0, "name": 1}},
            {"$sort": {"name": 1}},
        ],
        expected=[{"name": "field_one_1"}, {"name": "field_two_-1"}],
        msg="$match with regex should filter index names by pattern",
    ),
]

# Property [Sort Ordering]: $sort after $indexStats orders index documents.
SORT_ORDERING_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="sort_by_name_ascending",
        indexes=[IndexModel([("c", 1)]), IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": {"$ne": "_id_"}}},
            {"$sort": {"name": 1}},
            {"$project": {"_id": 0, "name": 1}},
        ],
        expected=[{"name": "a_1"}, {"name": "b_1"}, {"name": "c_1"}],
        msg="$sort ascending should order indexes alphabetically",
    ),
    StageTestCase(
        id="sort_by_name_descending",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)]), IndexModel([("c", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": {"$ne": "_id_"}}},
            {"$sort": {"name": -1}},
            {"$project": {"_id": 0, "name": 1}},
        ],
        expected=[{"name": "c_1"}, {"name": "b_1"}, {"name": "a_1"}],
        msg="$sort descending should reverse order",
    ),
]

# Property [Project Reshaping]: $project after $indexStats reshapes output
# documents.
PROJECT_RESHAPING_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="project_inclusion",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": "a_1"}},
            {"$project": {"_id": 0, "name": 1, "key": 1}},
        ],
        expected=[{"name": "a_1", "key": {"a": 1}}],
        msg="$project inclusion should keep only specified fields",
    ),
    StageTestCase(
        id="project_exclusion",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": "a_1"}},
            {"$project": {"_id": 0, "host": 0, "accesses": 0, "spec": 0}},
        ],
        expected=[{"name": "a_1", "key": {"a": 1}}],
        msg="$project exclusion should remove specified fields",
    ),
    StageTestCase(
        id="project_computed_field",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": "a_1"}},
            {
                "$project": {
                    "_id": 0,
                    "indexName": "$name",
                    "numKeys": {"$size": {"$objectToArray": "$key"}},
                }
            },
        ],
        expected=[{"indexName": "a_1", "numKeys": 1}],
        msg="$project with expressions should compute new fields from indexStats output",
    ),
]

# Property [AddFields Augmentation]: $addFields after $indexStats adds
# computed fields to index documents.
ADD_FIELDS_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="add_fields_constant",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": "a_1"}},
            {"$addFields": {"isUserIndex": True}},
            {"$project": {"_id": 0, "name": 1, "isUserIndex": 1}},
        ],
        expected=[{"name": "a_1", "isUserIndex": True}],
        msg="$addFields should augment indexStats documents with constants",
    ),
    StageTestCase(
        id="add_fields_expression",
        indexes=[IndexModel([("a", 1), ("b", -1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": "a_1_b_-1"}},
            {"$addFields": {"keyCount": {"$size": {"$objectToArray": "$key"}}}},
            {"$project": {"_id": 0, "name": 1, "keyCount": 1}},
        ],
        expected=[{"name": "a_1_b_-1", "keyCount": 2}],
        msg="$addFields with expression should compute from indexStats fields",
    ),
]

# Property [Group Aggregation]: $group after $indexStats aggregates across
# index documents.
GROUP_AGGREGATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="group_count_all",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$group": {"_id": None, "count": {"$sum": 1}}},
            {"$project": {"_id": 0, "count": 1}},
        ],
        expected=[{"count": 3}],  # _id_ + a_1 + b_1
        msg="$group should count all indexes including _id",
    ),
    StageTestCase(
        id="group_collect_names",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$sort": {"name": 1}},
            {"$group": {"_id": None, "names": {"$push": "$name"}}},
            {"$project": {"_id": 0, "names": 1}},
        ],
        expected=[{"names": ["_id_", "a_1", "b_1"]}],
        msg="$group with $push should collect all index names",
    ),
]

# Property [Limit and Skip]: $limit and $skip after $indexStats control
# result pagination.
LIMIT_SKIP_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="limit_one",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$sort": {"name": 1}},
            {"$limit": 1},
            {"$project": {"_id": 0, "name": 1}},
        ],
        expected=[{"name": "_id_"}],
        msg="$limit should restrict number of index documents returned",
    ),
    StageTestCase(
        id="skip_one",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$sort": {"name": 1}},
            {"$skip": 1},
            {"$project": {"_id": 0, "name": 1}},
        ],
        expected=[{"name": "a_1"}, {"name": "b_1"}],
        msg="$skip should skip index documents",
    ),
    StageTestCase(
        id="skip_and_limit",
        indexes=[
            IndexModel([("a", 1)]),
            IndexModel([("b", 1)]),
            IndexModel([("c", 1)]),
        ],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$sort": {"name": 1}},
            {"$skip": 1},
            {"$limit": 2},
            {"$project": {"_id": 0, "name": 1}},
        ],
        expected=[{"name": "a_1"}, {"name": "b_1"}],
        msg="$skip then $limit should paginate index results",
    ),
]

# Property [Unwind on Key]: $unwind after $indexStats can expand compound
# key fields into separate documents.
UNWIND_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="unwind_key_array",
        indexes=[IndexModel([("a", 1), ("b", -1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": "a_1_b_-1"}},
            {"$project": {"_id": 0, "name": 1, "fields": {"$objectToArray": "$key"}}},
            {"$unwind": "$fields"},
            {"$project": {"name": 1, "fieldName": "$fields.k"}},
        ],
        expected=[
            {"name": "a_1_b_-1", "fieldName": "a"},
            {"name": "a_1_b_-1", "fieldName": "b"},
        ],
        msg="$unwind should expand key fields into separate documents",
    ),
]

# Property [ReplaceRoot]: $replaceRoot after $indexStats can promote
# nested fields to top level.
REPLACE_ROOT_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="replace_root_with_spec",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": "a_1"}},
            {"$replaceRoot": {"newRoot": "$spec"}},
            {"$project": {"_id": 0, "key": 1, "name": 1}},
        ],
        expected=[{"key": {"a": 1}, "name": "a_1"}],
        msg="$replaceRoot should promote spec subdocument to top level",
    ),
]

# Property [Count]: $count after $indexStats counts index documents.
COUNT_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="count_all_indexes",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$count": "totalIndexes"},
        ],
        expected=[{"totalIndexes": 3}],  # _id_ + a_1 + b_1
        msg="$count should return total number of indexes",
    ),
    StageTestCase(
        id="count_after_match",
        indexes=[
            IndexModel([("x", 1)]),
            IndexModel([("y", 1)]),
            IndexModel([("z", 1)]),
        ],
        docs=[],
        pipeline=[
            {"$indexStats": {}},
            {"$match": {"name": {"$ne": "_id_"}}},
            {"$count": "userIndexes"},
        ],
        expected=[{"userIndexes": 3}],
        msg="$count after $match should count only matched indexes",
    ),
]

ALL_POSITION_TESTS = (
    FIRST_STAGE_TESTS
    + NOT_FIRST_POSITION_TESTS
    + FACET_RESTRICTION_TESTS
    + MATCH_FILTERING_TESTS
    + SORT_ORDERING_TESTS
    + PROJECT_RESHAPING_TESTS
    + ADD_FIELDS_TESTS
    + GROUP_AGGREGATION_TESTS
    + LIMIT_SKIP_TESTS
    + UNWIND_TESTS
    + REPLACE_ROOT_TESTS
    + COUNT_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(ALL_POSITION_TESTS))
def test_indexStats_position(collection: Collection, test_case: StageTestCase):
    """Test $indexStats pipeline position requirements."""
    coll = populate_collection(collection, test_case)
    result = execute_command(
        coll,
        {
            "aggregate": coll.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
