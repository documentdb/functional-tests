"""
Field removal with $$REMOVE in $project and $addFields.

Covers top-level and nested fields, sibling preservation, and _id removal.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (  # noqa: E501
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field Removal]: assigning $$REMOVE to a field in $project or $addFields
# omits exactly that field — top-level, nested, or _id — while leaving siblings and
# the parent subdocument otherwise intact, and materializes an empty parent object
# when a dotted destination path's parent does not exist on the source document.
#
# Basic $project/$addFields removal and dotted-path removal are covered once, as
# shared expression-engine wiring, in
# ``test_system_variables_remove_expression_engine.py``. The cases below are
# $$REMOVE's own deeper/edge behavior: _id removal, the object-expression nested
# form, $addFields sibling preservation, missing-parent materialization, and the
# $$REMOVE.<path> trailing-path form.
FIELD_REMOVAL_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="removes_id_field",
        docs=[{"_id": 1, "a": 2}],
        pipeline=[{"$project": {"_id": "$$REMOVE", "a": 1}}],
        expected=[{"a": 2}],
        msg="Should remove _id when assigned $$REMOVE",
    ),
    StageTestCase(
        id="removes_nested_field_via_object_expression",
        docs=[{"_id": 1, "a": {"b": 1, "c": 2}}],
        pipeline=[{"$project": {"a": {"b": "$$REMOVE"}}}],
        expected=[{"_id": 1, "a": {}}],
        msg="Nested object expression form should remove the same nested field",
    ),
    StageTestCase(
        id="removes_nested_field_in_addFields_preserving_siblings",
        docs=[{"_id": 1, "a": {"b": 1, "c": 2}}],
        pipeline=[{"$addFields": {"a.b": "$$REMOVE"}}],
        expected=[{"_id": 1, "a": {"c": 2}}],
        msg="$addFields should remove only the nested field and keep siblings",
    ),
    StageTestCase(
        id="dotted_path_materializes_empty_parent_in_project_when_parent_missing",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"x.y": "$$REMOVE"}}],
        expected=[{"_id": 1, "x": {}}],
        msg="$project should materialize an empty parent object for a dotted $$REMOVE "
        "path whose parent does not exist on the source document",
    ),
    StageTestCase(
        id="dotted_path_materializes_empty_parent_in_addFields_when_parent_missing",
        docs=[{"_id": 1}],
        pipeline=[{"$addFields": {"x.y": "$$REMOVE"}}],
        expected=[{"_id": 1, "x": {}}],
        msg="$addFields should materialize an empty parent object for a dotted $$REMOVE "
        "path whose parent does not exist on the source document",
    ),
    StageTestCase(
        id="with_trailing_path_omits_field_in_addFields",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$addFields": {"a": "$$REMOVE.y"}}],
        expected=[{"_id": 1}],
        msg="$addFields with $$REMOVE.<path> should omit the target field",
    ),
    StageTestCase(
        id="with_trailing_path_omits_field_in_project",
        docs=[{"_id": 1, "x": 1}],
        pipeline=[{"$project": {"_id": 0, "x": "$$REMOVE.y.z"}}],
        expected=[{}],
        msg="$project with $$REMOVE.<path> should still evaluate to missing",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_REMOVAL_TESTS))
def test_remove_variable_field_removal(collection, test: StageTestCase):
    """$$REMOVE in $project/$addFields removes only the targeted field."""
    populate_collection(collection, test)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, test.msg, ignore_doc_order=True)
