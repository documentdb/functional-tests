"""
Tests for $jsonSchema keyword combinations and logical composition.

Validates combined keyword usage, enum matching, type-inapplicable keyword behavior,
collation, allOf, anyOf, oneOf, not, nested logical composition, and $jsonSchema
combined with query-level logical operators ($and, $or, $nor).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

KEYWORD_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bsontype_with_minimum",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "int", "minimum": 5}}}},
        doc=[{"_id": 1, "x": 10}, {"_id": 2, "x": 3}, {"_id": 3, "x": "hello"}],
        expected=[{"_id": 1, "x": 10}],
        msg="bsonType int combined with minimum should filter both",
    ),
    QueryTestCase(
        id="bsontype_string_with_length",
        filter={
            "$jsonSchema": {
                "properties": {"x": {"bsonType": "string", "minLength": 1, "maxLength": 100}}
            }
        },
        doc=[{"_id": 1, "x": "abc"}, {"_id": 2, "x": ""}, {"_id": 3, "x": 42}],
        expected=[{"_id": 1, "x": "abc"}],
        msg="bsonType string combined with minLength and maxLength should filter both",
    ),
    QueryTestCase(
        id="bsontype_array_with_items",
        filter={
            "$jsonSchema": {
                "properties": {
                    "x": {"bsonType": "array", "minItems": 1, "items": {"bsonType": "int"}}
                }
            }
        },
        doc=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": []}, {"_id": 3, "x": "not_array"}],
        expected=[{"_id": 1, "x": [1, 2]}],
        msg="bsonType array combined with minItems and items should filter all",
    ),
    QueryTestCase(
        id="required_properties_additionalProperties",
        filter={
            "$jsonSchema": {
                "required": ["a", "b"],
                "properties": {"_id": {}, "a": {"bsonType": "string"}, "b": {"bsonType": "int"}},
                "additionalProperties": False,
            }
        },
        doc=[
            {"_id": 1, "a": "hello", "b": 42},
            {"_id": 2, "a": "hello"},
            {"_id": 3, "a": "hello", "b": 42, "c": "extra"},
        ],
        expected=[{"_id": 1, "a": "hello", "b": 42}],
        msg="required + properties + additionalProperties should all apply",
    ),
    QueryTestCase(
        id="not_null_pattern",
        filter={"$jsonSchema": {"properties": {"x": {"not": {"bsonType": "null"}}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": None}, {"_id": 3, "x": 42}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 3, "x": 42}],
        msg="not bsonType null should reject null fields",
    ),
    QueryTestCase(
        id="enum_matches",
        filter={"$jsonSchema": {"properties": {"x": {"enum": [1, 2, 3]}}}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": 4}, {"_id": 3, "x": 2}],
        expected=[{"_id": 1, "x": 1}, {"_id": 3, "x": 2}],
        msg="enum should match values in the enum list",
    ),
    QueryTestCase(
        id="enum_mixed_types",
        filter={"$jsonSchema": {"properties": {"x": {"enum": ["a", None, 1]}}}},
        doc=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": None},
            {"_id": 3, "x": 1},
            {"_id": 4, "x": True},
        ],
        expected=[{"_id": 1, "x": "a"}, {"_id": 2, "x": None}, {"_id": 3, "x": 1}],
        msg="enum with mixed types should match string, null, and int",
    ),
    QueryTestCase(
        id="enum_single_value",
        filter={"$jsonSchema": {"properties": {"x": {"enum": [1]}}}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        expected=[{"_id": 1, "x": 1}],
        msg="enum with single value should match only that value",
    ),
    QueryTestCase(
        id="non_applicable_minimum_on_string",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 5}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 10}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 10}],
        msg="minimum on string field should pass (does not apply)",
    ),
    QueryTestCase(
        id="non_applicable_minLength_on_int",
        filter={"$jsonSchema": {"properties": {"x": {"minLength": 1}}}},
        doc=[{"_id": 1, "x": 42}, {"_id": 2, "x": "abc"}],
        expected=[{"_id": 1, "x": 42}, {"_id": 2, "x": "abc"}],
        msg="minLength on int field should pass (does not apply)",
    ),
    QueryTestCase(
        id="non_applicable_minItems_on_string",
        filter={"$jsonSchema": {"properties": {"x": {"minItems": 1}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": [1, 2]}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": [1, 2]}],
        msg="minItems on string field should pass (does not apply)",
    ),
    QueryTestCase(
        id="non_applicable_minProperties_on_array",
        filter={"$jsonSchema": {"properties": {"x": {"minProperties": 1}}}},
        doc=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": {"a": 1, "b": 2}}],
        expected=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": {"a": 1, "b": 2}}],
        msg="minProperties on array field should pass (does not apply)",
    ),
    QueryTestCase(
        id="non_applicable_required_on_non_object",
        filter={"$jsonSchema": {"properties": {"x": {"required": ["a"]}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": {"a": 1}}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": {"a": 1}}],
        msg="required on non-object field should pass (does not apply)",
    ),
    QueryTestCase(
        id="enum_with_bsontype",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "int", "enum": [1, "a"]}}}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}, {"_id": 3, "x": 2}],
        expected=[{"_id": 1, "x": 1}],
        msg="bsonType + enum should both apply — only int 1 passes both",
    ),
    QueryTestCase(
        id="not_required",
        filter={"$jsonSchema": {"properties": {"x": {"not": {"required": ["a"]}}}}},
        doc=[{"_id": 1, "x": {"a": 1}}, {"_id": 2, "x": {"b": 1}}, {"_id": 3, "x": "str"}],
        expected=[{"_id": 2, "x": {"b": 1}}],
        msg="not required should match objects where nested field is absent",
    ),
    QueryTestCase(
        id="dependencies_with_required",
        filter={"$jsonSchema": {"required": ["a"], "dependencies": {"a": ["b"]}}},
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1}, {"_id": 3, "b": 2}],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="required + dependencies — a must exist and b must follow",
    ),
    QueryTestCase(
        id="patternProperties_with_additionalProperties_false",
        filter={
            "$jsonSchema": {
                "properties": {"_id": {}},
                "patternProperties": {"^s_": {"bsonType": "string"}},
                "additionalProperties": False,
            }
        },
        doc=[
            {"_id": 1, "s_name": "hello"},
            {"_id": 2, "s_name": "hello", "other": 1},
            {"_id": 3, "s_name": 42},
        ],
        expected=[{"_id": 1, "s_name": "hello"}],
        msg="patternProperties + additionalProperties:false — only matched fields allowed",
    ),
    QueryTestCase(
        id="items_minItems_maxItems",
        filter={
            "$jsonSchema": {
                "properties": {"x": {"items": {"minimum": 0}, "minItems": 1, "maxItems": 3}}
            }
        },
        doc=[
            {"_id": 1, "x": [1, 2]},
            {"_id": 2, "x": []},
            {"_id": 3, "x": [1, 2, 3, 4]},
            {"_id": 4, "x": [-1, 2]},
        ],
        expected=[{"_id": 1, "x": [1, 2]}],
        msg="items + minItems + maxItems — all array constraints together",
    ),
    QueryTestCase(
        id="required_with_oneOf_in_properties",
        filter={
            "$jsonSchema": {
                "required": ["x"],
                "properties": {"x": {"oneOf": [{"bsonType": "string"}, {"bsonType": "int"}]}},
            }
        },
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": [1]}, {"_id": 3}],
        expected=[{"_id": 1, "x": "hello"}],
        msg="required + oneOf — field must exist and satisfy exactly one",
    ),
    QueryTestCase(
        id="not_enum",
        filter={"$jsonSchema": {"properties": {"x": {"not": {"enum": [1, 2]}}}}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": 3}, {"_id": 3, "x": "a"}],
        expected=[{"_id": 2, "x": 3}, {"_id": 3, "x": "a"}],
        msg="not enum should match anything NOT in the list",
    ),
    QueryTestCase(
        id="multiple_jsonschema_in_and",
        filter={
            "$and": [
                {"$jsonSchema": {"properties": {"x": {"bsonType": "int"}}}},
                {"$jsonSchema": {"properties": {"x": {"minimum": 5}}}},
            ]
        },
        doc=[{"_id": 1, "x": 10}, {"_id": 2, "x": 3}, {"_id": 3, "x": "a"}],
        expected=[{"_id": 1, "x": 10}],
        msg="Multiple $jsonSchema in $and — both must pass",
    ),
]


@pytest.mark.parametrize("test", pytest_params(KEYWORD_COMBINATION_TESTS))
def test_jsonSchema_keyword_combinations(collection, test):
    """Test $jsonSchema keyword combinations and non-applicable type behavior."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


