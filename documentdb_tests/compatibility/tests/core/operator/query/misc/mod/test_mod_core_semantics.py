"""
Tests for $mod query operator core modulo semantics.

Covers basic modulo matching, floating-point truncation toward zero,
negative dividend behavior, and truncation of field values.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

BASIC_DOCS = [{"_id": i, "a": i} for i in range(13)]

CORE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="mod_4_0_matches_multiples_of_4",
        filter={"a": {"$mod": [4, 0]}},
        doc=BASIC_DOCS,
        expected=[{"_id": 0, "a": 0}, {"_id": 4, "a": 4}, {"_id": 8, "a": 8}, {"_id": 12, "a": 12}],
        msg="$mod [4,0] should match multiples of 4",
    ),
    QueryTestCase(
        id="mod_4_1_matches_remainder_1",
        filter={"a": {"$mod": [4, 1]}},
        doc=BASIC_DOCS,
        expected=[{"_id": 1, "a": 1}, {"_id": 5, "a": 5}, {"_id": 9, "a": 9}],
        msg="$mod [4,1] should match values with remainder 1",
    ),
    QueryTestCase(
        id="mod_4_3_matches_remainder_3",
        filter={"a": {"$mod": [4, 3]}},
        doc=BASIC_DOCS,
        expected=[{"_id": 3, "a": 3}, {"_id": 7, "a": 7}, {"_id": 11, "a": 11}],
        msg="$mod [4,3] should match values with remainder 3",
    ),
    QueryTestCase(
        id="mod_1_0_matches_all_integers",
        filter={"a": {"$mod": [1, 0]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 5}, {"_id": 3, "a": -3}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 5}, {"_id": 3, "a": -3}],
        msg="$mod [1,0] should match all integers",
    ),
    QueryTestCase(
        id="mod_2_0_matches_even",
        filter={"a": {"$mod": [2, 0]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}, {"_id": 4, "a": 4}],
        expected=[{"_id": 2, "a": 2}, {"_id": 4, "a": 4}],
        msg="$mod [2,0] should match even numbers",
    ),
    QueryTestCase(
        id="mod_2_1_matches_odd",
        filter={"a": {"$mod": [2, 1]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}, {"_id": 4, "a": 4}],
        expected=[{"_id": 1, "a": 1}, {"_id": 3, "a": 3}],
        msg="$mod [2,1] should match odd numbers",
    ),
]


TRUNCATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="divisor_4_0_same_as_4",
        filter={"a": {"$mod": [4.0, 0]}},
        doc=BASIC_DOCS[:9],
        expected=[{"_id": 0, "a": 0}, {"_id": 4, "a": 4}, {"_id": 8, "a": 8}],
        msg="$mod [4.0,0] should behave same as [4,0]",
    ),
    QueryTestCase(
        id="divisor_4_5_truncates_to_4",
        filter={"a": {"$mod": [4.5, 0]}},
        doc=BASIC_DOCS[:9],
        expected=[{"_id": 0, "a": 0}, {"_id": 4, "a": 4}, {"_id": 8, "a": 8}],
        msg="$mod [4.5,0] should truncate divisor to 4",
    ),
    QueryTestCase(
        id="neg_divisor_4_5_truncates_toward_zero",
        filter={"a": {"$mod": [-4.5, 0]}},
        doc=BASIC_DOCS[:9],
        expected=[{"_id": 0, "a": 0}, {"_id": 4, "a": 4}, {"_id": 8, "a": 8}],
        msg="$mod [-4.5,0] should truncate toward zero to -4",
    ),
    QueryTestCase(
        id="remainder_1_7_truncates_to_1",
        filter={"a": {"$mod": [3, 1.7]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 4}, {"_id": 3, "a": 7}, {"_id": 4, "a": 3}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 4}, {"_id": 3, "a": 7}],
        msg="$mod [3,1.7] should truncate remainder to 1",
    ),
    QueryTestCase(
        id="remainder_neg_1_7_truncates_toward_zero",
        filter={"a": {"$mod": [3, -1.7]}},
        doc=[{"_id": 1, "a": -1}, {"_id": 2, "a": -4}, {"_id": 3, "a": 2}, {"_id": 4, "a": 3}],
        expected=[{"_id": 1, "a": -1}, {"_id": 2, "a": -4}],
        msg="$mod [3,-1.7] should truncate remainder toward zero to -1",
    ),
    # Truncation of field values (double and decimal128 fields)
    QueryTestCase(
        id="double_field_truncation",
        filter={"a": {"$mod": [3, 0]}},
        doc=[
            {"_id": 1, "a": 3.2},
            {"_id": 2, "a": 3.7},
            {"_id": 3, "a": 6.1},
            {"_id": 4, "a": 6.9},
        ],
        expected=[
            {"_id": 1, "a": 3.2},
            {"_id": 2, "a": 3.7},
            {"_id": 3, "a": 6.1},
            {"_id": 4, "a": 6.9},
        ],
        msg="$mod on double fields should truncate field values for modulo",
    ),
    QueryTestCase(
        id="decimal128_field_truncation",
        filter={"a": {"$mod": [3, 0]}},
        doc=[
            {"_id": 1, "a": Decimal128("3.2")},
            {"_id": 2, "a": Decimal128("3.7")},
            {"_id": 3, "a": Decimal128("6.1")},
            {"_id": 4, "a": Decimal128("6.9")},
        ],
        expected=[
            {"_id": 1, "a": Decimal128("3.2")},
            {"_id": 2, "a": Decimal128("3.7")},
            {"_id": 3, "a": Decimal128("6.1")},
            {"_id": 4, "a": Decimal128("6.9")},
        ],
        msg="$mod on decimal128 fields should truncate field values for modulo",
    ),
]


NEGATIVE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="neg5_mod_3_0_no_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": -5}],
        expected=[],
        msg="-5 % 3 = -2, should not match remainder 0",
    ),
    QueryTestCase(
        id="neg6_mod_3_0_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": -6}],
        expected=[{"_id": 1, "a": -6}],
        msg="-6 % 3 = 0, should match remainder 0",
    ),
    QueryTestCase(
        id="neg1_mod_3_neg1_match",
        filter={"a": {"$mod": [3, -1]}},
        doc=[{"_id": 1, "a": -1}],
        expected=[{"_id": 1, "a": -1}],
        msg="-1 % 3 = -1, should match remainder -1",
    ),
    QueryTestCase(
        id="neg3_mod_3_0_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": -3}],
        expected=[{"_id": 1, "a": -3}],
        msg="-3 % 3 = 0, should match remainder 0",
    ),
    QueryTestCase(
        id="neg1_mod_2_neg1_match",
        filter={"a": {"$mod": [2, -1]}},
        doc=[{"_id": 1, "a": -1}],
        expected=[{"_id": 1, "a": -1}],
        msg="-1 % 2 = -1, should match remainder -1",
    ),
    QueryTestCase(
        id="neg1_mod_2_1_no_match",
        filter={"a": {"$mod": [2, 1]}},
        doc=[{"_id": 1, "a": -1}],
        expected=[],
        msg="-1 % 2 = -1, should not match remainder 1",
    ),
    QueryTestCase(
        id="negative_divisor_field5_mod_neg3_2",
        filter={"a": {"$mod": [-3, 2]}},
        doc=[{"_id": 1, "a": 5}],
        expected=[{"_id": 1, "a": 5}],
        msg="5 % -3 = 2, should match remainder 2",
    ),
    QueryTestCase(
        id="neg_field_neg_divisor_neg_remainder",
        filter={"a": {"$mod": [-3, -2]}},
        doc=[{"_id": 1, "a": -5}, {"_id": 2, "a": -2}, {"_id": 3, "a": -6}, {"_id": 4, "a": 5}],
        expected=[{"_id": 1, "a": -5}, {"_id": 2, "a": -2}],
        msg="-5 % -3 = -2 and -2 % -3 = -2, should match remainder -2",
    ),
    QueryTestCase(
        id="neg_divisor_neg3_remainder_0",
        filter={"a": {"$mod": [-3, 0]}},
        doc=[{"_id": 1, "a": 6}, {"_id": 2, "a": -6}, {"_id": 3, "a": 5}],
        expected=[{"_id": 1, "a": 6}, {"_id": 2, "a": -6}],
        msg="$mod [-3,0] should match multiples of 3",
    ),
]

ALL_TESTS = CORE_TESTS + TRUNCATION_TESTS + NEGATIVE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_mod_core_semantics(collection, test):
    """Parametrized test for $mod core modulo semantics."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
