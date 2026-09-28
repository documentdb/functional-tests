"""Aggregation $facet stage tests - all error cases.

Consolidates negative TEST_COVERAGE.md cases for the $facet stage: argument
handling, parse-time validation, forbidden sub-pipeline stages, sub-pipeline
runtime errors, output size limits, and boundary behaviours.
"""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    BSON_OBJECT_TOO_LARGE_ERROR,
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    FACET_PIPELINE_NOT_ARRAY_ERROR,
    FACET_PIPELINE_STAGE_NOT_OBJECT_ERROR,
    FACET_SPEC_NOT_OBJECT_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_DOT_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    INVALID_NAMESPACE_ERROR,
    LIMIT_NOT_POSITIVE_ERROR,
    LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
    UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    UNKNOWN_PIPELINE_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ExistingDatabase

# Documents used by the argument, forbidden-stage, and independence error cases.
DOCS = [{"_id": 1, "cat": "A"}, {"_id": 2, "cat": "B"}]

# Documents used by the boundary/core-semantics error case.
CORE_DOCS = [
    {"_id": 1, "category": "A", "price": 10},
    {"_id": 2, "category": "B", "price": 20},
    {"_id": 3, "category": "A", "price": 30},
]

# Documents used by the output size limit error cases.
_BIG_STRING = "x" * 100_000
_BIG_DOCS = [{"_id": i, "s": _BIG_STRING} for i in range(200)]

# Property [Specification Type]: the $facet argument must be a non-empty object;
# non-objects, null, and an empty object are all rejected with 40169.
FACET_SPEC_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="spec_number",
        docs=DOCS,
        pipeline=[{"$facet": 1}],
        error_code=FACET_SPEC_NOT_OBJECT_ERROR,
        msg="Numeric $facet specification should be rejected",
    ),
    StageTestCase(
        id="spec_string",
        docs=DOCS,
        pipeline=[{"$facet": "x"}],
        error_code=FACET_SPEC_NOT_OBJECT_ERROR,
        msg="String $facet specification should be rejected",
    ),
    StageTestCase(
        id="spec_bool",
        docs=DOCS,
        pipeline=[{"$facet": True}],
        error_code=FACET_SPEC_NOT_OBJECT_ERROR,
        msg="Boolean $facet specification should be rejected",
    ),
    StageTestCase(
        id="spec_array",
        docs=DOCS,
        pipeline=[{"$facet": [1, 2]}],
        error_code=FACET_SPEC_NOT_OBJECT_ERROR,
        msg="Array $facet specification should be rejected",
    ),
    StageTestCase(
        id="spec_null",
        docs=DOCS,
        pipeline=[{"$facet": None}],
        error_code=FACET_SPEC_NOT_OBJECT_ERROR,
        msg="Null $facet specification should be rejected",
    ),
    StageTestCase(
        id="spec_empty_object",
        docs=DOCS,
        pipeline=[{"$facet": {}}],
        error_code=FACET_SPEC_NOT_OBJECT_ERROR,
        msg="Empty $facet specification object should be rejected",
    ),
]

# Property [Sub-Pipeline Type]: each output field's value must be an array;
# non-array values are rejected with 40170.
FACET_PIPELINE_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="subpipeline_string",
        docs=DOCS,
        pipeline=[{"$facet": {"a": "notArray"}}],
        error_code=FACET_PIPELINE_NOT_ARRAY_ERROR,
        msg="String sub-pipeline value should be rejected",
    ),
    StageTestCase(
        id="subpipeline_number",
        docs=DOCS,
        pipeline=[{"$facet": {"a": 5}}],
        error_code=FACET_PIPELINE_NOT_ARRAY_ERROR,
        msg="Numeric sub-pipeline value should be rejected",
    ),
    StageTestCase(
        id="subpipeline_object",
        docs=DOCS,
        pipeline=[{"$facet": {"a": {"$match": {}}}}],
        error_code=FACET_PIPELINE_NOT_ARRAY_ERROR,
        msg="Object sub-pipeline value should be rejected",
    ),
]

# Property [Sub-Pipeline Element Type]: every element of a sub-pipeline array
# must be a stage document; non-documents and null are rejected with 40171.
FACET_PIPELINE_ELEMENT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="element_number",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [1]}}],
        error_code=FACET_PIPELINE_STAGE_NOT_OBJECT_ERROR,
        msg="Numeric element in a sub-pipeline should be rejected",
    ),
    StageTestCase(
        id="element_string",
        docs=DOCS,
        pipeline=[{"$facet": {"a": ["x"]}}],
        error_code=FACET_PIPELINE_STAGE_NOT_OBJECT_ERROR,
        msg="String element in a sub-pipeline should be rejected",
    ),
    StageTestCase(
        id="element_null",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [None]}}],
        error_code=FACET_PIPELINE_STAGE_NOT_OBJECT_ERROR,
        msg="Null element in a sub-pipeline should be rejected",
    ),
]

