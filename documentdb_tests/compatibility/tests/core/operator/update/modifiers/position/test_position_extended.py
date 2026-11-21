"""
Extended tests for $position modifier with $push.

Covers insertion at the beginning (0), middle, end (beyond length), negative
positions, negative beyond array length (clamps to 0), Int64 typed position,
non-integer errors (string, float), $position without $each (treated as plain
value push), upsert:true, multi:true, findAndModify, and composition with
$slice.

Oracle: MongoDB 7.0.
SUT-agnostic: assertions follow observed MongoDB behavior; engine divergences
are tracked via `engine_xfail` markers with tracking links.
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.update


# ---- $position 0: inserts at the beginning -----------------------------------


def test_position_zero_inserts_at_beginning(collection):
    """$position: 0 inserts new elements at the start of the array."""
    collection.insert_one({"_id": 1, "items": ["C", "D"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {"items": {"$each": ["A", "B"], "$position": 0}}
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["A", "B", "C", "D"]}])


# ---- $position in the middle -------------------------------------------------


def test_position_middle_inserts_at_index(collection):
    """$position: 1 inserts new elements starting at index 1."""
    collection.insert_one({"_id": 1, "items": ["A", "D"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {"items": {"$each": ["B", "C"], "$position": 1}}
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["A", "B", "C", "D"]}])


# ---- $position beyond array length: appends at end ---------------------------


def test_position_beyond_length_appends_at_end(collection):
    """$position beyond the array length appends elements at the end."""
    collection.insert_one({"_id": 1, "items": ["A", "B"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {"items": {"$each": ["Z"], "$position": 100}}
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["A", "B", "Z"]}])


# ---- negative $position: counts from end -------------------------------------


def test_position_negative_inserts_from_end(collection):
    """$position: -1 inserts before the last element."""
    collection.insert_one({"_id": 1, "items": ["A", "B", "C"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {"items": {"$each": ["X"], "$position": -1}}
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["A", "B", "X", "C"]}])


# ---- negative $position beyond array length: clamps to 0 --------------------


def test_position_negative_beyond_length_clamps_to_zero(collection):
    """Negative $position beyond array length clamps to position 0 (front)."""
    collection.insert_one({"_id": 1, "items": ["A", "B"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {"items": {"$each": ["X"], "$position": -100}}
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["X", "A", "B"]}])


# ---- Int64 typed $position ---------------------------------------------------


def test_position_int64_value(collection):
    """$position with an Int64 value works the same as a regular integer."""
    collection.insert_one({"_id": 1, "items": ["A", "C"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {
                            "items": {"$each": ["B"], "$position": Int64(1)}
                        }
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["A", "B", "C"]}])


# ---- error: $position with string value --------------------------------------


def test_position_string_value_errors(collection):
    """$position with a non-numeric string value fails with code 2."""
    collection.insert_one({"_id": 1, "items": [1, 2]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {
                            "items": {"$each": ["X"], "$position": "abc"}
                        }
                    },
                }
            ],
        },
    )
    assertFailureCode(result, 2)


# ---- error: $position with float value --------------------------------------


def test_position_float_value_errors(collection):
    """$position with a float value (1.5) fails with code 2."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {
                            "items": {"$each": ["X"], "$position": 1.5}
                        }
                    },
                }
            ],
        },
    )
    assertFailureCode(result, 2)


# ---- $position without $each: treated as plain value push --------------------


def test_position_without_each_pushes_document_as_value(collection):
    """$position without $each is not treated as a modifier; the whole doc is pushed."""
    collection.insert_one({"_id": 1, "items": [1, 2]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"items": {"$position": 0}}},
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 2, {"$position": 0}]}])


# ---- $position with upsert:true ---------------------------------------------


def test_position_with_upsert_creates_document(collection):
    """$push with $each + $position and upsert:true creates document with array."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 77},
                    "u": {
                        "$push": {
                            "items": {"$each": ["A", "B"], "$position": 0}
                        }
                    },
                    "upsert": True,
                }
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 77}, "sort": {"_id": 1}},
    )
    assertSuccess(result, [{"_id": 77, "items": ["A", "B"]}])


# ---- $position with multi:true -----------------------------------------------


def test_position_multi_true(collection):
    """$push with $each + $position and multi:true applies to all matched docs."""
    collection.insert_many(
        [{"_id": 1, "items": ["B"]}, {"_id": 2, "items": ["B"]}]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {},
                    "u": {
                        "$push": {
                            "items": {"$each": ["A"], "$position": 0}
                        }
                    },
                    "multi": True,
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [{"_id": 1, "items": ["A", "B"]}, {"_id": 2, "items": ["A", "B"]}],
    )


# ---- findAndModify with $position -------------------------------------------


def test_position_find_and_modify_post_image(collection):
    """$push with $each + $position via findAndModify returns updated document."""
    collection.insert_one({"_id": 1, "items": ["B", "C"]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {
                "$push": {"items": {"$each": ["A"], "$position": 0}}
            },
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "items": ["A", "B", "C"]}})


# ---- $position with $slice (composition) ------------------------------------


def test_position_with_slice_limits_result(collection):
    """$push with $each + $position + $slice inserts at position then slices."""
    collection.insert_one({"_id": 1, "items": ["B", "C", "D"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {
                            "items": {
                                "$each": ["A"],
                                "$position": 0,
                                "$slice": 3,
                            }
                        }
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["A", "B", "C"]}])


# ---- $position on empty array ------------------------------------------------


def test_position_on_empty_array(collection):
    """$position: 0 on an empty array correctly inserts the elements."""
    collection.insert_one({"_id": 1, "items": []})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {
                            "items": {"$each": ["A", "B"], "$position": 0}
                        }
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["A", "B"]}])
