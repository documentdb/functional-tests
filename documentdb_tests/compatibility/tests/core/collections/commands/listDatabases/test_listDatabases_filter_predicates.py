"""Tests for listDatabases filter query predicates."""

from __future__ import annotations

import functools
from typing import Any

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import OVERFLOW_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Eq, Len, NotContains

# Property [Filter Query Predicate Support]: the filter parameter
# accepts standard query predicates that correctly select databases by
# matching against per-database fields (name, sizeOnDisk, empty), and
# returns empty results for unknown or response-level fields.
FILTER_QUERY_PREDICATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "filter": {}},
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="Empty filter should return all databases",
        id="filter_empty_doc",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": {"name": "admin"}},
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="Implicit $eq on name should match",
        id="filter_eq_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$ne": "admin"}},
        },
        expected={"ok": Eq(1.0), "databases": NotContains("name", "admin")},
        msg="$ne should exclude the matched database",
        id="filter_ne_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$gt": "config"}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "local")},
        msg="$gt should return databases with name after config",
        id="filter_gt_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$gte": "config"}},
        },
        expected={"ok": Eq(1.0), "databases": NotContains("name", "admin")},
        msg="$gte should include the boundary value",
        id="filter_gte_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$lt": "config"}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$lt should return databases with name before config",
        id="filter_lt_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$lte": "config"}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "config")},
        msg="$lte should include the boundary value",
        id="filter_lte_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$in": ["admin", "local"]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "local")},
        msg="$in should match databases in the list",
        id="filter_in_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$nin": ["admin"]}},
        },
        expected={"ok": Eq(1.0), "databases": NotContains("name", "admin")},
        msg="$nin should exclude databases in the list",
        id="filter_nin_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$exists": True}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$exists true on name should match all databases",
        id="filter_exists_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"sizeOnDisk": {"$type": "number"}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$type number should match Int64 sizeOnDisk",
        id="filter_type_number_sizeondisk",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$type": -1}},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="$type with negative int should silently return no results",
        id="filter_type_negative",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$regex": "^ad"}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$regex should match name field",
        id="filter_regex_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$not": {"$eq": "admin"}}},
        },
        expected={"ok": Eq(1.0), "databases": NotContains("name", "admin")},
        msg="$not should negate the inner predicate",
        id="filter_not_eq_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"sizeOnDisk": {"$mod": [2, 0]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$mod should work on sizeOnDisk",
        id="filter_mod_sizeondisk",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$all": ["admin"]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$all on scalar name field should work",
        id="filter_all_name",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$elemMatch": {"$eq": "admin"}}},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="$elemMatch on scalar name should return 0 results",
        id="filter_elemmatch_scalar",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$size": 1}},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="$size on scalar name should return 0 results",
        id="filter_size_scalar",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"sizeOnDisk": {"$bitsAllSet": 0}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$bitsAllSet with 0 should match all sizeOnDisk values",
        id="filter_bitsallset_sizeondisk",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"sizeOnDisk": {"$bitsAnySet": 0}},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="$bitsAnySet with 0 should match no sizeOnDisk values",
        id="filter_bitsanyset_sizeondisk",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"sizeOnDisk": {"$bitsAllClear": 0}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$bitsAllClear with 0 should match all sizeOnDisk values",
        id="filter_bitsallclear_sizeondisk",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"sizeOnDisk": {"$bitsAnyClear": 0}},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="$bitsAnyClear with 0 should match no sizeOnDisk values",
        id="filter_bitsanyclear_sizeondisk",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$jsonSchema": {"properties": {"name": {"pattern": "^admin$"}}}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$jsonSchema should filter by name pattern",
        id="filter_jsonschema",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": "admin", "$comment": "test"},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$comment in filter should not affect results",
        id="filter_comment",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"unknownField": "x"},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="Unknown field in filter should return empty result",
        id="filter_unknown_field",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"totalSize": 0},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="Response-level field totalSize should return empty result",
        id="filter_response_level_field",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"empty": False},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="Filtering on empty field should work",
        id="filter_empty_field",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$gte": "admin"}, "empty": False},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="Implicit $and with multiple fields should work",
        id="filter_compound_implicit_and",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {
                "$and": [
                    {"name": {"$gte": "admin"}},
                    {"empty": False},
                ]
            },
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="Explicit $and should work",
        id="filter_compound_explicit_and",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$or": [{"name": "admin"}, {"name": "local"}]},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "local")},
        msg="$or should return databases matching either condition",
        id="filter_compound_or",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"$nor": [{"name": "admin"}]},
        },
        expected={"ok": Eq(1.0), "databases": NotContains("name", "admin")},
        msg="$nor should exclude databases matching the condition",
        id="filter_compound_nor",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": functools.reduce(
                lambda inner, _: {"$and": [inner]}, range(99), dict[str, Any]({"name": "admin"})
            ),
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="Nesting depth up to 99 levels should be accepted",
        id="filter_nesting_99",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": functools.reduce(
                lambda inner, _: {"$and": [inner]}, range(100), dict[str, Any]({"name": "admin"})
            ),
        },
        error_code=OVERFLOW_ERROR,
        msg="Nesting depth of 100 levels should be rejected",
        id="filter_nesting_100_rejected",
    ),
]

# Property [Filter Regex Support]: regex filtering works with $regex
# string, BSON Regex object, and case-insensitive $options.
FILTER_REGEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$regex": "^ad"}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$regex string should match the name field",
        id="regex_string",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": Regex("^ad")},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="BSON Regex object should match the name field",
        id="regex_bson_object",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": {"$regex": "^ADMIN", "$options": "i"}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="$options 'i' should enable case-insensitive matching",
        id="regex_options_i",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"sizeOnDisk": {"$regex": ".*"}},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="$regex on non-string field should return 0 results",
        id="regex_non_string_field",
    ),
]

FILTER_PREDICATE_TESTS: list[CommandTestCase] = FILTER_QUERY_PREDICATE_TESTS + FILTER_REGEX_TESTS


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(FILTER_PREDICATE_TESTS))
def test_listDatabases_filter_predicates(collection, test):
    """Test listDatabases filter query predicate support."""
    ctx = CommandContext.from_collection(collection)
    collection.database.create_collection(collection.name)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
