"""Tests for $lookup let parameter validation errors."""

from __future__ import annotations

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    LET_UNDEFINED_VARIABLE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [let Parameter Type Validation]: non-document non-null values
# for let produce a type mismatch error.
LOOKUP_LET_TYPE_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_int_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": 123,
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (int)",
    ),
    LookupTestCase(
        "let_string_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": "abc",
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (string)",
    ),
    LookupTestCase(
        "let_array_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": [1],
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (array)",
    ),
    LookupTestCase(
        "let_bool_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": True,
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (bool)",
    ),
    LookupTestCase(
        "let_float_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": 1.5,
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (float)",
    ),
    LookupTestCase(
        "let_int64_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": Int64(1),
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (Int64)",
    ),
    LookupTestCase(
        "let_decimal128_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": Decimal128("1"),
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (Decimal128)",
    ),
    LookupTestCase(
        "let_binary_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": Binary(b"x"),
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (Binary)",
    ),
    LookupTestCase(
        "let_objectid_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": ObjectId(),
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (ObjectId)",
    ),
    LookupTestCase(
        "let_regex_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": Regex("x"),
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (Regex)",
    ),
    LookupTestCase(
        "let_code_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": Code("x"),
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (Code)",
    ),
    LookupTestCase(
        "let_code_with_scope_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": Code("x", {}),
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (Code with scope)",
    ),
    LookupTestCase(
        "let_timestamp_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": Timestamp(1, 1),
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (Timestamp)",
    ),
    LookupTestCase(
        "let_minkey_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": MinKey(),
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (MinKey)",
    ),
    LookupTestCase(
        "let_maxkey_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": MaxKey(),
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-document let (MaxKey)",
    ),
]

# Property [let Requires pipeline]: let without pipeline or let with
# localField/foreignField but no pipeline produces a parse error.
LOOKUP_LET_REQUIRES_PIPELINE_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_without_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$_id"},
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject let without pipeline",
    ),
    LookupTestCase(
        "let_with_local_foreign_field_no_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$_id"},
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject let with localField/foreignField but no pipeline",
    ),
]

# Property [let Variable Name Validation]: let variable names must
# conform to the server's identifier rules for start and continuation
# characters.
LOOKUP_LET_VARIABLE_NAME_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_varname_uppercase_ascii_start",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"Abc": "$_id"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject let variable name starting with uppercase ASCII",
    ),
    LookupTestCase(
        "let_varname_digit_start",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"1abc": "$_id"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject let variable name starting with a digit",
    ),
    LookupTestCase(
        "let_varname_underscore_start",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"_abc": "$_id"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject let variable name starting with underscore",
    ),
    LookupTestCase(
        "let_varname_dollar_start",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"$abc": "$_id"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject let variable name starting with dollar sign",
    ),
    LookupTestCase(
        "let_varname_dot_start",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {".abc": "$_id"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject let variable name starting with dot",
    ),
    LookupTestCase(
        "let_varname_empty",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"": "$_id"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject empty string as let variable name",
    ),
    LookupTestCase(
        "let_varname_dot_in_continuation",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"a.b": "$_id"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject dot in let variable name continuation",
    ),
    LookupTestCase(
        "let_varname_dollar_in_continuation",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"a$b": "$_id"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject dollar sign in let variable name continuation",
    ),
    LookupTestCase(
        "let_varname_hyphen_in_continuation",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"a-b": "$_id"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject hyphen in let variable name continuation",
    ),
    LookupTestCase(
        "let_varname_space_in_continuation",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"a b": "$_id"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject space in let variable name continuation",
    ),
]

# Property [let Variable Reference Errors]: self-referencing and
# cross-referencing between sibling let variable definitions produce an
# undefined variable error.
LOOKUP_LET_VARIABLE_REFERENCE_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_self_referencing_variable",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$$x"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$lookup should reject self-referencing let variable definitions",
    ),
    LookupTestCase(
        "let_cross_referencing_variables",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$$y", "y": "$$x"},
                    "pipeline": [],
                    "as": "j",
                }
            }
        ],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$lookup should reject cross-referencing between sibling let variable definitions",
    ),
]

LOOKUP_LET_ERROR_TESTS: list[LookupTestCase] = (
    LOOKUP_LET_TYPE_ERROR_TESTS
    + LOOKUP_LET_REQUIRES_PIPELINE_ERROR_TESTS
    + LOOKUP_LET_VARIABLE_NAME_ERROR_TESTS
    + LOOKUP_LET_VARIABLE_REFERENCE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_LET_ERROR_TESTS))
def test_lookup_let_errors(collection, test_case: LookupTestCase):
    """Test $lookup let parameter validation errors."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
