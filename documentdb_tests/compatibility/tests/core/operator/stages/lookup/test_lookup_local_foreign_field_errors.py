"""Tests for $lookup localField/foreignField validation errors."""

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
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_NULL_BYTE_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    OVERFLOW_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [localField/foreignField Type Validation]: non-string non-null
# values for localField or foreignField produce a type mismatch error.
LOOKUP_LOCAL_FOREIGN_FIELD_TYPE_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "localfield_int_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": 123,
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (int)",
    ),
    LookupTestCase(
        "localfield_float_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": 1.5,
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (float)",
    ),
    LookupTestCase(
        "localfield_bool_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": True,
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (bool)",
    ),
    LookupTestCase(
        "localfield_array_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": [],
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (array)",
    ),
    LookupTestCase(
        "localfield_document_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": {"a": 1},
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (document)",
    ),
    LookupTestCase(
        "localfield_int64_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": Int64(1),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (Int64)",
    ),
    LookupTestCase(
        "localfield_decimal128_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": Decimal128("1"),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (Decimal128)",
    ),
    LookupTestCase(
        "localfield_binary_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": Binary(b"x"),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (Binary)",
    ),
    LookupTestCase(
        "localfield_objectid_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": ObjectId(),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (ObjectId)",
    ),
    LookupTestCase(
        "localfield_regex_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": Regex("x"),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (Regex)",
    ),
    LookupTestCase(
        "localfield_code_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": Code("x"),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (Code)",
    ),
    LookupTestCase(
        "localfield_code_with_scope_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": Code("x", {}),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (Code with scope)",
    ),
    LookupTestCase(
        "localfield_timestamp_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": Timestamp(1, 1),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (Timestamp)",
    ),
    LookupTestCase(
        "localfield_minkey_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": MinKey(),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (MinKey)",
    ),
    LookupTestCase(
        "localfield_maxkey_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": MaxKey(),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string localField (MaxKey)",
    ),
    LookupTestCase(
        "foreignfield_int_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": 123,
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (int)",
    ),
    LookupTestCase(
        "foreignfield_float_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": 1.5,
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (float)",
    ),
    LookupTestCase(
        "foreignfield_bool_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": True,
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (bool)",
    ),
    LookupTestCase(
        "foreignfield_array_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": [],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (array)",
    ),
    LookupTestCase(
        "foreignfield_document_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": {"a": 1},
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (document)",
    ),
    LookupTestCase(
        "foreignfield_int64_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": Int64(1),
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (Int64)",
    ),
    LookupTestCase(
        "foreignfield_decimal128_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": Decimal128("1"),
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (Decimal128)",
    ),
    LookupTestCase(
        "foreignfield_binary_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": Binary(b"x"),
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (Binary)",
    ),
    LookupTestCase(
        "foreignfield_objectid_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": ObjectId(),
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (ObjectId)",
    ),
    LookupTestCase(
        "foreignfield_regex_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": Regex("x"),
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (Regex)",
    ),
    LookupTestCase(
        "foreignfield_code_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": Code("x"),
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (Code)",
    ),
    LookupTestCase(
        "foreignfield_code_with_scope_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": Code("x", {}),
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (Code with scope)",
    ),
    LookupTestCase(
        "foreignfield_timestamp_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": Timestamp(1, 1),
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (Timestamp)",
    ),
    LookupTestCase(
        "foreignfield_minkey_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": MinKey(),
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (MinKey)",
    ),
    LookupTestCase(
        "foreignfield_maxkey_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": MaxKey(),
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-string foreignField (MaxKey)",
    ),
]

# Property [localField/foreignField Pairing Constraint]: localField and
# foreignField must both be present or both absent.
LOOKUP_LOCAL_FOREIGN_FIELD_PAIRING_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "null_localfield_produces_parse_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": None,
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject null localField",
    ),
    LookupTestCase(
        "null_foreignfield_produces_parse_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": None,
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject null foreignField",
    ),
    LookupTestCase(
        "empty_string_localfield_triggers_both_or_neither",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg=(
            "$lookup should treat empty string localField as absent"
            ' and trigger the "both or neither" error'
        ),
    ),
    LookupTestCase(
        "empty_string_foreignfield_triggers_both_or_neither",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg=(
            "$lookup should treat empty string foreignField as absent"
            ' and trigger the "both or neither" error'
        ),
    ),
    LookupTestCase(
        "localfield_without_foreignfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject localField without foreignField",
    ),
    LookupTestCase(
        "foreignfield_without_localfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject foreignField without localField",
    ),
]

# Property [localField/foreignField Path Validation]: invalid field path
# syntax in localField or foreignField produces the appropriate path
# validation error.
LOOKUP_LOCAL_FOREIGN_FIELD_PATH_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "dollar_prefix_localfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "$field",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$lookup should reject localField starting with $",
    ),
    LookupTestCase(
        "dollar_prefix_foreignfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "$field",
                    "as": "j",
                }
            }
        ],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$lookup should reject foreignField starting with $",
    ),
    LookupTestCase(
        "leading_dot_localfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": ".field",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$lookup should reject localField with a leading dot",
    ),
    LookupTestCase(
        "leading_dot_foreignfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": ".field",
                    "as": "j",
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$lookup should reject foreignField with a leading dot",
    ),
    LookupTestCase(
        "trailing_dot_localfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "field.",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$lookup should reject localField with a trailing dot",
    ),
    LookupTestCase(
        "trailing_dot_foreignfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "field.",
                    "as": "j",
                }
            }
        ],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$lookup should reject foreignField with a trailing dot",
    ),
    LookupTestCase(
        "double_dots_localfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "a..b",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$lookup should reject localField with double dots",
    ),
    LookupTestCase(
        "double_dots_foreignfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "a..b",
                    "as": "j",
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$lookup should reject foreignField with double dots",
    ),
    LookupTestCase(
        "null_byte_localfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "a\x00b",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$lookup should reject localField with a null byte",
    ),
    LookupTestCase(
        "null_byte_foreignfield",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "a\x00b",
                    "as": "j",
                }
            }
        ],
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$lookup should reject foreignField with a null byte",
    ),
    LookupTestCase(
        "deep_path_localfield_exceeds_200_levels",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": ".".join(["a"] * 201),
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=OVERFLOW_ERROR,
        msg="$lookup should reject localField path depth exceeding 200 levels",
    ),
    LookupTestCase(
        "deep_path_foreignfield_exceeds_200_levels",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": ".".join(["a"] * 201),
                    "as": "j",
                }
            }
        ],
        error_code=OVERFLOW_ERROR,
        msg="$lookup should reject foreignField path depth exceeding 200 levels",
    ),
]

LOOKUP_LOCAL_FOREIGN_FIELD_ERROR_TESTS: list[LookupTestCase] = (
    LOOKUP_LOCAL_FOREIGN_FIELD_TYPE_ERROR_TESTS
    + LOOKUP_LOCAL_FOREIGN_FIELD_PAIRING_ERROR_TESTS
    + LOOKUP_LOCAL_FOREIGN_FIELD_PATH_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_LOCAL_FOREIGN_FIELD_ERROR_TESTS))
def test_lookup_local_foreign_field_errors(collection, test_case: LookupTestCase):
    """Test $lookup localField/foreignField validation errors."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
