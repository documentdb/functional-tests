"""Tests for $pull with query operator conditions.

Covers: comparison operators ($eq, $ne, $gt, $gte, $lt, $lte, $in, $nin),
element operators ($exists, $type), $regex, $mod, $all, $size, $or, $not,
and implicit $and.
"""

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

PULL_QUERY_OPERATOR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "eq",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 2]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$eq": 2}}},
        expected={"_id": 1, "arr": [1, 3]},
        msg="Should remove elements equal to value with $eq",
    ),
    UpdateTestCase(
        "ne",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 2]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$ne": 2}}},
        expected={"_id": 1, "arr": [2, 2]},
        msg="Should remove elements not equal to value with $ne",
    ),
    UpdateTestCase(
        "gt",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$gt": 3}}},
        expected={"_id": 1, "arr": [1, 2, 3]},
        msg="Should remove elements > value with $gt",
    ),
    UpdateTestCase(
        "gte",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$gte": 3}}},
        expected={"_id": 1, "arr": [1, 2]},
        msg="Should remove elements >= value with $gte",
    ),
    UpdateTestCase(
        "lt",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$lt": 3}}},
        expected={"_id": 1, "arr": [3, 4, 5]},
        msg="Should remove elements < value with $lt",
    ),
    UpdateTestCase(
        "lte",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$lte": 3}}},
        expected={"_id": 1, "arr": [4, 5]},
        msg="Should remove elements <= value with $lte",
    ),
    UpdateTestCase(
        "in",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$in": [2, 4]}}},
        expected={"_id": 1, "arr": [1, 3, 5]},
        msg="Should remove elements in list with $in",
    ),
    UpdateTestCase(
        "nin",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$nin": [2, 4]}}},
        expected={"_id": 1, "arr": [2, 4]},
        msg="Should remove elements NOT in list with $nin",
    ),
    UpdateTestCase(
        "exists_on_embedded_doc",
        setup_docs=[{"_id": 1, "arr": [{"a": 1, "b": 2}, {"a": 1}, {"c": 3}]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"b": {"$exists": True}}}},
        expected={"_id": 1, "arr": [{"a": 1}, {"c": 3}]},
        msg="Should remove embedded docs where field exists",
    ),
    UpdateTestCase(
        "exists_false_on_embedded_doc",
        setup_docs=[{"_id": 1, "arr": [{"a": 1, "b": 2}, {"a": 1}, {"c": 3}]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"b": {"$exists": False}}}},
        expected={"_id": 1, "arr": [{"a": 1, "b": 2}]},
        msg="Should remove embedded docs where field does not exist",
    ),
    UpdateTestCase(
        "type_string",
        setup_docs=[{"_id": 1, "arr": [1, "two", 3, "four", True]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$type": "string"}}},
        expected={"_id": 1, "arr": [1, 3, True]},
        msg="Should remove elements of specified BSON type with $type",
    ),
    UpdateTestCase(
        "regex",
        setup_docs=[{"_id": 1, "arr": ["apple", "banana", "avocado", "cherry"]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$regex": "^a"}}},
        expected={"_id": 1, "arr": ["banana", "cherry"]},
        msg="Should remove string elements matching $regex",
    ),
    UpdateTestCase(
        "regex_bson_type",
        setup_docs=[{"_id": 1, "arr": ["apple", "banana", "avocado", "cherry"]}],
        query={"_id": 1},
        update={"$pull": {"arr": Regex("^a")}},
        expected={"_id": 1, "arr": ["banana", "cherry"]},
        msg="Should remove string elements matching BSON Regex value",
    ),
    UpdateTestCase(
        "mod",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5, 6]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$mod": [2, 0]}}},
        expected={"_id": 1, "arr": [1, 3, 5]},
        msg="Should remove elements matching $mod condition",
    ),
    UpdateTestCase(
        "implicit_and_gt_lt",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5, 6]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$gt": 2, "$lt": 5}}},
        expected={"_id": 1, "arr": [1, 2, 5, 6]},
        msg="Should remove elements matching all conditions (implicit $and)",
    ),
    UpdateTestCase(
        "explicit_and",
        setup_docs=[{"_id": 1, "arr": [{"x": 1, "y": 5}, {"x": 3, "y": 8}, {"x": 5, "y": 2}]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$and": [{"x": {"$gte": 3}}, {"y": {"$gte": 5}}]}}},
        expected={"_id": 1, "arr": [{"x": 1, "y": 5}, {"x": 5, "y": 2}]},
        msg="Should remove elements matching all conditions with explicit $and",
    ),
    UpdateTestCase(
        "all_on_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [1, 2, 3], [2, 3], [1, 2]]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$all": [1, 2]}}},
        expected={"_id": 1, "arr": [[2, 3]]},
        msg="Should remove array elements containing all specified values with $all",
    ),
    UpdateTestCase(
        "size_on_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [3, 4, 5], [6, 7]]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$size": 2}}},
        expected={"_id": 1, "arr": [[3, 4, 5]]},
        msg="Should remove array elements of specified size with $size",
    ),
    UpdateTestCase(
        "or_on_embedded_docs",
        setup_docs=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}, {"x": 10}]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$or": [{"x": {"$lt": 2}}, {"x": {"$gt": 8}}]}}},
        expected={"_id": 1, "arr": [{"x": 5}]},
        msg="Should remove embedded docs matching any $or condition",
    ),
    UpdateTestCase(
        "not_on_embedded_doc_field",
        setup_docs=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}, {"x": 10}]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"x": {"$not": {"$gte": 5}}}}},
        expected={"_id": 1, "arr": [{"x": 5}, {"x": 10}]},
        msg="Should remove embedded docs where field does NOT match inner condition",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PULL_QUERY_OPERATOR_TESTS))
def test_pull_query_operators(collection, test: UpdateTestCase):
    """Test $pull with query operator conditions."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
