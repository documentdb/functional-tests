"""Tests for $pullAll data type matching semantics.

Covers: numeric equivalence, BSON type distinction, NaN/Infinity handling,
cross-type NaN/Infinity/negative-zero equivalence.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

NUMERIC_EQUIVALENCE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "mixed_types_in_values_list",
        setup_docs=[{"_id": 1, "a": [1, 2.0, Int64(3), Decimal128("4")]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [Int64(1), 2, Decimal128("3"), 4.0]}},
        expected={"_id": 1, "a": []},
        msg="Should remove with mixed numeric types in values list",
    ),
]

BSON_TYPE_DISTINCTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "false_does_not_remove_int_zero",
        setup_docs=[{"_id": 1, "a": [0, False]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [False]}},
        expected={"_id": 1, "a": [0]},
        msg="false should NOT remove int(0) — distinct BSON types",
    ),
    UpdateTestCase(
        "true_does_not_remove_int_one",
        setup_docs=[{"_id": 1, "a": [1, True]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [True]}},
        expected={"_id": 1, "a": [1]},
        msg="true should NOT remove int(1) — distinct BSON types",
    ),
    UpdateTestCase(
        "null_removes_only_null",
        setup_docs=[{"_id": 1, "a": [None, 0, "", False]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [None]}},
        expected={"_id": 1, "a": [0, "", False]},
        msg="Should remove only null elements",
    ),
    UpdateTestCase(
        "empty_string_does_not_remove_null",
        setup_docs=[{"_id": 1, "a": [None, ""]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [""]}},
        expected={"_id": 1, "a": [None]},
        msg="empty string should NOT remove null — distinct types",
    ),
]

NAN_INFINITY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "float_nan_removes_nan",
        setup_docs=[{"_id": 1, "a": [FLOAT_NAN, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [FLOAT_NAN]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="Should remove NaN elements",
    ),
    UpdateTestCase(
        "decimal128_nan_removes_nan",
        setup_docs=[{"_id": 1, "a": [DECIMAL128_NAN, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [DECIMAL128_NAN]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="Should remove Decimal128 NaN elements",
    ),
    UpdateTestCase(
        "infinity_removes_infinity",
        setup_docs=[{"_id": 1, "a": [FLOAT_INFINITY, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [FLOAT_INFINITY]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="Should remove Infinity elements",
    ),
    UpdateTestCase(
        "neg_infinity_removes_neg_infinity",
        setup_docs=[{"_id": 1, "a": [FLOAT_NEGATIVE_INFINITY, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [FLOAT_NEGATIVE_INFINITY]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="Should remove -Infinity elements",
    ),
    UpdateTestCase(
        "neg_zero_removes_zero",
        setup_docs=[{"_id": 1, "a": [0.0, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [DOUBLE_NEGATIVE_ZERO]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="Should remove 0.0 via -0.0 (numeric equivalence)",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_removes_zero",
        setup_docs=[{"_id": 1, "a": [Decimal128("0"), 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [DECIMAL128_NEGATIVE_ZERO]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="Should remove Decimal128 0 via Decimal128 -0 (numeric equivalence)",
    ),
    UpdateTestCase(
        "float_nan_matches_decimal128_nan",
        setup_docs=[{"_id": 1, "a": [DECIMAL128_NAN, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [FLOAT_NAN]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="float NaN should match Decimal128 NaN (cross-type NaN equivalence)",
    ),
    UpdateTestCase(
        "float_inf_matches_decimal128_inf",
        setup_docs=[{"_id": 1, "a": [DECIMAL128_INFINITY, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [FLOAT_INFINITY]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="float Infinity should match Decimal128 Infinity (cross-type equivalence)",
    ),
    UpdateTestCase(
        "decimal128_neg_infinity_removes_self",
        setup_docs=[{"_id": 1, "a": [DECIMAL128_NEGATIVE_INFINITY, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [DECIMAL128_NEGATIVE_INFINITY]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="Should remove Decimal128 -Infinity elements",
    ),
    UpdateTestCase(
        "float_neg_inf_matches_decimal128_neg_inf",
        setup_docs=[{"_id": 1, "a": [DECIMAL128_NEGATIVE_INFINITY, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [FLOAT_NEGATIVE_INFINITY]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="float -Infinity should match Decimal128 -Infinity (cross-type equivalence)",
    ),
    UpdateTestCase(
        "float_neg_nan_removes_nan",
        setup_docs=[{"_id": 1, "a": [FLOAT_NEGATIVE_NAN, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [FLOAT_NEGATIVE_NAN]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="Should remove float -NaN elements",
    ),
    UpdateTestCase(
        "decimal128_neg_nan_removes_nan",
        setup_docs=[{"_id": 1, "a": [DECIMAL128_NEGATIVE_NAN, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [DECIMAL128_NEGATIVE_NAN]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="Should remove Decimal128 -NaN elements",
    ),
    UpdateTestCase(
        "float_nan_matches_float_neg_nan",
        setup_docs=[{"_id": 1, "a": [FLOAT_NEGATIVE_NAN, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [FLOAT_NAN]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="float NaN should match float -NaN (NaN sign equivalence)",
    ),
    UpdateTestCase(
        "decimal128_nan_matches_decimal128_neg_nan",
        setup_docs=[{"_id": 1, "a": [DECIMAL128_NEGATIVE_NAN, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [DECIMAL128_NAN]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="Decimal128 NaN should match Decimal128 -NaN (NaN sign equivalence)",
    ),
    UpdateTestCase(
        "float_neg_nan_matches_decimal128_nan",
        setup_docs=[{"_id": 1, "a": [DECIMAL128_NAN, 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [FLOAT_NEGATIVE_NAN]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="float -NaN should match Decimal128 NaN (cross-type NaN equivalence)",
    ),
    UpdateTestCase(
        "float_neg_zero_removes_decimal128_zero",
        setup_docs=[{"_id": 1, "a": [Decimal128("0"), 1, 2]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [DOUBLE_NEGATIVE_ZERO]}},
        expected={"_id": 1, "a": [1, 2]},
        msg="float -0.0 should remove Decimal128 0 (cross-type negative zero equivalence)",
    ),
]

ALL_TESTS = NUMERIC_EQUIVALENCE_TESTS + BSON_TYPE_DISTINCTION_TESTS + NAN_INFINITY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_pullAll_data_type_matching(collection, test: UpdateTestCase):
    """Test $pullAll data type matching semantics."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
