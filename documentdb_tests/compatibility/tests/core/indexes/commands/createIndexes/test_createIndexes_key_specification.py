"""Tests for createIndexes key specification.

Validates key direction values and field names.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

KEY_DIRECTION_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="ascending_key",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Ascending (1) key succeeds",
    ),
    IndexTestCase(
        id="descending_key",
        indexes=({"key": {"a": -1}, "name": "a_neg1"},),
        msg="Descending (-1) key succeeds",
    ),
    IndexTestCase(
        id="key_direction_two",
        indexes=({"key": {"a": 2}, "name": "a_2"},),
        msg="Direction 2 succeeds",
    ),
    IndexTestCase(
        id="fractional_positive_direction",
        indexes=({"key": {"a": 1.9999}, "name": "a_frac_pos"},),
        msg="Fractional positive direction (1.9999) succeeds",
    ),
    IndexTestCase(
        id="fractional_negative_direction",
        indexes=({"key": {"a": -1.9999}, "name": "a_frac_neg"},),
        msg="Fractional negative direction (-1.9999) succeeds",
    ),
    IndexTestCase(
        id="fractional_near_zero_direction",
        indexes=({"key": {"a": 0.9999}, "name": "a_frac_zero"},),
        msg="Fractional direction (0.9999) succeeds",
    ),
]

KEY_FIELD_NAME_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="nested_field",
        indexes=({"key": {"a.b": 1}, "name": "a.b_1"},),
        msg="Nested field a.b succeeds",
    ),
    IndexTestCase(
        id="deeply_nested_field",
        indexes=({"key": {"a.b.c.d": 1}, "name": "a.b.c.d_1"},),
        msg="Deeply nested field a.b.c.d succeeds",
    ),
    IndexTestCase(
        id="numeric_field_name",
        indexes=({"key": {"0": 1}, "name": "0_1"},),
        msg="Numeric field name succeeds",
    ),
    IndexTestCase(
        id="field_with_spaces",
        indexes=({"key": {"my field": 1}, "name": "my field_1"},),
        msg="Field name with spaces succeeds",
    ),
    IndexTestCase(
        id="unicode_field_name",
        indexes=({"key": {"日本語": 1}, "name": "unicode_1"},),
        msg="Unicode field name succeeds",
    ),
    IndexTestCase(
        id="long_field_name",
        indexes=({"key": {"a" * 100: 1}, "name": "long_field_1"},),
        msg="Very long field name (100 chars) succeeds",
    ),
]

ALL_TESTS = KEY_DIRECTION_TESTS + KEY_FIELD_NAME_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_createIndexes_key_specification(collection, test):
    """Test createIndexes key specification patterns."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": list(test.indexes),
        },
    )
    assertSuccessPartial(result, index_created_response(), test.msg)


def test_createIndexes_id_field(collection):
    """Test creating index on _id field is a noop (default _id index exists)."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"_id": 1}, "name": "_id_1"}],
        },
    )
    assertSuccessPartial(
        result,
        index_created_response(num_indexes_before=1, num_indexes_after=1),
        "_id field succeeds",
    )
