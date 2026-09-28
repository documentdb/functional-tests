"""
Tests for $addToSet set semantics in window context — the core behavior.

Covers deduplication (including sliding-window removal and reappearance),
numeric equivalence coalescing, BSON type distinction, null vs missing, document
and array deep equality, mixed BSON types, and NaN-as-a-set-element. Results
compared with ignore_order_in=["result"].
"""

from datetime import datetime, timezone

from bson import Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN

WHOLE = {"documents": ["unbounded", "unbounded"]}
# Whole-partition frames give every row the same set; project one row for a concise assertion.
FIRST_ROW = [{"$sort": {"_id": 1}}, {"$limit": 1}, {"$project": {"_id": 0, "result": 1}}]
ALL_ROWS = [{"$sort": {"_id": 1}}, {"$project": {"_id": 1, "result": 1}}]


# Property [Deduplication under Sliding Window]: values dedup within the frame; a value leaves
# the set when its doc exits the frame and can reappear later.


def test_addToSet_dedup_sliding_window_removal_and_reappear(collection):
    """$addToSet dedups within a sliding frame; a value leaves and later reappears."""
    docs = [
        {"_id": 1, "partition": "A", "v": 1},
        {"_id": 2, "partition": "A", "v": 2},
        {"_id": 3, "partition": "A", "v": 3},
        {"_id": 4, "partition": "A", "v": 1},
    ]
    result = run_window_operator(
        collection,
        "$addToSet",
        docs,
        {"documents": [-1, 0]},
        expression="$v",
        extra_stages=ALL_ROWS,
    )
    # Window [-1,0] = previous + current. Value 1 present at _id1, gone at _id2/_id3, back at _id4.
    expected = [
        {"_id": 1, "result": [1]},
        {"_id": 2, "result": [1, 2]},
        {"_id": 3, "result": [2, 3]},
        {"_id": 4, "result": [1, 3]},
    ]
    assertSuccess(
        result,
        expected,
        msg="sliding-window dedup with removal and reappearance",
        ignore_order_in=["result"],
    )


# Property [Numeric Equivalence Coalescing]: numerically equal values across types collapse to one.


