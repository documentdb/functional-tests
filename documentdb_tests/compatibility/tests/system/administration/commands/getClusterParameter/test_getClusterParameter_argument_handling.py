"""Tests for getClusterParameter argument handling.

Covers accepted argument forms (single string, wildcard, array of
strings, duplicate names, unrecognized extra field) and BSON type
rejection for the command argument.
"""

import pytest

from documentdb_tests.compatibility.tests.system.administration.utils.administration_test_case import (  # noqa: E501
    AdministrationTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"
_VALID_PARAM_2 = "defaultMaxTimeMS"

_ARGUMENT_TYPE_SPEC = [
    BsonTypeTestCase(
        id="getClusterParameter_argument",
        msg="getClusterParameter should reject non-string/non-array argument types",
        keyword="getClusterParameter",
        valid_types=[BsonType.STRING, BsonType.ARRAY],
        default_error_code=TYPE_MISMATCH_ERROR,
        skip_rejection_types=[BsonType.NULL],
    ),
]

_ARGUMENT_REJECTION_CASES = generate_bson_rejection_test_cases(_ARGUMENT_TYPE_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", _ARGUMENT_REJECTION_CASES)
def test_getClusterParameter_argument_rejects_type(collection, bson_type, sample_value, spec):
    """Test getClusterParameter rejects non-string/non-array argument types."""
    result = execute_admin_command(collection, {"getClusterParameter": sample_value})
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"getClusterParameter should reject {bson_type.value} argument.",
    )


ARGUMENT_FORM_TESTS: list[AdministrationTestCase] = [
    AdministrationTestCase(
        id="wildcard_returns_all",
        command={"getClusterParameter": "*"},
        checks={"ok": Eq(1.0)},
        msg="Wildcard '*' should return ok:1",
    ),
    AdministrationTestCase(
        id="single_name_returns_one",
        command={"getClusterParameter": _VALID_PARAM},
        checks={"ok": Eq(1.0), "clusterParameters": Len(1)},
        msg="Single name should return ok:1 with one parameter",
    ),
    AdministrationTestCase(
        id="array_two_names_returns_two",
        command={"getClusterParameter": [_VALID_PARAM, _VALID_PARAM_2]},
        checks={"ok": Eq(1.0), "clusterParameters": Len(2)},
        msg="Array of two names should return two parameters",
    ),
    AdministrationTestCase(
        id="array_duplicate_names",
        command={"getClusterParameter": [_VALID_PARAM, _VALID_PARAM]},
        checks={"ok": Eq(1.0)},
        msg="Duplicate names in array should succeed",
    ),
    AdministrationTestCase(
        id="unrecognized_field_accepted",
        command={"getClusterParameter": "*", "unknownField": "test"},
        checks={"ok": Eq(1.0)},
        msg="Unrecognized extra field should be accepted",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_FORM_TESTS))
def test_getClusterParameter_argument_forms(collection, test):
    """Test accepted argument forms each return ok:1 with expected clusterParameters length."""
    result = execute_admin_command(collection, test.build_command())
    assertProperties(result, test.build_checks(), msg=test.msg, raw_res=True)