# Property [Stage Name Validation]: unknown stage names and names without a
# leading '$' inside a sub-pipeline are rejected with 40324 at parse time.
FACET_STAGE_NAME_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="unknown_stage",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$notAStage": {}}]}}],
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="Unknown stage name in a sub-pipeline should be rejected",
    ),
    StageTestCase(
        id="stage_name_no_dollar",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"match": {}}]}}],
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="Stage name without a leading '$' should be rejected",
    ),
]

# Property [Field Name Validation]: invalid output field name forms (empty string,
# dotted path, dollar-prefix, double-dollar system-variable) are each rejected with
# the appropriate field-path error code.
FACET_FIELD_NAME_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="empty_string_field_name",
        docs=DOCS,
        pipeline=[{"$facet": {"": [{"$match": {}}]}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="Empty-string output field name should be rejected",
    ),
    StageTestCase(
        id="dotted_field_name",
        docs=DOCS,
        pipeline=[{"$facet": {"a.b": [{"$count": "n"}]}}],
        error_code=FIELD_PATH_DOT_ERROR,
        msg="Dotted output field name should be rejected",
    ),
    StageTestCase(
        id="dollar_prefix_field_name",
        docs=DOCS,
        pipeline=[{"$facet": {"$x": [{"$count": "n"}]}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="Dollar-prefixed output field name should be rejected",
    ),
    StageTestCase(
        id="double_dollar_field_name",
        docs=DOCS,
        pipeline=[{"$facet": {"$$ROOT": [{"$count": "n"}]}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="System-variable-like output field name should be rejected",
    ),
]

# Property [Extra Stage Fields]: an unexpected top-level key alongside $facet in
# the stage document is rejected with 40323.
FACET_EXTRA_FIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="extra_top_level_key",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$count": "n"}]}, "extraKey": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="An unexpected extra top-level key in the $facet stage should be rejected",
    ),
]

# Property [Parse-Time Validation]: structural errors fire even on empty and
# non-existent collections, before any documents are processed.
FACET_PARSE_TIME_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="empty_collection_unknown_stage",
        docs=[],
        pipeline=[{"$facet": {"a": [{"$notAStage": {}}]}}],
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="Unknown stage should be rejected at parse time on an empty collection",
    ),
    StageTestCase(
        id="nonexistent_collection_unknown_stage",
        docs=None,
        pipeline=[{"$facet": {"a": [{"$notAStage": {}}]}}],
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="Unknown stage should be rejected at parse time on a non-existent collection",
    ),
    StageTestCase(
        id="empty_collection_non_array_pipeline",
        docs=[],
        pipeline=[{"$facet": {"a": "notArray"}}],
        error_code=FACET_PIPELINE_NOT_ARRAY_ERROR,
        msg="Non-array sub-pipeline should be rejected at parse time on an empty collection",
    ),
]

# Property [Core Semantic Boundary]: $limit 0 inside a sub-pipeline is rejected.
FACET_BOUNDARY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="limit_zero_rejected",
        docs=CORE_DOCS,
        pipeline=[{"$facet": {"a": [{"$limit": 0}]}}],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="$facet should reject $limit 0 inside a sub-pipeline",
    ),
]

