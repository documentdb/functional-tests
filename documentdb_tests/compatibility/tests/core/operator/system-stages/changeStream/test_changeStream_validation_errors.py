"""Tests for $changeStream spec validation errors (malformed specs and option values)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, DBRef, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CHANGE_STREAM_SPEC_NOT_OBJECT_ERROR,
    FAILED_TO_PARSE_ERROR,
    KEYSTRING_UNKNOWN_TYPE_ERROR,
    RESUME_TOKEN_EMPTY_ERROR,
    RESUME_TOKEN_MALFORMED_ERROR,
    RESUME_TOKEN_TYPEBITS_WRONG_TYPE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Spec-Level Non-Object Rejection]: a spec value of any non-object
# BSON type, including null and an array, produces an error; an array spec is
# not unwrapped into its elements.
CHANGESTREAM_SPEC_NON_OBJECT_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"spec_non_object_{tid}",
        pipeline=[{"$changeStream": val}],
        error_code=CHANGE_STREAM_SPEC_NOT_OBJECT_ERROR,
        msg=f"$changeStream should reject a {tid} spec as not a nested object",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "x"),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("null", None),
        ("empty_array", []),
        ("array_of_spec", [{"fullDocument": "default"}]),
    ]
]

# Property [Spec-Level Unknown Field Rejection]: an option field name that is
# not a recognized option produces an unknown-field error; option names are
# case-sensitive, are not trimmed, and a DBRef spec is treated as a nested
# object whose reserved keys are unrecognized fields.
CHANGESTREAM_SPEC_UNKNOWN_FIELD_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unknown_field",
        pipeline=[{"$changeStream": {"bogus": 1}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$changeStream should reject an unknown option field",
    ),
    StageTestCase(
        "wrong_case_capitalized",
        pipeline=[{"$changeStream": {"FullDocument": "default"}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$changeStream should reject a capitalized option name as unknown",
    ),
    StageTestCase(
        "wrong_case_upper",
        pipeline=[{"$changeStream": {"FULLDOCUMENT": "default"}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$changeStream should reject an upper-case option name as unknown",
    ),
    StageTestCase(
        "wrong_case_lower",
        pipeline=[{"$changeStream": {"fulldocument": "default"}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$changeStream should reject a lower-case option name as unknown",
    ),
    StageTestCase(
        "leading_whitespace",
        pipeline=[{"$changeStream": {" fullDocument": "default"}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$changeStream should reject an option name with leading whitespace as unknown",
    ),
    StageTestCase(
        "dollar_prefixed_name",
        pipeline=[{"$changeStream": {"$fullDocument": "default"}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$changeStream should reject a dollar-prefixed option name as unknown",
    ),
    StageTestCase(
        "empty_name",
        pipeline=[{"$changeStream": {"": "x"}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$changeStream should reject an empty option name as unknown",
    ),
    StageTestCase(
        "dbref_object",
        pipeline=[{"$changeStream": DBRef("c", 1)}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$changeStream should treat a DBRef spec as an object with unknown fields",
    ),
]

# Property [Expression Arguments Are Not Evaluated]: no option value is
# evaluated as an aggregation expression; an expression-shaped value is read as
# literal BSON at parse time and falls through to the type/enum/token validation
# for its literal shape rather than producing its evaluated result.
CHANGESTREAM_EXPRESSION_NOT_EVALUATED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "all_changes_for_cluster_literal_true",
        pipeline=[{"$changeStream": {"allChangesForCluster": {"$literal": True}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=(
            "$changeStream should reject an expression object for"
            " allChangesForCluster as wrong type"
        ),
    ),
    StageTestCase(
        "show_expanded_events_cond",
        pipeline=[{"$changeStream": {"showExpandedEvents": {"$cond": [True, True, False]}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$changeStream should reject an expression object for showExpandedEvents as wrong type",
    ),
    StageTestCase(
        "full_document_literal",
        pipeline=[{"$changeStream": {"fullDocument": {"$literal": "updateLookup"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$changeStream should reject an expression object for fullDocument as wrong type",
    ),
    StageTestCase(
        "full_document_before_change_concat",
        pipeline=[
            {"$changeStream": {"fullDocumentBeforeChange": {"$concat": ["when", "Available"]}}}
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg=(
            "$changeStream should reject an expression object for"
            " fullDocumentBeforeChange as wrong type"
        ),
    ),
    StageTestCase(
        "start_at_operation_time_literal",
        pipeline=[{"$changeStream": {"startAtOperationTime": {"$literal": Timestamp(1, 1)}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=(
            "$changeStream should reject an expression object for"
            " startAtOperationTime as wrong type"
        ),
    ),
    StageTestCase(
        "resume_after_literal",
        pipeline=[{"$changeStream": {"resumeAfter": {"$literal": {"_data": "8264000000"}}}}],
        error_code=RESUME_TOKEN_MALFORMED_ERROR,
        msg="$changeStream should reject an expression object for resumeAfter as a malformed token",
    ),
    StageTestCase(
        "start_after_concat",
        pipeline=[{"$changeStream": {"startAfter": {"$concat": ["8264", "000000"]}}}],
        error_code=RESUME_TOKEN_MALFORMED_ERROR,
        msg="$changeStream should reject an expression object for startAfter as a malformed token",
    ),
    StageTestCase(
        "full_document_field_path",
        pipeline=[{"$changeStream": {"fullDocument": "$someField"}}],
        error_code=BAD_VALUE_ERROR,
        msg=(
            "$changeStream should reject a field-path string for"
            " fullDocument as an invalid enum value"
        ),
    ),
    StageTestCase(
        "full_document_variable",
        pipeline=[{"$changeStream": {"fullDocument": "$$ROOT"}}],
        error_code=BAD_VALUE_ERROR,
        msg=(
            "$changeStream should reject a variable string for"
            " fullDocument as an invalid enum value"
        ),
    ),
    StageTestCase(
        "full_document_before_change_field_path",
        pipeline=[{"$changeStream": {"fullDocumentBeforeChange": "$someField"}}],
        error_code=BAD_VALUE_ERROR,
        msg=(
            "$changeStream should reject a field-path string for"
            " fullDocumentBeforeChange as an invalid enum value"
        ),
    ),
]

# Property [Boolean Option Type Rejection]: each boolean option
# (allChangesForCluster, showExpandedEvents) rejects any non-boolean BSON type
# with a TypeMismatch error; there is no coercion from numbers, numeric
# strings, arrays, objects, or any other type to a boolean.
CHANGESTREAM_BOOLEAN_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"bool_type_{opt_id}_{tid}",
        pipeline=[{"$changeStream": {opt: val}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$changeStream should reject a non-boolean value for {opt}",
    )
    for opt, opt_id in [
        ("allChangesForCluster", "all_changes"),
        ("showExpandedEvents", "show_expanded"),
    ]
    for tid, val in [
        ("int32_zero", 0),
        ("int32_one", 1),
        ("double_zero", DOUBLE_ZERO),
        ("double_one", 1.0),
        ("int64", Int64(1)),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("nan", FLOAT_NAN),
        ("positive_infinity", FLOAT_INFINITY),
        ("negative_infinity", FLOAT_NEGATIVE_INFINITY),
        ("string_true", "true"),
        ("string_false", "false"),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        # DBRef encodes as a BSON object and is rejected as a non-boolean object.
        ("dbref", DBRef("c", 1)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("empty_array", []),
        ("array_true", [True]),
        ("array_false", [False]),
        ("empty_object", {}),
    ]
]

# Property [Boolean Option Null Rejection]: each boolean option rejects an
# explicit null with a TypeMismatch error, so only field omission yields the
# default; this contrasts with the five non-boolean options that accept null as
# unset.
CHANGESTREAM_BOOLEAN_NULL_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"bool_null_{opt_id}",
        pipeline=[{"$changeStream": {opt: None}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$changeStream should reject an explicit null for {opt}",
    )
    for opt, opt_id in [
        ("allChangesForCluster", "all_changes"),
        ("showExpandedEvents", "show_expanded"),
    ]
]

# Property [String Enum Option Type Rejection]: each string-enum option
# (fullDocument, fullDocumentBeforeChange) rejects any non-string, non-null BSON
# type with a TypeMismatch error; an array is not unwrapped to its element.
CHANGESTREAM_ENUM_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"enum_type_{opt_id}_{tid}",
        pipeline=[{"$changeStream": {opt: val}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$changeStream should reject a non-string value for {opt}",
    )
    for opt, opt_id in [
        ("fullDocument", "full_document"),
        ("fullDocumentBeforeChange", "before_change"),
    ]
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        # DBRef encodes as a BSON object and is rejected as a non-string object.
        ("dbref", DBRef("c", 1)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("empty_object", {}),
        ("object", {"a": 1}),
        ("empty_array", []),
        ("array_single", ["default"]),
        ("array_multi", ["default", "off"]),
        ("array_nested", [["default"]]),
    ]
]

# Property [String Enum Option Value Rejection]: a string that is not a member
# of the option's enum set produces a BadValue error; comparison is exact, with
# no case folding, whitespace trimming, NUL truncation, Unicode normalization,
# or stripping of invisible or marker characters, and a sibling option's value
# or a dollar-prefixed string is treated as a plain invalid enum string.
CHANGESTREAM_ENUM_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"enum_value_{opt_id}_{suffix}",
        pipeline=[{"$changeStream": {opt: val}}],
        error_code=BAD_VALUE_ERROR,
        msg=f"$changeStream should reject an invalid {opt} enum string",
    )
    for opt, opt_id, suffix, val in [
        ("fullDocument", "full_document", "empty", ""),
        ("fullDocument", "full_document", "sibling_off", "off"),
        ("fullDocument", "full_document", "case_capitalized", "Default"),
        ("fullDocument", "full_document", "case_upper", "DEFAULT"),
        ("fullDocument", "full_document", "case_update_lookup", "UpdateLookup"),
        ("fullDocument", "full_document", "leading_space", " default"),
        ("fullDocument", "full_document", "trailing_space", "default "),
        ("fullDocument", "full_document", "trailing_tab", "default\t"),
        ("fullDocument", "full_document", "trailing_cr", "default\r"),
        ("fullDocument", "full_document", "trailing_lf", "updateLookup\n"),
        ("fullDocument", "full_document", "interior_space", "when available"),
        ("fullDocument", "full_document", "trailing_nul", "default\x00"),
        ("fullDocument", "full_document", "leading_nul", "\x00default"),
        ("fullDocument", "full_document", "interior_nul", "default\x00default"),
        # Fullwidth latin small d (U+FF44) in place of the ASCII d.
        ("fullDocument", "full_document", "fullwidth_d", "\uff44efault"),
        # Fullwidth latin small d (U+FF44) in place of the trailing ASCII d.
        ("fullDocument", "full_document", "fullwidth_require_d", "require\uff44"),
        # No-break space (U+00A0) prefix.
        ("fullDocument", "full_document", "nbsp", "\u00a0default"),
        # En space (U+2000) prefix.
        ("fullDocument", "full_document", "en_space", "\u2000default"),
        # Em space (U+2003) suffix.
        ("fullDocument", "full_document", "em_space", "default\u2003"),
        # Byte order mark (U+FEFF) prefix.
        ("fullDocument", "full_document", "bom", "\ufeffdefault"),
        # Zero-width space (U+200B) prefix.
        ("fullDocument", "full_document", "zwsp", "\u200bdefault"),
        # Zero-width joiner (U+200D) prefix.
        ("fullDocument", "full_document", "zwj", "\u200ddefault"),
        # Left-to-right mark (U+200E) prefix.
        ("fullDocument", "full_document", "ltr_mark", "\u200edefault"),
        # Right-to-left mark (U+200F) prefix.
        ("fullDocument", "full_document", "rtl_mark", "\u200fdefault"),
        ("fullDocument", "full_document", "dollar", "$"),
        ("fullDocument", "full_document", "double_dollar", "$$"),
        ("fullDocument", "full_document", "dollar_value", "$default"),
        ("fullDocument", "full_document", "double_dollar_value", "$$default"),
        ("fullDocumentBeforeChange", "before_change", "empty", ""),
        ("fullDocumentBeforeChange", "before_change", "sibling_default", "default"),
        ("fullDocumentBeforeChange", "before_change", "sibling_update_lookup", "updateLookup"),
        ("fullDocumentBeforeChange", "before_change", "case_capitalized", "Off"),
        ("fullDocumentBeforeChange", "before_change", "case_upper", "OFF"),
        ("fullDocumentBeforeChange", "before_change", "case_when_available", "WhenAvailable"),
        ("fullDocumentBeforeChange", "before_change", "leading_mixed_ws", " \t\n\r off"),
        ("fullDocumentBeforeChange", "before_change", "trailing_space", "off "),
        ("fullDocumentBeforeChange", "before_change", "trailing_tab", "off\t"),
        ("fullDocumentBeforeChange", "before_change", "trailing_cr", "off\r"),
        ("fullDocumentBeforeChange", "before_change", "trailing_lf", "whenAvailable\n"),
        ("fullDocumentBeforeChange", "before_change", "interior_space", "when available"),
        ("fullDocumentBeforeChange", "before_change", "trailing_nul", "off\x00"),
        ("fullDocumentBeforeChange", "before_change", "leading_nul", "\x00off"),
        ("fullDocumentBeforeChange", "before_change", "interior_nul", "off\x00off"),
        # Fullwidth latin small o (U+FF4F) in place of the leading ASCII o.
        ("fullDocumentBeforeChange", "before_change", "fullwidth_o", "\uff4fff"),
        # No-break space (U+00A0) prefix.
        ("fullDocumentBeforeChange", "before_change", "nbsp", "\u00a0off"),
        # En space (U+2000) prefix.
        ("fullDocumentBeforeChange", "before_change", "en_space", "\u2000off"),
        # Em space (U+2003) suffix.
        ("fullDocumentBeforeChange", "before_change", "em_space", "off\u2003"),
        # Byte order mark (U+FEFF) prefix.
        ("fullDocumentBeforeChange", "before_change", "bom", "\ufeffoff"),
        # Zero-width space (U+200B) prefix.
        ("fullDocumentBeforeChange", "before_change", "zwsp", "\u200boff"),
        # Zero-width joiner (U+200D) prefix.
        ("fullDocumentBeforeChange", "before_change", "zwj", "\u200doff"),
        # Left-to-right mark (U+200E) prefix.
        ("fullDocumentBeforeChange", "before_change", "ltr_mark", "\u200eoff"),
        # Right-to-left mark (U+200F) prefix.
        ("fullDocumentBeforeChange", "before_change", "rtl_mark", "\u200foff"),
        ("fullDocumentBeforeChange", "before_change", "dollar", "$"),
        ("fullDocumentBeforeChange", "before_change", "dollar_value", "$off"),
    ]
]

# Property [Resume Token Type Rejection]: each resume-token option (resumeAfter,
# startAfter) rejects any non-object, non-null BSON type with a TypeMismatch
# error; there is no coercion of a scalar, string, or array to a resume-token
# object.
CHANGESTREAM_RESUME_TOKEN_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"resume_token_type_{opt_id}_{tid}",
        pipeline=[{"$changeStream": {opt: val}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$changeStream should reject a non-object value for {opt}",
    )
    for opt, opt_id in [
        ("resumeAfter", "resume_after"),
        ("startAfter", "start_after"),
    ]
    for tid, val in [
        ("string", "x"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", []),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Resume Token Structure Rejection]: a resume-token object that fails
# structure validation is rejected with an error reflecting the failure mode; a
# missing or non-string _data, an empty-string _data, a non-hex or odd-length
# _data, a well-formed-hex _data that decodes to a malformed KeyString, and a
# wrong-type _typeBits each produce their own distinct error.
CHANGESTREAM_RESUME_TOKEN_STRUCTURE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"resume_token_structure_{opt_id}_{suffix}",
        pipeline=[{"$changeStream": {opt: token}}],
        error_code=error_code,
        msg=f"$changeStream should reject a malformed {opt} resume token ({suffix})",
    )
    for opt, opt_id in [
        ("resumeAfter", "resume_after"),
        ("startAfter", "start_after"),
    ]
    for token, error_code, suffix in [
        ({}, RESUME_TOKEN_MALFORMED_ERROR, "empty_object"),
        ({"a": 1}, RESUME_TOKEN_MALFORMED_ERROR, "no_data_key"),
        ({"_data": 42}, RESUME_TOKEN_MALFORMED_ERROR, "data_int"),
        ({"_data": None}, RESUME_TOKEN_MALFORMED_ERROR, "data_null"),
        ({"_data": True}, RESUME_TOKEN_MALFORMED_ERROR, "data_bool"),
        ({"_data": Binary(b"\x01")}, RESUME_TOKEN_MALFORMED_ERROR, "data_binary"),
        ({"_data": [1]}, RESUME_TOKEN_MALFORMED_ERROR, "data_array"),
        ({"_data": {"x": 1}}, RESUME_TOKEN_MALFORMED_ERROR, "data_object"),
        # A DBRef encodes as a BSON object, so it passes the type check and is
        # then rejected as a token with no string _data field.
        (DBRef("c", 1), RESUME_TOKEN_MALFORMED_ERROR, "dbref"),
        ({"_data": ""}, RESUME_TOKEN_EMPTY_ERROR, "data_empty"),
        ({"_data": "xyz"}, FAILED_TO_PARSE_ERROR, "data_nonhex"),
        ({"_data": "ZZ"}, FAILED_TO_PARSE_ERROR, "data_nonhex_letters"),
        ({"_data": "abc"}, FAILED_TO_PARSE_ERROR, "data_odd_length"),
        ({"_data": "00"}, KEYSTRING_UNKNOWN_TYPE_ERROR, "data_unknown_keystring_type"),
        (
            {"_data": "00", "_typeBits": "x"},
            RESUME_TOKEN_TYPEBITS_WRONG_TYPE_ERROR,
            "typebits_string",
        ),
    ]
]

# Property [Timestamp Option Type Rejection]: startAtOperationTime rejects any
# non-timestamp, non-null BSON type with a TypeMismatch error; there is no
# coercion from a number, string, datetime, array, or object to a timestamp, and
# an array is not unwrapped to a contained timestamp.
CHANGESTREAM_TIMESTAMP_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"timestamp_type_{tid}",
        pipeline=[{"$changeStream": {"startAtOperationTime": val}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$changeStream should reject a non-timestamp value for startAtOperationTime",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        # DBRef encodes as a BSON object and is rejected as a non-timestamp object.
        ("dbref", DBRef("c", 1)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("empty_object", {}),
        ("object", {"a": 1}),
        ("empty_array", []),
        ("array_single", [Timestamp(1, 1)]),
        ("array_multi", [Timestamp(1, 1), Timestamp(2, 2)]),
    ]
]

CHANGESTREAM_ERROR_TESTS = (
    CHANGESTREAM_SPEC_NON_OBJECT_TESTS
    + CHANGESTREAM_SPEC_UNKNOWN_FIELD_TESTS
    + CHANGESTREAM_EXPRESSION_NOT_EVALUATED_TESTS
    + CHANGESTREAM_BOOLEAN_TYPE_ERROR_TESTS
    + CHANGESTREAM_BOOLEAN_NULL_ERROR_TESTS
    + CHANGESTREAM_ENUM_TYPE_ERROR_TESTS
    + CHANGESTREAM_ENUM_VALUE_ERROR_TESTS
    + CHANGESTREAM_RESUME_TOKEN_TYPE_ERROR_TESTS
    + CHANGESTREAM_RESUME_TOKEN_STRUCTURE_ERROR_TESTS
    + CHANGESTREAM_TIMESTAMP_TYPE_ERROR_TESTS
)


@pytest.mark.replica_set
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_ERROR_TESTS))
def test_changeStream_error_cases(collection, test_case: StageTestCase):
    """Test $changeStream rejects malformed specs and reads option values as literal BSON."""
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg, raw_res=True)
