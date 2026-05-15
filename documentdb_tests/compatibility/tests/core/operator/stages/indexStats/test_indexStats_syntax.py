"""Tests for $indexStats syntax validation."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INDEX_STATS_ARG_ERROR,
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [Non-Empty Document]: any non-empty document argument to
# $indexStats produces INDEX_STATS_ARG_ERROR, regardless of key names or
# values.
NON_EMPTY_DOC_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {"unknown": 1}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="unknown_field",
        msg="Non-empty document with unknown field should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {"a": None}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="null_value",
        msg="Non-empty document with null value should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {"a": {}}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="nested_empty_doc",
        msg="Non-empty document with nested empty doc should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {"$foo": 1}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="dollar_prefixed_key",
        msg="Non-empty document with $-prefixed key should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {"a.b": 1}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="dot_notation_key",
        msg="Non-empty document with dot-notation key should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {"_id": 1}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="id_key",
        msg="Non-empty document with _id key should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {"": 1}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="empty_string_key",
        msg="Non-empty document with empty string key should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {"a": 1, "b": 2}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="multiple_keys",
        msg="Non-empty document with multiple keys should be rejected",
    ),
]

# Property [Non-Document Types]: all non-document BSON types produce
# INDEX_STATS_ARG_ERROR.
NON_DOCUMENT_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": "hello"}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="string",
        msg="String argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": 42}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="int32",
        msg="Int32 argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": Int64(42)}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="int64",
        msg="Int64 argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": 3.14}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="double",
        msg="Double argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": DECIMAL128_ONE_AND_HALF}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="decimal128",
        msg="Decimal128 argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": True}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="bool",
        msg="Bool argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": None}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="null",
        msg="Null argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": [1, 2]}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="array",
        msg="Array argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": ObjectId()}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="objectid",
        msg="ObjectId argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": datetime(2024, 1, 1)}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="datetime",
        msg="Datetime argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": Timestamp(1, 1)}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="timestamp",
        msg="Timestamp argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": Binary(b"\x00")}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="binary",
        msg="Binary argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": Regex(".*")}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="regex",
        msg="Regex argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": Code("function(){}")}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="code",
        msg="Code argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": Code("function(){}", {})}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="code_with_scope",
        msg="Code with scope argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": MinKey()}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="minkey",
        msg="MinKey argument should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": MaxKey()}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="maxkey",
        msg="MaxKey argument should be rejected",
    ),
]

# Property [Expression-Like Objects]: expression-like documents are not
# evaluated and produce INDEX_STATS_ARG_ERROR.
EXPRESSION_LIKE_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {"$literal": {}}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="literal_expression",
        msg="$literal expression should not be evaluated",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {"$add": [1, 2]}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="add_expression",
        msg="$add expression should not be evaluated",
    ),
]

# Property [Array Variants]: array arguments of any shape are rejected
# with INDEX_STATS_ARG_ERROR; the stage parser does not unwrap
# single-element arrays.
ARRAY_VARIANT_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": [{}]}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="array_with_empty_doc",
        msg="Array containing empty doc should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": [None]}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="array_with_null",
        msg="Array containing null should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": [[]]}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="array_with_empty_array",
        msg="Array containing empty array should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": []}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="empty_array",
        msg="Empty array should be rejected",
    ),
]

# Property [Extra Keys in Stage Document]: any extra key alongside
# $indexStats in the stage document produces
# PIPELINE_STAGE_EXTRA_FIELD_ERROR, regardless of key order or whether
# the extra key is another stage name.
EXTRA_KEY_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {}, "extra": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        id="extra_key",
        msg="Extra key in stage document should be rejected",
    ),
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": {}, "$match": {}}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        id="extra_key_is_stage_name",
        msg="Extra key that is another stage name should be rejected",
    ),
]

# Property [Error Precedence - Extra Keys Over Argument]: extra keys in
# the stage document (PIPELINE_STAGE_EXTRA_FIELD_ERROR) take precedence
# over argument validation (INDEX_STATS_ARG_ERROR).
EXTRA_KEY_OVER_ARG_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[],
        pipeline=[{"$indexStats": "bad", "extra": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        id="extra_key_over_bad_arg",
        msg="Extra key should take precedence over invalid argument",
    ),
]

# Property [Validation on Nonexistent Collection]: argument validation
# fires even when the target collection does not exist.
VALIDATION_WITHOUT_DOCS_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=None,
        pipeline=[{"$indexStats": {"bad": 1}}],
        error_code=INDEX_STATS_ARG_ERROR,
        id="bad_arg_nonexistent_collection",
        msg="Argument error should fire on non-existent collection",
    ),
]

SYNTAX_ERROR_TESTS = (
    NON_EMPTY_DOC_TESTS
    + NON_DOCUMENT_TYPE_TESTS
    + EXPRESSION_LIKE_TESTS
    + ARRAY_VARIANT_TESTS
    + EXTRA_KEY_TESTS
    + EXTRA_KEY_OVER_ARG_TESTS
    + VALIDATION_WITHOUT_DOCS_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SYNTAX_ERROR_TESTS))
def test_indexStats_syntax_error(collection: Collection, test_case: StageTestCase):
    """Test $indexStats rejects invalid syntax."""
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
    )