# Property [Forbidden Sub-Pipeline Stages]: stages that cannot run inside a
# $facet sub-pipeline are rejected with 40600, independent of documents.
FACET_FORBIDDEN_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="collStats",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$collStats": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$collStats inside a $facet sub-pipeline should be rejected with 40600",
    ),
    StageTestCase(
        id="nested_facet",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$facet": {"b": [{"$match": {}}]}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="Nested $facet should be rejected with 40600",
    ),
    StageTestCase(
        id="geoNear",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$geoNear": {
                                "near": {"type": "Point", "coordinates": [0, 0]},
                                "distanceField": "d",
                                "spherical": True,
                            }
                        }
                    ]
                }
            }
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$geoNear inside a $facet sub-pipeline should be rejected with 40600",
    ),
    StageTestCase(
        id="indexStats",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$indexStats": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$indexStats inside a $facet sub-pipeline should be rejected with 40600",
    ),
    StageTestCase(
        id="out",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$out": "outcoll"}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$out inside a $facet sub-pipeline should be rejected with 40600",
    ),
    StageTestCase(
        id="merge",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$merge": {"into": "mcoll"}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$merge inside a $facet sub-pipeline should be rejected with 40600",
    ),
    StageTestCase(
        id="planCacheStats",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$planCacheStats": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$planCacheStats inside a $facet sub-pipeline should be rejected with 40600",
    ),
    StageTestCase(
        id="listSessions",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$listSessions": {}}]}}],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$listSessions inside a $facet sub-pipeline should be rejected with 73",
    ),
    # $listLocalSessions only reaches the $facet restriction at database scope.
    # Against a collection it reports the namespace error instead, which is a
    # different contract that the bare stage raises with no $facet involved.
    StageTestCase(
        id="listLocalSessions",
        docs=[],
        pipeline=[{"$facet": {"a": [{"$listLocalSessions": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$listLocalSessions inside a $facet sub-pipeline should be rejected",
        extra_command_fields={"aggregate": 1},
    ),
    StageTestCase(
        id="changeStreamSplitLargeEvent",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$changeStreamSplitLargeEvent": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$changeStreamSplitLargeEvent inside a $facet sub-pipeline should be rejected",
    ),
    StageTestCase(
        id="querySettings",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$querySettings": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$querySettings inside a $facet sub-pipeline should be rejected",
    ),
    # $listClusterCatalog reports a collection-level error at collection scope, so
    # only the database-scoped form reaches the $facet restriction.
    StageTestCase(
        id="listClusterCatalog",
        docs=[],
        pipeline=[{"$facet": {"a": [{"$listClusterCatalog": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$listClusterCatalog inside a $facet sub-pipeline should be rejected",
        extra_command_fields={"aggregate": 1},
    ),
    # $queryStats is admin-only, so like $currentOp it reports the namespace error
    # anywhere else and only reaches the $facet restriction on admin.
    StageTestCase(
        id="queryStats",
        target_collection=ExistingDatabase(db_name="admin"),
        docs=[],
        pipeline=[{"$facet": {"a": [{"$queryStats": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$queryStats inside a $facet sub-pipeline should be rejected",
        extra_command_fields={"aggregate": 1},
    ),
    # $listSampledQueries needs the admin database to reach the $facet check, and
    # cluster_admin because a target without it rejects the stage outright.
    StageTestCase(
        id="listSampledQueries",
        target_collection=ExistingDatabase(db_name="admin"),
        docs=[],
        pipeline=[{"$facet": {"a": [{"$listSampledQueries": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$listSampledQueries inside a $facet sub-pipeline should be rejected",
        extra_command_fields={"aggregate": 1},
        marks=(pytest.mark.requires(cluster_admin=True),),
    ),
    # The search surfaces are gated on the search capability: without it the
    # server rejects them before the $facet check, a different contract.
    StageTestCase(
        id="search",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$search": {"text": {"query": "x", "path": "cat"}}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$search inside a $facet sub-pipeline should be rejected",
        marks=(pytest.mark.requires(search=True),),
    ),
    StageTestCase(
        id="searchMeta",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$searchMeta": {"text": {"query": "x", "path": "cat"}}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$searchMeta inside a $facet sub-pipeline should be rejected",
        marks=(pytest.mark.requires(search=True),),
    ),
    StageTestCase(
        id="listSearchIndexes",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$listSearchIndexes": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$listSearchIndexes inside a $facet sub-pipeline should be rejected",
        marks=(pytest.mark.requires(search=True),),
    ),
    StageTestCase(
        id="vectorSearch",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$vectorSearch": {
                                "index": "i",
                                "path": "v",
                                "queryVector": [1.0],
                                "numCandidates": 10,
                                "limit": 1,
                            }
                        }
                    ]
                }
            }
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$vectorSearch inside a $facet sub-pipeline should be rejected",
        marks=(pytest.mark.requires(search=True),),
    ),
    # $documents is collectionless-only, so at collection scope it is rejected
    # for the $facet restriction rather than the namespace error it raises as a
    # top-level stage against a collection.
    StageTestCase(
        id="documents",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$documents": [{"x": 1}]}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$documents inside a $facet sub-pipeline should be rejected",
    ),
    # $currentOp only reaches the $facet restriction at database scope on the
    # admin database. Against a collection, or any other database, it reports the
    # namespace error instead, which is a different contract. docs=[] is required
    # for target_collection to be resolved.
    StageTestCase(
        id="currentOp",
        target_collection=ExistingDatabase(db_name="admin"),
        docs=[],
        pipeline=[{"$facet": {"a": [{"$currentOp": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$currentOp inside a $facet sub-pipeline should be rejected",
        extra_command_fields={"aggregate": 1},
    ),
    # Only the error code is asserted for $changeStream because the server
    # desugars the stage before the $facet check, so the message names an
    # internal stage. Gated on change_streams because a target without them
    # rejects it earlier for the topology, a different contract.
    StageTestCase(
        id="changeStream",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$changeStream": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$changeStream inside a $facet sub-pipeline should be rejected",
        marks=(pytest.mark.requires(change_streams=True),),
    ),
    StageTestCase(
        id="listCatalog",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$listCatalog": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$listCatalog inside a $facet sub-pipeline should be rejected",
    ),
    StageTestCase(
        id="searchBeta",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$searchBeta": {"text": {"query": "x", "path": "cat"}}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$searchBeta inside a $facet sub-pipeline should be rejected",
        marks=(pytest.mark.requires(search=True),),
    ),
    StageTestCase(
        id="valid_plus_forbidden",
        docs=DOCS,
        pipeline=[{"$facet": {"ok": [{"$match": {"cat": "A"}}], "bad": [{"$out": "outcoll"}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="A forbidden stage in any sub-pipeline should fail the whole $facet",
    ),
]

# Property [Lookup Pipeline Forbidden Stages]: the $facet-forbidden stages
# ($out, $merge, $collStats, $indexStats, $planCacheStats, $geoNear, $facet)
# are also rejected when nested inside a pipeline-form $lookup that is itself
# inside a $facet sub-pipeline. Each produces LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR
# (51047) at parse time, before any documents are processed.
_LOOKUP_FROM = "_facet_test_foreign"

FACET_LOOKUP_PIPELINE_FORBIDDEN_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="out_in_lookup_pipeline",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$lookup": {
                                "from": _LOOKUP_FROM,
                                "let": {},
                                "pipeline": [{"$out": "outcoll"}],
                                "as": "j",
                            }
                        }
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$out inside a $lookup pipeline within $facet should be rejected with 51047",
    ),
    StageTestCase(
        id="merge_in_lookup_pipeline",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$lookup": {
                                "from": _LOOKUP_FROM,
                                "let": {},
                                "pipeline": [{"$merge": {"into": "mcoll"}}],
                                "as": "j",
                            }
                        }
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$merge inside a $lookup pipeline within $facet should be rejected with 51047",
    ),
    StageTestCase(
        id="collStats_in_lookup_pipeline",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$lookup": {
                                "from": _LOOKUP_FROM,
                                "let": {},
                                "pipeline": [{"$collStats": {}}],
                                "as": "j",
                            }
                        }
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$collStats inside a $lookup pipeline within $facet should be rejected with 40600",
    ),
    StageTestCase(
        id="indexStats_in_lookup_pipeline",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$lookup": {
                                "from": _LOOKUP_FROM,
                                "let": {},
                                "pipeline": [{"$indexStats": {}}],
                                "as": "j",
                            }
                        }
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$indexStats inside a $lookup pipeline within $facet should be rejected with 40600",
    ),
    StageTestCase(
        id="planCacheStats_in_lookup_pipeline",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$lookup": {
                                "from": _LOOKUP_FROM,
                                "let": {},
                                "pipeline": [{"$planCacheStats": {}}],
                                "as": "j",
                            }
                        }
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$planCacheStats inside a $lookup pipeline within $facet should be rejected with 40600",
    ),
    StageTestCase(
        id="geoNear_in_lookup_pipeline",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$lookup": {
                                "from": _LOOKUP_FROM,
                                "let": {},
                                "pipeline": [
                                    {
                                        "$geoNear": {
                                            "near": {"type": "Point", "coordinates": [0, 0]},
                                            "distanceField": "d",
                                            "spherical": True,
                                        }
                                    }
                                ],
                                "as": "j",
                            }
                        }
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$geoNear inside a $lookup pipeline within $facet should be rejected with 40600",
    ),
    StageTestCase(
        id="nested_facet_in_lookup_pipeline",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$lookup": {
                                "from": _LOOKUP_FROM,
                                "let": {},
                                "pipeline": [{"$facet": {"b": [{"$match": {}}]}}],
                                "as": "j",
                            }
                        }
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$facet inside a $lookup pipeline within $facet should be rejected with 40600",
    ),
]


# Property [UnionWith Pipeline Forbidden Stages]: the $facet restriction also
# reaches through a $unionWith sub-pipeline nested inside a $facet sub-pipeline,
# the same way it reaches through $lookup above. $out is caught earlier by
# $unionWith's own restriction, which is a different contract and is asserted as
# such.
FACET_UNIONWITH_PIPELINE_FORBIDDEN_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="indexStats_in_unionWith_pipeline",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$unionWith": {
                                "coll": "_facet_test_union",
                                "pipeline": [{"$indexStats": {}}],
                            }
                        }
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$indexStats inside a $unionWith pipeline within $facet should be rejected",
    ),
    StageTestCase(
        id="nested_facet_in_unionWith_pipeline",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$unionWith": {
                                "coll": "_facet_test_union",
                                "pipeline": [{"$facet": {"b": [{"$count": "n"}]}}],
                            }
                        }
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$facet inside a $unionWith pipeline within $facet should be rejected",
    ),
    StageTestCase(
        id="out_in_unionWith_pipeline",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "a": [
                        {
                            "$unionWith": {
                                "coll": "_facet_test_union",
                                "pipeline": [{"$out": "outcoll"}],
                            }
                        }
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        error_code=UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$out inside a $unionWith pipeline within $facet should be rejected",
    ),
]


# Property [Sub-Pipeline Independence]: a runtime error in any sub-pipeline fails
# the whole $facet stage.
INDEPENDENCE_DOCS = [
    {"_id": 1, "cat": "A", "v": 10},
    {"_id": 2, "cat": "A", "v": 20},
    {"_id": 3, "cat": "B", "v": 30},
]
FACET_INDEPENDENCE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="subpipeline_error_fails_whole_stage",
        docs=INDEPENDENCE_DOCS,
        pipeline=[
            {
                "$facet": {
                    "ok": [{"$match": {"cat": "A"}}],
                    "bad": [{"$project": {"x": {"$divide": [1, 0]}}}],
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="An error in any sub-pipeline should fail the whole $facet stage",
    ),
]

# Property [Output Size Limits]: the final $facet output document is subject to
# the 16 MiB BSON limit, and allowDiskUse does not raise that limit.
FACET_SIZE_LIMIT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="output_exceeds_16mib",
        docs=_BIG_DOCS,
        pipeline=[{"$facet": {"all": [{"$group": {"_id": None, "arr": {"$push": "$s"}}}]}}],
        error_code=BSON_OBJECT_TOO_LARGE_ERROR,
        msg="A $facet output document exceeding 16 MiB should be rejected",
    ),
    StageTestCase(
        id="allowdiskuse_does_not_raise_16mib_limit",
        docs=_BIG_DOCS,
        pipeline=[{"$facet": {"all": [{"$group": {"_id": None, "arr": {"$push": "$s"}}}]}}],
        error_code=BSON_OBJECT_TOO_LARGE_ERROR,
        extra_command_fields={"allowDiskUse": True},
        msg="allowDiskUse:true should not raise the 16 MiB output-document limit",
    ),
]

FACET_ERROR_TESTS = (
    FACET_SPEC_TYPE_ERROR_TESTS
    + FACET_PIPELINE_TYPE_ERROR_TESTS
    + FACET_PIPELINE_ELEMENT_ERROR_TESTS
    + FACET_STAGE_NAME_ERROR_TESTS
    + FACET_FIELD_NAME_ERROR_TESTS
    + FACET_EXTRA_FIELD_ERROR_TESTS
    + FACET_PARSE_TIME_ERROR_TESTS
    + FACET_BOUNDARY_ERROR_TESTS
    + FACET_FORBIDDEN_STAGE_TESTS
    + FACET_LOOKUP_PIPELINE_FORBIDDEN_STAGE_TESTS
    + FACET_UNIONWITH_PIPELINE_FORBIDDEN_STAGE_TESTS
    + FACET_INDEPENDENCE_ERROR_TESTS
    + FACET_SIZE_LIMIT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(FACET_ERROR_TESTS))
def test_facet_errors(collection, test_case: StageTestCase):
    """Test all $facet error cases."""
    coll = populate_collection(collection, test_case)
    command: dict[str, Any] = {
        "aggregate": coll.name,
        "pipeline": test_case.pipeline,
        "cursor": {},
    }
    command.update(test_case.extra_command_fields)
    result = execute_command(coll, command)
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=test_case.ignore_doc_order,
        ignore_order_in=test_case.ignore_order_in,
    )
