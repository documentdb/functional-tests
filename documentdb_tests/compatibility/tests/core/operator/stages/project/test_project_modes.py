"""Tests for $project inclusion and exclusion mode determination."""

from __future__ import annotations

from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_ZERO,
)

# Property [Inclusion Semantics]: only explicitly included fields (plus _id)
# appear in the output.
PROJECT_INCLUSION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "inclusion_id_default_and_only_specified",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[{"$project": {"a": 1}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should include _id by default and only output explicitly included fields",
    ),
    StageTestCase(
        "inclusion_nonexistent_field_omitted",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a": 1, "z": 1}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should silently omit a non-existent included field",
    ),
    StageTestCase(
        "inclusion_multiple_fields",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[{"$project": {"a": 1, "c": 1}}],
        expected=[{"_id": 1, "a": 10, "c": 30}],
        msg="$project should include multiple fields simultaneously",
    ),
]

# Property [Truthy Inclusion Flags]: various non-zero numeric types and true
# are all treated as inclusion flags equivalent to 1.
PROJECT_INCLUSION_FLAG_TESTS: list[StageTestCase] = [
    StageTestCase(
        "inclusion_flag_int_positive",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": 2}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat non-zero positive integer as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_int_negative",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": -1}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat negative integer as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_float_fraction",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": 0.5}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat non-zero float as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_float_nan",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": FLOAT_NAN}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat NaN as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_float_infinity",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": FLOAT_INFINITY}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat Infinity as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_float_neg_infinity",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": FLOAT_NEGATIVE_INFINITY}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat -Infinity as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_int64",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": Int64(99)}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat non-zero Int64 as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_decimal128",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": Decimal128("42")}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat non-zero Decimal128 as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_decimal128_nan",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": DECIMAL128_NAN}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat Decimal128('NaN') as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_decimal128_infinity",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": DECIMAL128_INFINITY}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat Decimal128('Infinity') as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_decimal128_neg_infinity",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": DECIMAL128_NEGATIVE_INFINITY}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat Decimal128('-Infinity') as truthy inclusion flag",
    ),
    StageTestCase(
        "inclusion_flag_bool_true",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": True}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should treat true as inclusion flag",
    ),
]

# Property [Exclusion Semantics]: excluding a field removes it from output
# while all other fields are returned.
PROJECT_EXCLUSION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "exclusion_removes_field",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[{"$project": {"b": 0}}],
        expected=[{"_id": 1, "a": 10, "c": 30}],
        msg="$project should remove excluded field and return all others",
    ),
    StageTestCase(
        "exclusion_nonexistent_field",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"z": 0}}],
        expected=[{"_id": 1, "a": 10, "b": 20}],
        msg="$project should have no effect when excluding a non-existent field",
    ),
    StageTestCase(
        "exclusion_multiple_fields",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[{"$project": {"a": 0, "c": 0}}],
        expected=[{"_id": 1, "b": 20}],
        msg="$project should exclude multiple fields simultaneously",
    ),
]

# Property [Falsy Exclusion Flags]: various zero-valued numeric types and false
# are all treated as exclusion flags equivalent to 0.
PROJECT_EXCLUSION_FLAG_TESTS: list[StageTestCase] = [
    StageTestCase(
        "exclusion_flag_int_zero",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": 0}}],
        expected=[{"_id": 1, "b": 20}],
        msg="$project should treat 0 as falsy exclusion flag",
    ),
    StageTestCase(
        "exclusion_flag_float_zero",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": DOUBLE_ZERO}}],
        expected=[{"_id": 1, "b": 20}],
        msg="$project should treat 0.0 as falsy exclusion flag",
    ),
    StageTestCase(
        "exclusion_flag_float_neg_zero",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": DOUBLE_NEGATIVE_ZERO}}],
        expected=[{"_id": 1, "b": 20}],
        msg="$project should treat -0.0 as falsy exclusion flag",
    ),
    StageTestCase(
        "exclusion_flag_int64_zero",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": INT64_ZERO}}],
        expected=[{"_id": 1, "b": 20}],
        msg="$project should treat Int64(0) as falsy exclusion flag",
    ),
    StageTestCase(
        "exclusion_flag_decimal128_zero",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": DECIMAL128_ZERO}}],
        expected=[{"_id": 1, "b": 20}],
        msg="$project should treat Decimal128('0') as falsy exclusion flag",
    ),
    StageTestCase(
        "exclusion_flag_decimal128_neg_zero",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": DECIMAL128_NEGATIVE_ZERO}}],
        expected=[{"_id": 1, "b": 20}],
        msg="$project should treat Decimal128('-0') as falsy exclusion flag",
    ),
    StageTestCase(
        "exclusion_flag_bool_false",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": False}}],
        expected=[{"_id": 1, "b": 20}],
        msg="$project should treat false as exclusion flag",
    ),
]

PROJECT_MODE_TESTS = (
    PROJECT_INCLUSION_TESTS
    + PROJECT_INCLUSION_FLAG_TESTS
    + PROJECT_EXCLUSION_TESTS
    + PROJECT_EXCLUSION_FLAG_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(PROJECT_MODE_TESTS))
def test_project_modes(collection: Any, test_case: StageTestCase) -> None:
    """Test $project inclusion and exclusion modes."""
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
