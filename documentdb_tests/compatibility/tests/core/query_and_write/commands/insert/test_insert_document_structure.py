"""
Insert document structure edge case tests.

Tests field name validation, nesting depth, array values,
and special document structures.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class DocStructureTest(BaseTestCase):
    doc: Any = None


# Property [Field Name Acceptance]: insert accepts underscore, numeric, unicode,
# and dollar-prefixed nested field names.
FIELD_NAME_TESTS: list[DocStructureTest] = [
    DocStructureTest(
        "underscore_prefix",
        doc={"_id": 1, "_field": "value"},
        expected={"_id": 1, "_field": "value"},
        msg="insert should accept underscore-prefixed field.",
    ),
    DocStructureTest(
        "numeric_chars",
        doc={"_id": 1, "field123": "value"},
        expected={"_id": 1, "field123": "value"},
        msg="insert should accept numeric field name.",
    ),
    DocStructureTest(
        "unicode",
        doc={"_id": 1, "名前": "テスト", "données": "valeur"},
        expected={"_id": 1, "名前": "テスト", "données": "valeur"},
        msg="insert should accept unicode field names.",
    ),
    DocStructureTest(
        "dollar_nested",
        doc={"_id": 1, "a": {"$b": 1}},
        expected={"_id": 1, "a": {"$b": 1}},
        msg="insert should accept $ in nested field.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(FIELD_NAME_TESTS))
def test_insert_field_names(collection, test):
    """Test that insert accepts various field name patterns."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [test.doc]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [test.expected], msg=test.msg)


# Property [Array Preservation]: insert preserves arrays including empty, nested,
# null-containing, and duplicate-containing.
ARRAY_TESTS: list[DocStructureTest] = [
    DocStructureTest(
        "empty_array",
        doc={"_id": 1, "arr": []},
        expected={"_id": 1, "arr": []},
        msg="insert should preserve empty array.",
    ),
    DocStructureTest(
        "nested_arrays",
        doc={"_id": 1, "arr": [[1, 2], [3, 4]]},
        expected={"_id": 1, "arr": [[1, 2], [3, 4]]},
        msg="insert should preserve nested arrays.",
    ),
    DocStructureTest(
        "null_elements",
        doc={"_id": 1, "arr": [1, None, 3]},
        expected={"_id": 1, "arr": [1, None, 3]},
        msg="insert should preserve nulls in array.",
    ),
    DocStructureTest(
        "duplicates",
        doc={"_id": 1, "arr": [1, 1, 2, 2, 3]},
        expected={"_id": 1, "arr": [1, 1, 2, 2, 3]},
        msg="insert should preserve duplicates in array.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(ARRAY_TESTS))
def test_insert_array_values(collection, test):
    """Test that insert preserves array structures."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [test.doc]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [test.expected], msg=test.msg)


# Property [Nesting and Shape]: insert preserves deeply nested documents
# and documents with many fields.
STRUCTURE_TESTS: list[DocStructureTest] = [
    DocStructureTest(
        "nested_empty_objects",
        doc={"_id": 1, "a": {"b": {"c": {"d": {}}}}},
        expected={"_id": 1, "a": {"b": {"c": {"d": {}}}}},
        msg="insert should preserve deeply nested empty objects.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(STRUCTURE_TESTS))
def test_insert_document_shapes(collection, test):
    """Test that insert preserves various document shapes."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [test.doc]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [test.expected], msg=test.msg)


@pytest.mark.insert
def test_insert_deeply_nested_document(collection):
    """Test insert with 50-level nested document structure."""
    doc = {"_id": 1}
    nested = doc
    for i in range(50):
        nested["n"] = {}
        nested = nested["n"]
    nested["leaf"] = "value"
    execute_command(
        collection,
        {"insert": collection.name, "documents": [doc]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [doc], msg="insert should accept 50-level nested document.")


@pytest.mark.insert
def test_insert_many_fields(collection):
    """Test insert document with 100 fields."""
    doc = {"_id": 1}
    for i in range(100):
        doc[f"field_{i}"] = i
    execute_command(
        collection,
        {"insert": collection.name, "documents": [doc]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [doc], msg="insert should accept document with 100 fields.")


# Property [Dollar Top-Level Field]: MongoDB 5.0+ allows dollar-prefixed field names at
# the top level of inserted documents. The field is stored and retrieved exactly.
@pytest.mark.insert
def test_insert_dollar_prefixed_top_level_field(collection):
    """Test insert accepts dollar-prefixed field name at top level (MongoDB 5.0+)."""
    doc = {"_id": 1, "$price": 9.99}
    execute_command(
        collection,
        {"insert": collection.name, "documents": [doc]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [doc], msg="insert should accept dollar-prefixed top-level field.")


# Property [Dot Field Name Acceptance]: MongoDB 5.0+ allows dot-containing field names
# in inserted documents. The literal key is stored and retrieved exactly.
@pytest.mark.insert
def test_insert_dot_in_field_name_accepted(collection):
    """Test insert accepts field names containing a dot (MongoDB 5.0+)."""
    doc = {"_id": 1, "a.b": 42}
    execute_command(
        collection,
        {"insert": collection.name, "documents": [doc]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [doc], msg="insert should accept dot-containing field name.")
