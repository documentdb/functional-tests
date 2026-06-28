"""
Error case tests for $mul update field operator.

Tests path validation, scalar path traversal, _id immutability, and int64 overflow.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    EMPTY_FIELD_NAME_ERROR,
    IMMUTABLE_FIELD_ERROR,
    PATH_NOT_VIABLE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_MAX, INT64_MIN

PATH_VALIDATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "empty_field_name",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$mul": {"": 2}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="$mul with empty field name should produce error",
    ),
    UpdateTestCase(
        "array_traversal_through_object",
        setup_docs=[{"_id": 1, "a": [{"b": 5}]}],
        query={"_id": 1},
        update={"$mul": {"a.b": 2}},
        error_code=PATH_NOT_VIABLE_ERROR,
        msg="$mul through array without numeric index should produce error",
    ),
]

SCALAR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "create_under_scalar",
        setup_docs=[{"_id": 1, "a": 5}],
        query={"_id": 1},
        update={"$mul": {"a.b": 2}},
        error_code=PATH_NOT_VIABLE_ERROR,
        msg="$mul creating sub-field under scalar should produce error",
    ),
    UpdateTestCase(
        "mul_on_array_field",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$mul": {"arr": 3}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$mul on array field without index should produce type mismatch error",
    ),
]

ID_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "mul_on_id_field",
        setup_docs=[{"_id": 5, "val": 10}],
        query={"_id": 5},
        update={"$mul": {"_id": 2}},
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$mul on _id field should produce immutable field error",
    ),
    UpdateTestCase(
        "mul_on_id_field_not_in_filter",
        setup_docs=[{"_id": 5, "val": 10, "group": "a"}],
        query={"group": "a"},
        update={"$mul": {"_id": 2}},
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$mul on _id field when _id not in filter should produce immutable field error",
    ),
]

INT64_OVERFLOW_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int64_max_x_2",
        setup_docs=[{"_id": 1, "val": INT64_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(2)}},
        error_code=BAD_VALUE_ERROR,
        msg="INT64_MAX × 2 should produce overflow error",
    ),
    UpdateTestCase(
        "int64_min_x_neg1",
        setup_docs=[{"_id": 1, "val": INT64_MIN}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(-1)}},
        error_code=BAD_VALUE_ERROR,
        msg="INT64_MIN × (-1) should produce overflow error",
    ),
    UpdateTestCase(
        "int64_min_x_2",
        setup_docs=[{"_id": 1, "val": INT64_MIN}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(2)}},
        error_code=BAD_VALUE_ERROR,
        msg="INT64_MIN × 2 should produce overflow error",
    ),
]

ALL_ERROR_TESTS = PATH_VALIDATION_TESTS + SCALAR_TESTS + ID_FIELD_TESTS + INT64_OVERFLOW_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_mul_error(collection, test: UpdateTestCase):
    """Test $mul error handling."""
    collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]
