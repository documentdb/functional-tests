"""Tests for $lookup spec shape validation errors."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.bson_helpers import build_raw_bson_doc
from documentdb_tests.framework.error_codes import (
    DUPLICATE_FIELD_ERROR,
    FAILED_TO_PARSE_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Spec Shape Validation Errors]: the $lookup spec must be an
# object with only recognized field names and no duplicates.
LOOKUP_SPEC_SHAPE_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "unknown_field_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "a",
                    "foreignField": "b",
                    "as": "j",
                    "unknown": 1,
                }
            }
        ],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$lookup should reject unknown fields in the spec",
    ),
    LookupTestCase(
        "case_sensitive_field_name_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "From": "other",
                    "localField": "a",
                    "foreignField": "b",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup field names are case-sensitive",
    ),
    LookupTestCase(
        "whitespace_field_name_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from ": "other",
                    "localField": "a",
                    "foreignField": "b",
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup field names are whitespace-sensitive",
    ),
    LookupTestCase(
        "empty_spec_produces_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": {}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject an empty spec",
    ),
]

# Property [Spec Shape Non-Object Error]: non-object BSON types as the
# $lookup spec produce a parse error.
LOOKUP_SPEC_NON_OBJECT_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "string_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": "string"}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a string spec",
    ),
    LookupTestCase(
        "int_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": 123}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject an int spec",
    ),
    LookupTestCase(
        "float_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": 1.5}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a float spec",
    ),
    LookupTestCase(
        "bool_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": True}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a bool spec",
    ),
    LookupTestCase(
        "null_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": None}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a null spec",
    ),
    LookupTestCase(
        "array_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": []}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject an array spec",
    ),
    LookupTestCase(
        "int64_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": Int64(1)}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject an Int64 spec",
    ),
    LookupTestCase(
        "decimal128_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": Decimal128("1")}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a Decimal128 spec",
    ),
    LookupTestCase(
        "binary_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": Binary(b"x")}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a Binary spec",
    ),
    LookupTestCase(
        "objectid_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": ObjectId()}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject an ObjectId spec",
    ),
    LookupTestCase(
        "datetime_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": datetime.datetime(2024, 1, 1)}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a datetime spec",
    ),
    LookupTestCase(
        "regex_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": Regex("x")}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a Regex spec",
    ),
    LookupTestCase(
        "code_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": Code("x")}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a Code spec",
    ),
    LookupTestCase(
        "code_with_scope_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": Code("x", {})}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a Code with scope spec",
    ),
    LookupTestCase(
        "timestamp_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": Timestamp(1, 1)}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a Timestamp spec",
    ),
    LookupTestCase(
        "minkey_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": MinKey()}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a MinKey spec",
    ),
    LookupTestCase(
        "maxkey_spec",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[{"$lookup": MaxKey()}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$lookup should reject a MaxKey spec",
    ),
]

# Property [Spec Shape Duplicate Field Error]: duplicate fields in the
# $lookup spec produce a duplicate field error.
LOOKUP_SPEC_DUPLICATE_FIELD_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "duplicate_from",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": build_raw_bson_doc(
                    [
                        ("from", "x"),
                        ("localField", "a"),
                        ("foreignField", "b"),
                        ("as", "j"),
                        ("from", "x"),
                    ]
                )
            }
        ],
        error_code=DUPLICATE_FIELD_ERROR,
        msg="$lookup should reject duplicate 'from' field",
    ),
    LookupTestCase(
        "duplicate_as",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": build_raw_bson_doc(
                    [
                        ("from", "x"),
                        ("localField", "a"),
                        ("foreignField", "b"),
                        ("as", "j"),
                        ("as", "j"),
                    ]
                )
            }
        ],
        error_code=DUPLICATE_FIELD_ERROR,
        msg="$lookup should reject duplicate 'as' field",
    ),
    LookupTestCase(
        "duplicate_localField",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": build_raw_bson_doc(
                    [
                        ("from", "x"),
                        ("localField", "a"),
                        ("foreignField", "b"),
                        ("as", "j"),
                        ("localField", "a"),
                    ]
                )
            }
        ],
        error_code=DUPLICATE_FIELD_ERROR,
        msg="$lookup should reject duplicate 'localField' field",
    ),
    LookupTestCase(
        "duplicate_foreignField",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": build_raw_bson_doc(
                    [
                        ("from", "x"),
                        ("localField", "a"),
                        ("foreignField", "b"),
                        ("as", "j"),
                        ("foreignField", "b"),
                    ]
                )
            }
        ],
        error_code=DUPLICATE_FIELD_ERROR,
        msg="$lookup should reject duplicate 'foreignField' field",
    ),
    LookupTestCase(
        "duplicate_let",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": build_raw_bson_doc(
                    [
                        ("from", "x"),
                        ("let", {}),
                        ("pipeline", []),
                        ("as", "j"),
                        ("let", {}),
                    ]
                )
            }
        ],
        error_code=DUPLICATE_FIELD_ERROR,
        msg="$lookup should reject duplicate 'let' field",
    ),
    LookupTestCase(
        "duplicate_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": build_raw_bson_doc(
                    [
                        ("from", "x"),
                        ("let", {}),
                        ("pipeline", []),
                        ("as", "j"),
                        ("pipeline", []),
                    ]
                )
            }
        ],
        error_code=DUPLICATE_FIELD_ERROR,
        msg="$lookup should reject duplicate 'pipeline' field",
    ),
]

LOOKUP_SPEC_VALIDATION_TESTS: list[LookupTestCase] = (
    LOOKUP_SPEC_SHAPE_ERROR_TESTS
    + LOOKUP_SPEC_NON_OBJECT_ERROR_TESTS
    + LOOKUP_SPEC_DUPLICATE_FIELD_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_SPEC_VALIDATION_TESTS))
def test_lookup_spec_validation(collection, test_case: LookupTestCase):
    """Test $lookup spec shape validation errors."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
