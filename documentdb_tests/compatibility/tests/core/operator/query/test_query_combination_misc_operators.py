"""
Tests for misc query operator combinations.

Covers $mod combined with logical operators ($not, $and, $or, $nor),
comparison operators ($gt), and array operators ($elemMatch).
Covers $regex inside $in, $regex with $not, $regex with $ne/$exists/$type,
$regex with $nin (implicit AND), $regex in $all, $regex with $and/$or/$nor,
and $regex with $elemMatch.
"""

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": i, "a": i} for i in range(1, 13)]

MOD_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_mod_4_0",
        filter={"a": {"$not": {"$mod": [4, 0]}}},
        doc=DOCS,
        expected=[d for d in DOCS if d["a"] % 4 != 0],
        msg="$not $mod [4,0] should match docs where field % 4 != 0",
    ),
    QueryTestCase(
        id="not_mod_missing_field",
        filter={"a": {"$not": {"$mod": [4, 0]}}},
        doc=[{"_id": 1, "b": 4}],
        expected=[{"_id": 1, "b": 4}],
        msg="$not $mod on missing field should match",
    ),
    QueryTestCase(
        id="mod_with_gt",
        filter={"a": {"$mod": [2, 0], "$gt": 5}},
        doc=DOCS,
        expected=[d for d in DOCS if d["a"] % 2 == 0 and d["a"] > 5],
        msg="$mod [2,0] with $gt 5 should match even numbers > 5",
    ),
    QueryTestCase(
        id="and_mod_2_mod_3",
        filter={"$and": [{"a": {"$mod": [2, 0]}}, {"a": {"$mod": [3, 0]}}]},
        doc=DOCS,
        expected=[d for d in DOCS if d["a"] % 2 == 0 and d["a"] % 3 == 0],
        msg="$and with $mod [2,0] and $mod [3,0] should match divisible by both",
    ),
    QueryTestCase(
        id="or_mod_2_mod_3",
        filter={"$or": [{"a": {"$mod": [2, 0]}}, {"a": {"$mod": [3, 0]}}]},
        doc=DOCS,
        expected=[d for d in DOCS if d["a"] % 2 == 0 or d["a"] % 3 == 0],
        msg="$or with $mod [2,0] and $mod [3,0] should match divisible by 2 or 3",
    ),
    QueryTestCase(
        id="nor_mod_2",
        filter={"$nor": [{"a": {"$mod": [2, 0]}}]},
        doc=DOCS,
        expected=[d for d in DOCS if d["a"] % 2 != 0],
        msg="$nor with $mod [2,0] should match odd numbers",
    ),
    QueryTestCase(
        id="elemmatch_mod_3_0",
        filter={"a": {"$elemMatch": {"$mod": [3, 0]}}},
        doc=[{"_id": 1, "a": [1, 3, 5]}],
        expected=[{"_id": 1, "a": [1, 3, 5]}],
        msg="$elemMatch with $mod should match if any element satisfies",
    ),
]