LOGICAL_COMPOSITION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="allOf_both_match",
        filter={"$jsonSchema": {"allOf": [{"required": ["a"]}, {"required": ["b"]}]}},
        doc=[{"_id": 1, "a": "hello", "b": 1}, {"_id": 2, "a": "hello"}, {"_id": 3, "b": 1}],
        expected=[{"_id": 1, "a": "hello", "b": 1}],
        msg="allOf should match documents satisfying all sub-schemas",
    ),
    QueryTestCase(
        id="allOf_conflicting_no_match",
        filter={
            "$jsonSchema": {
                "allOf": [
                    {"properties": {"x": {"bsonType": "string"}}},
                    {"properties": {"x": {"bsonType": "int"}}},
                ]
            }
        },
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}],
        expected=[],
        msg="allOf with conflicting schemas should match nothing",
    ),
    QueryTestCase(
        id="allOf_single_element",
        filter={"$jsonSchema": {"allOf": [{"required": ["a"]}]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2}],
        expected=[{"_id": 1, "a": 1}],
        msg="allOf with single sub-schema should behave like that schema alone",
    ),
    QueryTestCase(
        id="anyOf_matches_either",
        filter={
            "$jsonSchema": {
                "anyOf": [
                    {"properties": {"x": {"bsonType": "string"}}},
                    {"properties": {"x": {"bsonType": "int"}}},
                ]
            }
        },
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}, {"_id": 3, "x": [1]}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}],
        msg="anyOf should match documents satisfying at least one sub-schema",
    ),
    QueryTestCase(
        id="anyOf_none_match",
        filter={
            "$jsonSchema": {
                "anyOf": [
                    {"properties": {"x": {"bsonType": "string"}}},
                    {"properties": {"x": {"bsonType": "int"}}},
                ]
            }
        },
        doc=[{"_id": 1, "x": [1]}, {"_id": 2, "x": True}],
        expected=[],
        msg="anyOf should reject documents satisfying no sub-schemas",
    ),
    QueryTestCase(
        id="oneOf_exactly_one",
        filter={
            "$jsonSchema": {"properties": {"x": {"oneOf": [{"multipleOf": 3}, {"multipleOf": 5}]}}}
        },
        doc=[{"_id": 1, "x": 3}, {"_id": 2, "x": 5}, {"_id": 3, "x": 15}, {"_id": 4, "x": 7}],
        expected=[{"_id": 1, "x": 3}, {"_id": 2, "x": 5}],
        msg="oneOf should match documents satisfying exactly one sub-schema",
    ),
    QueryTestCase(
        id="oneOf_both_match_rejected",
        filter={
            "$jsonSchema": {"properties": {"x": {"oneOf": [{"multipleOf": 3}, {"multipleOf": 5}]}}}
        },
        doc=[{"_id": 1, "x": 15}, {"_id": 2, "x": 3}],
        expected=[{"_id": 2, "x": 3}],
        msg="oneOf should reject documents satisfying more than one sub-schema",
    ),
    QueryTestCase(
        id="oneOf_none_match_rejected",
        filter={
            "$jsonSchema": {"properties": {"x": {"oneOf": [{"multipleOf": 3}, {"multipleOf": 5}]}}}
        },
        doc=[{"_id": 1, "x": 7}],
        expected=[],
        msg="oneOf should reject documents satisfying zero sub-schemas",
    ),
    QueryTestCase(
        id="not_matches_non_matching",
        filter={"$jsonSchema": {"properties": {"x": {"not": {"bsonType": "string"}}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}],
        expected=[{"_id": 2, "x": 42}],
        msg="not should match documents that do not satisfy the sub-schema",
    ),
    QueryTestCase(
        id="not_empty_matches_none",
        filter={"$jsonSchema": {"not": {}}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        expected=[],
        msg="not with empty schema should reject all documents",
    ),
    QueryTestCase(
        id="double_negation",
        filter={"$jsonSchema": {"properties": {"x": {"not": {"not": {"bsonType": "string"}}}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}],
        expected=[{"_id": 1, "x": "hello"}],
        msg="not-not should be equivalent to the original schema",
    ),
    QueryTestCase(
        id="nested_allOf_within_anyOf",
        filter={
            "$jsonSchema": {
                "properties": {
                    "x": {
                        "anyOf": [
                            {"allOf": [{"minimum": 5}, {"maximum": 8}]},
                            {"allOf": [{"minimum": 9}, {"maximum": 11}]},
                        ]
                    }
                }
            }
        },
        doc=[{"_id": 1, "x": 6}, {"_id": 2, "x": 10}, {"_id": 3, "x": 7}],
        expected=[{"_id": 1, "x": 6}, {"_id": 2, "x": 10}, {"_id": 3, "x": 7}],
        msg="Nested allOf within anyOf should work correctly",
    ),
    QueryTestCase(
        id="find_with_and",
        filter={
            "$and": [
                {"$jsonSchema": {"properties": {"x": {"bsonType": "int"}}}},
                {"x": {"$gt": 5}},
            ]
        },
        doc=[{"_id": 1, "x": 10}, {"_id": 2, "x": 3}, {"_id": 3, "x": "a"}],
        expected=[{"_id": 1, "x": 10}],
        msg="$jsonSchema combined with $and should work",
    ),
    QueryTestCase(
        id="find_with_or",
        filter={
            "$or": [
                {"$jsonSchema": {"properties": {"x": {"bsonType": "string"}}}},
                {"$jsonSchema": {"properties": {"x": {"bsonType": "int"}}}},
            ]
        },
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}, {"_id": 3, "x": [1]}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}],
        msg="$jsonSchema combined with $or should work",
    ),
    QueryTestCase(
        id="find_with_nor",
        filter={"$nor": [{"$jsonSchema": {"properties": {"x": {"bsonType": "string"}}}}]},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}],
        expected=[{"_id": 2, "x": 42}],
        msg="$jsonSchema combined with $nor should work",
    ),
    QueryTestCase(
        id="find_implicit_and",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "int"}}}, "x": {"$gt": 5}},
        doc=[{"_id": 1, "x": 10}, {"_id": 2, "x": 3}, {"_id": 3, "x": "a"}],
        expected=[{"_id": 1, "x": 10}],
        msg="$jsonSchema with sibling field predicate (implicit $and) should work",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LOGICAL_COMPOSITION_TESTS))
