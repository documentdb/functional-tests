"""Aggregation $group stage tests - N-accumulator and $percentile error cases."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    MISSING_FIELD_ERROR,
    N_ACCUMULATOR_INVALID_N_ERROR,
    N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
    N_ACCUMULATOR_MISSING_N_TOPN_FAMILY_ERROR,
    PERCENTILE_INVALID_P_FIELD_ERROR,
    PERCENTILE_INVALID_P_VALUE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [N-Accumulator Invalid n]: $topN, $bottomN, $firstN, $lastN,
# $maxN, and $minN reject null, string, zero, and negative values for n.
GROUP_N_ACCUMULATOR_INVALID_N_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="topn_null_n",
        docs=[{"_id": 1, "v": 5, "s": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$topN": {"sortBy": {"s": 1}, "output": "$v", "n": None}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$topN with null n should produce an error",
    ),
    StageTestCase(
        id="topn_string_n",
        docs=[{"_id": 1, "v": 5, "s": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$topN": {"sortBy": {"s": 1}, "output": "$v", "n": "bad"}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$topN with string n should produce an error",
    ),
    StageTestCase(
        id="topn_zero_n",
        docs=[{"_id": 1, "v": 5, "s": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$topN": {"sortBy": {"s": 1}, "output": "$v", "n": 0}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$topN with n=0 should produce an error",
    ),
    StageTestCase(
        id="topn_negative_n",
        docs=[{"_id": 1, "v": 5, "s": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$topN": {"sortBy": {"s": 1}, "output": "$v", "n": -1}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$topN with negative n should produce an error",
    ),
    StageTestCase(
        id="bottomn_null_n",
        docs=[{"_id": 1, "v": 5, "s": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$bottomN": {"sortBy": {"s": 1}, "output": "$v", "n": None}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$bottomN with null n should produce an error",
    ),
    StageTestCase(
        id="bottomn_string_n",
        docs=[{"_id": 1, "v": 5, "s": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$bottomN": {"sortBy": {"s": 1}, "output": "$v", "n": "bad"}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$bottomN with string n should produce an error",
    ),
    StageTestCase(
        id="bottomn_zero_n",
        docs=[{"_id": 1, "v": 5, "s": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$bottomN": {"sortBy": {"s": 1}, "output": "$v", "n": 0}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$bottomN with n=0 should produce an error",
    ),
    StageTestCase(
        id="bottomn_negative_n",
        docs=[{"_id": 1, "v": 5, "s": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$bottomN": {"sortBy": {"s": 1}, "output": "$v", "n": -1}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$bottomN with negative n should produce an error",
    ),
    StageTestCase(
        id="firstn_null_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$firstN": {"input": "$v", "n": None}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$firstN with null n should produce an error",
    ),
    StageTestCase(
        id="firstn_string_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$firstN": {"input": "$v", "n": "bad"}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$firstN with string n should produce an error",
    ),
    StageTestCase(
        id="firstn_zero_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$firstN": {"input": "$v", "n": 0}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$firstN with n=0 should produce an error",
    ),
    StageTestCase(
        id="firstn_negative_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$firstN": {"input": "$v", "n": -1}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$firstN with negative n should produce an error",
    ),
    StageTestCase(
        id="lastn_null_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$lastN": {"input": "$v", "n": None}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN with null n should produce an error",
    ),
    StageTestCase(
        id="lastn_string_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$lastN": {"input": "$v", "n": "bad"}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN with string n should produce an error",
    ),
    StageTestCase(
        id="lastn_zero_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$lastN": {"input": "$v", "n": 0}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN with n=0 should produce an error",
    ),
    StageTestCase(
        id="lastn_negative_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$lastN": {"input": "$v", "n": -1}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN with negative n should produce an error",
    ),
    StageTestCase(
        id="maxn_null_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$maxN": {"input": "$v", "n": None}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$maxN with null n should produce an error",
    ),
    StageTestCase(
        id="maxn_string_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$maxN": {"input": "$v", "n": "bad"}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$maxN with string n should produce an error",
    ),
    StageTestCase(
        id="maxn_zero_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$maxN": {"input": "$v", "n": 0}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$maxN with n=0 should produce an error",
    ),
    StageTestCase(
        id="maxn_negative_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$maxN": {"input": "$v", "n": -1}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$maxN with negative n should produce an error",
    ),
    StageTestCase(
        id="minn_null_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$minN": {"input": "$v", "n": None}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$minN with null n should produce an error",
    ),
    StageTestCase(
        id="minn_string_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$minN": {"input": "$v", "n": "bad"}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$minN with string n should produce an error",
    ),
    StageTestCase(
        id="minn_zero_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$minN": {"input": "$v", "n": 0}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$minN with n=0 should produce an error",
    ),
    StageTestCase(
        id="minn_negative_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$minN": {"input": "$v", "n": -1}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$minN with negative n should produce an error",
    ),
]

# Property [N-Accumulator Missing n]: missing n produces different error codes
# by accumulator family - $topN/$bottomN and $firstN/$lastN/$maxN/$minN use
# distinct error codes.
GROUP_N_ACCUMULATOR_MISSING_N_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="topn_missing_n",
        docs=[{"_id": 1, "v": 5, "s": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$topN": {"sortBy": {"s": 1}, "output": "$v"}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_MISSING_N_TOPN_FAMILY_ERROR,
        msg="$topN with missing n should produce an error",
    ),
    StageTestCase(
        id="bottomn_missing_n",
        docs=[{"_id": 1, "v": 5, "s": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$bottomN": {"sortBy": {"s": 1}, "output": "$v"}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_MISSING_N_TOPN_FAMILY_ERROR,
        msg="$bottomN with missing n should produce an error",
    ),
    StageTestCase(
        id="firstn_missing_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$firstN": {"input": "$v"}}}}],
        error_code=N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
        msg="$firstN with missing n should produce an error",
    ),
    StageTestCase(
        id="lastn_missing_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$lastN": {"input": "$v"}}}}],
        error_code=N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
        msg="$lastN with missing n should produce an error",
    ),
    StageTestCase(
        id="maxn_missing_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$maxN": {"input": "$v"}}}}],
        error_code=N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
        msg="$maxN with missing n should produce an error",
    ),
    StageTestCase(
        id="minn_missing_n",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$minN": {"input": "$v"}}}}],
        error_code=N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
        msg="$minN with missing n should produce an error",
    ),
]


# Property [$percentile Parameter Validation]: $percentile rejects invalid
# percentile values outside [0, 1], empty or null p arrays, invalid method
# strings, and missing method field.
GROUP_PERCENTILE_PARAM_VALIDATION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="percentile_p_value_above_one",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$percentile": {
                            "input": "$x",
                            "p": [1.5],
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        error_code=PERCENTILE_INVALID_P_VALUE_ERROR,
        msg="$percentile with p value > 1 should produce an error",
    ),
    StageTestCase(
        id="percentile_p_value_below_zero",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$percentile": {
                            "input": "$x",
                            "p": [-0.1],
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        error_code=PERCENTILE_INVALID_P_VALUE_ERROR,
        msg="$percentile with p value < 0 should produce an error",
    ),
    StageTestCase(
        id="percentile_empty_p_array",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$percentile": {
                            "input": "$x",
                            "p": [],
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        error_code=PERCENTILE_INVALID_P_FIELD_ERROR,
        msg="$percentile with empty p array should produce an error",
    ),
    StageTestCase(
        id="percentile_null_p",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$percentile": {
                            "input": "$x",
                            "p": None,
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        error_code=PERCENTILE_INVALID_P_FIELD_ERROR,
        msg="$percentile with null p should produce an error",
    ),
    StageTestCase(
        id="percentile_invalid_method",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$percentile": {
                            "input": "$x",
                            "p": [0.5],
                            "method": "invalid",
                        }
                    },
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$percentile with invalid method should produce an error",
    ),
    StageTestCase(
        id="percentile_missing_method",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$percentile": {
                            "input": "$x",
                            "p": [0.5],
                        }
                    },
                }
            }
        ],
        error_code=MISSING_FIELD_ERROR,
        msg="$percentile with missing method should produce an error",
    ),
]


GROUP_N_ACCUMULATOR_ERROR_TESTS = (
    GROUP_N_ACCUMULATOR_INVALID_N_ERROR_TESTS
    + GROUP_N_ACCUMULATOR_MISSING_N_ERROR_TESTS
    + GROUP_PERCENTILE_PARAM_VALIDATION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_N_ACCUMULATOR_ERROR_TESTS))
def test_group_n_accumulator_error(collection, test_case: StageTestCase):
    """Test $group stage N-accumulator and $percentile error cases."""
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
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
