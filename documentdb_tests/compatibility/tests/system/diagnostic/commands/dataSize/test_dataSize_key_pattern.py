"""Tests for dataSize command keyPattern and min/max parameters."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


@dataclass(frozen=True)
class KeyPatternTest(BaseTestCase):
    """Test case for dataSize keyPattern/min/max parameter combinations."""

    doc_count: int = 10
    create_index: bool = False
    key_pattern: Dict[str, Any] = field(default_factory=lambda: {"_id": 1})
    min_bound: Optional[Dict[str, Any]] = None
    max_bound: Optional[Dict[str, Any]] = None


KEY_PATTERN_TESTS: list[KeyPatternTest] = [
    KeyPatternTest(
        "keyPattern_id",
        expected={"ok": 1.0},
        key_pattern={"_id": 1},
        msg="keyPattern _id should succeed",
    ),
    KeyPatternTest(
        "with_min_max",
        expected={"ok": 1.0},
        doc_count=100,
        create_index=True,
        key_pattern={"x": 1},
        min_bound={"x": 10},
        max_bound={"x": 50},
        msg="keyPattern with min/max should succeed",
    ),
    KeyPatternTest(
        "min_max_no_match",
        expected={"numObjects": Int64(0)},
        create_index=True,
        key_pattern={"x": 1},
        min_bound={"x": 1000},
        max_bound={"x": 2000},
        msg="No match should return 0",
    ),
    KeyPatternTest(
        "without_min_max",
        expected={"ok": 1.0},
        create_index=True,
        key_pattern={"x": 1},
        msg="keyPattern without min/max should succeed",
    ),
    KeyPatternTest(
        "min_equal_max",
        expected={"numObjects": Int64(0)},
        create_index=True,
        key_pattern={"x": 1},
        min_bound={"x": 5},
        max_bound={"x": 5},
        msg="min==max should return 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(KEY_PATTERN_TESTS))
def test_dataSize_key_pattern(collection, test):
    """Test dataSize with keyPattern and optional min/max parameters."""
    collection.insert_many([{"_id": i, "x": i} for i in range(test.doc_count)])
    if test.create_index:
        collection.create_index("x")
    ns = f"{collection.database.name}.{collection.name}"
    cmd = {"dataSize": ns, "keyPattern": test.key_pattern}
    if test.min_bound is not None:
        cmd["min"] = test.min_bound
    if test.max_bound is not None:
        cmd["max"] = test.max_bound
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, test.expected, msg=test.msg)