def test_jsonSchema_logical_composition(collection, test):
    """Test $jsonSchema logical composition keywords."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


def test_jsonSchema_enum_ignores_collation(database_client):
    """Test $jsonSchema enum does not respect collection-default case-insensitive collation."""
    coll_name = "test_collation_enum"
    database_client.drop_collection(coll_name)
    database_client.command(
        {
            "create": coll_name,
            "collation": {"locale": "en", "strength": 2},
        }
    )
    try:
        coll = database_client[coll_name]
        coll.insert_many([{"_id": 1, "x": "ABC"}, {"_id": 2, "x": "abc"}, {"_id": 3, "x": "def"}])
        result = execute_command(
            coll,
            {
                "find": coll_name,
                "filter": {"$jsonSchema": {"properties": {"x": {"enum": ["abc"]}}}},
            },
        )
        # $jsonSchema enum does NOT respect collation — only exact match
        assertSuccess(result, [{"_id": 2, "x": "abc"}])
    finally:
        database_client.drop_collection(coll_name)


def test_jsonSchema_uniqueItems_ignores_collation(database_client):
    """Test $jsonSchema uniqueItems does not respect case-insensitive collation."""
    coll_name = "test_collation_uniqueItems"
    database_client.drop_collection(coll_name)
    database_client.command(
        {
            "create": coll_name,
            "collation": {"locale": "en", "strength": 2},
        }
    )
    try:
        coll = database_client[coll_name]
        coll.insert_many(
            [
                {"_id": 1, "x": ["abc", "ABC"]},
                {"_id": 2, "x": ["abc", "def"]},
            ]
        )
        result = execute_command(
            coll,
            {
                "find": coll_name,
                "filter": {"$jsonSchema": {"properties": {"x": {"uniqueItems": True}}}},
            },
        )
        # uniqueItems uses binary comparison, ignores collation — "abc" and "ABC" are distinct
        assertSuccess(result, [{"_id": 1, "x": ["abc", "ABC"]}, {"_id": 2, "x": ["abc", "def"]}])
    finally:
        database_client.drop_collection(coll_name)
