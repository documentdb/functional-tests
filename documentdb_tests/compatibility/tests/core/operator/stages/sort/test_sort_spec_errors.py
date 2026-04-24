from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)
from bson.raw_bson import RawBSONDocument

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.bson_helpers import build_raw_bson_doc
from documentdb_tests.framework.error_codes import (
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_EMPTY_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    OVERFLOW_ERROR,
    SORT_COMPOUND_KEY_LIMIT_ERROR,
    SORT_DUPLICATE_KEY_ERROR,
    SORT_EMPTY_SPEC_ERROR,
    SORT_NON_OBJECT_SPEC_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Sort Specification Validation Errors]: a non-document argument or
# an empty sort specification produces an error; non-document rejection applies
# to all BSON types.
SORT_SPEC_VALIDATION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "spec_non_document_string",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": "not_a_doc"}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a string sort specification",
    ),
    StageTestCase(
        "spec_non_document_int",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": 42}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject an integer sort specification",
    ),
    StageTestCase(
        "spec_non_document_float",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": 3.14}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a float sort specification",
    ),
    StageTestCase(
        "spec_non_document_bool",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": True}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a boolean sort specification",
    ),
    StageTestCase(
        "spec_non_document_null",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": None}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a null sort specification",
    ),
    StageTestCase(
        "spec_non_document_array",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": [1, 2]}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject an array sort specification",
    ),
    StageTestCase(
        "spec_non_document_int64",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": Int64(42)}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject an Int64 sort specification",
    ),
    StageTestCase(
        "spec_non_document_decimal128",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": Decimal128("3.14")}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a Decimal128 sort specification",
    ),
    StageTestCase(
        "spec_non_document_objectid",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": ObjectId()}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject an ObjectId sort specification",
    ),
    StageTestCase(
        "spec_non_document_datetime",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a datetime sort specification",
    ),
    StageTestCase(
        "spec_non_document_binary",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": Binary(b"\x01")}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a Binary sort specification",
    ),
    StageTestCase(
        "spec_non_document_regex",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": Regex("^abc")}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a Regex sort specification",
    ),
    StageTestCase(
        "spec_non_document_timestamp",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": Timestamp(1, 1)}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a Timestamp sort specification",
    ),
    StageTestCase(
        "spec_non_document_minkey",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": MinKey()}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a MinKey sort specification",
    ),
    StageTestCase(
        "spec_non_document_maxkey",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": MaxKey()}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a MaxKey sort specification",
    ),
    StageTestCase(
        "spec_non_document_code",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": Code("function(){}")}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a Code sort specification",
    ),
    StageTestCase(
        "spec_non_document_codewithscope",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": Code("function(){}", {"x": 1})}],
        error_code=SORT_NON_OBJECT_SPEC_ERROR,
        msg="$sort should reject a CodeWithScope sort specification",
    ),
    StageTestCase(
        "spec_empty",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {}}],
        error_code=SORT_EMPTY_SPEC_ERROR,
        msg="$sort should reject an empty sort specification",
    ),
]

# Property [Field Path Validation Errors]: invalid field paths in the sort
# specification produce errors for empty strings, leading or trailing dots,
# consecutive dots, leading dollar signs in any path component, and paths
# exceeding 200 components.
SORT_FIELD_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_path_empty_string",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"": 1}}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$sort should reject an empty string as a field path",
    ),
    StageTestCase(
        "field_path_trailing_dot",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"a.": 1}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$sort should reject a field path with a trailing dot",
    ),
    StageTestCase(
        "field_path_leading_dot",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {".a": 1}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$sort should reject a field path with a leading dot",
    ),
    StageTestCase(
        "field_path_consecutive_dots",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"a..b": 1}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$sort should reject a field path with consecutive dots",
    ),
    StageTestCase(
        "field_path_leading_dollar",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"$a": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$sort should reject a field path with a leading $ in the first component",
    ),
    StageTestCase(
        "field_path_dollar_natural",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"$natural": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$sort should reject $natural as a field path",
    ),
    StageTestCase(
        "field_path_bare_dollar",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"$": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$sort should reject a bare $ as a field path",
    ),
    StageTestCase(
        "field_path_bare_double_dollar",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"$$": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$sort should reject a bare $$ as a field path",
    ),
    StageTestCase(
        "field_path_nested_leading_dollar",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"a.$b": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$sort should reject a leading $ in a nested path component",
    ),
    StageTestCase(
        "field_path_depth_exceeds_200",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {".".join(["a"] * 201): 1}}],
        error_code=OVERFLOW_ERROR,
        msg="$sort should reject a field path exceeding 200 components",
    ),
]

# Property [Compound Sort Key Limit Errors]: more than 32 unique numeric sort
# keys produce an error.
SORT_COMPOUND_KEY_LIMIT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "compound_key_limit_33",
        docs=[{"_id": 1}],
        pipeline=[{"$sort": {f"f{i}": 1 for i in range(33)}}],
        error_code=SORT_COMPOUND_KEY_LIMIT_ERROR,
        msg="$sort should reject more than 32 unique numeric sort keys",
    ),
]

SORT_SPEC_ERROR_TESTS = (
    SORT_SPEC_VALIDATION_ERROR_TESTS
    + SORT_FIELD_PATH_ERROR_TESTS
    + SORT_COMPOUND_KEY_LIMIT_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SORT_SPEC_ERROR_TESTS))
def test_sort_spec_errors(collection, test_case: StageTestCase):
    """Test $sort specification and field path validation errors."""
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


def _build_raw_sort_stage(fields: list[tuple[str, int]]) -> RawBSONDocument:
    """Build a raw BSON $sort stage with the given fields, preserving duplicates."""
    inner = build_raw_bson_doc(fields)
    stage_elements = b"\x03$sort\x00" + inner.raw
    doc_len = 4 + len(stage_elements) + 1
    return RawBSONDocument(doc_len.to_bytes(4, "little") + stage_elements + b"\x00")


def test_sort_spec_errors_duplicate_fields(collection):
    """Test $sort rejects duplicate field names in the sort specification."""
    collection.insert_many(
        [
            {"_id": 1, "v": 30},
            {"_id": 2, "v": 10},
            {"_id": 3, "v": 20},
        ]
    )
    sort_stage = _build_raw_sort_stage([("v", 1), ("v", -1)])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [sort_stage],
            "cursor": {},
        },
    )
    assertResult(
        result,
        error_code=SORT_DUPLICATE_KEY_ERROR,
        msg="$sort should reject duplicate field names in the sort specification",
    )
