"""Tests for $out stage - document field type errors."""

from __future__ import annotations

from datetime import datetime

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

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Document Form Field Type Errors]: non-string types for db or
# coll in document form produce a type mismatch error, with db checked
# before coll when both have type errors.
OUT_DOCUMENT_FIELD_TYPE_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "db_type_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": 42, "coll": "target"}}],
        msg="$out should reject int32 db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": True, "coll": "target"}}],
        msg="$out should reject bool db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_array",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": ["test"], "coll": "target"}}],
        msg="$out should reject array db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_object",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": {"x": 1}, "coll": "target"}}],
        msg="$out should reject object db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": Int64(1), "coll": "target"}}],
        msg="$out should reject Int64 db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_double",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": 1.0, "coll": "target"}}],
        msg="$out should reject double db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": Decimal128("1"), "coll": "target"}}],
        msg="$out should reject Decimal128 db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": ObjectId(), "coll": "target"}}],
        msg="$out should reject ObjectId db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": datetime(2024, 1, 1), "coll": "target"}}],
        msg="$out should reject datetime db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": Binary(b"\x01"), "coll": "target"}}],
        msg="$out should reject Binary db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": Regex("abc"), "coll": "target"}}],
        msg="$out should reject Regex db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": Timestamp(1, 1), "coll": "target"}}],
        msg="$out should reject Timestamp db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": MinKey(), "coll": "target"}}],
        msg="$out should reject MinKey db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": MaxKey(), "coll": "target"}}],
        msg="$out should reject MaxKey db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "db_type_code",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": Code("function() {}"), "coll": "target"}}],
        msg="$out should reject Code db as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": 42}}],
        msg="$out should reject int32 coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": True}}],
        msg="$out should reject bool coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_array",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": ["target"]}}],
        msg="$out should reject array coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_object",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": {"x": 1}}}],
        msg="$out should reject object coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": Int64(1)}}],
        msg="$out should reject Int64 coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_double",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": 1.0}}],
        msg="$out should reject double coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": Decimal128("1")}}],
        msg="$out should reject Decimal128 coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": ObjectId()}}],
        msg="$out should reject ObjectId coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": datetime(2024, 1, 1)}}],
        msg="$out should reject datetime coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": Binary(b"\x01")}}],
        msg="$out should reject Binary coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": Regex("abc")}}],
        msg="$out should reject Regex coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": Timestamp(1, 1)}}],
        msg="$out should reject Timestamp coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": MinKey()}}],
        msg="$out should reject MinKey coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": MaxKey()}}],
        msg="$out should reject MaxKey coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "coll_type_code",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": Code("function() {}")}}],
        msg="$out should reject Code coll as a type mismatch",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]

# Property [Document Form Unknown Fields]: any field other than db, coll,
# and timeseries in the document form is rejected as an unknown field, and
# field name matching is case-sensitive and whitespace-sensitive.


OUT_DOCUMENT_FIELD_ERROR_TESTS = OUT_DOCUMENT_FIELD_TYPE_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_DOCUMENT_FIELD_ERROR_TESTS))
def test_out_error(collection, test_case: OutTestCase):
    """Test $out rejects invalid configurations with the expected error code."""
    populate_collection(collection, test_case)
    pipeline = test_case.pipeline
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
