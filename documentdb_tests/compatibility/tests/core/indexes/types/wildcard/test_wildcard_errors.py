"""Tests for wildcard index error cases."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CANNOT_CREATE_INDEX_ERROR,
    CANNOT_USE_MIN_MAX_ERROR,
    FAILED_TO_PARSE_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    INDEX_NOT_FOUND_ERROR,
    INDEX_OPTIONS_CONFLICT_ERROR,
    INVALID_INDEX_SPEC_OPTION_ERROR,
    NO_QUERY_EXECUTION_PLANS_ERROR,
    PROJECT_COMPUTED_FIELD_BANNED_ERROR,
    PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
    WILDCARD_COMPOUND_PREFIX_MULTIKEY_ERROR,
    WILDCARD_COMPOUND_PREFIX_NOT_EXCLUDED_ERROR,
    WILDCARD_MULTIPLE_FIELDS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


INCOMPATIBLE_OPTION_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="unique",
        indexes=({"key": {"$**": 1}, "name": "wc", "unique": True},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard index with unique:true should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="sparse",
        indexes=({"key": {"$**": 1}, "name": "wc", "sparse": True},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard index with sparse:true should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="ttl_expireAfterSeconds",
        indexes=({"key": {"$**": 1}, "name": "wc", "expireAfterSeconds": 3600},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard index with expireAfterSeconds should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="key_type_2d",
        indexes=({"key": {"$**": "2d"}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard key with 2d type should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="key_type_2dsphere",
        indexes=({"key": {"$**": "2dsphere"}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard key with 2dsphere type should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="key_type_hashed",
        indexes=({"key": {"$**": "hashed"}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard key with hashed type should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="sort_order_zero",
        indexes=({"key": {"$**": 0}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard key with sort order 0 should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="scoped_sort_order_zero",
        indexes=({"key": {"sub.$**": 0}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Scoped wildcard key with sort order 0 should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="key_nan",
        indexes=({"key": {"$**": float("nan")}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard key with NaN direction should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="index_version_v0",
        indexes=({"key": {"$**": 1}, "name": "wc", "v": 0},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard index with v:0 should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="index_version_v1",
        indexes=({"key": {"$**": 1}, "name": "wc", "v": 1},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard index with v:1 should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="string_key_wildcard_on_dollar",
        indexes=({"key": {"$**": "wildcard"}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg='Wildcard key with string type "wildcard" should fail with CannotCreateIndex',
    ),
    IndexTestCase(
        id="string_key_hello",
        indexes=({"key": {"$**": "hello"}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard key with arbitrary string type should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="chained_wildcard_specifier",
        indexes=({"key": {"a.$**.$**": 1}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Chained wildcard specifier a.$**.$** should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="double_wildcard_specifier",
        indexes=({"key": {"$**.$**": 1}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Double wildcard specifier $**.$** should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="two_wildcard_terms_in_compound",
        indexes=({"key": {"$**": 1, "sub.$**": 1}, "name": "cwi_two_wc"},),
        expected=WILDCARD_MULTIPLE_FIELDS_ERROR,
        msg="Two wildcard terms should fail with WildcardMultipleFields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INCOMPATIBLE_OPTION_TESTS))
def test_wildcard_create_incompatible_option_fails(collection, test):
    """Verify incompatible wildcard index options/types are rejected."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.expected, msg=test.msg)


BAD_SPECIFIER_PLACEMENT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="wildcard_with_continuation",
        indexes=({"key": {"$**.a": 1}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard specifier with continuation $**.a should fail with CannotCreateIndex",
    ),
    IndexTestCase(
        id="wildcard_not_final_component",
        indexes=({"key": {"a.$**.b": 1}, "name": "wc"},),
        expected=CANNOT_CREATE_INDEX_ERROR,
        msg="Wildcard specifier not final component should fail with CannotCreateIndex",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BAD_SPECIFIER_PLACEMENT_TESTS))
