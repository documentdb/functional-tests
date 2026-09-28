"""$$NOW write paths: update pipelines, findAndModify, $merge pipelines, document validators."""

import time
from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import DOCUMENT_VALIDATION_FAILURE_ERROR
from documentdb_tests.framework.executor import execute_command

# The whenMatched pipeline reads its own $$NOW, so it can land a few milliseconds after the
# outer pipeline's value. The bound is deliberately close to the observed sub-millisecond drift:
# a wide bound would pass even if the inner pipeline read a stale or unrelated timestamp, which
# is the regression these tests exist to catch. Widen only if real load produces failures here.
DRIFT_BOUND_MS = 500

# Secondary collection names are derived from the test's own (already-unique) collection name
# rather than hardcoded, so they stay collision-free per test/worker even if a future test in
# this file needs its own distinct merge/out/validated collection.
MERGE_TARGET_SUFFIX = "_now_merge_target"
OUT_TARGET_SUFFIX = "_now_out_target"
VALIDATED_COLLECTION_SUFFIX = "_now_validated"


@pytest.mark.update
def test_now_in_update_pipeline_with_command_let(collection):
    """Test an update pipeline sets $$NOW as a date alongside a command-level let variable."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {},
                    "u": [{"$addFields": {"t": "$$NOW", "v": "$$userVar"}}],
                    "multi": True,
                }
            ],
            "let": {"userVar": 5},
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "allDatesAndLetValues": {
                            "$min": {
                                "$and": [
                                    {"$eq": [{"$type": "$t"}, "date"]},
                                    {"$eq": ["$v", 5]},
                                ]
                            }
                        },
                    }
                },
                {"$project": {"_id": 0, "allDatesAndLetValues": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"allDatesAndLetValues": True}],
        msg="An update pipeline should set $$NOW as a date alongside a command-level let value",
    )


@pytest.mark.update
def test_now_in_update_pipeline_constant_across_documents(collection):
    """Test an update pipeline writes the same $$NOW value to every matched document."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": [{"$addFields": {"t": "$$NOW"}}], "multi": True}],
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": "$t"}}, {"$count": "groups"}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"groups": 1}],
        msg="$$NOW in an update pipeline should be identical for all updated documents",
    )


@pytest.mark.update
def test_now_in_update_query_expr(collection):
    """Test $$NOW in an update's query filter matches only the qualifying documents."""
    collection.insert_many(
        [{"_id": 1, "d": datetime(2000, 1, 1)}, {"_id": 2, "d": datetime(2100, 1, 1)}]
    )
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"$expr": {"$lt": ["$d", "$$NOW"]}},
                    "u": [{"$addFields": {"t": "$$NOW"}}],
                    "multi": True,
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1},
        msg="$$NOW in an update query should match only documents dated before now",
    )


@pytest.mark.update
def test_now_constant_across_bulk_updates(collection):
    """Test $$NOW stays constant across every statement in a single update command."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": {"$lte": 2}},
                    "u": [{"$addFields": {"t": "$$NOW"}}],
                    "multi": True,
                },
                {
                    "q": {"_id": {"$gt": 2}},
                    "u": [{"$addFields": {"t": "$$NOW"}}],
                    "multi": True,
                },
            ],
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": "$t"}}, {"$count": "groups"}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"groups": 1}],
        msg="$$NOW should be constant across every update in one bulk operation",
    )


@pytest.mark.update
def test_now_update_explain_succeeds(collection):
    """Test explain of an update whose pipeline references $$NOW succeeds."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "explain": {
                "update": collection.name,
                "updates": [{"q": {}, "u": [{"$addFields": {"t": "$$NOW"}}]}],
            },
            "verbosity": "queryPlanner",
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="explain of an update referencing $$NOW should succeed",
    )


