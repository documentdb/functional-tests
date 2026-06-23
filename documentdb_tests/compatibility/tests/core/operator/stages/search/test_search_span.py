"""Tests for the $search span operator."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SEARCH_EXECUTOR_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

pytestmark = pytest.mark.requires(search=True)


# Property [Span Sub-operator Execution]: span sub-operators execute positional
# and proximity matches against an analyzed path.
SEARCH_SPAN_TESTS: list[StageTestCase] = [
    StageTestCase(
        "span_term_token_match",
        pipeline=[
            {"$search": {"span": {"term": {"path": "title", "query": "quick"}}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search span term should execute a token match over the analyzed path",
    ),
    StageTestCase(
        "span_first_positional",
        # first bounds the span's end position, so only a token at the start of
        # the field matches; doc 4's "$quick" tokenizes to "quick" at position 0
        # while docs 1 and 3 carry "quick" later in the field.
        pipeline=[
            {
                "$search": {
                    "span": {
                        "first": {
                            "operator": {"term": {"path": "title", "query": "quick"}},
                            "endPositionLte": 1,
                        }
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 4)]},
        msg="$search span first should match only spans ending within the position bound",
    ),
    StageTestCase(
        "span_near_adjacent",
        pipeline=[
            {
                "$search": {
                    "span": {
                        "near": {
                            "clauses": [
                                {"term": {"path": "title", "query": "quick"}},
                                {"term": {"path": "title", "query": "brown"}},
                            ],
                            "slop": 0,
                            "inOrder": True,
                        }
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search span near with slop 0 should match adjacent in-order spans",
    ),
    StageTestCase(
        "span_near_slop_excludes_gap",
        pipeline=[
            {
                "$search": {
                    "span": {
                        "near": {
                            "clauses": [
                                {"term": {"path": "title", "query": "quick"}},
                                {"term": {"path": "title", "query": "fox"}},
                            ],
                            "slop": 0,
                            "inOrder": True,
                        }
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search span near with slop 0 should exclude spans separated by an "
        "intervening token",
    ),
    StageTestCase(
        "span_near_slop_permits_gap",
        pipeline=[
            {
                "$search": {
                    "span": {
                        "near": {
                            "clauses": [
                                {"term": {"path": "title", "query": "quick"}},
                                {"term": {"path": "title", "query": "fox"}},
                            ],
                            "slop": 1,
                            "inOrder": True,
                        }
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search span near should permit an intervening token within the slop bound",
    ),
    StageTestCase(
        "span_near_order_enforced",
        pipeline=[
            {
                "$search": {
                    "span": {
                        "near": {
                            "clauses": [
                                {"term": {"path": "title", "query": "brown"}},
                                {"term": {"path": "title", "query": "quick"}},
                            ],
                            "slop": 0,
                            "inOrder": True,
                        }
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search span near with inOrder should not match clauses in the reversed order",
    ),
    StageTestCase(
        "span_or_union",
        pipeline=[
            {
                "$search": {
                    "span": {
                        "or": {
                            "clauses": [
                                {"term": {"path": "title", "query": "quick"}},
                                {"term": {"path": "title", "query": "turtle"}},
                            ]
                        }
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(4),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search span or should match the union of its clause spans",
    ),
    StageTestCase(
        "span_subtract_excludes_overlap",
        # subtract removes include spans that overlap an exclude span, so
        # subtracting the same token's spans from themselves leaves nothing.
        pipeline=[
            {
                "$search": {
                    "span": {
                        "subtract": {
                            "include": {"term": {"path": "title", "query": "quick"}},
                            "exclude": {"term": {"path": "title", "query": "quick"}},
                        }
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search span subtract should remove include spans that overlap the exclude spans",
    ),
    StageTestCase(
        "span_contains_inner",
        # little=quick is contained by the big quick-brown span, so spanToReturn
        # inner returns the document carrying that containment.
        pipeline=[
            {
                "$search": {
                    "span": {
                        "contains": {
                            "little": {"term": {"path": "title", "query": "quick"}},
                            "big": {
                                "near": {
                                    "clauses": [
                                        {"term": {"path": "title", "query": "quick"}},
                                        {"term": {"path": "title", "query": "brown"}},
                                    ],
                                    "slop": 0,
                                    "inOrder": True,
                                }
                            },
                            "spanToReturn": "inner",
                        }
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search span contains spanToReturn inner should return the document whose little "
        "span is contained by the big span",
    ),
    StageTestCase(
        "span_contains_outer",
        pipeline=[
            {
                "$search": {
                    "span": {
                        "contains": {
                            "little": {"term": {"path": "title", "query": "quick"}},
                            "big": {
                                "near": {
                                    "clauses": [
                                        {"term": {"path": "title", "query": "quick"}},
                                        {"term": {"path": "title", "query": "brown"}},
                                    ],
                                    "slop": 0,
                                    "inOrder": True,
                                }
                            },
                            "spanToReturn": "outer",
                        }
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search span contains spanToReturn outer should return the document whose big span "
        "contains the little span",
    ),
    StageTestCase(
        "span_contains_excludes_non_contained",
        # little=turtle is not contained by the big quick-brown span, so the
        # containment constraint excludes every document.
        pipeline=[
            {
                "$search": {
                    "span": {
                        "contains": {
                            "little": {"term": {"path": "title", "query": "turtle"}},
                            "big": {
                                "near": {
                                    "clauses": [
                                        {"term": {"path": "title", "query": "quick"}},
                                        {"term": {"path": "title", "query": "brown"}},
                                    ],
                                    "slop": 0,
                                    "inOrder": True,
                                }
                            },
                            "spanToReturn": "inner",
                        }
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search span contains should exclude a document whose little span is not contained "
        "by the big span",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_SPAN_TESTS))
def test_search_span_cases(indexed_collection, test_case: StageTestCase):
    """Test $search span single sub-operator execution."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [Span Operator Required]: a span document with no sub-operator key
