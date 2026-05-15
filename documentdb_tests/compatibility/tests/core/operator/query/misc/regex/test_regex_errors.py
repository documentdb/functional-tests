"""
Tests for $regex query operator error cases.

Covers invalid pattern types (int, bool, null, object, array, double, Int64,
Decimal128, Binary, ObjectId, datetime, Timestamp, MinKey, MaxKey, Code),
invalid regex patterns (unbalanced brackets), null bytes in pattern and options,
maximum pattern length, invalid $options types, invalid option characters,
conflicting options between inline flags and $options, and $in with $regex
expression.
"""

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    REGEX_BAD_OPTION_ERROR,
    REGEX_COMPILE_ERROR,
    REGEX_FLAGS_AND_OPTIONS_CONFLICT_ERROR,
    REGEX_OPTIONS_BEFORE_REGEX_FLAGS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": 1, "a": "abc"}]

INVALID_PATTERN_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="pattern_int",
        filter={"a": {"$regex": 123}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with int pattern should return error",
    ),
    QueryTestCase(
        id="pattern_bool",
        filter={"a": {"$regex": True}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with boolean pattern should return error",
    ),
    QueryTestCase(
        id="pattern_object",
        filter={"a": {"$regex": {"x": 1}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with object pattern should return error",
    ),
    QueryTestCase(
        id="pattern_array",
        filter={"a": {"$regex": ["abc"]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with array pattern should return error",
    ),
    QueryTestCase(
        id="pattern_null",
        filter={"a": {"$regex": None}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with null pattern should return error",
    ),
    QueryTestCase(
        id="pattern_double",
        filter={"a": {"$regex": 1.5}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with double pattern should return error",
    ),
    QueryTestCase(
        id="pattern_int64",
        filter={"a": {"$regex": Int64(123)}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with Int64 pattern should return error",
    ),
    QueryTestCase(
        id="pattern_decimal128",
        filter={"a": {"$regex": Decimal128("1.5")}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with Decimal128 pattern should return error",
    ),
    QueryTestCase(
        id="pattern_binary",
        filter={"a": {"$regex": Binary(b"abc")}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with Binary pattern should return error",
    ),
    QueryTestCase(
        id="pattern_objectid",
        filter={"a": {"$regex": ObjectId()}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with ObjectId pattern should return error",
    ),
    QueryTestCase(
        id="pattern_datetime",
        filter={"a": {"$regex": datetime.datetime(2024, 1, 1)}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with datetime pattern should return error",
    ),
    QueryTestCase(
        id="pattern_timestamp",
        filter={"a": {"$regex": Timestamp(1, 1)}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with Timestamp pattern should return error",
    ),
    QueryTestCase(
        id="pattern_minkey",
        filter={"a": {"$regex": MinKey()}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with MinKey pattern should return error",
    ),
    QueryTestCase(
        id="pattern_maxkey",
        filter={"a": {"$regex": MaxKey()}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with MaxKey pattern should return error",
    ),
    QueryTestCase(
        id="pattern_code",
        filter={"a": {"$regex": Code("function(){}")}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with Code pattern should return error",
    ),
]

INVALID_OPTIONS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="options_int",
        filter={"a": {"$regex": "abc", "$options": 123}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with int $options should return error",
    ),
    QueryTestCase(
        id="options_bool",
        filter={"a": {"$regex": "abc", "$options": True}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with boolean $options should return error",
    ),
    QueryTestCase(
        id="options_object",
        filter={"a": {"$regex": "abc", "$options": {"x": 1}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with object $options should return error",
    ),
]

INVALID_PATTERN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="unbalanced_bracket",
        filter={"a": {"$regex": "[invalid"}},
        doc=DOCS,
        error_code=REGEX_COMPILE_ERROR,
        msg="$regex with unbalanced bracket should return error",
    ),
    QueryTestCase(
        id="null_byte_in_string_pattern",
        filter={"a": {"$regex": "abc\x00def"}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with null byte in string pattern should return error",
    ),
    QueryTestCase(
        id="null_byte_in_options",
        filter={"a": {"$regex": "abc", "$options": "i\x00m"}},
        doc=DOCS,
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regex with null byte in $options should return error",
    ),
]

PATTERN_LENGTH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="exceeding_max_pattern_length",
        filter={"a": {"$regex": "a" * 32769}},
        doc=DOCS,
        error_code=REGEX_COMPILE_ERROR,
        msg="$regex exceeding max pattern length should error",
    ),
]

OPTIONS_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="options_g_global_rejected",
        filter={"a": {"$regex": "abc", "$options": "g"}},
        doc=DOCS,
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regex with 'g' option should return error (global not supported)",
    ),
    QueryTestCase(
        id="options_invalid_mixed_ig",
        filter={"a": {"$regex": "abc", "$options": "ig"}},
        doc=DOCS,
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regex with 'ig' should return error due to invalid 'g'",
    ),
    QueryTestCase(
        id="options_uppercase_I_rejected",
        filter={"a": {"$regex": "abc", "$options": "I"}},
        doc=DOCS,
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regex with uppercase 'I' option should return error",
    ),
    QueryTestCase(
        id="options_numeric_1_rejected",
        filter={"a": {"$regex": "abc", "$options": "1"}},
        doc=DOCS,
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regex with numeric '1' option should return error",
    ),
    QueryTestCase(
        id="options_null_rejected",
        filter={"a": {"$regex": "abc", "$options": None}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$regex with null $options should return error",
    ),
]

CONFLICTING_OPTIONS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="regex_flags_and_options_conflict",
        filter={"a": {"$regex": Regex("abc", "i"), "$options": "m"}},
        doc=DOCS,
        error_code=REGEX_FLAGS_AND_OPTIONS_CONFLICT_ERROR,
        msg="$regex with regex object flags AND $options should return error",
    ),
    QueryTestCase(
        id="options_before_regex_flags_conflict",
        filter={"a": {"$options": "m", "$regex": Regex("abc", "i")}},
        doc=DOCS,
        error_code=REGEX_OPTIONS_BEFORE_REGEX_FLAGS_ERROR,
        msg="$options before $regex with regex flags should return error",
    ),
]

IN_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="in_with_regex_expression_rejected",
        filter={"a": {"$in": [{"$regex": "^acme"}]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$in with $regex expression (not Regex object) should return error",
    ),
]

ALL_TESTS = (
    INVALID_PATTERN_TYPE_TESTS
    + INVALID_OPTIONS_TYPE_TESTS
    + INVALID_PATTERN_TESTS
    + PATTERN_LENGTH_TESTS
    + OPTIONS_ERROR_TESTS
    + CONFLICTING_OPTIONS_TESTS
    + IN_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_regex_errors(collection, test):
    """Parametrized test for $regex error cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, test.msg)
