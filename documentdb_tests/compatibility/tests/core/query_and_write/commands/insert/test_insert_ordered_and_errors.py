"""
Insert ordered/unordered behavior and error handling tests.

Tests ordered vs unordered insert semantics, duplicate key errors,
batch error handling, and bulk insert behavior.
"""

from dataclasses import dataclass
from typing import Any, Optional

import pytest

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.error_codes import DUPLICATE_KEY_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class OrderedTest(BaseTestCase):
    ordered: Optional[bool] = None
    pre_existing: Optional[Any] = None
    documents: Any = None
    expected_n: int = 0
    expected_errors: Any = None


# Property [Ordered Semantics]: ordered:true stops at first error;
# ordered:false continues past errors.
ORDERED_BEHAVIOR_TESTS: list[OrderedTest] = [
    OrderedTest(
        "ordered_stops_at_error",
        ordered=True,
        pre_existing="existing",
        documents=[{"_id": "a"}, {"_id": "existing"}, {"_id": "b"}],
        expected_n=1,
        expected_errors=[{"index": 1, "code": DUPLICATE_KEY_ERROR}],
        msg="insert ordered:true should stop at first error.",
    ),
    OrderedTest(
        "unordered_continues_past_error",
        ordered=False,
        pre_existing="existing",
        documents=[{"_id": "a"}, {"_id": "existing"}, {"_id": "b"}],
        expected_n=2,
        expected_errors=[{"index": 1, "code": DUPLICATE_KEY_ERROR}],
        msg="insert ordered:false should continue past error.",
    ),
    OrderedTest(
        "ordered_all_valid",
        ordered=True,
        pre_existing=None,
        documents=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        expected_n=3,
        expected_errors=None,
        msg="insert ordered:true should insert all valid docs.",
    ),
    OrderedTest(
        "unordered_all_valid",
        ordered=False,
        pre_existing=None,
        documents=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        expected_n=3,
        expected_errors=None,
        msg="insert ordered:false should insert all valid docs.",
    ),
    OrderedTest(
        "ordered_all_dup",
        ordered=True,
        pre_existing=1,
        documents=[{"_id": 1}, {"_id": 1}, {"_id": 1}],
        expected_n=0,
        expected_errors=[{"index": 0, "code": DUPLICATE_KEY_ERROR}],
        msg="insert ordered:true should stop at first dup.",
    ),
    OrderedTest(
        "unordered_all_dup",
        ordered=False,
        pre_existing=1,
        documents=[{"_id": 1}, {"_id": 1}, {"_id": 1}],
        expected_n=0,
        expected_errors=[
            {"index": 0, "code": DUPLICATE_KEY_ERROR},
            {"index": 1, "code": DUPLICATE_KEY_ERROR},
            {"index": 2, "code": DUPLICATE_KEY_ERROR},
        ],
        msg="insert ordered:false should report all dup errors.",
    ),
    OrderedTest(
        "default_ordered_stops",
        ordered=None,
        pre_existing="existing",
        documents=[{"_id": "a"}, {"_id": "existing"}, {"_id": "b"}],
        expected_n=1,
        expected_errors=[{"index": 1, "code": DUPLICATE_KEY_ERROR}],
        msg="insert should default to ordered:true behavior.",
    ),
    OrderedTest(
        "ordered_intra_batch_dup",
        ordered=True,
        pre_existing=None,
        documents=[{"_id": 1}, {"_id": 2}, {"_id": 1}],
        expected_n=2,
        expected_errors=[{"index": 2, "code": DUPLICATE_KEY_ERROR}],
        msg="insert ordered:true should insert until intra-batch dup.",
    ),
    OrderedTest(
        "unordered_intra_batch_dup",
        ordered=False,
        pre_existing=None,
        documents=[{"_id": 1}, {"_id": 2}, {"_id": 1}],
        expected_n=2,
        expected_errors=[{"index": 2, "code": DUPLICATE_KEY_ERROR}],
        msg="insert ordered:false should skip intra-batch dup.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(ORDERED_BEHAVIOR_TESTS))
def test_insert_ordered_behavior(collection, test):
    """Test insert ordered/unordered semantics."""
    if test.pre_existing is not None:
        collection.insert_one({"_id": test.pre_existing})

    cmd = {"insert": collection.name, "documents": test.documents}
    if test.ordered is not None:
        cmd["ordered"] = test.ordered

    result = execute_command(collection, cmd)

    expected = {"ok": 1.0, "n": test.expected_n}
    if test.expected_errors is not None:
        expected["writeErrors"] = test.expected_errors
    assertSuccessPartial(result, expected, msg=test.msg)


@pytest.mark.insert
def test_insert_ordered_third_not_inserted(collection):
    """Test that ordered:true does NOT insert docs after the error."""
    collection.insert_one({"_id": "existing"})
    execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": "a"}, {"_id": "existing"}, {"_id": "b"}],
            "ordered": True,
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": "b"}})
    assertSuccess(result, [], msg="insert ordered:true should not insert docs after error.")


@pytest.mark.insert
def test_insert_batch_100_documents(collection):
    """Test inserting 100 documents in a single batch."""
    docs = [{"_id": i, "value": i} for i in range(100)]
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": docs},
    )
    assertSuccessPartial(result, {"ok": 1.0, "n": 100}, msg="insert should handle 100-doc batch.")
