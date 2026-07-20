"""
Tests for $eq string-equality subtleties.

Covers case sensitivity, multibyte UTF-8, absence of Unicode normalization,
embedded null bytes, and whitespace significance — all under plain (non-regex)
byte-wise string equality.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

STRING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="case_sensitive",
        filter={"a": {"$eq": "abc"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "ABC"}],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$eq string equality is case-sensitive: 'abc' does NOT match 'ABC'",
    ),
    QueryTestCase(
        id="multibyte_utf8",
        filter={"a": {"$eq": "caf\u00e9\u2603\U0001d7d9"}},
        doc=[
            {"_id": 1, "a": "caf\u00e9\u2603\U0001d7d9"},
            {"_id": 2, "a": "cafe\u2603\U0001d7d9"},
        ],
        expected=[{"_id": 1, "a": "caf\u00e9\u2603\U0001d7d9"}],
        msg="$eq matches a string with 2/3/4-byte UTF-8 characters exactly",
    ),
    QueryTestCase(
        id="no_unicode_normalization",
        filter={"a": {"$eq": "\u00e9"}},
        doc=[{"_id": 1, "a": "\u00e9"}, {"_id": 2, "a": "e\u0301"}],
        expected=[{"_id": 1, "a": "\u00e9"}],
        msg="$eq does NOT normalize Unicode: precomposed U+00E9 != decomposed 'e'+U+0301",
    ),
    QueryTestCase(
        id="embedded_null_byte",
        filter={"a": {"$eq": "a\x00b"}},
        doc=[
            {"_id": 1, "a": "a\x00b"},
            {"_id": 2, "a": "ab"},
            {"_id": 3, "a": "a"},
        ],
        expected=[{"_id": 1, "a": "a\x00b"}],
        msg="$eq matches only the exact embedded-null-byte string, not the truncated forms",
    ),
    QueryTestCase(
        id="whitespace_significant",
        filter={"a": {"$eq": "a b"}},
        doc=[
            {"_id": 1, "a": "a b"},
            {"_id": 2, "a": "a  b"},
            {"_id": 3, "a": "ab"},
        ],
        expected=[{"_id": 1, "a": "a b"}],
        msg="$eq treats whitespace as significant: 'a b' does not match 'a  b' or 'ab'",
    ),
]


ALL_TESTS = STRING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_eq_string(collection, test):
    """Parametrized test for $eq string-equality subtleties."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
