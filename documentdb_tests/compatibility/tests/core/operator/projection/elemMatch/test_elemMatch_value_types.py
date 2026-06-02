"""
Tests BSON type value matching for the $elemMatch projection operator.
"""

from __future__ import annotations

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DECIMAL128_HALF,
    OID_EPOCH,
    TS_EPOCH,
)

# Property [Null Matching Within Array Elements]: {field: null} matches elements
# where the field is missing or explicitly null; $type: "null" matches only
# explicit null; $exists: false matches only missing fields.
ELEMMATCH_NULL_MATCHING_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "null_match_field_null_matches_missing",
        doc=[{"_id": 1, "arr": [{"a": 5}, {"x": None}, {"x": 1}]}],
        projection={"arr": {"$elemMatch": {"x": None}}},
        expected=[{"_id": 1, "arr": [{"a": 5}]}],
        msg="$elemMatch {field: null} should match an element where the field is missing",
    ),
    ProjectionTestCase(
        "null_match_field_null_matches_explicit_null",
        doc=[{"_id": 1, "arr": [{"x": 5}, {"x": None}, {"a": 1}]}],
        projection={"arr": {"$elemMatch": {"x": None}}},
        expected=[{"_id": 1, "arr": [{"x": None}]}],
        msg="$elemMatch {field: null} should match an element where the field is explicitly null",
    ),
    ProjectionTestCase(
        "null_match_type_null_matches_only_explicit_null",
        doc=[{"_id": 1, "arr": [{"a": 5}, {"x": None}, {"x": 1}]}],
        projection={"arr": {"$elemMatch": {"x": {"$type": "null"}}}},
        expected=[{"_id": 1, "arr": [{"x": None}]}],
        msg="$elemMatch $type: null should skip missing fields and match only explicit null",
    ),
    ProjectionTestCase(
        "null_match_type_null_no_match_when_all_missing",
        doc=[{"_id": 1, "arr": [{"a": 5}, {"b": 6}]}],
        projection={"arr": {"$elemMatch": {"x": {"$type": "null"}}}},
        expected=[{"_id": 1}],
        msg="$elemMatch $type: null should not match elements where the field is missing",
    ),
    ProjectionTestCase(
        "null_match_exists_false_matches_only_missing",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": None}, {"a": 5}]}],
        projection={"arr": {"$elemMatch": {"x": {"$exists": False}}}},
        expected=[{"_id": 1, "arr": [{"a": 5}]}],
        msg="$elemMatch $exists: false should skip null fields and match only missing fields",
    ),
    ProjectionTestCase(
        "null_match_exists_false_no_match_when_none_missing",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": None}]}],
        projection={"arr": {"$elemMatch": {"x": {"$exists": False}}}},
        expected=[{"_id": 1}],
        msg="$elemMatch $exists: false should not match elements where the field is null",
    ),
]

# Property [BSON Type Coverage in Arrays]: any BSON type representable by pymongo can
# appear as an array element and be matched, preserving the element intact.
ELEMMATCH_BSON_TYPE_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        f"bson_{tid}",
        # The placeholder precedes the value so the test fails if a different
        # element is selected.
        doc=[{"_id": 1, "arr": [{"placeholder": "skip"}, val]}],
        projection={"arr": {"$elemMatch": cond}},
        expected=[{"_id": 1, "arr": [val]}],
        msg=f"$elemMatch should match and preserve a {tid} array element",
    )
    for tid, cond, val in [
        ("int32", {"$eq": 42}, 42),
        ("int64", {"$eq": Int64(99)}, Int64(99)),
        ("double", {"$eq": 3.14}, 3.14),
        ("decimal128", {"$eq": DECIMAL128_HALF}, DECIMAL128_HALF),
        ("string", {"$eq": "hello"}, "hello"),
        ("bool", {"$eq": True}, True),
        ("null", {"$type": "null"}, None),
        ("object", {"k": "v"}, {"k": "v"}),
        ("nested_array", {"$eq": [1, 2]}, [1, 2]),
        ("objectid", {"$eq": OID_EPOCH}, OID_EPOCH),
        ("datetime", {"$eq": DATE_EPOCH}, DATE_EPOCH),
        ("timestamp", {"$eq": TS_EPOCH}, TS_EPOCH),
        ("binary", {"$eq": Binary(b"\x00\x01\x02")}, b"\x00\x01\x02"),
        ("regex", {"$type": "regex"}, Regex("^abc", "i")),
        ("code", {"$eq": Code("function(){}")}, Code("function(){}")),
        ("minkey", {"$eq": MinKey()}, MinKey()),
        ("maxkey", {"$eq": MaxKey()}, MaxKey()),
    ]
]

