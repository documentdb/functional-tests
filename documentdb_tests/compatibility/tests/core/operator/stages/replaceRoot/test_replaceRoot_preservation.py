"""Tests for the $replaceRoot aggregation stage."""

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
from bson.binary import UUID_SUBTYPE

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import OrderedKeys

# Property [Value and Type Preservation (Promoted)]: every BSON type held as a
# value inside a promoted stored sub-document is preserved verbatim with no
# value-level coercion.
REPLACEROOT_TYPE_PRESERVATION_PROMOTED_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"type_preserved_promoted_{tid}",
        docs=[{"_id": 1, "wrap": {"v": val}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$wrap"}}],
        expected=[{"v": val}],
        msg=f"$replaceRoot should preserve a {tid} value verbatim in a promoted document",
    )
    for tid, val in [
        ("string", "hello"),
        ("int32", 7),
        ("int64", Int64(9_999_999_999)),
        ("double", 3.5),
        ("decimal128", Decimal128("123.456")),
        ("bool", True),
        ("null", None),
        ("array", [1, 2, 3]),
        ("object", {"x": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1_700_000_000, 1)),
        ("regex", Regex("^abc", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Value and Type Preservation (Constructed)]: every BSON type held as a
# value inside a constructed object literal is preserved verbatim with no
# value-level coercion.
REPLACEROOT_TYPE_PRESERVATION_CONSTRUCTED_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"type_preserved_constructed_{tid}",
        docs=[{"_id": 1, "v": val}],
        pipeline=[{"$replaceRoot": {"newRoot": {"v": "$v"}}}],
        expected=[{"v": val}],
        msg=f"$replaceRoot should preserve a {tid} value verbatim in a constructed document",
    )
    for tid, val in [
        ("string", "hello"),
        ("int32", 7),
        ("int64", Int64(9_999_999_999)),
        ("double", 3.5),
        ("decimal128", Decimal128("123.456")),
        ("bool", True),
        ("null", None),
        ("array", [1, 2, 3]),
        ("object", {"x": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1_700_000_000, 1)),
        ("regex", Regex("^abc", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Binary Subtype Preservation]: a binary value's subtype is preserved
# with no normalization, so subtype-0 and subtype-4 (UUID) binaries round-trip
# unchanged whether promoted or constructed.
REPLACEROOT_BINARY_SUBTYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "binary_subtype0_promoted",
        docs=[{"_id": 1, "wrap": {"v": Binary(b"\x01\x02\x03", 0)}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$wrap"}}],
        expected=[{"v": b"\x01\x02\x03"}],
        msg="$replaceRoot should preserve a subtype-0 binary verbatim in a promoted document",
    ),
    StageTestCase(
        "binary_subtype0_constructed",
        docs=[{"_id": 1, "v": Binary(b"\x01\x02\x03", 0)}],
        pipeline=[{"$replaceRoot": {"newRoot": {"v": "$v"}}}],
        expected=[{"v": b"\x01\x02\x03"}],
        msg="$replaceRoot should preserve a subtype-0 binary verbatim in a constructed document",
    ),
    StageTestCase(
        "binary_subtype4_promoted",
        docs=[{"_id": 1, "wrap": {"v": Binary(bytes(range(16)), UUID_SUBTYPE)}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$wrap"}}],
        expected=[{"v": Binary(bytes(range(16)), UUID_SUBTYPE)}],
        msg="$replaceRoot should preserve a subtype-4 binary subtype in a promoted document",
    ),
    StageTestCase(
        "binary_subtype4_constructed",
        docs=[{"_id": 1, "v": Binary(bytes(range(16)), UUID_SUBTYPE)}],
        pipeline=[{"$replaceRoot": {"newRoot": {"v": "$v"}}}],
        expected=[{"v": Binary(bytes(range(16)), UUID_SUBTYPE)}],
        msg="$replaceRoot should preserve a subtype-4 binary subtype in a constructed document",
    ),
]

# Property [Field Order Preservation]: the field order of the resolved object is
# preserved verbatim, with no reordering or alphabetization, whether promoted or
# constructed.
REPLACEROOT_FIELD_ORDER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_order_promoted_embedded_doc",
        docs=[{"_id": 1, "data": {"zebra": 1, "apple": 2, "mango": 3}}],
        pipeline=[{"$replaceRoot": {"newRoot": "$data"}}],
        expected={"": OrderedKeys(["zebra", "apple", "mango"])},
        msg="$replaceRoot should preserve the field order of a promoted embedded document",
    ),
    StageTestCase(
        "field_order_constructed_literal_mixed",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$replaceRoot": {
                    "newRoot": {"zebra": "$a", "apple": "lit", "mango": {"$add": [1, 2]}}
                }
            }
        ],
        expected={"": OrderedKeys(["zebra", "apple", "mango"])},
        msg="$replaceRoot should preserve declaration order of a constructed mixed literal",
    ),
]

REPLACEROOT_PRESERVATION_TESTS = (
    REPLACEROOT_TYPE_PRESERVATION_PROMOTED_TESTS
    + REPLACEROOT_TYPE_PRESERVATION_CONSTRUCTED_TESTS
    + REPLACEROOT_BINARY_SUBTYPE_TESTS
    + REPLACEROOT_FIELD_ORDER_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REPLACEROOT_PRESERVATION_TESTS))
def test_replaceRoot_preservation_cases(collection, test_case: StageTestCase):
    """Test $replaceRoot preservation cases."""
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
        ignore_doc_order=True,
    )
