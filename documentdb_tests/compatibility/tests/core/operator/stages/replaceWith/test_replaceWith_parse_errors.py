"""Tests for the $replaceWith aggregation stage."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_DOT_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Object-Literal Field-Name Errors]: a constructed object literal with
# an invalid key is rejected at parse time, each invalid-key kind hitting a
# distinct code, with no reclassification when nested in a sub-object.
REPLACEWITH_FIELD_NAME_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "fieldname_empty_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": {"": 1}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$replaceWith should reject a constructed literal with an empty key",
    ),
    StageTestCase(
        "fieldname_sole_dollar_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": {"$x": 1}}],
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="$replaceWith should reject a sole dollar-prefixed key as an unknown operator",
    ),
    StageTestCase(
        "fieldname_dollar_key_with_sibling",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": {"good": 1, "$bad": 2}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$replaceWith should reject a dollar-prefixed key alongside a plain sibling field",
    ),
    StageTestCase(
        "fieldname_multiple_dollar_keys",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": {"$a": 1, "$b": 2}}],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$replaceWith should reject multiple dollar-prefixed operator keys in one object",
    ),
    StageTestCase(
        "fieldname_dotted_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": {"a.b": 1}}],
        error_code=FIELD_PATH_DOT_ERROR,
        msg="$replaceWith should reject a dotted key without expanding it into a path",
    ),
    StageTestCase(
        "fieldname_nested_empty_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": {"a": {"b": {"": 1}}}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$replaceWith should reject an empty key in a sub-object identically",
    ),
    StageTestCase(
        "fieldname_nested_sole_dollar_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": {"a": {"b": {"$x": 1}}}}],
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="$replaceWith should reject a sole dollar-prefixed key in a sub-object identically",
    ),
    StageTestCase(
        "fieldname_nested_dollar_key_with_sibling",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": {"a": {"b": {"good": 1, "$bad": 2}}}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$replaceWith should reject a dollar-prefixed key with a sibling in a sub-object",
    ),
    StageTestCase(
        "fieldname_nested_multiple_dollar_keys",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": {"a": {"b": {"$a": 1, "$b": 2}}}}],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$replaceWith should reject multiple dollar-prefixed keys in a sub-object identically",
    ),
    StageTestCase(
        "fieldname_nested_dotted_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": {"a": {"b": {"c.d": 1}}}}],
        error_code=FIELD_PATH_DOT_ERROR,
        msg="$replaceWith should reject a dotted key in a sub-object identically",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REPLACEWITH_FIELD_NAME_ERROR_TESTS))
def test_replaceWith_parse_error_cases(collection, test_case: StageTestCase):
    """Test $replaceWith parse error cases."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
