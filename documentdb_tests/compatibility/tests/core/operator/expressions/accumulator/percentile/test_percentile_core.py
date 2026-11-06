"""Core selection semantics for the $percentile expression operator.

With ``method: "approximate"`` (a t-digest), small inputs return the actual data
point at rank ceil(p*n). Results are returned as an array, one value per ``p``,
in the same order as ``p``. Captured against MongoDB 8.3.4.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.percentile.utils.percentile_common import (  # noqa: E501
    PercentileTest,
    percentile_spec,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Percentile Selection]: $percentile returns the value at the rank
# corresponding to each probability, selecting an order statistic of the input.
PERCENTILE_SELECTION_TESTS: list[PercentileTest] = [
    PercentileTest(
        "core_median",
        spec=percentile_spec([10, 20, 30], [0.5]),
        expected=[20.0],
        msg="$percentile p=[0.5] over [10,20,30] should return the median [20.0]",
    ),
    PercentileTest(
        "core_min_p0",
        spec=percentile_spec([10, 20, 30], [0.0]),
        expected=[10.0],
        msg="$percentile p=[0.0] should return the minimum [10.0]",
    ),
    PercentileTest(
        "core_max_p1",
        spec=percentile_spec([10, 20, 30], [1.0]),
        expected=[30.0],
        msg="$percentile p=[1.0] should return the maximum [30.0]",
    ),
    PercentileTest(
        "core_single_element",
        spec=percentile_spec([42], [0.5]),
        expected=[42.0],
        msg="$percentile over a single-element array should return that element",
    ),
    PercentileTest(
        "core_unsorted_input",
        spec=percentile_spec([30, 10, 20], [0.5]),
        expected=[20.0],
        msg="$percentile should sort input internally; median of [30,10,20] is [20.0]",
    ),
    PercentileTest(
        "core_all_equal",
        spec=percentile_spec([7, 7, 7], [0.5]),
        expected=[7.0],
        msg="$percentile over all-equal values should return that value",
    ),
    PercentileTest(
        "core_large_input",
        spec=percentile_spec(list(range(10_000)), [0.5]),
        expected=[4999.0],
        msg="$percentile should handle a large (10000-element) input",
    ),
]

# Property [P Ordering]: results follow the order of the ``p`` array, including
# descending and duplicate probabilities.
PERCENTILE_ORDERING_TESTS: list[PercentileTest] = [
    PercentileTest(
        "order_multiple_ascending",
        spec=percentile_spec([10, 20, 30, 40, 50], [0.25, 0.5, 0.95]),
        expected=[20.0, 30.0, 50.0],
        msg="$percentile with multiple ascending p values should return results in p order",
    ),
    PercentileTest(
        "order_descending_p",
        spec=percentile_spec([10, 20, 30, 40, 50], [0.95, 0.05]),
        expected=[50.0, 10.0],
        msg="$percentile should preserve descending p order in the output",
    ),
    PercentileTest(
        "order_duplicate_p",
        spec=percentile_spec([10, 20, 30], [0.5, 0.5]),
        expected=[20.0, 20.0],
        msg="$percentile with duplicate p values should return a result for each",
    ),
    PercentileTest(
        "order_boundaries_both",
        spec=percentile_spec([10, 20, 30], [0.0, 1.0]),
        expected=[10.0, 30.0],
        msg="$percentile with p=[0.0, 1.0] should return [min, max]",
    ),
]

PERCENTILE_CORE_ALL_TESTS = PERCENTILE_SELECTION_TESTS + PERCENTILE_ORDERING_TESTS


@pytest.mark.parametrize("test_case", pytest_params(PERCENTILE_CORE_ALL_TESTS))
def test_percentile_core(collection, test_case: PercentileTest):
    """Test $percentile core selection semantics."""
    result = execute_expression(collection, {"$percentile": test_case.spec})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