def test_addToSet_numeric_coalescing_collapses(collection):
    """$addToSet collapses numerically-equal values across types into one element."""
    docs = [
        {"_id": 1, "partition": "A", "v": 1},
        {"_id": 2, "partition": "A", "v": Int64(1)},
        {"_id": 3, "partition": "A", "v": 1.0},
        {"_id": 4, "partition": "A", "v": Decimal128("1")},
        {"_id": 5, "partition": "A", "v": 2},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    # int1 / long1 / double1.0 / decimal1 all coalesce to one element; the kept representation
    # is the first encountered under the _id:1 sort (int32 here).
    expected = [{"result": [1, 2]}]
    assertSuccess(
        result,
        expected,
        msg="numeric equivalents coalesce to one element",
        ignore_order_in=["result"],
    )


# Property [BSON Type Distinction]: booleans are distinct from numbers (false != 0, true != 1).


def test_addToSet_bool_vs_number_distinct(collection):
    """$addToSet keeps booleans distinct from numerically-equal integers."""
    docs = [
        {"_id": 1, "partition": "A", "v": False},
        {"_id": 2, "partition": "A", "v": 0},
        {"_id": 3, "partition": "A", "v": True},
        {"_id": 4, "partition": "A", "v": 1},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    expected = [{"result": [False, 0, True, 1]}]
    assertSuccess(
        result,
        expected,
        msg="false!=0 and true!=1 — four distinct elements",
        ignore_order_in=["result"],
    )


# Property [Null vs Missing]: an explicit null is collected; a missing field contributes nothing.


def test_addToSet_null_collected_missing_skipped(collection):
    """$addToSet collects an explicit null once and skips a missing field."""
    docs = [
        {"_id": 1, "partition": "A", "v": None},
        {"_id": 2, "partition": "A"},
        {"_id": 3, "partition": "A", "v": None},
        {"_id": 4, "partition": "A", "v": 5},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    expected = [{"result": [None, 5]}]
    assertSuccess(
        result,
        expected,
        msg="explicit null collected once, missing skipped",
        ignore_order_in=["result"],
    )


def test_addToSet_all_missing_frame_empty(collection):
    """$addToSet over a frame where every doc is missing the field returns []."""
    docs = [
        {"_id": 1, "partition": "A"},
        {"_id": 2, "partition": "A"},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    expected = [{"result": []}]
    assertSuccess(result, expected, msg="all-missing frame returns []", ignore_order_in=["result"])


# Property [Document Deep Equality]: identical documents collapse; differing ones stay distinct.


def test_addToSet_document_exact_duplicates_collapse(collection):
    """$addToSet collapses identical documents and keeps documents that differ."""
    docs = [
        {"_id": 1, "partition": "A", "v": {"a": 1, "b": 2}},
        {"_id": 2, "partition": "A", "v": {"a": 1, "b": 2}},
        {"_id": 3, "partition": "A", "v": {"a": 1, "b": 3}},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    expected = [{"result": [{"a": 1, "b": 2}, {"a": 1, "b": 3}]}]
    assertSuccess(
        result,
        expected,
        msg="identical documents collapse, differing ones distinct",
        ignore_order_in=["result"],
    )


def test_addToSet_document_field_order_distinct(collection):
    """$addToSet treats documents with different field order as distinct elements."""
    docs = [
        {"_id": 1, "partition": "A", "v": {"a": 1, "b": 2}},
        {"_id": 2, "partition": "A", "v": {"b": 2, "a": 1}},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    # {a:1,b:2} and {b:2,a:1} are distinct elements (field order matters) — two elements.
    expected = [{"result": [{"a": 1, "b": 2}, {"b": 2, "a": 1}]}]
    assertSuccess(
        result,
        expected,
        msg="documents with different field order are distinct",
        ignore_order_in=["result"],
    )


# Property [Array Deep Equality]: element order matters; identical arrays collapse.


def test_addToSet_array_element_order_distinct(collection):
    """$addToSet keeps arrays with different element order distinct; identical ones collapse."""
    docs = [
        {"_id": 1, "partition": "A", "v": [1, 2]},
        {"_id": 2, "partition": "A", "v": [2, 1]},
        {"_id": 3, "partition": "A", "v": [1, 2]},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    expected = [{"result": [[1, 2], [2, 1]]}]
    assertSuccess(
        result,
        expected,
        msg="[1,2] and [2,1] are distinct; duplicate [1,2] collapses",
        ignore_order_in=["result"],
    )


# Property [Mixed BSON Types]: values of any type accumulate; duplicates collapse.


def test_addToSet_mixed_bson_types_accumulate(collection):
    """$addToSet accumulates mixed BSON types and dedups duplicates."""
    date_val = datetime(2024, 1, 1, tzinfo=timezone.utc)
    oid = ObjectId("64000000000000000000000a")
    docs = [
        {"_id": 1, "partition": "A", "v": "x"},
        {"_id": 2, "partition": "A", "v": "x"},
        {"_id": 3, "partition": "A", "v": True},
        {"_id": 4, "partition": "A", "v": date_val},
        {"_id": 5, "partition": "A", "v": oid},
        {"_id": 6, "partition": "A", "v": {"nested": [1, 2]}},
        {"_id": 7, "partition": "A", "v": Timestamp(1, 1)},
        {"_id": 8, "partition": "A", "v": MinKey()},
        {"_id": 9, "partition": "A", "v": MaxKey()},
        {"_id": 10, "partition": "A", "v": Regex("abc", "i")},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    # "x" collapses; all other types are distinct elements.
    expected = [
        {
            "result": [
                "x",
                True,
                date_val,
                oid,
                {"nested": [1, 2]},
                Timestamp(1, 1),
                MinKey(),
                MaxKey(),
                Regex("abc", "i"),
            ]
        }
    ]
    assertSuccess(
        result, expected, msg="mixed BSON types accumulate with dedup", ignore_order_in=["result"]
    )


# Property [Value Distinction]: values that look similar across types stay distinct.


def test_addToSet_string_vs_number_distinct(collection):
    """$addToSet keeps the string "1" distinct from the number 1."""
    docs = [
        {"_id": 1, "partition": "A", "v": "1"},
        {"_id": 2, "partition": "A", "v": 1},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    expected = [{"result": ["1", 1]}]
    assertSuccess(
        result, expected, msg='string "1" is distinct from number 1', ignore_order_in=["result"]
    )


def test_addToSet_signed_zero_collapses(collection):
    """$addToSet collapses 0, -0.0, and 0.0 into a single element."""
    docs = [
        {"_id": 1, "partition": "A", "v": 0},
        {"_id": 2, "partition": "A", "v": -0.0},
        {"_id": 3, "partition": "A", "v": 0.0},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    expected = [{"result": [0]}]
    assertSuccess(
        result, expected, msg="signed/typed zeros collapse to one", ignore_order_in=["result"]
    )


def test_addToSet_infinities_distinct(collection):
    """$addToSet keeps +Infinity and -Infinity distinct; duplicate +Infinity collapses."""
    docs = [
        {"_id": 1, "partition": "A", "v": float("inf")},
        {"_id": 2, "partition": "A", "v": float("-inf")},
        {"_id": 3, "partition": "A", "v": float("inf")},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    expected = [{"result": [float("inf"), float("-inf")]}]
    assertSuccess(
        result, expected, msg="+Infinity and -Infinity are distinct", ignore_order_in=["result"]
    )


def test_addToSet_empty_values_all_distinct(collection):
    """$addToSet keeps "", [], {}, null, and 0 as five distinct elements."""
    docs = [
        {"_id": 1, "partition": "A", "v": ""},
        {"_id": 2, "partition": "A", "v": []},
        {"_id": 3, "partition": "A", "v": {}},
        {"_id": 4, "partition": "A", "v": None},
        {"_id": 5, "partition": "A", "v": 0},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    expected = [{"result": ["", [], {}, None, 0]}]
    assertSuccess(
        result, expected, msg='"", [], {}, null, 0 are all distinct', ignore_order_in=["result"]
    )


def test_addToSet_empty_array_vs_null_distinct(collection):
    """$addToSet keeps an empty array distinct from null; identical empty arrays collapse."""
    docs = [
        {"_id": 1, "partition": "A", "v": []},
        {"_id": 2, "partition": "A", "v": None},
        {"_id": 3, "partition": "A", "v": []},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    expected = [{"result": [[], None]}]
    assertSuccess(
        result, expected, msg="empty array is distinct from null", ignore_order_in=["result"]
    )


# Property [Multiplicity]: a value stays while >=1 in-frame doc carries it (no inverse;
# the set is recomputed per frame), vanishing only when its last occurrence leaves.


def test_addToSet_value_persists_until_last_occurrence_leaves(collection):
    """$addToSet keeps a value while any in-frame doc has it; it leaves with the last one."""
    docs = [
        {"_id": 1, "partition": "A", "v": "a"},
        {"_id": 2, "partition": "A", "v": "a"},
        {"_id": 3, "partition": "A", "v": "b"},
        {"_id": 4, "partition": "A", "v": "c"},
        {"_id": 5, "partition": "A", "v": "d"},
    ]
    result = run_window_operator(
        collection,
        "$addToSet",
        docs,
        {"documents": [-2, 0]},
        expression="$v",
        extra_stages=ALL_ROWS,
    )
    # At _id4 the frame is rows 2-4 (a,b,c): _id1's "a" slid out but "a" stays via _id2.
    # At _id5 the frame is rows 3-5 (b,c,d): both "a"s are gone.
    expected = [
        {"_id": 1, "result": ["a"]},
        {"_id": 2, "result": ["a"]},
        {"_id": 3, "result": ["a", "b"]},
        {"_id": 4, "result": ["a", "b", "c"]},
        {"_id": 5, "result": ["b", "c", "d"]},
    ]
    assertSuccess(
        result,
        expected,
        msg="value persists until its last in-frame occurrence leaves",
        ignore_order_in=["result"],
    )


# Property [NaN as Element]: two NaNs collapse to a single element.


def test_addToSet_nan_collapses(collection):
    """$addToSet collapses duplicate NaN values into a single element."""
    docs = [
        {"_id": 1, "partition": "A", "v": float("nan")},
        {"_id": 2, "partition": "A", "v": float("nan")},
        {"_id": 3, "partition": "A", "v": 1.0},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$v", extra_stages=FIRST_ROW
    )
    # Two NaNs collapse to one; 1.0 is kept as a double.
    expected = [{"result": [float("nan"), 1.0]}]
    assertSuccessNaN(
        result, expected, msg="duplicate NaN collapses to one element", ignore_order_in=["result"]
    )
