"""
$$CLUSTER_TIME nesting, set semantics, and pipeline contexts.

Resolves at depth and inside operator arguments; behaves as a truthy scalar in
set operations; coexists with the variables $redact and $reduce bind themselves.
Also covers the stage and collection-type contexts that have no wiring file of
their own ($set, $replaceWith, $bucket, $bucketAuto, $graphLookup, $documents,
$collStats, $indexStats, $listLocalSessions, time-series and clustered
collections); the $project, $addFields, $group and $match contexts live in those
stages' own ``test_operators_in_*.py`` files.

Single-level object, array, $cond and $let nesting is covered once in
``test_system_variables_cluster_time_expression_engine.py``. Per-operation
constancy at scale lives in ``test_cluster_time_clock_progression.py``.
"""

from datetime import datetime

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.error_codes import SETUNION_TYPE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import TS_EPOCH

pytestmark = [pytest.mark.aggregate, pytest.mark.requires(cluster_time=True)]


# Property [Nesting]: the variable resolves wherever the expression engine
# accepts an expression — at depth and inside operator arguments — always
# yielding a timestamp. The bare position and the single-level object, array,
# $cond and $let cases are covered once in the shared expression-engine file.
CLUSTER_TIME_NESTING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="at_depth_four",
        expression={
            "$type": {
                "$getField": {
                    "field": "b",
                    "input": {
                        "$arrayElemAt": [
                            [{"b": {"$arrayElemAt": [["$$CLUSTER_TIME"], 0]}}],
                            0,
                        ]
                    },
                }
            }
        },
        expected="timestamp",
        msg="$$CLUSTER_TIME should resolve when nested four levels deep",
    ),
    ExpressionTestCase(
        id="in_switch_branch",
        expression={
            "$type": {
                "$switch": {"branches": [{"case": True, "then": "$$CLUSTER_TIME"}], "default": None}
            }
        },
        expected="timestamp",
        msg="$$CLUSTER_TIME should resolve in a $switch branch",
    ),
    ExpressionTestCase(
        id="in_nested_let",
        expression={
            "$let": {
                "vars": {"outer": "$$CLUSTER_TIME"},
                "in": {
                    "$let": {
                        "vars": {"inner": "$$outer"},
                        "in": {"$eq": ["$$inner", "$$CLUSTER_TIME"]},
                    }
                },
            }
        },
        expected=True,
        msg="A $let binding nested two levels deep should still equal a direct reference",
    ),
    ExpressionTestCase(
        id="in_reduce_body",
        expression={
            "$reduce": {
                "input": [1, 2, 3],
                "initialValue": True,
                "in": {"$and": ["$$value", {"$eq": [{"$type": "$$CLUSTER_TIME"}, "timestamp"]}]},
            }
        },
        expected=True,
        msg="$$CLUSTER_TIME should resolve inside a $reduce body alongside $$value and $$this",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CLUSTER_TIME_NESTING_TESTS))
