"""Tests for count command hint behavior and type strictness."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    NO_QUERY_EXECUTION_PLANS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ViewCollection

# Property [Hint Behavior]: the count command uses the specified hint to
# select which index to use for query execution.
COUNT_HINT_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_default_id_by_name",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "hint": "_id_"},
        expected={"n": 5, "ok": 1.0},
        msg="count should accept the default _id_ index by name",
    ),
    CommandTestCase(
        "hint_default_id_by_key_pattern",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "hint": {"_id": 1}},
        expected={"n": 5, "ok": 1.0},
        msg="count should accept the default _id index by key pattern",
    ),
    CommandTestCase(
        "hint_string_by_name",
        docs=[{"_id": i, "x": i} for i in range(5)],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {"count": ctx.collection, "hint": "x_1"},
        expected={"n": 5, "ok": 1.0},
        msg="count should accept a string hint specifying an index by name",
    ),
    CommandTestCase(
        "hint_string_case_sensitive",
        docs=[{"_id": i, "x": i} for i in range(5)],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {"count": ctx.collection, "hint": "X_1"},
        error_code=BAD_VALUE_ERROR,
        msg="count string hint should be case-sensitive",
    ),
    CommandTestCase(
        "hint_string_no_trimming",
        docs=[{"_id": i, "x": i} for i in range(5)],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {"count": ctx.collection, "hint": " x_1 "},
        error_code=BAD_VALUE_ERROR,
        msg="count string hint should not trim whitespace",
    ),
    CommandTestCase(
        "hint_doc_key_pattern",
        docs=[{"_id": i, "x": i} for i in range(5)],
        indexes=[IndexModel([("x", 1)])],
        command=lambda ctx: {"count": ctx.collection, "hint": {"x": 1}},
        expected={"n": 5, "ok": 1.0},
        msg="count should accept a document hint specifying an index by key pattern",
    ),
    CommandTestCase(
        "hint_doc_compound_order_matters",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        indexes=[IndexModel([("a", 1), ("b", 1)])],
        command=lambda ctx: {"count": ctx.collection, "hint": {"b": 1, "a": 1}},
        error_code=BAD_VALUE_ERROR,
        msg="count document hint should require correct field order for compound indexes",
    ),
    CommandTestCase(
        "hint_empty_doc",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "hint": {}},
        expected={"n": 5, "ok": 1.0},
        msg="count with empty document hint should be treated as no hint",
    ),
    CommandTestCase(
        "hint_natural_forward",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "hint": {"$natural": 1}},
        expected={"n": 5, "ok": 1.0},
        msg='count should accept {"$natural": 1} as a document hint',
    ),
    CommandTestCase(
        "hint_natural_reverse",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "hint": {"$natural": -1}},
        expected={"n": 5, "ok": 1.0},
        msg='count should accept {"$natural": -1} as a document hint',
    ),
    CommandTestCase(
        "hint_direction_int64",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "hint": {"$natural": Int64(1)}},
        expected={"n": 5, "ok": 1.0},
        msg="count document hint should accept Int64 direction value",
    ),
    CommandTestCase(
        "hint_direction_double",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "hint": {"$natural": 1.0}},
        expected={"n": 5, "ok": 1.0},
        msg="count document hint should accept double direction value",
    ),
    CommandTestCase(
        "hint_direction_decimal128",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "hint": {"$natural": Decimal128("1")},
        },
        expected={"n": 5, "ok": 1.0},
        msg="count document hint should accept Decimal128 direction value",
    ),
    CommandTestCase(
        "hint_direction_decimal128_neg",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "hint": {"$natural": Decimal128("-1")},
        },
        expected={"n": 5, "ok": 1.0},
        msg="count document hint should accept Decimal128(-1) direction value",
    ),
    CommandTestCase(
        "hint_nonexistent_collection_string",
        docs=None,
        command=lambda ctx: {"count": ctx.collection, "hint": "any_index"},
        expected={"n": 0, "ok": 1.0},
        msg="count on non-existent collection should accept any string hint",
    ),
    CommandTestCase(
        "hint_nonexistent_collection_doc",
        docs=None,
        command=lambda ctx: {"count": ctx.collection, "hint": {"a": 1}},
        expected={"n": 0, "ok": 1.0},
        msg="count on non-existent collection should accept any document hint",
    ),
    CommandTestCase(
        "hint_sparse_index",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": 2},
            {"_id": 3},
            {"_id": 4, "x": None},
            {"_id": 5},
        ],
        indexes=[IndexModel([("x", 1)], name="x_sparse", sparse=True)],
        command=lambda ctx: {"count": ctx.collection, "hint": "x_sparse"},
        expected={"n": 3, "ok": 1.0},
        msg="count with sparse index hint should only count documents with the indexed field",
    ),
    CommandTestCase(
        "hint_partial_filter",
        docs=[
            {"_id": 1, "x": 1, "status": "active"},
            {"_id": 2, "x": 2, "status": "active"},
            {"_id": 3, "x": 3, "status": "inactive"},
            {"_id": 4, "x": 4, "status": "active"},
            {"_id": 5, "x": 5, "status": "inactive"},
        ],
        indexes=[
            IndexModel(
                [("x", 1)],
                name="x_partial",
                partialFilterExpression={"status": "active"},
            )
        ],
        command=lambda ctx: {"count": ctx.collection, "hint": "x_partial"},
        expected={"n": 3, "ok": 1.0},
        msg="count with partial filter index hint should only count documents matching the filter",
    ),
]

# Property [Hint Validation Errors]: invalid hint values produce an error.
COUNT_HINT_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_err_natural_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": "$natural"},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject $natural as a string hint",
    ),
    CommandTestCase(
        "hint_err_natural_combined_with_other_field",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "hint": {"$natural": 1, "x": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject $natural combined with other fields in a document hint",
    ),
    CommandTestCase(
        "hint_err_direction_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": {"$natural": 0}},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject zero as a direction value in document hint",
    ),
    CommandTestCase(
        "hint_err_direction_fractional",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": {"$natural": 0.5}},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject non-integer direction value in document hint",
    ),
    CommandTestCase(
        "hint_err_direction_out_of_range",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": {"$natural": 2}},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject out-of-range direction value in document hint",
    ),
    CommandTestCase(
        "hint_err_direction_boolean",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": {"$natural": True}},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject boolean direction value in document hint",
    ),
    CommandTestCase(
        "hint_err_direction_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": {"$natural": None}},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject null direction value in document hint",
    ),
    CommandTestCase(
        "hint_err_direction_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "hint": {"$natural": "forward"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject string direction value in document hint",
    ),
    CommandTestCase(
        "hint_err_nonexistent_index_name",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": "nonexistent_idx"},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject a non-existent index name on an existing collection",
    ),
    CommandTestCase(
        "hint_err_nonexistent_index_spec",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": {"z": 1}},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject a non-existent index spec on an existing collection",
    ),
    CommandTestCase(
        "hint_err_nonexistent_index_empty_collection",
        docs=[],
        command=lambda ctx: {"count": ctx.collection, "hint": "nonexistent_idx"},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject a non-existent index name on an empty collection",
    ),
]

COUNT_HINT_TESTS = COUNT_HINT_BEHAVIOR_TESTS + COUNT_HINT_VALIDATION_ERROR_TESTS

# Property [Type Strictness: hint]: only string and document types are accepted
# for the hint field; all other BSON types produce a FailedToParse error.
COUNT_TYPE_STRICTNESS_HINT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_hint_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": 42},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject int32 for hint",
    ),
    CommandTestCase(
        "type_hint_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": Int64(1)},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject Int64 for hint",
    ),
    CommandTestCase(
        "type_hint_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": 3.14},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject double for hint",
    ),
    CommandTestCase(
        "type_hint_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": Decimal128("1")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject Decimal128 for hint",
    ),
    CommandTestCase(
        "type_hint_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": True},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject bool for hint",
    ),
    CommandTestCase(
        "type_hint_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": None},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject null for hint",
    ),
    CommandTestCase(
        "type_hint_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": [1, 2]},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject array for hint",
    ),
    CommandTestCase(
        "type_hint_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": ObjectId()},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject ObjectId for hint",
    ),
    CommandTestCase(
        "type_hint_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "hint": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject datetime for hint",
    ),
    CommandTestCase(
        "type_hint_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": Timestamp(1, 1)},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject Timestamp for hint",
    ),
    CommandTestCase(
        "type_hint_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "hint": Binary(b"\x01\x02"),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject Binary for hint",
    ),
    CommandTestCase(
        "type_hint_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": Regex("^abc")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject Regex for hint",
    ),
    CommandTestCase(
        "type_hint_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "hint": Code("function(){}"),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject Code for hint",
    ),
    CommandTestCase(
        "type_hint_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "hint": Code("function(){}", {"x": 1}),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject Code with scope for hint",
    ),
    CommandTestCase(
        "type_hint_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": MinKey()},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject MinKey for hint",
    ),
    CommandTestCase(
        "type_hint_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "hint": MaxKey()},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject MaxKey for hint",
    ),
]

# Property [Text Search and Hint Interaction]: a $text query combined with a
# hint produces an error, but an empty document hint {} is exempt from this
# restriction.
COUNT_TEXT_SEARCH_HINT_INTERACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "text_hint_error",
        docs=[{"_id": 1, "s": "hello world"}, {"_id": 2, "s": "foo bar"}],
        indexes=[IndexModel([("s", "text")])],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"$text": {"$search": "hello"}},
            "hint": "s_text",
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject $text query combined with a hint",
    ),
    CommandTestCase(
        "text_hint_empty_doc_exempt",
        docs=[{"_id": 1, "s": "hello world"}, {"_id": 2, "s": "foo bar"}],
        indexes=[IndexModel([("s", "text")])],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"$text": {"$search": "hello"}},
            "hint": {},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should allow $text query with empty document hint",
    ),
]

# Property [Hint on View Errors]: a hint referencing a non-existent index on a
# view produces an error.
COUNT_HINT_ON_VIEW_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_view_nonexistent_index_string",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(3)],
        command=lambda ctx: {"count": ctx.collection, "hint": "nonexistent_idx"},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject a non-existent index name hint on a view",
    ),
    CommandTestCase(
        "hint_view_nonexistent_index_doc",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(3)],
        command=lambda ctx: {"count": ctx.collection, "hint": {"z": 1}},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject a non-existent index spec hint on a view",
    ),
]

# Property [Wildcard Index Hint]: a wildcard index hint without a query produces
# an error because the planner cannot generate a plan from a wildcard index alone.
COUNT_WILDCARD_INDEX_HINT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wildcard_hint_no_query",
        docs=[{"_id": i, "x": i} for i in range(5)],
        indexes=[IndexModel([("$**", 1)], name="wildcard_all")],
        command=lambda ctx: {"count": ctx.collection, "hint": "wildcard_all"},
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="count with wildcard index hint without a query should produce an error",
    ),
]

COUNT_HINT_ALL_TESTS: list[CommandTestCase] = (
    COUNT_HINT_TESTS
    + COUNT_TYPE_STRICTNESS_HINT_TESTS
    + COUNT_TEXT_SEARCH_HINT_INTERACTION_TESTS
    + COUNT_HINT_ON_VIEW_ERROR_TESTS
    + COUNT_WILDCARD_INDEX_HINT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_HINT_ALL_TESTS))
def test_count_hint(database_client, collection, test):
    """Test count command hint behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
