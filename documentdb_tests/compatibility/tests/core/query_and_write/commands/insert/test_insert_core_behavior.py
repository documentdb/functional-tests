"""
Insert core behavior and response structure tests.

Tests basic insert operations, implicit collection creation,
and response field verification.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import (
    assertProperties,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, NonEmptyStr
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ResponseTest(BaseTestCase):
    """Test case asserting insert response fields (ok, n)."""

    documents: Any = None
    response_expected: Any = None


@dataclass(frozen=True)
class DocCheckTest(BaseTestCase):
    """Test case asserting document state after insert via find."""

    documents: Any = None
    find_filter: Any = None
    find_expected: Any = None


# Property [Response Structure]: insert returns ok=1.0 and the correct inserted
# count for single documents, multiple documents, and empty documents.
RESPONSE_TESTS: list[ResponseTest] = [
    ResponseTest(
        "single_document",
        documents=[{"_id": 1, "a": 1}],
        response_expected={"ok": 1.0, "n": 1},
        msg="insert should succeed with n=1.",
    ),
    ResponseTest(
        "multiple_documents",
        documents=[{"_id": 1}, {"_id": 2}],
        response_expected={"ok": 1.0, "n": 2},
        msg="insert should return ok=1.0 and n matching the document count.",
    ),
    ResponseTest(
        "empty_document",
        documents=[{}],
        response_expected={"ok": 1.0, "n": 1},
        msg="insert should accept an empty document and generate an _id.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(RESPONSE_TESTS))
def test_insert_response(collection, test: ResponseTest):
    """Test insert response structure."""
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": test.documents},
    )
    assertSuccessPartial(result, test.response_expected, msg=test.msg)


# Property [Document Preservation]: insert stores field values exactly, including
# empty-like values (empty string, null, empty array, empty object).
DOC_TESTS: list[DocCheckTest] = [
    DocCheckTest(
        "empty_like_field_values",
        documents=[{"_id": 1, "a": "", "b": None, "c": [], "d": {}}],
        find_filter={"_id": 1},
        find_expected=[{"_id": 1, "a": "", "b": None, "c": [], "d": {}}],
        msg="insert should preserve empty string, null, empty array, and empty object fields.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(DOC_TESTS))
def test_insert_document_preservation(collection, test: DocCheckTest):
    """Test that insert stores field values exactly as supplied."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": test.documents},
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.find_filter})
    assertSuccess(result, test.find_expected, msg=test.msg)


# Implicit collection creation requires a derived collection name and cleanup.
# These two cases test different commands (insert response vs. listCollections),
# so they remain as focused standalones.
@pytest.mark.insert
def test_insert_creates_collection_implicitly(collection):
    """Test insert into non-existent collection creates it."""
    coll_name = f"{collection.name}_implicit"
    coll = collection.database[coll_name]
    try:
        result = execute_command(
            coll,
            {"insert": coll_name, "documents": [{"_id": 1}]},
        )
        assertSuccessPartial(
            result, {"ok": 1.0, "n": 1}, msg="insert should auto-create collection."
        )
    finally:
        coll.drop()


@pytest.mark.insert
def test_insert_implicit_collection_exists_after(collection):
    """Test collection exists in listCollections after implicit creation."""
    coll_name = f"{collection.name}_verify_exists"
    coll = collection.database[coll_name]
    try:
        execute_command(coll, {"insert": coll_name, "documents": [{"_id": 1}]})
        result = execute_command(
            coll,
            {"listCollections": 1, "filter": {"name": coll_name}},
        )
        assertProperties(
            result,
            {"name": Eq(coll_name)},
            msg="insert should make collection visible in listCollections.",
        )
    finally:
        coll.drop()


@pytest.mark.insert
def test_insert_write_errors_errmsg_is_non_empty_string(collection):
    """Test that writeErrors[0].errmsg is a non-empty string on duplicate key error."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1}]},
    )
    assertProperties(
        result,
        {"writeErrors.0.errmsg": NonEmptyStr()},
        raw_res=True,
        msg="insert writeErrors should contain a non-empty errmsg string.",
    )