def test_cluster_time_nesting(collection, test: ExpressionTestCase):
    """Test $$CLUSTER_TIME resolves in nested expression positions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Set Element Semantics]: the timestamp participates in set operations
# as a single scalar element, deduplicating against itself but never against its
# own derived date.
CLUSTER_TIME_SET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="set_union_deduplicates",
        expression={"$size": {"$setUnion": [["$$CLUSTER_TIME"], ["$$CLUSTER_TIME"]]}},
        expected=1,
        msg="$setUnion should deduplicate two references to $$CLUSTER_TIME",
    ),
    ExpressionTestCase(
        id="set_difference_with_itself_is_empty",
        expression={"$setDifference": [["$$CLUSTER_TIME"], ["$$CLUSTER_TIME"]]},
        expected=[],
        msg="$setDifference of $$CLUSTER_TIME with itself should be empty",
    ),
    ExpressionTestCase(
        id="set_is_subset_of_superset",
        expression={"$setIsSubset": [["$$CLUSTER_TIME"], ["$$CLUSTER_TIME", 1]]},
        expected=True,
        msg="$setIsSubset should hold for $$CLUSTER_TIME against a superset",
    ),
    ExpressionTestCase(
        id="timestamp_and_derived_date_stay_distinct",
        expression={"$size": {"$setUnion": [["$$CLUSTER_TIME"], [{"$toDate": "$$CLUSTER_TIME"}]]}},
        expected=2,
        msg="A timestamp and its derived date should remain distinct set elements",
    ),
    ExpressionTestCase(
        id="any_element_true",
        expression={"$anyElementTrue": [["$$CLUSTER_TIME"]]},
        expected=True,
        msg="$anyElementTrue should treat a non-zero timestamp as truthy",
    ),
    ExpressionTestCase(
        id="all_elements_true",
        expression={"$allElementsTrue": [["$$CLUSTER_TIME"]]},
        expected=True,
        msg="$allElementsTrue should treat a non-zero timestamp as truthy",
    ),
    ExpressionTestCase(
        id="rejected_where_array_required",
        expression={"$setUnion": ["$$CLUSTER_TIME", []]},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a timestamp where an array is required",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CLUSTER_TIME_SET_TESTS))
def test_cluster_time_set_semantics(collection, test: ExpressionTestCase):
    """Test $$CLUSTER_TIME behaves as a single scalar element under set semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


def test_cluster_time_mixed_with_field_paths_preserves_order(collection):
    """Test an array mixing a field path and $$CLUSTER_TIME preserves element order."""
    result = execute_expression_with_insert(
        collection,
        {"$map": {"input": ["$a", "$$CLUSTER_TIME"], "in": {"$type": "$$this"}}},
        {"_id": 1, "a": 1},
    )
    assert_expression_result(
        result,
        expected=["int", "timestamp"],
        msg="An array mixing a field path and $$CLUSTER_TIME should preserve order",
    )


def test_cluster_time_constant_across_map_iterations(collection):
    """Test $$CLUSTER_TIME in a $map body is the same value for every element."""
    result = execute_expression_with_insert(
        collection,
        {"$size": {"$setUnion": [{"$map": {"input": "$arr", "in": "$$CLUSTER_TIME"}}]}},
        {"_id": 1, "arr": [1, 2, 3]},
    )
    assert_expression_result(
        result,
        expected=1,
        msg="$$CLUSTER_TIME in a $map body should be constant across iterations",
    )


def test_cluster_time_is_truthy_in_filter_cond(collection):
    """Test a non-zero timestamp is truthy, so a $filter condition keeps every element."""
    result = execute_expression_with_insert(
        collection,
        {"$filter": {"input": "$arr", "cond": "$$CLUSTER_TIME"}},
        {"_id": 1, "arr": [1, 2, 3]},
    )
    assert_expression_result(
        result,
        expected=[1, 2, 3],
        msg="A non-zero timestamp should be truthy as a $filter condition",
    )


def test_cluster_time_is_truthy_in_cond_if(collection):
    """Test a non-zero timestamp is truthy in the condition position of $cond."""
    result = execute_expression(
        collection, {"$cond": {"if": "$$CLUSTER_TIME", "then": "taken", "else": "not taken"}}
    )
    assert_expression_result(
        result,
        expected="taken",
        msg="A non-zero timestamp should be truthy in a $cond condition",
    )


def test_cluster_time_merges_into_root_document(collection):
    """Test $mergeObjects adds the timestamp to the root document without altering it."""
    collection.insert_one({"_id": 1, "a": 2})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$replaceWith": {"$mergeObjects": ["$$ROOT", {"ct": "$$CLUSTER_TIME"}]}},
                {"$project": {"_id": 1, "a": 1, "kind": {"$type": "$ct"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1, "a": 2, "kind": "timestamp"}],
        msg="$mergeObjects should add the timestamp without altering existing fields",
    )


def test_cluster_time_prunes_every_document_in_redact(collection):
    """Test a $redact condition driven by $$CLUSTER_TIME can prune every document."""
    collection.insert_many([{"_id": 1}, {"_id": 2}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$redact": {
                        "$cond": [
                            {"$gt": ["$$CLUSTER_TIME", None]},
                            "$$PRUNE",
                            "$$KEEP",
                        ]
                    }
                }
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [],
        msg="A $redact condition on $$CLUSTER_TIME should prune every document uniformly",
    )


