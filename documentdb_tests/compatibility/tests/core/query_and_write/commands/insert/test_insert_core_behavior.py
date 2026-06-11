"""
Insert core behavior and response structure tests.

Tests basic insert operations, implicit collection creation,
and response field verification.
"""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertProperties,
    assertResult,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, NonEmptyStr

# Property [Response Structure]: insert returns ok=1.0 and the correct inserted
# count for single documents, multiple documents, and empty documents.
RESPONSE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "single_document",
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "a": 1}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="insert should succeed with n=1.",
    ),
    CommandTestCase(
        "multiple_documents",
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1}, {"_id": 2}],
        },
        expected={"ok": 1.0, "n": 2},
        msg="insert should return ok=1.0 and n matching the document count.",
    ),
    CommandTestCase(
        "empty_document",
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="insert should accept an empty document and generate an _id.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(RESPONSE_TESTS))
def test_insert_response(collection, test: CommandTestCase):
    """Test insert response structure."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, expected=test.build_expected(ctx), msg=test.msg, raw_res=True)


# Property [Document Preservation]: insert stores field values exactly, including
# empty-like values (empty string, null, empty array, empty object).
DOC_PRESERVATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_like_field_values",
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "a": "", "b": None, "c": [], "d": {}}],
        },
        expected=[{"_id": 1, "a": "", "b": None, "c": [], "d": {}}],
        msg="insert should preserve empty string, null, empty array, and empty object fields.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(DOC_PRESERVATION_TESTS))
def test_insert_document_preservation(collection, test: CommandTestCase):
    """Test that insert stores field values exactly as supplied."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    execute_command(collection, test.build_command(ctx))
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.build_expected(ctx), msg=test.msg)


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