# Property [String and Unicode]: string elements are matched by exact byte-level
# comparison without Unicode normalization, so precomposed and decomposed forms
# remain distinct.
ELEMMATCH_STRING_UNICODE_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "string_empty",
        doc=[{"_id": 1, "arr": ["x", ""]}],
        projection={"arr": {"$elemMatch": {"$eq": ""}}},
        expected=[{"_id": 1, "arr": [""]}],
        msg="$elemMatch should match an empty string literally",
    ),
    ProjectionTestCase(
        "string_null_byte",
        doc=[{"_id": 1, "arr": ["x", "a\x00b"]}],
        projection={"arr": {"$elemMatch": {"$eq": "a\x00b"}}},
        expected=[{"_id": 1, "arr": ["a\x00b"]}],
        msg="$elemMatch should match a string containing a null byte literally",
    ),
    ProjectionTestCase(
        "string_dollar_prefix",
        doc=[{"_id": 1, "arr": ["x", "$field"]}],
        projection={"arr": {"$elemMatch": {"$eq": "$field"}}},
        expected=[{"_id": 1, "arr": ["$field"]}],
        msg="$elemMatch should match a dollar-prefixed string literally",
    ),
    ProjectionTestCase(
        "string_whitespace",
        doc=[{"_id": 1, "arr": ["x", "  \t\n "]}],
        projection={"arr": {"$elemMatch": {"$eq": "  \t\n "}}},
        expected=[{"_id": 1, "arr": ["  \t\n "]}],
        msg="$elemMatch should match a whitespace-only string literally",
    ),
    ProjectionTestCase(
        "string_bom",
        doc=[{"_id": 1, "arr": ["x", "\ufeffhi"]}],  # U+FEFF byte order mark.
        projection={"arr": {"$elemMatch": {"$eq": "\ufeffhi"}}},
        expected=[{"_id": 1, "arr": ["\ufeffhi"]}],
        msg="$elemMatch should preserve and match a byte order mark exactly",
    ),
    ProjectionTestCase(
        "string_zwsp",
        doc=[{"_id": 1, "arr": ["x", "a\u200bb"]}],  # U+200B zero-width space.
        projection={"arr": {"$elemMatch": {"$eq": "a\u200bb"}}},
        expected=[{"_id": 1, "arr": ["a\u200bb"]}],
        msg="$elemMatch should preserve and match a zero-width space exactly",
    ),
    ProjectionTestCase(
        "string_zwj",
        doc=[{"_id": 1, "arr": ["x", "a\u200db"]}],  # U+200D zero-width joiner.
        projection={"arr": {"$elemMatch": {"$eq": "a\u200db"}}},
        expected=[{"_id": 1, "arr": ["a\u200db"]}],
        msg="$elemMatch should preserve and match a zero-width joiner exactly",
    ),
    ProjectionTestCase(
        "string_precomposed_does_not_match_decomposed",
        doc=[{"_id": 1, "arr": ["x", "e\u0301"]}],  # Precomposed U+00E9.
        projection={"arr": {"$elemMatch": {"$eq": "\u00e9"}}},  # Decomposed e + U+0301.
        expected=[{"_id": 1}],
        msg="$elemMatch should not match a precomposed form against a decomposed form",
    ),
    ProjectionTestCase(
        "string_decomposed_matches_decomposed",
        doc=[{"_id": 1, "arr": ["x", "e\u0301"]}],  # Decomposed e + U+0301.
        projection={"arr": {"$elemMatch": {"$eq": "e\u0301"}}},
        expected=[{"_id": 1, "arr": ["e\u0301"]}],
        msg="$elemMatch should match identical decomposed forms exactly",
    ),
    ProjectionTestCase(
        "string_cjk",
        doc=[{"_id": 1, "arr": ["x", "\u4f60\u597d"]}],  # CJK characters.
        projection={"arr": {"$elemMatch": {"$eq": "\u4f60\u597d"}}},
        expected=[{"_id": 1, "arr": ["\u4f60\u597d"]}],
        msg="$elemMatch should match CJK strings exactly",
    ),
    ProjectionTestCase(
        "string_emoji",
        doc=[{"_id": 1, "arr": ["x", "\U0001f600\U0001f389"]}],  # Emoji.
        projection={"arr": {"$elemMatch": {"$eq": "\U0001f600\U0001f389"}}},
        expected=[{"_id": 1, "arr": ["\U0001f600\U0001f389"]}],
        msg="$elemMatch should match emoji strings exactly",
    ),
    ProjectionTestCase(
        "string_accented",
        doc=[{"_id": 1, "arr": ["x", "caf\u00e9"]}],  # Precomposed accented.
        projection={"arr": {"$elemMatch": {"$eq": "caf\u00e9"}}},
        expected=[{"_id": 1, "arr": ["caf\u00e9"]}],
        msg="$elemMatch should match accented strings exactly",
    ),
]

VALUE_TYPES_TESTS = (
    ELEMMATCH_NULL_MATCHING_TESTS + ELEMMATCH_BSON_TYPE_TESTS + ELEMMATCH_STRING_UNICODE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(VALUE_TYPES_TESTS))
def test_elemmatch_value_types(collection, test):
    """Test $elemMatch projection BSON type matching cases."""
    collection.insert_many(test.doc)
    cmd = {
        "find": collection.name,
        "projection": test.projection,
    }
    if test.filter is not None:
        cmd["filter"] = test.filter
    result = execute_command(collection, cmd)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