def test_wildcard_create_bad_specifier_placement_fails(collection, test):
    """Verify mis-placed wildcard specifiers are rejected with CannotCreateIndex."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.expected, msg=test.msg)


INVALID_PROJECTION_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="mixed_inclusion_exclusion",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a": 1, "b": 0}},),
        expected=PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
        msg="Mixed inclusion/exclusion (no _id exception) should fail with 31254",
    ),
    IndexTestCase(
        id="empty_projection",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {}},),
        expected=FAILED_TO_PARSE_ERROR,
        msg="Empty wildcardProjection should fail with FailedToParse",
    ),
    IndexTestCase(
        id="field_path_key_with_projection",
        indexes=({"key": {"sub.$**": 1}, "name": "wc", "wildcardProjection": {"a": 1}},),
        expected=FAILED_TO_PARSE_ERROR,
        msg="Field-path wildcard key with wildcardProjection should fail with FailedToParse",
    ),
    IndexTestCase(
        id="non_wildcard_index_with_projection",
        indexes=({"key": {"a": 1}, "name": "reg", "wildcardProjection": {"a": 1}},),
        expected=BAD_VALUE_ERROR,
        msg="Non-wildcard index with wildcardProjection should fail with BadValue",
    ),
    IndexTestCase(
        id="value_string",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a": "yes"}},),
        expected=PROJECT_COMPUTED_FIELD_BANNED_ERROR,
        msg="wildcardProjection with a string value is parsed as a computed field and rejected",
    ),
    IndexTestCase(
        id="value_numeric_string",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a": "1"}},),
        expected=PROJECT_COMPUTED_FIELD_BANNED_ERROR,
        msg="wildcardProjection with a numeric-string value is a computed field and rejected",
    ),
    IndexTestCase(
        id="value_array",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a": [1]}},),
        expected=PROJECT_COMPUTED_FIELD_BANNED_ERROR,
        msg="wildcardProjection with an array value is a computed field and rejected",
    ),
    IndexTestCase(
        id="value_null",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a": None}},),
        expected=PROJECT_COMPUTED_FIELD_BANNED_ERROR,
        msg="wildcardProjection with a null value is a computed field and rejected",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_PROJECTION_TESTS))
def test_wildcard_projection_invalid(collection, test):
    """Verify invalid wildcardProjection configurations are rejected with the correct code."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.expected, msg=test.msg)


MIN_MAX_HINT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="min",
        command_options={"min": {"a": 2}},
        msg="min with wildcard hint -> 51174",
    ),
    IndexTestCase(
        id="max",
        command_options={"max": {"a": 4}},
        msg="max with wildcard hint -> 51174",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MIN_MAX_HINT_TESTS))
def test_wildcard_hint_min_max_fails(collection, test):
    """Using min/max bounds with a wildcard index hint fails with error 51174."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 5}])
    cmd = {"find": collection.name, "hint": {"$**": 1}, **test.command_options}
    result = execute_command(collection, cmd)
    assertFailureCode(result, CANNOT_USE_MIN_MAX_ERROR, msg=test.msg)


HINT_REJECTED_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="inclusion_non_projected_field",
        indexes=({"key": {"$**": 1}, "name": "wc_inc", "wildcardProjection": {"a": 1}},),
        doc=({"_id": 1, "a": 1, "b": 2},),
        filter={"b": 2},
        hint="wc_inc",
        expected=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Hinting wildcard for a non-projected field should be rejected",
    ),
    IndexQueryTestCase(
        id="exclusion_excluded_field",
        indexes=({"key": {"$**": 1}, "name": "wc_exc", "wildcardProjection": {"a": 0}},),
        doc=({"_id": 1, "a": 1, "b": 2},),
        filter={"a": 1},
        hint="wc_exc",
        expected=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Hinting wildcard for an excluded field should be rejected",
    ),
    IndexQueryTestCase(
        id="scoped_path_not_in_query",
        indexes=({"key": {"sub.$**": 1}, "name": "wc_sub"},),
        doc=({"_id": 1, "other": 1, "sub": {"x": 1}},),
        filter={"other": 1},
        hint="wc_sub",
        expected=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Hint scoped wildcard on out-of-scope path -> NoQueryExecutionPlans",
    ),
    IndexQueryTestCase(
        id="id_excluded_from_default_wildcard",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        filter={"_id": 2},
        hint="wc_all",
        expected=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Hinting default wildcard index for _id query should be rejected",
    ),
    IndexQueryTestCase(
        id="dollar_path_projection",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 5},),
        filter={"a": 5},
        hint="wc_all",
        command_options={"projection": {"$_path": 1}},
        expected=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="Projecting $_path is rejected with 16410",
    ),
    IndexQueryTestCase(
        id="nonexistent_index",
        indexes=(),
        doc=({"_id": 1, "a": 1},),
        filter={"a": 1},
        hint={"$**": 1},
        expected=BAD_VALUE_ERROR,
        msg="Hint on non-existent wildcard index -> BadValue",
    ),
]


@pytest.mark.parametrize("test", pytest_params(HINT_REJECTED_TESTS))
def test_wildcard_hint_rejected(collection, test):
    """Verify wildcard index hint rejection cases."""
    if test.indexes:
        execute_command(
            collection,
            {"createIndexes": collection.name, "indexes": list(test.indexes)},
        )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter, "hint": test.hint}
    if test.command_options:
        cmd.update(test.command_options)
    result = execute_command(collection, cmd)
    assertFailureCode(result, test.expected, msg=test.msg)


def test_wildcard_create_failure_leaves_no_index(collection):
    """A failed wildcard index creation leaves no extra index on the collection."""
    collection.insert_one({"_id": 1, "a": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"$**": 1}, "name": "wc", "unique": True}],
        },
    )
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        ["_id_"],
        transform=lambda batch: sorted(idx["name"] for idx in batch),
        msg="Failed wildcard index creation should leave only the _id index",
    )


def test_clustered_index_with_wildcard_key_fails(collection):
    """Creating a clustered collection whose clustered index key uses wildcard syntax fails."""
    name = f"{collection.name}_bad_clustered"
    result = execute_command(
        collection,
        {"create": name, "clusteredIndex": {"key": {"$**": 1}, "unique": True}},
    )
    assertFailureCode(
        result,
        INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="Clustered index with wildcard key should fail with InvalidIndexSpecificationOption",
    )


def test_wildcard_text_query_no_text_index_fails(collection):
    """A $text query on a collection with only a wildcard index fails (no text index)."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_many([{"_id": 1, "t": "hello world"}])
    result = execute_command(
        collection, {"find": collection.name, "filter": {"$text": {"$search": "hello"}}}
    )
    assertFailureCode(
        result, INDEX_NOT_FOUND_ERROR, msg="$text with only a wildcard index should fail"
    )