def test_cluster_time_keeps_every_document_in_redact(collection):
    """Test the mirrored $redact condition keeps every document, proving evaluation."""
    collection.insert_many([{"_id": 1}, {"_id": 2}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$redact": {
                        "$cond": [
                            {"$lt": ["$$CLUSTER_TIME", None]},
                            "$$PRUNE",
                            "$$KEEP",
                        ]
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}],
        msg="The mirrored $redact condition should keep every document",
    )


def test_cluster_time_in_set_stage(collection):
    """Test $set accepts $$CLUSTER_TIME and preserves the original fields."""
    collection.insert_one({"_id": 1, "a": 2})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$set": {"t": "$$CLUSTER_TIME"}},
                {"$project": {"_id": 1, "a": 1, "kind": {"$type": "$t"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1, "a": 2, "kind": "timestamp"}],
        msg="$set should add a timestamp field without disturbing existing fields",
    )


def test_cluster_time_in_replace_with(collection):
    """Test $replaceWith can build a new document from $$CLUSTER_TIME."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$replaceWith": {"t": "$$CLUSTER_TIME"}},
                {"$project": {"_id": 0, "kind": {"$type": "$t"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"kind": "timestamp"}],
        msg="$replaceWith should accept $$CLUSTER_TIME as a field value",
    )


def test_cluster_time_identical_on_every_unwound_document(collection):
    """Test $unwind produces documents that all share one $$CLUSTER_TIME value."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"t": "$$CLUSTER_TIME"}},
                {"$unwind": "$arr"},
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}, "n": {"$sum": 1}}},
                {"$project": {"_id": 0, "n": 1, "distinct": {"$size": "$values"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"n": 3, "distinct": 1}],
        msg="Every unwound document should carry the same $$CLUSTER_TIME value",
    )


