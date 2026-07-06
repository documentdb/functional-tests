"""
Shared test case for array expression operator tests.

Used across the $arrayElemAt, $arrayToObject, $concatArrays, and $in test files.
"""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ArrayTestClass(BaseTestCase):
    """Test case for array expression operators.

    Attributes:
        idx: An index argument (e.g. $arrayElemAt).
        arrays: The array input. Holds a single array for $arrayElemAt and
            $arrayToObject, or a list of arrays for $concatArrays.
        value: A value argument (e.g. $in search value).
        array: A single array argument (e.g. $in search array).
    """

    idx: Any = None
    arrays: Any = None
    value: Any = None
    array: Any = None
