"""Tests for distinct command key field behavior."""

from __future__ import annotations

from functools import reduce
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null Field Value]: when a document has an explicit null value for the
# key field, null appears in the distinct values; missing fields are silently skipped.
DISTINCT_NULL_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_explicit_null_included",
        docs=[{"_id": 1, "x": None}, {"_id": 2, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [None, "a"], "ok": 1.0},
        msg="distinct should include explicit null in results",
    ),
    CommandTestCase(
        "null_missing_field_skipped",
        docs=[{"_id": 1, "y": "a"}, {"_id": 2, "y": "b"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should return empty when all documents are missing the key field",
    ),
    CommandTestCase(
        "null_missing_does_not_contribute_null",
        docs=[{"_id": 1}, {"_id": 2, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should not add null for documents missing the key field",
    ),
    CommandTestCase(
        "null_explicit_null_deduplicated",
        docs=[{"_id": 1, "x": None}, {"_id": 2, "x": None}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [None], "ok": 1.0},
        msg="distinct should deduplicate multiple explicit null values",
    ),
    CommandTestCase(
        "null_mixed_null_and_missing",
        docs=[{"_id": 1, "x": None}, {"_id": 2}, {"_id": 3, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [None, "a"], "ok": 1.0},
        msg="distinct should include explicit null but skip missing fields",
    ),
]

# Property [Dot Notation and Field Path Traversal]: the key parameter supports
# dot notation to traverse nested document structures.
DISTINCT_DOT_NOTATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "dot_embedded_document",
        docs=[
            {"_id": 1, "item": {"sku": "abc"}},
            {"_id": 2, "item": {"sku": "def"}},
            {"_id": 3, "item": {"sku": "abc"}},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "item.sku"},
        expected={"values": ["abc", "def"], "ok": 1.0},
        msg="distinct should access fields within embedded documents via dot notation",
    ),
    CommandTestCase(
        "dot_numeric_array_index",
        docs=[
            {"_id": 1, "temps": [{"value": 10}, {"value": 20}]},
            {"_id": 2, "temps": [{"value": 30}, {"value": 40}]},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "temps.1.value"},
        expected={"values": [20, 40], "ok": 1.0},
        msg="distinct should use numeric path components to address array positions",
    ),
    CommandTestCase(
        "dot_descend_into_array_of_objects",
        docs=[
            {"_id": 1, "items": [{"name": "a"}, {"name": "b"}]},
            {"_id": 2, "items": [{"name": "b"}, {"name": "c"}]},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "items.name"},
        expected={"values": ["a", "b", "c"], "ok": 1.0},
        msg=(
            "distinct should descend into array elements to extract"
            " nested fields from each object"
        ),
    ),
    CommandTestCase(
        "dot_multi_level_array_traversal",
        docs=[
            {"_id": 1, "a": [{"b": [{"c": 1}, {"c": 2}]}, {"b": [{"c": 3}]}]},
            {"_id": 2, "a": [{"b": [{"c": 2}, {"c": 4}]}]},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "a.b.c"},
        expected={"values": [1, 2, 3, 4], "ok": 1.0},
        msg="distinct should traverse multiple levels of nested arrays",
    ),
    CommandTestCase(
        "dot_leading_dot_empty",
        docs=[{"_id": 1, "x": "hello"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": ".x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should return empty results for a key with a leading dot",
    ),
    CommandTestCase(
        "dot_trailing_dot_empty",
        docs=[{"_id": 1, "x": "hello"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x."},
        expected={"values": [], "ok": 1.0},
        msg="distinct should return empty results for a key with a trailing dot",
    ),
    CommandTestCase(
        "dot_consecutive_dots_empty",
        docs=[{"_id": 1, "x": {"y": "hello"}}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x..y"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should return empty results for a key with consecutive dots",
    ),
    CommandTestCase(
        "dot_negative_numeric_empty",
        docs=[{"_id": 1, "arr": ["a", "b", "c"]}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "arr.-1"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should return empty results for negative numeric path components",
    ),
    CommandTestCase(
        "dot_out_of_bounds_empty",
        docs=[{"_id": 1, "arr": ["a", "b", "c"]}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "arr.99"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should return empty results for out-of-bounds numeric path components",
    ),
    CommandTestCase(
        "dot_beyond_int32_literal_field_name",
        docs=[{"_id": 1, "data": {"2147483648": "found"}}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "data.2147483648"},
        expected={"values": ["found"], "ok": 1.0},
        msg="distinct should treat numeric components beyond int32 range as literal field names",
    ),
    CommandTestCase(
        "dot_deeply_nested_accepted",
        docs=[{"_id": 1, **reduce(lambda inner, _: {"n": inner}, range(100), {"val": "deep"})}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": ".".join(["n"] * 100 + ["val"]),
        },
        expected={"values": ["deep"], "ok": 1.0},
        msg="distinct should accept deeply nested paths with 100+ segments without error",
    ),
    CommandTestCase(
        "dot_mixed_object_and_array_at_path",
        docs=[
            {"_id": 1, "x": {"y": "from_obj"}},
            {"_id": 2, "x": [{"y": "from_arr1"}, {"y": "from_arr2"}]},
            {"_id": 3, "x": "scalar"},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x.y"},
        expected={"values": ["from_arr1", "from_arr2", "from_obj"], "ok": 1.0},
        msg=(
            "distinct should traverse both objects and arrays at the same path"
            " across different documents"
        ),
    ),
    CommandTestCase(
        "dot_numeric_on_mixed_object_and_array",
        docs=[
            {"_id": 1, "data": ["arr_zero", "arr_one"]},
            {"_id": 2, "data": {"0": "obj_zero", "1": "obj_one"}},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "data.0"},
        expected={"values": ["arr_zero", "obj_zero"], "ok": 1.0},
        msg=(
            "distinct should match numeric path component as both array index"
            " and literal field name across documents"
        ),
    ),
]

# Property [Key Field Special Characters]: dollar signs, whitespace, Unicode
# characters, and empty string are treated as literal field name characters in
# the key parameter.
DISTINCT_SPECIAL_CHARS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "special_dollar_in_key",
        docs=[{"_id": 1, "$price": 9.99}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "$price"},
        expected={"values": [9.99], "ok": 1.0},
        msg="distinct should treat dollar sign in key as a literal field name character",
    ),
    CommandTestCase(
        "special_dollar_only",
        docs=[{"_id": 1, "x": "hello"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "$"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should succeed with $ as entire key (returns empty if no matching field)",
    ),
    CommandTestCase(
        "special_double_dollar",
        docs=[{"_id": 1, "x": "hello"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "$$"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should succeed with $$ as entire key (returns empty if no matching field)",
    ),
    CommandTestCase(
        "special_space_in_key",
        docs=[{"_id": 1, "my field": "space_value"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "my field"},
        expected={"values": ["space_value"], "ok": 1.0},
        msg="distinct should accept space characters in key field names",
    ),
    CommandTestCase(
        "special_tab_in_key",
        docs=[{"_id": 1, "tab\tfield": "tab_value"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "tab\tfield"},
        expected={"values": ["tab_value"], "ok": 1.0},
        msg="distinct should accept tab characters in key field names",
    ),
    CommandTestCase(
        "special_newline_in_key",
        docs=[{"_id": 1, "new\nline": "newline_value"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "new\nline"},
        expected={"values": ["newline_value"], "ok": 1.0},
        msg="distinct should accept newline characters in key field names",
    ),
    CommandTestCase(
        "special_cjk_in_key",
        # CJK Unified Ideographs.
        docs=[{"_id": 1, "\u65e5\u672c\u8a9e": "cjk_value"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "\u65e5\u672c\u8a9e"},
        expected={"values": ["cjk_value"], "ok": 1.0},
        msg="distinct should accept CJK characters in key field names",
    ),
    CommandTestCase(
        "special_emoji_in_key",
        docs=[{"_id": 1, "\U0001f389": "emoji_value"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "\U0001f389"},
        expected={"values": ["emoji_value"], "ok": 1.0},
        msg="distinct should accept emoji characters in key field names",
    ),
    CommandTestCase(
        "special_combining_mark_in_key",
        # U+0065 U+0301 (e + combining acute accent).
        docs=[{"_id": 1, "e\u0301": "combining_value"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "e\u0301"},
        expected={"values": ["combining_value"], "ok": 1.0},
        msg="distinct should accept combining mark characters in key field names",
    ),
    CommandTestCase(
        "special_empty_string_key",
        docs=[{"_id": 1, "": "empty_key_value"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": ""},
        expected={"values": ["empty_key_value"], "ok": 1.0},
        msg='distinct should match documents with a field literally named ""',
    ),
]

# Property [Distinct on _id Field]: the _id field can be used as the key
# parameter and returns the distinct _id values.
DISTINCT_ID_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "id_field_as_key",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}, {"_id": 3, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "_id"},
        expected={"values": [1, 2, 3], "ok": 1.0},
        msg="distinct should return all _id values when key is '_id'",
    ),
    CommandTestCase(
        "id_field_dot_notation",
        docs=[
            {"_id": {"a": 1, "b": 2}, "x": "hello"},
            {"_id": {"a": 1, "b": 3}, "x": "world"},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "_id.a"},
        expected={"values": [1], "ok": 1.0},
        msg="distinct should support dot notation into compound _id fields",
    ),
]

DISTINCT_KEY_FIELD_TESTS: list[CommandTestCase] = (
    DISTINCT_NULL_FIELD_TESTS
    + DISTINCT_DOT_NOTATION_TESTS
    + DISTINCT_SPECIAL_CHARS_TESTS
    + DISTINCT_ID_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DISTINCT_KEY_FIELD_TESTS))
def test_distinct_key_field(database_client: Any, collection: Any, test: CommandTestCase) -> None:
    """Test distinct key field cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
        ignore_order_in=test.ignore_order_in,
    )
