"""Aggregation $group stage tests - group key behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Simple _id Null Equivalence]: in a simple (non-compound) _id, a
# missing field reference, $literal null, an expression evaluating to null, and
# $$REMOVE all evaluate to null and group together with explicit null.
GROUP_SIMPLE_NULL_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="missing_field_groups_with_null",
        docs=[
            {"_id": 1, "v": "a"},
            {"_id": 2},
            {"_id": 3, "v": None},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": "a", "ids": [1]},
            {"_id": None, "ids": [2, 3]},
        ],
        msg="Missing field reference and explicit null should group together",
    ),
    StageTestCase(
        id="literal_null_groups_all",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$group": {"_id": {"$literal": None}, "ids": {"$push": "$_id"}}}],
        expected=[{"_id": None, "ids": [1, 2]}],
        msg="$literal null should group all documents under null",
    ),
    StageTestCase(
        id="expression_null_groups_with_null",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2, "v": 10},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": {"$cond": [{"$eq": ["$v", None]}, None, "$v"]},
                    "ids": {"$push": "$_id"},
                }
            }
        ],
        expected=[
            {"_id": None, "ids": [1]},
            {"_id": 10, "ids": [2]},
        ],
        msg="Expression evaluating to null should group with explicit null",
    ),
    StageTestCase(
        id="remove_in_simple_id",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$group": {"_id": "$$REMOVE", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": None, "ids": [1, 2]}],
        msg="$$REMOVE in simple _id should evaluate to null, grouping all docs",
    ),
]

# Property [Compound _id Null vs Missing]: in a compound _id, a field set to
# null produces a key containing that field with a null value, while $$REMOVE
# or a missing field reference omits the field entirely, producing a different
# group key.
GROUP_COMPOUND_NULL_MISSING_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="compound_null_vs_missing_field",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": "hello"},
        ],
        pipeline=[{"$group": {"_id": {"x": "$v", "y": "constant"}, "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": {"x": None, "y": "constant"}, "ids": [1]},
            {"_id": {"y": "constant"}, "ids": [2]},
            {"_id": {"x": "hello", "y": "constant"}, "ids": [3]},
        ],
        msg=(
            "Compound _id: null field produces {x: null, y: ...} while missing"
            " field omits x, producing separate groups"
        ),
    ),
    StageTestCase(
        id="compound_remove_matches_missing",
        docs=[
            {"_id": 1, "v": "remove_me"},
            {"_id": 2},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": {
                        "x": {
                            "$cond": [
                                {"$eq": ["$v", "remove_me"]},
                                "$$REMOVE",
                                "$v",
                            ]
                        },
                        "y": "constant",
                    },
                    "ids": {"$push": "$_id"},
                }
            }
        ],
        expected=[{"_id": {"y": "constant"}, "ids": [1, 2]}],
        msg=(
            "$$REMOVE in compound _id removes the field, producing the same"
            " group key as a document where that field is missing"
        ),
    ),
    StageTestCase(
        id="compound_remove_vs_null_separate",
        docs=[
            {"_id": 1, "v": "remove_me"},
            {"_id": 2, "v": "null_me"},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": {
                        "x": {
                            "$cond": [
                                {"$eq": ["$v", "remove_me"]},
                                "$$REMOVE",
                                None,
                            ]
                        },
                        "y": "constant",
                    },
                    "ids": {"$push": "$_id"},
                }
            }
        ],
        expected=[
            {"_id": {"y": "constant"}, "ids": [1]},
            {"_id": {"x": None, "y": "constant"}, "ids": [2]},
        ],
        msg=(
            "$$REMOVE and null in compound _id produce different group keys:"
            " removed field vs present-with-null"
        ),
    ),
]

GROUP_NULL_MISSING_TESTS = GROUP_SIMPLE_NULL_TESTS + GROUP_COMPOUND_NULL_MISSING_TESTS

# Property [Distinct Group Keys]: each distinct _id value produces exactly one
# output document, and the output _id field reflects the evaluated group key.
GROUP_DISTINCT_KEY_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="distinct_values_produce_one_doc_each",
        docs=[
            {"_id": 1, "v": "a"},
            {"_id": 2, "v": "b"},
            {"_id": 3, "v": "a"},
            {"_id": 4, "v": "c"},
            {"_id": 5, "v": "b"},
        ],
        pipeline=[{"$group": {"_id": "$v", "count": {"$sum": 1}}}],
        expected=[
            {"_id": "a", "count": 2},
            {"_id": "b", "count": 2},
            {"_id": "c", "count": 1},
        ],
        msg="Each distinct _id value should produce exactly one output document",
    ),
    StageTestCase(
        id="output_id_reflects_group_key",
        docs=[{"_id": 1, "v": 42}, {"_id": 2, "v": 42}],
        pipeline=[{"$group": {"_id": "$v", "count": {"$sum": 1}}}],
        expected=[{"_id": 42, "count": 2}],
        msg="Output _id should reflect the evaluated group key value",
    ),
]

# Property [Null and Constant _id]: _id set to null or any other constant
# produces a single group that aggregates all input documents.
GROUP_CONSTANT_ID_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="null_id_single_group",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$group": {"_id": None, "total": {"$sum": "$v"}}}],
        expected=[{"_id": None, "total": 60}],
        msg="_id: null should produce a single group aggregating all documents",
    ),
    StageTestCase(
        id="constant_int_id_single_group",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$group": {"_id": 1, "total": {"$sum": "$v"}}}],
        expected=[{"_id": 1, "total": 30}],
        msg="_id: 1 should produce a single group aggregating all documents",
    ),
]

# Property [_id Accepts Field References, Expressions, and Compound Keys]: _id
# can be a field reference, an expression (such as $cond or $add), or a
# subdocument with multiple fields, and each form correctly determines the
# group key.
GROUP_ID_FORMS_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="expression_id_cond",
        docs=[
            {"_id": 1, "score": 80},
            {"_id": 2, "score": 40},
            {"_id": 3, "score": 90},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": {"$cond": [{"$gte": ["$score", 50]}, "pass", "fail"]},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[
            {"_id": "pass", "count": 2},
            {"_id": "fail", "count": 1},
        ],
        msg="_id as a $cond expression should group by the expression result",
    ),
    StageTestCase(
        id="compound_key_id",
        docs=[
            {"_id": 1, "dept": "eng", "level": "senior"},
            {"_id": 2, "dept": "eng", "level": "junior"},
            {"_id": 3, "dept": "eng", "level": "senior"},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": {"dept": "$dept", "level": "$level"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[
            {"_id": {"dept": "eng", "level": "senior"}, "count": 2},
            {"_id": {"dept": "eng", "level": "junior"}, "count": 1},
        ],
        msg="_id as a compound key should group by the subdocument",
    ),
    StageTestCase(
        id="id_add_expression",
        docs=[
            {"_id": 1, "x": 10, "y": 5},
            {"_id": 2, "x": 10, "y": 5},
            {"_id": 3, "x": 20, "y": 3},
        ],
        pipeline=[{"$group": {"_id": {"$add": ["$x", "$y"]}, "count": {"$sum": 1}}}],
        expected=[
            {"_id": 15, "count": 2},
            {"_id": 23, "count": 1},
        ],
        msg="_id with $add expression should group by the computed sum",
    ),
]

# Property [String Literal vs Field Reference]: a non-$-prefixed string in _id
# is a constant value, while a $-prefixed string is a field reference.
GROUP_STRING_LITERAL_VS_REF_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="non_dollar_string_is_constant",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$group": {"_id": "hello", "count": {"$sum": 1}}}],
        expected=[{"_id": "hello", "count": 2}],
        msg=(
            "Non-$-prefixed string in _id should be treated as a constant,"
            " grouping all documents together"
        ),
    ),
    StageTestCase(
        id="dollar_string_is_field_ref",
        docs=[
            {"_id": 1, "hello": "x"},
            {"_id": 2, "hello": "y"},
            {"_id": 3, "hello": "x"},
        ],
        pipeline=[{"$group": {"_id": "$hello", "count": {"$sum": 1}}}],
        expected=[
            {"_id": "x", "count": 2},
            {"_id": "y", "count": 1},
        ],
        msg="$-prefixed string in _id should be treated as a field reference",
    ),
]

GROUP_KEY_BEHAVIOR_TESTS = (
    GROUP_DISTINCT_KEY_TESTS
    + GROUP_CONSTANT_ID_TESTS
    + GROUP_ID_FORMS_TESTS
    + GROUP_STRING_LITERAL_VS_REF_TESTS
)


GROUP_KEY_TESTS = GROUP_NULL_MISSING_TESTS + GROUP_KEY_BEHAVIOR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_KEY_TESTS))
def test_group_key(collection, test_case: StageTestCase):
    """Test $group stage - key behavior."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
