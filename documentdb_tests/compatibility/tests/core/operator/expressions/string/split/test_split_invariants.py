from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_project,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.split_common import (
    SplitTest,
)

# Property [Return Type]: the result is always an array when the expression
# succeeds.
SPLIT_RETURN_TYPE_TESTS: list[SplitTest] = [
    SplitTest(
        "return_type_basic",
        string="a-b",
        delimiter="-",
        msg="$split result should be an array of strings for basic split",
    ),
    SplitTest(
        "return_type_no_match",
        string="hello",
        delimiter="-",
        msg="$split result should be an array of strings when delimiter not found",
    ),
    SplitTest(
        "return_type_empty_string",
        string="",
        delimiter="-",
        msg="$split result should be an array of strings for empty input",
    ),
    SplitTest(
        "return_type_unicode",
        string="café",
        delimiter="é",
        msg="$split result should be an array of strings for unicode input",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SPLIT_RETURN_TYPE_TESTS))
def test_split_return_type(collection, test_case: SplitTest):
    """Test $split result is always an array of strings."""
    split = {"$split": [test_case.string, test_case.delimiter]}
    result = execute_project(
        collection,
        {
            "isArray": {"$isArray": split},
            "allStrings": {
                "$allElementsTrue": {
                    "$map": {
                        "input": split,
                        "as": "el",
                        "in": {"$eq": [{"$type": "$$el"}, "string"]},
                    }
                }
            },
        },
    )
    assertSuccess(result, [{"isArray": True, "allStrings": True}], msg=test_case.msg)


# Property [Round-Trip]: joining the result array elements with the delimiter
# reproduces the original input string.
SPLIT_ROUND_TRIP_TESTS: list[SplitTest] = [
    SplitTest(
        "round_trip_basic",
        string="a-b-c",
        delimiter="-",
        msg="$split round-trip should reproduce original string",
    ),
    SplitTest(
        "round_trip_no_match",
        string="hello",
        delimiter="-",
        msg="$split round-trip should reproduce string when delimiter not found",
    ),
    SplitTest(
        "round_trip_delim_at_edges",
        string="-a-",
        delimiter="-",
        msg="$split round-trip should reproduce string with delimiter at edges",
    ),
    SplitTest(
        "round_trip_consecutive",
        string="a--b",
        delimiter="-",
        msg="$split round-trip should reproduce string with consecutive delimiters",
    ),
    SplitTest(
        "round_trip_empty_string",
        string="",
        delimiter="-",
        msg="$split round-trip should reproduce empty string",
    ),
    SplitTest(
        "round_trip_all_delimiters",
        string="---",
        delimiter="-",
        msg="$split round-trip should reproduce string of only delimiters",
    ),
    SplitTest(
        "round_trip_multi_char_delim",
        string="aXYbXYc",
        delimiter="XY",
        msg="$split round-trip should reproduce string with multi-char delimiter",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SPLIT_ROUND_TRIP_TESTS))
def test_split_round_trip(collection, test_case: SplitTest):
    """Test $split round-trip: joining result with delimiter reproduces input."""
    split = {"$split": [test_case.string, test_case.delimiter]}
    result = execute_project(
        collection,
        {
            "roundTrip": {
                "$reduce": {
                    "input": split,
                    "initialValue": None,
                    "in": {
                        "$cond": [
                            {"$eq": ["$$value", None]},
                            "$$this",
                            {"$concat": ["$$value", test_case.delimiter, "$$this"]},
                        ]
                    },
                }
            },
            "original": test_case.string,
        },
    )
    assertSuccess(
        result, [{"roundTrip": test_case.string, "original": test_case.string}], msg=test_case.msg
    )
