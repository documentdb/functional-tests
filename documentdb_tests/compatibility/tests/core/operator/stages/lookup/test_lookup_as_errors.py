"""Tests for $lookup as parameter validation errors."""

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
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_EMPTY_ERROR,
    FIELD_PATH_NULL_BYTE_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [as Parameter Type Errors]: non-string values for the as
# parameter produce a type or missing-field error.
LOOKUP_AS_TYPE_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "as_int_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": 123,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (int)",
    ),
    LookupTestCase(
        "as_bool_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": True,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (bool)",
    ),
    LookupTestCase(
        "as_array_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": ["x"],
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (array)",
    ),
    LookupTestCase(
        "as_float_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": 1.5,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (float)",
    ),
    LookupTestCase(
        "as_dict_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": {"a": 1},
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (document)",
    ),
    LookupTestCase(
        "as_int64_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": Int64(1),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (Int64)",
    ),
    LookupTestCase(
        "as_decimal128_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": Decimal128("1"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (Decimal128)",
    ),
    LookupTestCase(
        "as_binary_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": Binary(b"x"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (Binary)",
    ),
    LookupTestCase(
        "as_objectid_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": ObjectId(),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (ObjectId)",
    ),
    LookupTestCase(
        "as_regex_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": Regex("x"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (Regex)",
    ),
    LookupTestCase(
        "as_code_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": Code("x"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (Code)",
    ),
    LookupTestCase(
        "as_code_with_scope_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": Code("x", {}),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (Code with scope)",
    ),
    LookupTestCase(
        "as_timestamp_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": Timestamp(1, 1),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (Timestamp)",
    ),
    LookupTestCase(
        "as_minkey_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": MinKey(),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (MinKey)",
    ),
    LookupTestCase(
        "as_maxkey_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": MaxKey(),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string as (MaxKey)",
    ),
    LookupTestCase(
        "as_null_treated_as_missing",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": None,
                }
            }
        ],
        error_code=MISSING_FIELD_ERROR,
        msg="$lookup should treat as=null as missing required field",
    ),
    LookupTestCase(
        "as_omitted_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                }
            }
        ],
        error_code=MISSING_FIELD_ERROR,
        msg="$lookup should reject omitting the as parameter",
    ),
]

# Property [as Parameter Path Validation Errors]: the as parameter
# rejects invalid field path syntax.
LOOKUP_AS_PATH_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "as_dollar_prefix_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "$bad",
                }
            }
        ],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$lookup should reject as with a dollar prefix",
    ),
    LookupTestCase(
        "as_empty_string_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "",
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$lookup should reject as with an empty string",
    ),
    LookupTestCase(
        "as_leading_dot_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": ".bad",
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$lookup should reject as with a leading dot",
    ),
    LookupTestCase(
        "as_trailing_dot_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "bad.",
                }
            }
        ],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$lookup should reject as with a trailing dot",
    ),
    LookupTestCase(
        "as_double_dots_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "a..b",
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$lookup should reject as with double dots",
    ),
    LookupTestCase(
        "as_null_byte_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "a\x00b",
                }
            }
        ],
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$lookup should reject as with a null byte",
    ),
]

LOOKUP_AS_ERROR_TESTS: list[LookupTestCase] = (
    LOOKUP_AS_TYPE_ERROR_TESTS + LOOKUP_AS_PATH_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_AS_ERROR_TESTS))
def test_lookup_as_errors(collection, test_case: LookupTestCase):
    """Test $lookup as parameter validation errors."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