# produces a spec validation error.
SEARCH_SPAN_OPERATOR_REQUIRED_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "span_empty",
        pipeline=[{"$search": {"span": {}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span should reject an empty document with no sub-operator",
    ),
]

# Property [Span Sub-operator Required Sub-fields]: a span sub-operator with a
# required sub-field omitted is rejected.
SEARCH_SPAN_SUBOPERATOR_REQUIRED_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "term_missing_path",
        pipeline=[{"$search": {"span": {"term": {"query": "quick"}}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span term should reject a missing path",
    ),
    StageTestCase(
        "term_missing_query",
        pipeline=[{"$search": {"span": {"term": {"path": "title"}}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span term should reject a missing query",
    ),
    StageTestCase(
        "first_missing_operator",
        pipeline=[
            {"$search": {"span": {"first": {"endPositionLte": 1}}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span first should reject a missing operator",
    ),
    StageTestCase(
        "near_missing_clauses",
        pipeline=[{"$search": {"span": {"near": {"slop": 0}}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span near should reject missing clauses",
    ),
    StageTestCase(
        "or_missing_clauses",
        pipeline=[{"$search": {"span": {"or": {}}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span or should reject missing clauses",
    ),
    StageTestCase(
        "subtract_missing_include",
        pipeline=[
            {
                "$search": {
                    "span": {"subtract": {"exclude": {"term": {"path": "title", "query": "quick"}}}}
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span subtract should reject a missing include",
    ),
    StageTestCase(
        "subtract_missing_exclude",
        pipeline=[
            {
                "$search": {
                    "span": {"subtract": {"include": {"term": {"path": "title", "query": "quick"}}}}
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span subtract should reject a missing exclude",
    ),
    StageTestCase(
        "contains_missing_little",
        pipeline=[
            {
                "$search": {
                    "span": {
                        "contains": {
                            "big": {"term": {"path": "title", "query": "quick"}},
                            "spanToReturn": "inner",
                        }
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span contains should reject a missing little",
    ),
    StageTestCase(
        "contains_missing_span_to_return",
        pipeline=[
            {
                "$search": {
                    "span": {
                        "contains": {
                            "little": {"term": {"path": "title", "query": "quick"}},
                            "big": {"term": {"path": "title", "query": "brown"}},
                        }
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span contains should reject a missing spanToReturn",
    ),
    StageTestCase(
        "contains_missing_big",
        pipeline=[
            {
                "$search": {
                    "span": {
                        "contains": {
                            "little": {"term": {"path": "title", "query": "quick"}},
                            "spanToReturn": "inner",
                        }
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span contains should reject a missing big",
    ),
]

# Property [Span Contains spanToReturn Enum]: span.contains.spanToReturn accepts
# only the values inner or outer, so a value outside that set is rejected.
SEARCH_SPAN_CONTAINS_ENUM_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "contains_span_to_return_bogus",
        pipeline=[
            {
                "$search": {
                    "span": {
                        "contains": {
                            "little": {"term": {"path": "title", "query": "quick"}},
                            "big": {"term": {"path": "title", "query": "brown"}},
                            "spanToReturn": "bogus",
                        }
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search span contains should reject a spanToReturn outside the [inner, outer] enum",
    ),
]

# Property [Span Near Sub-field Type Rejection]: a near sub-operator's non-integer
# slop or non-boolean inOrder is rejected with no coercion.
SEARCH_SPAN_NEAR_TYPE_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"near_slop_type_{tid}",
            pipeline=[
                {
                    "$search": {
                        "span": {
                            "near": {
                                "clauses": [{"term": {"path": "title", "query": "quick"}}],
                                "slop": val,
                            }
                        }
                    }
                },
            ],
            error_code=SEARCH_EXECUTOR_ERROR,
            msg=f"$search span near should reject a {tid} slop as a non-integer",
        )
        for tid, val in [
            ("string", "1"),
            ("double", 1.5),
            ("bool", True),
            ("object", {"a": 1}),
            ("array", [1]),
            ("objectid", ObjectId("0123456789abcdef01234567")),
            ("datetime", datetime.datetime(2020, 1, 1)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
        ]
    ],
    *[
        StageTestCase(
            f"near_inorder_type_{tid}",
            pipeline=[
                {
                    "$search": {
                        "span": {
                            "near": {
                                "clauses": [{"term": {"path": "title", "query": "quick"}}],
                                "inOrder": val,
                            }
                        }
                    }
                },
            ],
            error_code=SEARCH_EXECUTOR_ERROR,
            msg=f"$search span near should reject a {tid} inOrder as a non-boolean",
        )
        for tid, val in [
            ("string", "true"),
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("object", {"a": 1}),
            ("array", [True]),
            ("objectid", ObjectId("0123456789abcdef01234567")),
            ("datetime", datetime.datetime(2020, 1, 1)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
        ]
    ],
]

SEARCH_SPAN_ERROR_TESTS = (
    SEARCH_SPAN_OPERATOR_REQUIRED_ERROR_TESTS
    + SEARCH_SPAN_SUBOPERATOR_REQUIRED_ERROR_TESTS
    + SEARCH_SPAN_CONTAINS_ENUM_ERROR_TESTS
    + SEARCH_SPAN_NEAR_TYPE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_SPAN_ERROR_TESTS))
def test_search_span_errors(indexed_collection, test_case: StageTestCase):
    """Test $search span rejects an empty operator, missing sub-fields, and mistyped near fields."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
