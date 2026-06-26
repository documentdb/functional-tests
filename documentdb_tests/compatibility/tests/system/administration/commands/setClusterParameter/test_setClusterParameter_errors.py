"""Tests for setClusterParameter error cases.

Validates error scenarios including non-admin database, unknown/empty/case-variant/
node-local parameter names, multiple parameters, invalid argument forms, wrong value
types, out-of-range and empty sub-document values, dollar-prefixed fields, and
rejected options (writeConcern, apiStrict).
"""

import pytest

from documentdb_tests.compatibility.tests.system.administration.utils.admin_test_case import (
    AdminTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    API_STRICT_ERROR,
    BAD_VALUE_ERROR,
    DOLLAR_PREFIXED_FIELD_NAME_ERROR,
    INVALID_OPTIONS_ERROR,
    MISSING_FIELD_ERROR,
    NO_SUCH_KEY_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]

PARAM_NAME = "changeStreamOptions"
VALID_VALUE = {"preAndPostImages": {"expireAfterSeconds": 7200}}


ERROR_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "multiple_parameters",
        command={
            "setClusterParameter": {
                PARAM_NAME: VALID_VALUE,
                "changeStreams": {"expireAfterSeconds": 3600},
            }
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Setting multiple parameters in one call should be rejected",
    ),
    AdminTestCase(
        "unknown_parameter",
        command={"setClusterParameter": {"unknownParam999": {"x": 1}}},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Unknown parameter name should be rejected",
    ),
    AdminTestCase(
        "api_strict_rejected",
        command={
            "setClusterParameter": {PARAM_NAME: VALID_VALUE},
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="apiStrict mode should reject setClusterParameter",
    ),
    AdminTestCase(
        "empty_document",
        command={"setClusterParameter": {}},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Empty document should fail",
    ),
    AdminTestCase(
        "null_argument",
        command={"setClusterParameter": None},
        error_code=MISSING_FIELD_ERROR,
        msg="Null argument should fail",
    ),
    AdminTestCase(
        "empty_key",
        command={"setClusterParameter": {"": {"x": 1}}},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Empty key should fail",
    ),
    AdminTestCase(
        "wrong_type_value",
        command={"setClusterParameter": {PARAM_NAME: "invalid"}},
        error_code=BAD_VALUE_ERROR,
        msg="String value should fail for document-typed parameter",
    ),
    AdminTestCase(
        "dollar_prefixed_field",
        command={"setClusterParameter": {PARAM_NAME: {"$bad": 1}}},
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="Dollar-prefixed field should fail",
    ),
    AdminTestCase(
        "case_variant_parameter_name",
        command={"setClusterParameter": {"ChangeStreamOptions": VALID_VALUE}},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Case-variant name should fail (names are case-sensitive)",
    ),
    AdminTestCase(
        "node_local_parameter",
        command={"setClusterParameter": {"logLevel": {"verbosity": 1}}},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Node-local parameter should be rejected by setClusterParameter",
    ),
    AdminTestCase(
        "extra_fields_in_value",
        command={
            "setClusterParameter": {
                PARAM_NAME: {
                    "preAndPostImages": {"expireAfterSeconds": 7200},
                    "extraField": "nope",
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Extra fields in parameter value should fail",
    ),
    AdminTestCase(
        "null_document_field_value",
        command={"setClusterParameter": {PARAM_NAME: {"preAndPostImages": None}}},
        error_code=BAD_VALUE_ERROR,
        msg="Null for a document-typed parameter field should fail",
    ),
    AdminTestCase(
        "negative_expireAfterSeconds",
        command={"setClusterParameter": {"changeStreams": {"expireAfterSeconds": -1}}},
        error_code=BAD_VALUE_ERROR,
        msg="Negative expireAfterSeconds (out of range for a positive-int field) should fail",
    ),
    AdminTestCase(
        "empty_subdocument_changeStreamOptions",
        command={"setClusterParameter": {PARAM_NAME: {}}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty sub-document for changeStreamOptions (required field missing) should fail",
    ),
    AdminTestCase(
        "changeStreamOptions_expireAfterSeconds_invalid_string",
        command={
            "setClusterParameter": {PARAM_NAME: {"preAndPostImages": {"expireAfterSeconds": "on"}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="changeStreamOptions.expireAfterSeconds rejects non-'off' string values",
    ),
    AdminTestCase(
        "changeStreamOptions_expireAfterSeconds_bool_rejected",
        command={
            "setClusterParameter": {PARAM_NAME: {"preAndPostImages": {"expireAfterSeconds": True}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="changeStreamOptions.expireAfterSeconds rejects bool (expects string or numeric)",
    ),
    AdminTestCase(
        "writeConcern_rejected",
        command={"setClusterParameter": {PARAM_NAME: VALID_VALUE}, "writeConcern": {"w": 1}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="writeConcern should be rejected",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_setClusterParameter_errors(collection, test):
    """Test setClusterParameter returns the expected error code for failure scenarios."""
    result = execute_admin_command(collection, test.command)
    assertResult(result, error_code=test.error_code, msg=test.msg)


def test_setClusterParameter_non_admin_database(collection):
    """Test setClusterParameter is rejected on non-admin database."""
    result = execute_command(collection, {"setClusterParameter": {PARAM_NAME: VALID_VALUE}})
    assertResult(result, error_code=UNAUTHORIZED_ERROR, msg="Non-admin db should be rejected")