def test_compound_wildcard_prefix_multikey_insert_fails(collection):
    """Inserting a doc whose non-wildcard prefix field is an array fails: a compound wildcard
    index's non-wildcard prefix cannot be multikey."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "$**": 1}, "name": "cwi", "wildcardProjection": {"a": 0}}],
        },
    )
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "a": [1, 2], "b": 5}]},
    )
    assertFailureCode(
        result,
        WILDCARD_COMPOUND_PREFIX_MULTIKEY_ERROR,
        msg="Inserting an array into the compound wildcard prefix field should fail with 7246301",
    )


def test_compound_wildcard_prefix_multikey_create_fails(collection):
    """Creating a compound wildcard index fails when existing data already has an array in the
    non-wildcard prefix field."""
    collection.insert_one({"_id": 1, "a": [1, 2], "b": 5})
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "$**": 1}, "name": "cwi", "wildcardProjection": {"a": 0}}],
        },
    )
    assertFailureCode(
        result,
        WILDCARD_COMPOUND_PREFIX_MULTIKEY_ERROR,
        msg="Creating a compound wildcard over an existing multikey prefix "
        "should fail with 7246301",
    )


def test_compound_wildcard_prefix_multikey_update_fails(collection):
    """Updating the non-wildcard prefix field to an array fails after a compound wildcard index
    exists."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "$**": 1}, "name": "cwi", "wildcardProjection": {"a": 0}}],
        },
    )
    collection.insert_one({"_id": 1, "a": 1, "b": 5})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": [1, 2]}}}],
        },
    )
    assertFailureCode(
        result,
        WILDCARD_COMPOUND_PREFIX_MULTIKEY_ERROR,
        msg="Updating the compound wildcard prefix field to an array should fail with 7246301",
    )


def test_compound_wildcard_overlapping_field_not_excluded_fails(collection):
    """A compound wildcard index whose regular key field also falls in wildcard scope must
    exclude that field via wildcardProjection. Providing a projection that does not exclude the
    overlapping field fails: the wildcardProjection must exclude all regular index fields."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"a": 1, "$**": 1},
                    "name": "cwi",
                    # 'a' is a regular key field and remains in wildcard scope (only 'b' excluded).
                    "wildcardProjection": {"b": 0},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        WILDCARD_COMPOUND_PREFIX_NOT_EXCLUDED_ERROR,
        msg="Compound wildcard whose projection does not exclude the overlapping regular key "
        "field should fail with 7246209",
    )


def test_two_compound_wildcards_same_spec_different_name_conflicts(collection):
    """Two compound wildcard indexes with the same prefix and identical wildcard scope
    (same key and wildcardProjection) but different names conflict with IndexOptionsConflict."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1, "$**": 1}, "name": "cwi_first", "wildcardProjection": {"a": 0}}
            ],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1, "$**": 1}, "name": "cwi_second", "wildcardProjection": {"a": 0}}
            ],
        },
    )
    assertFailureCode(
        result,
        INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Identical compound wildcard spec under a different name should fail with "
        "IndexOptionsConflict",
    )
