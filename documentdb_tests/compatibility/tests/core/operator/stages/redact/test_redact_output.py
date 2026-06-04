"""Tests for $redact output fidelity: value passthrough across BSON types and order preservation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, OrderedKeys, PerDoc
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [Value Passthrough]: a kept field value is returned unchanged for
# every BSON type under $$KEEP.
REDACT_PASSTHROUGH_KEEP_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"passthrough_keep_{tid}",
        docs=[{"_id": 1, "val": val}],
        pipeline=[{"$redact": "$$KEEP"}],
        expected=[{"_id": 1, "val": val}],
        msg=f"$redact should return a stored {tid} value unchanged under $$KEEP",
    )
    for tid, val in [
        ("string", "hello"),
        ("int32", 7),
        ("int64", Int64(9)),
        ("double", 3.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("document", {"a": 1, "b": {"c": 2}}),
        ("array", [1, "x", {"y": 2}]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", b"\x01\x02\x03"),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("null", None),
    ]
]

# Property [Value Passthrough]: a kept field value is returned unchanged for
# every BSON type under $$DESCEND.
REDACT_PASSTHROUGH_DESCEND_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"passthrough_descend_{tid}",
        docs=[{"_id": 1, "val": val}],
        pipeline=[{"$redact": "$$DESCEND"}],
        expected=[{"_id": 1, "val": val}],
        msg=f"$redact should return a stored {tid} value unchanged under $$DESCEND",
    )
    for tid, val in [
        ("string", "hello"),
        ("int32", 7),
        ("int64", Int64(9)),
        ("double", 3.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("document", {"a": 1, "b": {"c": 2}}),
        ("array", [1, "x", {"y": 2}]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", b"\x01\x02\x03"),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("null", None),
    ]
]

# Property [Prune Across Types]: a document is removed under $$PRUNE regardless
# of the BSON type of a stored field.
REDACT_PRUNE_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"prune_{tid}",
        docs=[{"_id": 1, "val": val}],
        pipeline=[{"$redact": "$$PRUNE"}],
        expected=[],
        msg=f"$redact should drop a document holding a stored {tid} value under $$PRUNE",
    )
    for tid, val in [
        ("string", "hello"),
        ("int32", 7),
        ("int64", Int64(9)),
        ("double", 3.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("document", {"a": 1, "b": {"c": 2}}),
        ("array", [1, "x", {"y": 2}]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", b"\x01\x02\x03"),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("null", None),
    ]
]

# Property [Order Preservation]: documents and the surviving fields within each
# document retain their original relative order.
REDACT_ORDER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "order_preserves_document_and_field_order",
        docs=[
            {"_id": 3, "a": 1, "b": {"drop": True}, "c": 3},
            {"_id": 1, "x": {"drop": True}},
            {"_id": 2, "a": 1, "c": 3},
        ],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$drop", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=PerDoc(
            {"_id": Eq(3), "": OrderedKeys(["_id", "a", "c"])},
            {"_id": Eq(1), "": OrderedKeys(["_id"])},
            {"_id": Eq(2), "": OrderedKeys(["_id", "a", "c"])},
        ),
        msg="$redact should preserve input document order and surviving field order",
    ),
]

REDACT_OUTPUT_TESTS = (
    REDACT_PASSTHROUGH_KEEP_TESTS
    + REDACT_PASSTHROUGH_DESCEND_TESTS
    + REDACT_PRUNE_TYPE_TESTS
    + REDACT_ORDER_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REDACT_OUTPUT_TESTS))
def test_redact_output_cases(collection, test_case: StageTestCase):
    """Test $redact value passthrough across BSON types and order preservation."""
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