@pytest.mark.update
def test_now_update_explain_performs_no_write(collection):
    """Test explain of a $$NOW update leaves the documents unmodified."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "explain": {
                "update": collection.name,
                "updates": [{"q": {}, "u": [{"$addFields": {"t": "$$NOW"}}]}],
            },
            "verbosity": "queryPlanner",
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"t": {"$exists": True}}}
    )
    assertSuccess(result, [], msg="explain of a $$NOW update should not write the field")


@pytest.fixture
def merged_target(collection):
    """Merge into a target collection twice and yield its name, capturing both the outer
    pipeline's $$NOW and the whenMatched pipeline's own $$NOW on every merged document."""
    target = collection.name + MERGE_TARGET_SUFFIX
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    merge_pipeline = [
        {"$addFields": {"t": "$$NOW"}},
        {
            "$merge": {
                "into": target,
                "let": {"outer": "$t"},
                "whenMatched": [{"$addFields": {"outerNow": "$$outer", "innerNow": "$$NOW"}}],
                "whenNotMatched": "insert",
            }
        },
    ]
    for _ in range(2):
        execute_command(
            collection,
            {"aggregate": collection.name, "pipeline": merge_pipeline, "cursor": {}},
        )
    yield target


@pytest.mark.update
def test_now_in_find_and_modify_update(collection):
    """Test a findAndModify update pipeline stores a date when setting a field to $$NOW."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": [{"$addFields": {"t": "$$NOW"}}],
            "new": True,
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "type": {"$type": "$t"}}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"type": "date"}],
        msg="A findAndModify update pipeline should store $$NOW as a date",
    )


@pytest.mark.update
def test_now_in_find_and_modify_is_later_than_prior_update(collection):
    """Test findAndModify writes a $$NOW value later than an earlier update's value."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": [{"$addFields": {"earlier": "$$NOW"}}]}],
        },
    )
    time.sleep(0.05)
    execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": [{"$addFields": {"later": "$$NOW"}}],
            "new": True,
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "advanced": {"$gt": ["$later", "$earlier"]}}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"advanced": True}],
        msg="findAndModify should see a $$NOW later than a prior update's value",
    )


@pytest.mark.update
def test_now_in_find_and_modify_upsert(collection):
    """Test a findAndModify upsert can set the document key to $$NOW on insert."""
    execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"marker": 1},
            "update": [{"$addFields": {"_id": "$$NOW", "t": "$$NOW"}}],
            "upsert": True,
            "new": True,
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        "keyIsDate": {"$eq": [{"$type": "$_id"}, "date"]},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"keyIsDate": True}],
        msg="A findAndModify upsert should be able to set the document key to $$NOW",
    )


@pytest.mark.delete
def test_now_in_find_and_modify_remove_query(collection):
    """Test $$NOW in a findAndModify remove query deletes only qualifying documents."""
    collection.insert_many(
        [{"_id": 1, "d": datetime(2000, 1, 1)}, {"_id": 2, "d": datetime(2100, 1, 1)}]
    )
    execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"$expr": {"$lt": ["$d", "$$NOW"]}},
            "remove": True,
        },
    )
    result = execute_command(collection, {"find": collection.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 2}],
        msg="A findAndModify remove with a $$NOW query should delete only past documents",
    )


@pytest.mark.update
def test_now_find_and_modify_explain_succeeds(collection):
    """Test explain of a findAndModify referencing $$NOW succeeds."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "explain": {
                "findAndModify": collection.name,
                "query": {"_id": 1},
                "update": [{"$addFields": {"t": "$$NOW"}}],
            },
            "verbosity": "queryPlanner",
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="explain of a findAndModify referencing $$NOW should succeed",
    )


@pytest.mark.update
def test_now_find_and_modify_explain_performs_no_write(collection):
    """Test explain of a $$NOW findAndModify leaves the documents unmodified."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "explain": {
                "findAndModify": collection.name,
                "query": {"_id": 1},
                "update": [{"$addFields": {"t": "$$NOW"}}],
            },
            "verbosity": "queryPlanner",
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"t": {"$exists": True}}}
    )
    assertSuccess(result, [], msg="explain of a $$NOW findAndModify should not write the field")


@pytest.mark.aggregate
def test_now_in_merge_pipeline_constant_across_documents(collection):
    """Test $$NOW written through $merge is identical for every merged document."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    target = collection.name + MERGE_TARGET_SUFFIX
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"t": "$$NOW"}},
                {
                    "$merge": {
                        "into": target,
                        "whenMatched": "replace",
                        "whenNotMatched": "insert",
                    }
                },
            ],
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": target,
            "pipeline": [{"$group": {"_id": "$t"}}, {"$count": "groups"}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"groups": 1}],
        msg="$$NOW merged into a target collection should be one value for all documents",
    )


