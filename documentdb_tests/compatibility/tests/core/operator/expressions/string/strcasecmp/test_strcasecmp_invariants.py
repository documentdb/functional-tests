from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.test_case import BaseTestCase, pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.strcasecmp.utils.strcasecmp_common import (
    StrcasecmpTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_project

# Property [Return Type]: the result is always an int equal to -1, 0, or 1.
STRCASECMP_RETURN_TYPE_TESTS: list[StrcasecmpTest] = [
    StrcasecmpTest(
        "return_type_less",
        string1="a",
        string2="b",
        msg="$strcasecmp should return int type when result is less",
    ),
    StrcasecmpTest(
        "return_type_equal",
        string1="hello",
        string2="hello",
        msg="$strcasecmp should return int type when result is equal",
    ),
    StrcasecmpTest(
        "return_type_greater",
        string1="b",
        string2="a",
        msg="$strcasecmp should return int type when result is greater",
    ),
    StrcasecmpTest(
        "return_type_null",
        string1=None,
        string2="a",
        msg="$strcasecmp should return int type when first arg is null",
    ),
    StrcasecmpTest(
        "return_type_unicode",
        string1="café",
        string2="zoo",
        msg="$strcasecmp should return int type for Unicode string comparison",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_RETURN_TYPE_TESTS))
def test_strcasecmp_return_type(collection, test_case: StrcasecmpTest):
    """Test $strcasecmp result is always an int in {-1, 0, 1}."""
    expression = {"$strcasecmp": [test_case.string1, test_case.string2]}
    result = execute_project(
        collection,
        {
            "type": {"$type": expression},
            "inSet": {"$in": [expression, [-1, 0, 1]]},
        },
    )
    assertSuccess(result, [{"type": "int", "inSet": True}], msg=test_case.msg)


# Property [Antisymmetry]: strcasecmp(a, b) == -strcasecmp(b, a).
@dataclass(frozen=True)
class StrcasecmpAntisymTest(BaseTestCase):
    """Test case for $strcasecmp antisymmetry."""

    a: Any = None
    b: Any = None


STRCASECMP_ANTISYM_TESTS: list[StrcasecmpAntisymTest] = [
    StrcasecmpAntisymTest(
        "antisym_strings",
        a="apple",
        b="banana",
        msg="$strcasecmp should satisfy antisymmetry for distinct strings",
    ),
    StrcasecmpAntisymTest(
        "antisym_case",
        a="ABC",
        b="abc",
        msg="$strcasecmp should satisfy antisymmetry for case-different strings",
    ),
    StrcasecmpAntisymTest(
        "antisym_equal",
        a="hello",
        b="hello",
        msg="$strcasecmp should satisfy antisymmetry for equal strings",
    ),
    StrcasecmpAntisymTest(
        "antisym_empty",
        a="",
        b="a",
        msg="$strcasecmp should satisfy antisymmetry for empty vs non-empty",
    ),
    StrcasecmpAntisymTest(
        "antisym_null",
        a=None,
        b="a",
        msg="$strcasecmp should satisfy antisymmetry for null vs string",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_ANTISYM_TESTS))
def test_strcasecmp_antisymmetry(collection, test_case: StrcasecmpAntisymTest):
    """Test $strcasecmp antisymmetry."""
    forward = {"$strcasecmp": [test_case.a, test_case.b]}
    reverse = {"$strcasecmp": [test_case.b, test_case.a]}
    result = execute_project(
        collection,
        {
            "equal": {
                "$eq": [
                    forward,
                    {"$multiply": [reverse, -1]},
                ]
            },
        },
    )
    assertSuccess(result, [{"equal": True}], msg=test_case.msg)


# Property [Transitivity]: if a < b and b < c, then a < c.
@dataclass(frozen=True)
class StrcasecmpTransitivityTest(BaseTestCase):
    """Test case for $strcasecmp transitivity."""

    a: Any = None
    b: Any = None
    c: Any = None


STRCASECMP_TRANSITIVITY_TESTS: list[StrcasecmpTransitivityTest] = [
    StrcasecmpTransitivityTest(
        "transitivity_strings",
        a="apple",
        b="banana",
        c="cherry",
        msg="$strcasecmp should satisfy transitivity for apple < banana < cherry",
    ),
    StrcasecmpTransitivityTest(
        "transitivity_empty_first",
        a="",
        b="a",
        c="b",
        msg="$strcasecmp should satisfy transitivity for '' < 'a' < 'b'",
    ),
    StrcasecmpTransitivityTest(
        "transitivity_case_fold",
        a="A",
        b="b",
        c="c",
        msg="$strcasecmp should satisfy transitivity with case folding",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_TRANSITIVITY_TESTS))
def test_strcasecmp_transitivity(collection, test_case: StrcasecmpTransitivityTest):
    """Test $strcasecmp transitivity."""
    result = execute_project(
        collection,
        {
            "abLess": {"$eq": [{"$strcasecmp": [test_case.a, test_case.b]}, -1]},
            "bcLess": {"$eq": [{"$strcasecmp": [test_case.b, test_case.c]}, -1]},
            "acLess": {"$eq": [{"$strcasecmp": [test_case.a, test_case.c]}, -1]},
        },
    )
    assertSuccess(result, [{"abLess": True, "bcLess": True, "acLess": True}], msg=test_case.msg)
