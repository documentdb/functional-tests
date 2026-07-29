"""
$$CURRENT's own document identity: the whole document, and how it's rescoped.

Covers the entire document across BSON types, its reported {$type}, the
empty-document case, and how $project/$group rescope it in a later stage.
"""

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_project_with_insert,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DATE_EPOCH, INT32_MAX, INT64_MAX, OID_EPOCH

ALL_BSON_TYPES_DOC = {
    "_id": 1,
    "double": 3.14,
    "string": "hello",
    "object": {"key": "value"},
    "array": ["a", "b", "c"],
    "binData": Binary(b"\x00\x01\x02", 128),
    "objectId": OID_EPOCH,
    "bool": True,
    "date": DATE_EPOCH,
    "null": None,
    "regex": Regex("^abc", "i"),
    "javascript": Code("function(){}"),
    "int": INT32_MAX,
    "timestamp": Timestamp(0, 1),
    "long": INT64_MAX,
    "decimal128": Decimal128("0.5"),
    "minKey": MinKey(),
    "maxKey": MaxKey(),
}

# Property [Document Identity]: $$CURRENT with no subfield resolves to the entire current
# document, byte-for-byte across every BSON type, preserving nested structure, numeric-type
# distinctions, and reporting BSON type "object".
DOCUMENT_VALUE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="current_returns_entire_document",
        expression={"doc": "$$CURRENT"},
        doc={"_id": 1, "a": 1, "b": {"c": 2}},
        expected=[{"doc": {"_id": 1, "a": 1, "b": {"c": 2}}}],
        msg="$$CURRENT should return the whole current document",
    ),
    ExpressionTestCase(
        id="current_returns_document_with_all_bson_types",
        expression={"doc": "$$CURRENT"},
        doc=dict(ALL_BSON_TYPES_DOC),
        expected=[{"doc": ALL_BSON_TYPES_DOC}],
        msg="$$CURRENT should return all BSON-typed fields unchanged",
    ),
    ExpressionTestCase(
        id="current_returns_nested_document_structure",
        expression={"doc": "$$CURRENT"},
        doc={"_id": 1, "a": {"b": {"c": [{"d": 1}, {"d": 2}]}}},
        expected=[{"doc": {"_id": 1, "a": {"b": {"c": [{"d": 1}, {"d": 2}]}}}}],
        msg="$$CURRENT should preserve the full nested document structure",
    ),
    ExpressionTestCase(
        id="current_type_is_object",
        expression={"t": {"$type": "$$CURRENT"}},
        doc={"_id": 1, "a": 1},
        expected=[{"t": "object"}],
        msg="Unmodified $$CURRENT should report BSON type object",
    ),
    ExpressionTestCase(
        id="current_preserves_bson_type_distinctions",
        expression={
            "types": {
                "$map": {
                    "input": {"$objectToArray": "$$CURRENT"},
                    "as": "kv",
                    "in": {"$type": "$$kv.v"},
                }
            },
        },
        doc={
            "_id": 1,
            "f_bool_false": False,
            "f_int_zero": 0,
            "f_bool_true": True,
            "f_int_one": 1,
            "f_empty_string": "",
            "f_null": None,
            "f_long": Int64(1),
            "f_double": 1.0,
            "f_decimal": Decimal128("1"),
        },
        expected=[
            {
                "types": [
                    "int",
                    "bool",
                    "int",
                    "bool",
                    "int",
                    "string",
                    "null",
                    "long",
                    "double",
                    "decimal",
                ]
            }
        ],
        msg="$$CURRENT should preserve BSON type distinctions of every field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DOCUMENT_VALUE_TESTS))
def test_system_variables_current_document_value(collection, test):
    """$$CURRENT with no subfield resolves to the entire current document."""
    result = execute_project_with_insert(collection, test.doc, test.expression)
    assertSuccess(result, test.expected, msg=test.msg)


# Property [Stage Rescoping]: $$CURRENT reflects the document as reshaped by whatever
# stage precedes it, not the originally stored document.
CURRENT_PIPELINE_RESCOPING_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="reflects_reshaped_document_after_project",
        docs=[{"_id": 1, "a": 1, "b": 2}],
        pipeline=[
            {"$project": {"a": 1}},
            {"$project": {"_id": 0, "doc": "$$CURRENT"}},
        ],
        expected=[{"doc": {"_id": 1, "a": 1}}],
        msg="$$CURRENT should reflect the document reshaped by $project",
    ),
    StageTestCase(
        id="reflects_grouped_document_after_group",
        docs=[{"_id": 1, "k": "x", "v": 1}, {"_id": 2, "k": "x", "v": 2}],
        pipeline=[
            {"$group": {"_id": "$k", "total": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "doc": "$$CURRENT"}},
        ],
        expected=[{"doc": {"_id": "x", "total": 3}}],
        msg="$$CURRENT should reflect the document produced by $group",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CURRENT_PIPELINE_RESCOPING_TESTS))
def test_current_pipeline_rescoping(collection, test: StageTestCase):
    """$$CURRENT reflects the document as reshaped by a preceding pipeline stage."""
    populate_collection(collection, test)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, msg=test.msg)


def test_current_returns_empty_object_for_empty_document(collection):
    """$$CURRENT resolves to an empty object when the current document has no fields."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {"$project": {"_id": 0, "doc": "$$CURRENT"}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"doc": {}}],
        msg="$$CURRENT should resolve to an empty object for an empty document",
    )