@pytest.mark.aggregate
def test_now_in_merge_when_matched_pipeline_is_not_earlier_than_outer(collection, merged_target):
    """Test $$NOW in a $merge whenMatched pipeline is not earlier than the outer value."""
    result = execute_command(
        collection,
        {
            "aggregate": merged_target,
            "pipeline": [
                {"$match": {"$expr": {"$gte": ["$innerNow", "$outerNow"]}}},
                {"$count": "ordered"},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"ordered": 3}],
        msg="$$NOW in a $merge whenMatched pipeline should not precede the outer value",
    )


@pytest.mark.aggregate
def test_now_in_merge_when_matched_pipeline_is_close_to_outer(collection, merged_target):
    """Test $$NOW in a $merge whenMatched pipeline stays close to the outer value.

    The whenMatched pipeline reads its own $$NOW, so strict equality would race; a bounded
    lag is the real invariant.
    """
    result = execute_command(
        collection,
        {
            "aggregate": merged_target,
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$lt": [{"$subtract": ["$innerNow", "$outerNow"]}, DRIFT_BOUND_MS]
                        }
                    }
                },
                {"$count": "close"},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"close": 3}],
        msg="$$NOW in a $merge whenMatched pipeline should closely follow the outer value",
    )


@pytest.mark.aggregate
def test_now_in_merge_when_matched_pipeline_returns_date(collection, merged_target):
    """Test the whenMatched pipeline's $$NOW is a date on every merged document."""
    result = execute_command(
        collection,
        {
            "aggregate": merged_target,
            "pipeline": [
                {"$group": {"_id": None, "types": {"$addToSet": {"$type": "$innerNow"}}}},
                {"$project": {"_id": 0, "types": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"types": ["date"]}],
        msg="A $merge whenMatched pipeline should resolve $$NOW to a date",
    )


@pytest.mark.aggregate
def test_now_in_merge_when_matched_pipeline_spread_is_bounded(collection, merged_target):
    """Test the whenMatched pipeline's $$NOW values are closely clustered.

    Each merged document re-evaluates $$NOW independently, so only a bounded spread is
    guaranteed, not a single distinct value.
    """
    result = execute_command(
        collection,
        {
            "aggregate": merged_target,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "first": {"$min": "$innerNow"},
                        "last": {"$max": "$innerNow"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "bounded": {"$lt": [{"$subtract": ["$last", "$first"]}, DRIFT_BOUND_MS]},
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"bounded": True}],
        msg="A $merge whenMatched pipeline's $$NOW values should be closely clustered",
    )


@pytest.mark.aggregate
def test_now_written_through_out_is_constant_across_documents(collection):
    """Test $$NOW written through $out is identical for every document in the target."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    target = collection.name + OUT_TARGET_SUFFIX
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$addFields": {"t": "$$NOW"}}, {"$out": target}],
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": target,
            "pipeline": [{"$group": {"_id": "$t"}}, {"$count": "groups"}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"groups": 1}],
        msg="$$NOW written through $out should be one value for all documents",
    )


@pytest.mark.validation
def test_now_validator_accepts_past_date(collection):
    """Test a validator comparing a stored date against $$NOW accepts a past date."""
    validated = collection.name + VALIDATED_COLLECTION_SUFFIX
    collection.database.command(
        {"create": validated, "validator": {"$expr": {"$lt": ["$d", "$$NOW"]}}}
    )
    result = execute_command(
        collection,
        {"insert": validated, "documents": [{"_id": 1, "d": datetime(2000, 1, 1)}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1},
        msg="A $$NOW validator should accept a document dated in the past",
    )


@pytest.mark.validation
def test_now_validator_rejects_future_date(collection):
    """Test a validator comparing a stored date against $$NOW rejects a future date."""
    validated = collection.name + VALIDATED_COLLECTION_SUFFIX
    collection.database.command(
        {"create": validated, "validator": {"$expr": {"$lt": ["$d", "$$NOW"]}}}
    )
    result = execute_command(
        collection,
        {"insert": validated, "documents": [{"_id": 1, "d": datetime(2100, 1, 1)}]},
    )
    assertFailureCode(
        result,
        DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="A $$NOW validator should reject a document dated in the future",
    )