TYPE_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_type_string_excludes_string",
        filter={"x": {"$not": {"$type": "string"}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}, {"_id": 3, "x": None}],
        expected=[{"_id": 2, "x": 42}, {"_id": 3, "x": None}],
        msg="$not $type: 'string' should match docs where field is NOT string",
    ),
    QueryTestCase(
        id="type_int_with_gt",
        filter={"x": {"$type": "int", "$gt": 5}},
        doc=[{"_id": 1, "x": 3}, {"_id": 2, "x": 10}, {"_id": 3, "x": "hello"}],
        expected=[{"_id": 2, "x": 10}],
        msg="$type: 'int' + $gt: 5 should match int fields > 5",
    ),
    QueryTestCase(
        id="elemMatch_type_string",
        filter={"x": {"$elemMatch": {"$type": "string"}}},
        doc=[{"_id": 1, "x": [1, "a", True]}, {"_id": 2, "x": [1, 2]}],
        expected=[{"_id": 1, "x": [1, "a", True]}],
        msg="$elemMatch with $type: 'string' should match array with string element",
    ),
    QueryTestCase(
        id="or_type_string_or_int",
        filter={"$or": [{"x": {"$type": "string"}}, {"x": {"$type": "int"}}]},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}, {"_id": 3, "x": 1.5}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}],
        msg="$or with $type: 'string' and $type: 'int' should match either type",
    ),
    QueryTestCase(
        id="nor_type_string",
        filter={"$nor": [{"x": {"$type": "string"}}]},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}, {"_id": 3, "x": 1.5}],
        expected=[{"_id": 2, "x": 42}, {"_id": 3, "x": 1.5}],
        msg="$nor with $type: 'string' should exclude string fields",
    ),
    QueryTestCase(
        id="and_impossible_string_and_int",
        filter={"$and": [{"x": {"$type": "string"}}, {"x": {"$type": "int"}}]},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}],
        expected=[],
        msg="$and with $type: 'string' and $type: 'int' should return no results",
    ),
    QueryTestCase(
        id="not_type_missing_field",
        filter={"x": {"$not": {"$type": "string"}}},
        doc=[{"_id": 1, "y": "hello"}, {"_id": 2, "x": 42}],
        expected=[{"_id": 1, "y": "hello"}, {"_id": 2, "x": 42}],
        msg="$not $type on missing field should match",
    ),
    QueryTestCase(
        id="type_string_with_regex",
        filter={"x": {"$type": "string", "$regex": "^he"}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": "world"}, {"_id": 3, "x": 42}],
        expected=[{"_id": 1, "x": "hello"}],
        msg="$type: 'string' + $regex should match strings matching pattern",
    ),
    QueryTestCase(
        id="type_int_with_in",
        filter={"x": {"$type": "int", "$in": [1, 3, "hello"]}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": "hello"}],
        expected=[{"_id": 1, "x": 1}],
        msg="$type: 'int' + $in should match only int values in the list",
    ),
    QueryTestCase(
        id="type_string_with_nin",
        filter={"x": {"$type": "string", "$nin": ["hello"]}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": "world"}, {"_id": 3, "x": 42}],
        expected=[{"_id": 2, "x": "world"}],
        msg="$type: 'string' + $nin should match strings not in the list",
    ),
]

REGEX_IN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="in_with_regex_objects",
        filter={"a": {"$in": [Regex("^acme", "i"), Regex("^ack")]}},
        doc=[
            {"_id": 1, "a": "Acme Corp"},
            {"_id": 2, "a": "ack123"},
            {"_id": 3, "a": "other"},
        ],
        expected=[{"_id": 1, "a": "Acme Corp"}, {"_id": 2, "a": "ack123"}],
        msg="$in with regex objects should match",
    ),
    QueryTestCase(
        id="in_mixed_regex_and_string",
        filter={"a": {"$in": [Regex("^acme", "i"), "exact"]}},
        doc=[
            {"_id": 1, "a": "Acme Corp"},
            {"_id": 2, "a": "exact"},
            {"_id": 3, "a": "other"},
        ],
        expected=[{"_id": 1, "a": "Acme Corp"}, {"_id": 2, "a": "exact"}],
        msg="$in with mixed regex and literal should match both",
    ),
]

REGEX_NOT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_with_regex_object",
        filter={"a": {"$not": Regex("^p.*")}},
        doc=[
            {"_id": 1, "a": "apple"},
            {"_id": 2, "a": "pear"},
            {"_id": 3, "a": "banana"},
        ],
        expected=[{"_id": 1, "a": "apple"}, {"_id": 3, "a": "banana"}],
        msg="$not with regex object should exclude matching docs",
    ),
    QueryTestCase(
        id="not_with_regex_expression",
        filter={"a": {"$not": {"$regex": "^p.*"}}},
        doc=[
            {"_id": 1, "a": "apple"},
            {"_id": 2, "a": "pear"},
            {"_id": 3, "a": "banana"},
        ],
        expected=[{"_id": 1, "a": "apple"}, {"_id": 3, "a": "banana"}],
        msg="$not with $regex expression should exclude matching docs",
    ),
    QueryTestCase(
        id="not_with_regex_object_in_regex",
        filter={"a": {"$not": {"$regex": Regex("^p.*")}}},
        doc=[
            {"_id": 1, "a": "apple"},
            {"_id": 2, "a": "pear"},
            {"_id": 3, "a": "banana"},
        ],
        expected=[{"_id": 1, "a": "apple"}, {"_id": 3, "a": "banana"}],
        msg="$not with {$regex: Regex(...)} should exclude matching docs",
    ),
    QueryTestCase(
        id="not_regex_includes_null_and_missing",
        filter={"a": {"$not": Regex("^p.*")}},
        doc=[
            {"_id": 1, "a": "pear"},
            {"_id": 2, "a": None},
            {"_id": 3, "b": "other"},
            {"_id": 4, "a": "apple"},
        ],
        expected=[
            {"_id": 2, "a": None},
            {"_id": 3, "b": "other"},
            {"_id": 4, "a": "apple"},
        ],
        msg="$not regex should include null and missing field docs",
    ),
]

