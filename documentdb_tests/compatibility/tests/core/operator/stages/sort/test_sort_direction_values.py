from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import QUERY_METADATA_NOT_AVAILABLE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Sort Order Value Acceptance]: int32, int64, double (truncation
# toward zero yields 1 or -1), and Decimal128 (banker's rounding of abs
# yields 1) are accepted as sort direction values.
SORT_ORDER_VALUE_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "accept_int64_asc",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": Int64(1)}}],
        expected=[{"_id": 2, "v": 10}, {"_id": 1, "v": 20}],
        msg="$sort should accept Int64(1) as ascending sort direction",
    ),
    StageTestCase(
        "accept_int64_desc",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": Int64(-1)}}],
        expected=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        msg="$sort should accept Int64(-1) as descending sort direction",
    ),
    StageTestCase(
        "accept_double_truncated_to_asc",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": 1.999}}],
        expected=[{"_id": 2, "v": 10}, {"_id": 1, "v": 20}],
        msg="$sort should accept double 1.999 truncated toward zero to 1",
    ),
    StageTestCase(
        "accept_double_truncated_to_desc",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": -1.999}}],
        expected=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        msg="$sort should accept double -1.999 truncated toward zero to -1",
    ),
    StageTestCase(
        "accept_decimal128_asc",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": Decimal128("1")}}],
        expected=[{"_id": 2, "v": 10}, {"_id": 1, "v": 20}],
        msg="$sort should accept Decimal128('1') as ascending sort direction",
    ),
    StageTestCase(
        "accept_decimal128_desc",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": Decimal128("-1")}}],
        expected=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        msg="$sort should accept Decimal128('-1') as descending sort direction",
    ),
    StageTestCase(
        "accept_decimal128_0_51_rounds_to_asc",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": Decimal128("0.51")}}],
        expected=[{"_id": 2, "v": 10}, {"_id": 1, "v": 20}],
        msg="$sort should accept Decimal128('0.51') banker's rounded to 1",
    ),
    StageTestCase(
        "accept_decimal128_1_49_rounds_to_asc",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": Decimal128("1.49")}}],
        expected=[{"_id": 2, "v": 10}, {"_id": 1, "v": 20}],
        msg="$sort should accept Decimal128('1.49') banker's rounded to 1",
    ),
    StageTestCase(
        "accept_decimal128_neg_0_51_rounds_to_desc",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": Decimal128("-0.51")}}],
        expected=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        msg="$sort should accept Decimal128('-0.51') banker's rounded to -1",
    ),
    StageTestCase(
        "accept_decimal128_neg_1_49_rounds_to_desc",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": Decimal128("-1.49")}}],
        expected=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        msg="$sort should accept Decimal128('-1.49') banker's rounded to -1",
    ),
]

# Property [$meta Sort Acceptance]: valid $meta values are accepted as sort
# order values, and $meta keys do not count toward the 32-key compound sort
# limit.
SORT_META_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "accept_meta_randval",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": 1, "r": {"$meta": "randVal"}}}],
        expected=[{"_id": 2, "v": 10}, {"_id": 1, "v": 20}],
        msg="$sort should accept {$meta: 'randVal'} as a sort order value",
    ),
    StageTestCase(
        "accept_meta_searchscore",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": 1, "s": {"$meta": "searchScore"}}}],
        expected=[{"_id": 2, "v": 10}, {"_id": 1, "v": 20}],
        msg="$sort should accept {$meta: 'searchScore'} as a sort order value",
    ),
    StageTestCase(
        "accept_meta_textscore",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": 1, "t": {"$meta": "textScore"}}}],
        error_code=QUERY_METADATA_NOT_AVAILABLE_ERROR,
        msg="$sort should accept {$meta: 'textScore'} but fail without a preceding $text stage",
    ),
    StageTestCase(
        "accept_meta_geoneardistance",
        docs=[{"_id": 1, "v": 20}, {"_id": 2, "v": 10}],
        pipeline=[{"$sort": {"v": 1, "d": {"$meta": "geoNearDistance"}}}],
        error_code=QUERY_METADATA_NOT_AVAILABLE_ERROR,
        msg=(
            "$sort should accept {$meta: 'geoNearDistance'}"
            " but fail without a preceding $geoNear stage"
        ),
    ),
    # $meta keys do not count toward the 32-key compound sort limit.
    StageTestCase(
        "accept_meta_beyond_32_key_limit",
        docs=[{"_id": 1, "f0": 20}, {"_id": 2, "f0": 10}],
        pipeline=[
            {
                "$sort": {
                    **{f"f{i}": 1 for i in range(32)},
                    "meta1": {"$meta": "randVal"},
                    "meta2": {"$meta": "searchScore"},
                }
            },
        ],
        expected=[{"_id": 2, "f0": 10}, {"_id": 1, "f0": 20}],
        msg="$sort should not count $meta keys toward the 32-key compound sort limit",
    ),
]

SORT_DIRECTION_VALUE_TESTS = SORT_ORDER_VALUE_ACCEPTANCE_TESTS + SORT_META_ACCEPTANCE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SORT_DIRECTION_VALUE_TESTS))
def test_sort_direction_values(collection, test_case: StageTestCase):
    """Test $sort accepted direction values."""
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
    )
