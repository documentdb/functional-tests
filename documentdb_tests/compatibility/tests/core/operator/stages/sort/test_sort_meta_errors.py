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

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    SORT_ILLEGAL_META_ERROR,
    SORT_NON_META_OBJECT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [$meta Non-Meta Object Error]: non-$meta objects as sort order
# values produce an error.
SORT_META_NON_META_OBJECT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "meta_non_meta_object",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$foo": 1}}}],
        error_code=SORT_NON_META_OBJECT_ERROR,
        msg="$sort should reject a non-$meta object as a sort order value",
    ),
]

# Property [$meta Extra Keys Error]: extra keys alongside $meta in a sort
# order object produce an error.
SORT_META_EXTRA_KEYS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "meta_extra_keys",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": "randVal", "extra": 1}}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$sort should reject extra keys in a $meta sort specification",
    ),
]

# Property [$meta Invalid Value Error]: invalid $meta values including
# unrecognized strings and non-string types produce an error.
SORT_META_INVALID_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "meta_invalid_unknown",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": "unknown"}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject $meta value 'unknown'",
    ),
    StageTestCase(
        "meta_invalid_searchhighlights",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": "searchHighlights"}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject $meta value 'searchHighlights'",
    ),
    StageTestCase(
        "meta_invalid_indexkey",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": "indexKey"}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject $meta value 'indexKey'",
    ),
    StageTestCase(
        "meta_invalid_sortkey",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": "sortKey"}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject $meta value 'sortKey'",
    ),
    StageTestCase(
        "meta_invalid_recordid",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": "recordId"}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject $meta value 'recordId'",
    ),
    StageTestCase(
        "meta_invalid_geonearpoint",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": "geoNearPoint"}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject $meta value 'geoNearPoint'",
    ),
    StageTestCase(
        "meta_invalid_empty_string",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": ""}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject an empty string as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_int",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": 1}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject an int as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_null",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": None}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject null as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_bool",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": True}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a boolean as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_object",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": {"a": 1}}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject an object as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_array",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": [1]}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject an array as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_float",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": 1.5}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a float as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_int64",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": Int64(1)}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject an Int64 as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_decimal128",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": Decimal128("1")}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a Decimal128 as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_objectid",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": ObjectId()}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject an ObjectId as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_datetime",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": datetime(2024, 1, 1, tzinfo=timezone.utc)}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a datetime as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_binary",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": Binary(b"\x01")}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a Binary as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_regex",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": Regex("a")}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a Regex as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_timestamp",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": Timestamp(1, 1)}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a Timestamp as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_minkey",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": MinKey()}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a MinKey as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_maxkey",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": MaxKey()}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a MaxKey as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_code",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": Code("f")}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a Code as a $meta value",
    ),
    StageTestCase(
        "meta_invalid_type_codewithscope",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": {"$meta": Code("f", {"x": 1})}}}],
        error_code=SORT_ILLEGAL_META_ERROR,
        msg="$sort should reject a CodeWithScope as a $meta value",
    ),
]

SORT_META_ERROR_TESTS = (
    SORT_META_NON_META_OBJECT_ERROR_TESTS
    + SORT_META_EXTRA_KEYS_ERROR_TESTS
    + SORT_META_INVALID_VALUE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SORT_META_ERROR_TESTS))
def test_sort_meta_errors(collection, test_case: StageTestCase):
    """Test $sort $meta validation errors."""
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