REGEX_COMBINED_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="regex_with_ne",
        filter={"a": {"$regex": "abc", "$ne": "abcdef"}},
        doc=[
            {"_id": 1, "a": "abc"},
            {"_id": 2, "a": "abcdef"},
            {"_id": 3, "a": "abcxyz"},
        ],
        expected=[{"_id": 1, "a": "abc"}, {"_id": 3, "a": "abcxyz"}],
        msg="$regex with $ne should match regex but exclude specific value",
    ),
    QueryTestCase(
        id="regex_with_exists",
        filter={"a": {"$regex": "abc", "$exists": True}},
        doc=[
            {"_id": 1, "a": "abc"},
            {"_id": 2, "b": "abc"},
        ],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex with $exists should combine conditions",
    ),
    QueryTestCase(
        id="regex_with_type_string",
        filter={"a": {"$regex": "abc", "$type": "string"}},
        doc=[
            {"_id": 1, "a": "abc"},
            {"_id": 2, "a": 123},
        ],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex with $type string should match (redundant but valid)",
    ),
    QueryTestCase(
        id="regex_with_nin",
        filter={"a": {"$regex": "acme.*corp", "$options": "i", "$nin": ["acmeblahcorp"]}},
        doc=[
            {"_id": 1, "a": "AcmeCorp"},
            {"_id": 2, "a": "acmeblahcorp"},
            {"_id": 3, "a": "AcmeXCorp"},
        ],
        expected=[{"_id": 1, "a": "AcmeCorp"}, {"_id": 3, "a": "AcmeXCorp"}],
        msg="$regex with $nin should match regex but exclude specific values",
    ),
    QueryTestCase(
        id="regex_in_all",
        filter={"a": {"$all": [Regex("^abc"), Regex("xyz$")]}},
        doc=[
            {"_id": 1, "a": "abcxyz"},
            {"_id": 2, "a": "abc"},
            {"_id": 3, "a": "xyz"},
        ],
        expected=[{"_id": 1, "a": "abcxyz"}],
        msg="$regex in $all should require all patterns to match",
    ),
]


REGEX_LOGICAL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="and_two_regex_patterns",
        filter={"$and": [{"a": {"$regex": "^abc"}}, {"a": {"$regex": "xyz$"}}]},
        doc=[
            {"_id": 1, "a": "abcxyz"},
            {"_id": 2, "a": "abc"},
            {"_id": 3, "a": "xyz"},
        ],
        expected=[{"_id": 1, "a": "abcxyz"}],
        msg="$and with two $regex should require both patterns to match",
    ),
    QueryTestCase(
        id="or_two_regex_patterns",
        filter={"$or": [{"a": {"$regex": "^abc"}}, {"a": {"$regex": "^xyz"}}]},
        doc=[
            {"_id": 1, "a": "abc123"},
            {"_id": 2, "a": "xyz456"},
            {"_id": 3, "a": "other"},
        ],
        expected=[{"_id": 1, "a": "abc123"}, {"_id": 2, "a": "xyz456"}],
        msg="$or with two $regex should match either pattern",
    ),
    QueryTestCase(
        id="nor_regex_pattern",
        filter={"$nor": [{"a": {"$regex": "^abc"}}, {"a": {"$regex": "^xyz"}}]},
        doc=[
            {"_id": 1, "a": "abc123"},
            {"_id": 2, "a": "xyz456"},
            {"_id": 3, "a": "other"},
        ],
        expected=[{"_id": 3, "a": "other"}],
        msg="$nor with $regex should exclude docs matching any pattern",
    ),
]

REGEX_ELEMMATCH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="elemMatch_with_regex",
        filter={"a": {"$elemMatch": {"$regex": "^abc"}}},
        doc=[
            {"_id": 1, "a": ["abc123", "def456"]},
            {"_id": 2, "a": ["def456"]},
        ],
        expected=[{"_id": 1, "a": ["abc123", "def456"]}],
        msg="$elemMatch with $regex should match array element",
    ),
    QueryTestCase(
        id="elemMatch_regex_case_insensitive",
        filter={"a": {"$elemMatch": {"$regex": "^ABC", "$options": "i"}}},
        doc=[
            {"_id": 1, "a": ["abc123", "def"]},
            {"_id": 2, "a": ["xyz"]},
        ],
        expected=[{"_id": 1, "a": ["abc123", "def"]}],
        msg="$elemMatch with case-insensitive $regex should match",
    ),
    QueryTestCase(
        id="elemMatch_regex_with_nin",
        filter={"a": {"$elemMatch": {"$regex": "^abc", "$nin": ["abc000"]}}},
        doc=[
            {"_id": 1, "a": ["abc123", "def"]},
            {"_id": 2, "a": ["abc000"]},
        ],
        expected=[{"_id": 1, "a": ["abc123", "def"]}],
        msg="$elemMatch with $regex and $nin should combine conditions",
    ),
]
ALL_TESTS = (
    MOD_COMBINATION_TESTS
    + REGEX_IN_TESTS
    + REGEX_NOT_TESTS
    + REGEX_COMBINED_OPERATOR_TESTS
    + REGEX_LOGICAL_TESTS
    + REGEX_ELEMMATCH_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_query_combination_misc_operators(collection, test):
    """Parametrized test for misc query operator combinations."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