def test_cluster_time_in_bucket_output(collection):
    """Test $bucket accepts $$CLUSTER_TIME in its output document."""
    collection.insert_many([{"_id": 1, "v": 1}, {"_id": 2, "v": 5}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$bucket": {
                        "groupBy": "$v",
                        "boundaries": [0, 10],
                        "output": {"t": {"$max": "$$CLUSTER_TIME"}},
                    }
                },
                {"$project": {"_id": 1, "kind": {"$type": "$t"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": 0, "kind": "timestamp"}],
        msg="$bucket should accept $$CLUSTER_TIME in its output document",
    )


def test_cluster_time_in_bucket_auto_output(collection):
    """Test $bucketAuto accepts $$CLUSTER_TIME in its output document."""
    collection.insert_many([{"_id": i, "v": i} for i in range(4)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$bucketAuto": {
                        "groupBy": "$v",
                        "buckets": 1,
                        "output": {"t": {"$max": "$$CLUSTER_TIME"}},
                    }
                },
                {"$project": {"_id": 0, "kind": {"$type": "$t"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"kind": "timestamp"}],
        msg="$bucketAuto should accept $$CLUSTER_TIME in its output document",
    )


def test_cluster_time_coexists_with_redact_variables(collection):
    """Test a $redact condition on $$CLUSTER_TIME can descend into every document."""
    collection.insert_many([{"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$redact": {
                        "$cond": [{"$gt": ["$$CLUSTER_TIME", TS_EPOCH]}, "$$DESCEND", "$$PRUNE"]
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}],
        msg="$$CLUSTER_TIME should coexist with $redact's own system variables",
    )


def test_cluster_time_in_documents_source_pipeline(collection):
    """Test a database-level $documents pipeline resolves $$CLUSTER_TIME consistently."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{"_id": 1}, {"_id": 2}, {"_id": 3}]},
                {"$addFields": {"t": "$$CLUSTER_TIME"}},
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}}},
                {"$project": {"_id": 0, "distinct": {"$size": "$values"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"distinct": 1}],
        msg="A $documents-sourced pipeline should resolve one $$CLUSTER_TIME value",
    )


def test_cluster_time_in_coll_stats_pipeline(collection):
    """Test a $collStats-led pipeline resolves $$CLUSTER_TIME in a later stage."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$collStats": {"count": {}}},
                {"$project": {"_id": 0, "kind": {"$type": "$$CLUSTER_TIME"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"kind": "timestamp"}],
        msg="A $collStats-led pipeline should resolve $$CLUSTER_TIME",
    )


def test_cluster_time_in_index_stats_pipeline(collection):
    """Test an $indexStats-led pipeline resolves $$CLUSTER_TIME in a later stage."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$indexStats": {}},
                {"$project": {"_id": 0, "kind": {"$type": "$$CLUSTER_TIME"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"kind": "timestamp"}],
        msg="An $indexStats-led pipeline should resolve $$CLUSTER_TIME",
    )


def test_cluster_time_in_graph_lookup_restrict_search(collection):
    """Test $graphLookup accepts $$CLUSTER_TIME in restrictSearchWithMatch."""
    collection.insert_many([{"_id": 1, "next": 2}, {"_id": 2, "next": 3}, {"_id": 3}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"_id": 1}},
                {
                    "$graphLookup": {
                        "from": collection.name,
                        "startWith": "$next",
                        "connectFromField": "next",
                        "connectToField": "_id",
                        "as": "chain",
                        "restrictSearchWithMatch": {"$expr": {"$gt": ["$$CLUSTER_TIME", TS_EPOCH]}},
                    }
                },
                {"$project": {"_id": 1, "reached": {"$size": "$chain"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1, "reached": 2}],
        msg="$graphLookup should accept $$CLUSTER_TIME in restrictSearchWithMatch",
    )


def test_cluster_time_in_time_series_collection_pipeline(collection):
    """Test a pipeline over a time-series collection resolves one $$CLUSTER_TIME value."""
    database = collection.database
    database.command(
        {
            "create": f"{collection.name}_timeseries",
            "timeseries": {"timeField": "ts", "metaField": "m"},
        }
    )
    database[f"{collection.name}_timeseries"].insert_many(
        [{"ts": datetime(2024, 1, 1), "m": "a", "v": i} for i in range(5)]
    )

    result = execute_command(
        collection,
        {
            "aggregate": f"{collection.name}_timeseries",
            "pipeline": [
                {"$addFields": {"t": "$$CLUSTER_TIME"}},
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}}},
                {"$project": {"_id": 0, "distinct": {"$size": "$values"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"distinct": 1}],
        msg="Bucket unpacking should not re-resolve $$CLUSTER_TIME per measurement",
    )


def test_cluster_time_in_list_local_sessions_pipeline(collection):
    """Test a $listLocalSessions-led pipeline resolves $$CLUSTER_TIME in a later stage."""
    # Seed a local session so $listLocalSessions is guaranteed to return at
    # least one document, regardless of connection pool state.
    with collection.database.client.start_session() as session:
        collection.database.command({"ping": 1}, session=session)

    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$listLocalSessions": {}},
                {"$limit": 1},
                {"$project": {"_id": 0, "kind": {"$type": "$$CLUSTER_TIME"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"kind": "timestamp"}],
        msg="A $listLocalSessions-led pipeline should resolve $$CLUSTER_TIME",
    )


def test_cluster_time_in_clustered_collection_pipeline(collection):
    """Test a pipeline over a clustered collection resolves $$CLUSTER_TIME normally."""
    database = collection.database
    database.command(
        {
            "create": f"{collection.name}_clustered",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
        }
    )
    database[f"{collection.name}_clustered"].insert_many([{"_id": i} for i in range(3)])

    result = execute_command(
        collection,
        {
            "aggregate": f"{collection.name}_clustered",
            "pipeline": [
                {"$addFields": {"t": "$$CLUSTER_TIME"}},
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}}},
                {"$project": {"_id": 0, "distinct": {"$size": "$values"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"distinct": 1}],
        msg="A clustered collection should not change $$CLUSTER_TIME behavior",
    )
