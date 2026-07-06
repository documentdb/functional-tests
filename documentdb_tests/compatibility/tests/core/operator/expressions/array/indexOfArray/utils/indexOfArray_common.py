"""
Shared test infrastructure for $indexOfArray expression tests.
"""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class IndexOfArrayTest(BaseTestCase):
    """Test case for $indexOfArray operator."""

    array: Any = None
    search: Any = None
    start: Any = None
    end: Any = None


def build_args(test: IndexOfArrayTest):
    """Build the argument list for $indexOfArray from a test case."""
    args = [test.array, test.search]
    if test.start is not None:
        args.append(test.start)
    if test.end is not None:
        args.append(test.end)
    return args


def build_insert_args(test: IndexOfArrayTest):
    """Build field-reference argument list and document for insert-based tests."""
    args = ["$arr", "$search"]
    doc = {"arr": test.array, "search": test.search}
    if test.start is not None:
        args.append("$start")
        doc["start"] = test.start
    if test.end is not None:
        args.append("$end")
        doc["end"] = test.end
    return args, doc
