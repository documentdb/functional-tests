"""Tests for $lookup from parameter validation."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    INVALID_NAMESPACE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [from Parameter Not Expression Context]: from is not an
# expression context and has no practical namespace length limit.
LOOKUP_FROM_PARAMETER_NOT_EXPRESSION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "double_dollar_now_treated_as_literal_name",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "$$NOW",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": []}],
        msg=(
            '$lookup should treat "$$NOW" in from as a literal'
            " collection name, not resolve it as a system variable"
        ),
    ),
    LookupTestCase(
        "long_collection_name_accepted",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "x" * 10_000,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": []}],
        msg="$lookup should accept from collection names up to 10,000+ characters without error",
    ),
]

# Property [from Parameter Special Names]: from accepts special characters
# and non-ASCII strings as valid collection names.
LOOKUP_FROM_PARAMETER_SPECIAL_NAMES: list[LookupTestCase] = [
    LookupTestCase(
        "whitespace",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "a b c",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": []}],
        msg="$lookup should accept from with whitespace in collection name",
    ),
    LookupTestCase(
        "dot_in_middle",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "a.b.c",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": []}],
        msg="$lookup should accept from with dots in collection name",
    ),
    LookupTestCase(
        "trailing_dot",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "abc.",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": []}],
        msg="$lookup should accept from with trailing dot in collection name",
    ),
    LookupTestCase(
        "dollar_prefix",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "$abc",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": []}],
        msg="$lookup should accept from with dollar prefix in collection name",
    ),
    LookupTestCase(
        "control_character",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "a\x01b",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": []}],
        msg="$lookup should accept from with control character in collection name",
    ),
    LookupTestCase(
        "unicode",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "données",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": []}],
        msg="$lookup should accept from with unicode in collection name",
    ),
    LookupTestCase(
        "punctuation",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "a!@#%^&*()b",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": []}],
        msg="$lookup should accept from with punctuation in collection name",
    ),
]

# Property [from Parameter Validation Errors]: invalid from values produce
# appropriate type, parse, namespace, or authorization errors.
LOOKUP_FROM_VALIDATION_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "from_int_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": 123,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (int)",
    ),
    LookupTestCase(
        "from_float_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": 1.5,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (float)",
    ),
    LookupTestCase(
        "from_bool_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": True,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (bool)",
    ),
    LookupTestCase(
        "from_array_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": [],
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (array)",
    ),
    LookupTestCase(
        "from_null_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": None,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject from: null",
    ),
    LookupTestCase(
        "from_int64_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": Int64(1),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (Int64)",
    ),
    LookupTestCase(
        "from_decimal128_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": Decimal128("1"),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (Decimal128)",
    ),
    LookupTestCase(
        "from_binary_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": Binary(b"x"),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (Binary)",
    ),
    LookupTestCase(
        "from_objectid_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": ObjectId(),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (ObjectId)",
    ),
    LookupTestCase(
        "from_datetime_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": datetime.datetime(2024, 1, 1),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (datetime)",
    ),
    LookupTestCase(
        "from_regex_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": Regex("x"),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (Regex)",
    ),
    LookupTestCase(
        "from_code_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": Code("x"),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (Code)",
    ),
    LookupTestCase(
        "from_code_with_scope_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": Code("x", {}),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (Code with scope)",
    ),
    LookupTestCase(
        "from_timestamp_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": Timestamp(1, 1),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (Timestamp)",
    ),
    LookupTestCase(
        "from_minkey_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": MinKey(),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (MinKey)",
    ),
    LookupTestCase(
        "from_maxkey_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": MaxKey(),
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject non-string non-object from (MaxKey)",
    ),
    LookupTestCase(
        "from_object_db_coll_not_supported",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": {"db": "test", "coll": "foo"},
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject object from with {db, coll} as not supported",
    ),
    LookupTestCase(
        "from_object_unknown_fields",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": {"x": 1},
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$lookup should reject object from with unknown fields",
    ),
    LookupTestCase(
        "omitting_from_without_documents_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject omitting from without a $documents-first pipeline",
    ),
    LookupTestCase(
        "from_empty_string_invalid_namespace",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$lookup should reject from with an empty string",
    ),
    LookupTestCase(
        "from_null_byte_invalid_namespace",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "a\x00b",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$lookup should reject from with a null byte",
    ),
    LookupTestCase(
        "from_leading_dot_invalid_namespace",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": ".abc",
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$lookup should reject from with a leading dot",
    ),
    LookupTestCase(
        "from_with_documents_first_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": "foo",
                    "pipeline": [{"$documents": [{"x": 1}]}],
                    "as": "j",
                }
            }
        ],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$lookup should reject from combined with a $documents-first pipeline",
    ),
    LookupTestCase(
        "from_object_non_string_db_type_mismatch",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": {"db": 123, "coll": "foo"},
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg=(
            "$lookup should reject object from with non-string db"
            " field with a type mismatch error before the not"
            " supported error"
        ),
    ),
]

LOOKUP_FROM_PARAMETER_TESTS: list[LookupTestCase] = (
    LOOKUP_FROM_PARAMETER_NOT_EXPRESSION_TESTS
    + LOOKUP_FROM_PARAMETER_SPECIAL_NAMES
    + LOOKUP_FROM_VALIDATION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_FROM_PARAMETER_TESTS))
def test_lookup_from_parameter(collection, test_case: LookupTestCase):
    """Test $lookup from parameter behavior."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
