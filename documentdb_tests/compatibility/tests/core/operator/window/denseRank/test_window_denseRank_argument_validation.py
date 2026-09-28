"""
Tests for $denseRank argument validation in window context.

$denseRank is a frameless rank operator with a fixed accepted shape:
- Its value must be exactly the empty object `{}` — any other value is rejected.
- It takes no other arguments, so a `window` key (or any extra key) is rejected.
- It requires a top-level `sortBy` with exactly one element — omitted, empty,
  and multi-field sortBy are all rejected.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    RANK_STYLE_WINDOW_EXTRA_ARGS_ERROR,
    RANK_STYLE_WINDOW_NON_EMPTY_ARG_ERROR,
    RANK_STYLE_WINDOW_SORTBY_ONE_ELEMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_command

SINGLE_DOC = [{"_id": 1, "partition": "A", "value": 10}]


# Property [Accepted Shape]: $denseRank takes exactly `{}` and no other arguments.


def test_denseRank_empty_object_accepted(collection):
    """$denseRank with `{}` as its value is the valid form."""
    result = run_window_operator(collection, "$denseRank", SINGLE_DOC, expression={})
    expected = [{"_id": 1, "partition": "A", "value": 10, "result": 1}]
    assertSuccess(result, expected, msg="$denseRank accepts empty object")


# Property [Non-Empty Value Rejected]: any value other than `{}` errors with 5371603.

NON_EMPTY_ARGS = [
    ("non_empty_object", {"a": 1}),
    ("field_path_string", "$value"),
    ("empty_string", ""),
    ("integer", 1),
    ("zero", 0),
    ("double", 1.5),
    ("bool_true", True),
    ("bool_false", False),
    ("null", None),
    ("empty_array", []),
    ("non_empty_array", [1, 2]),
]


@pytest.mark.parametrize("case_id,arg", NON_EMPTY_ARGS, ids=[c[0] for c in NON_EMPTY_ARGS])
def test_denseRank_non_empty_value_errors(collection, case_id, arg):
    """$denseRank rejects any value that is not the empty object."""
    result = run_window_operator(collection, "$denseRank", SINGLE_DOC, expression=arg)
    assertFailureCode(
        result,
        RANK_STYLE_WINDOW_NON_EMPTY_ARG_ERROR,
        msg=f"$denseRank rejects {case_id} value — only '{{}}' is valid",
    )


# Property [Frameless]: $denseRank takes no other arguments, including `window`.


@pytest.mark.parametrize(
    "case_id,window",
    [
        ("documents_cumulative", {"documents": ["unbounded", "current"]}),
        ("documents_whole_partition", {"documents": ["unbounded", "unbounded"]}),
        ("documents_sliding", {"documents": [-1, 1]}),
        ("range_bounds", {"range": ["unbounded", "current"]}),
    ],
    ids=["documents_cumulative", "documents_whole_partition", "documents_sliding", "range_bounds"],
)
def test_denseRank_window_key_errors(collection, case_id, window):
    """$denseRank is frameless — specifying a `window` key is rejected."""
    result = run_window_operator(collection, "$denseRank", SINGLE_DOC, window=window, expression={})
    assertFailureCode(
        result,
        RANK_STYLE_WINDOW_EXTRA_ARGS_ERROR,
        msg=f"$denseRank rejects a {case_id} window — it is frameless",
    )


def test_denseRank_unknown_key_in_output_field_errors(collection):
    """An unknown key alongside $denseRank in the output field is rejected."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {"result": {"$denseRank": {}, "unknownKey": 1}},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        RANK_STYLE_WINDOW_EXTRA_ARGS_ERROR,
        msg="unknown key alongside $denseRank rejected",
    )


def test_denseRank_second_operator_in_output_field_errors(collection):
    """Another window operator in the same output field as $denseRank is rejected."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {"result": {"$denseRank": {}, "$rank": {}}},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        RANK_STYLE_WINDOW_EXTRA_ARGS_ERROR,
        msg="a second window operator alongside $denseRank rejected",
    )


# Property [sortBy Requirement]: $denseRank needs a top-level sortBy with one element.


def test_denseRank_sortBy_omitted_errors(collection):
    """$denseRank requires sortBy — omitting it is rejected."""
    collection.insert_many(SINGLE_DOC)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "output": {"result": {"$denseRank": {}}},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        RANK_STYLE_WINDOW_SORTBY_ONE_ELEMENT_ERROR,
        msg="$denseRank requires a sortBy expression",
    )


def test_denseRank_sortBy_empty_object_errors(collection):
    """An empty sortBy object has no elements, so $denseRank rejects it."""
    result = run_window_operator(collection, "$denseRank", SINGLE_DOC, sort_by={}, expression={})
    assertFailureCode(
        result,
        RANK_STYLE_WINDOW_SORTBY_ONE_ELEMENT_ERROR,
        msg="$denseRank rejects an empty sortBy object",
    )


def test_denseRank_multi_field_sortBy_errors(collection):
    """$denseRank requires exactly one sortBy element — two fields are rejected."""
    result = run_window_operator(
        collection, "$denseRank", SINGLE_DOC, sort_by={"value": -1, "_id": 1}, expression={}
    )
    assertFailureCode(
        result,
        RANK_STYLE_WINDOW_SORTBY_ONE_ELEMENT_ERROR,
        msg="$denseRank rejects a multi-field sortBy",
    )
