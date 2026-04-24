from __future__ import annotations

import pytest
from bson import Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.set.utils.set_common import (
    STAGE_NAMES,
    replace_stage_name,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Null and Missing Field Values]: null is a concrete value that is
# included in output, while a reference to a missing field causes the output
# field to be omitted entirely.
SET_NULL_MISSING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_literal",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"b": None}}],
        expected=[{"_id": 1, "a": 1, "b": None}],
        msg="$set should add a field with value null when set to null literal",
    ),
    StageTestCase(
        "null_overwrite_existing",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$set": {"a": None}}],
        expected=[{"_id": 1, "a": None}],
        msg="$set should overwrite an existing field with null",
    ),
    StageTestCase(
        "missing_field_ref_omits",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"b": MISSING}}],
        expected=[{"_id": 1, "a": 1}],
        msg="$set should omit the field when set to a reference to a missing field",
    ),
    StageTestCase(
        "missing_field_ref_removes_existing",
        docs=[{"_id": 1, "a": 1, "b": 2}],
        pipeline=[{"$set": {"b": MISSING}}],
        expected=[{"_id": 1, "a": 1}],
        msg="$set should remove an existing field when set to a reference to a missing field",
    ),
    StageTestCase(
        "multi_field_null_and_missing_independent",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"b": None, "c": MISSING, "d": 42}}],
        expected=[{"_id": 1, "a": 1, "b": None, "d": 42}],
        msg=(
            "$set should apply null and missing behaviors independently"
            " per field in a multi-field spec"
        ),
    ),
]

# Property [Field Addition]: setting a field that does not exist on the input
# document adds it to the output, preserving all existing fields.
SET_FIELD_ADDITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "add_new_field",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"b": 2}}],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="$set should add a new field when the field name does not exist",
    ),
    StageTestCase(
        "add_new_field_expression",
        docs=[{"_id": 1, "a": 5}],
        pipeline=[{"$set": {"b": {"$add": ["$a", 10]}}}],
        expected=[{"_id": 1, "a": 5, "b": 15}],
        msg="$set should add a new field computed from an expression",
    ),
    StageTestCase(
        "add_multiple_fields",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"b": 2, "c": 3, "d": 4}}],
        expected=[{"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4}],
        msg="$set should add multiple new fields in a single stage",
    ),
    StageTestCase(
        "add_large_spec_500_fields",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {f"f{i}": i for i in range(500)}}],
        expected=[{"_id": 1, **{f"f{i}": i for i in range(500)}}],
        msg="$set should succeed with 500 fields in a single specification",
    ),
]

# Property [Field Overwrite]: setting a field that already exists on the input
# document replaces its value, and _id can be overwritten with a literal or
# expression result.
SET_FIELD_OVERWRITE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "overwrite_existing_field",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$set": {"a": 99}}],
        expected=[{"_id": 1, "a": 99}],
        msg="$set should replace the value of an existing field",
    ),
    StageTestCase(
        "overwrite_id_literal",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"_id": "new_id"}}],
        expected=[{"_id": "new_id", "a": 1}],
        msg="$set should overwrite _id with a literal value",
    ),
    StageTestCase(
        "overwrite_id_expression",
        docs=[{"_id": 1, "a": 5}],
        pipeline=[{"$set": {"_id": {"$add": ["$a", 10]}}}],
        expected=[{"_id": 15, "a": 5}],
        msg="$set should overwrite _id with an expression result",
    ),
]

# Property [$$REMOVE]: the $$REMOVE system variable explicitly removes a field
# from the output document. $literal wrapping prevents removal and produces the
# literal string instead.
SET_REMOVE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "remove_existing_field",
        docs=[{"_id": 1, "a": 1, "b": 2}],
        pipeline=[{"$set": {"b": "$$REMOVE"}}],
        expected=[{"_id": 1, "a": 1}],
        msg="$set should remove an existing field when set to $$REMOVE",
    ),
    StageTestCase(
        "remove_nonexistent_field",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"b": "$$REMOVE"}}],
        expected=[{"_id": 1, "a": 1}],
        msg="$set should be a no-op when $$REMOVE targets a non-existent field",
    ),
    StageTestCase(
        "remove_id",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"_id": "$$REMOVE"}}],
        expected=[{"a": 1}],
        msg="$set should remove _id when set to $$REMOVE",
    ),
    StageTestCase(
        "remove_all_fields",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"_id": "$$REMOVE", "a": "$$REMOVE"}}],
        expected=[{}],
        msg="$set should produce an empty document when all fields are removed via $$REMOVE",
    ),
    StageTestCase(
        "remove_dot_notation",
        docs=[{"_id": 1, "a": {"x": 1, "y": 2}}],
        pipeline=[{"$set": {"a.x": "$$REMOVE"}}],
        expected=[{"_id": 1, "a": {"y": 2}}],
        msg="$set should remove a nested field via dot notation with $$REMOVE",
    ),
    StageTestCase(
        "remove_array_traversal",
        docs=[{"_id": 1, "arr": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}],
        pipeline=[{"$set": {"arr.x": "$$REMOVE"}}],
        expected=[{"_id": 1, "arr": [{"y": 2}, {"y": 4}]}],
        msg="$set should remove a field from each array element via $$REMOVE with dot notation",
    ),
    StageTestCase(
        "remove_nested_array_traversal",
        docs=[{"_id": 1, "arr": [[{"x": 1, "y": 2}], [{"x": 3, "y": 4}]]}],
        pipeline=[{"$set": {"arr.x": "$$REMOVE"}}],
        expected=[{"_id": 1, "arr": [[{"y": 2}], [{"y": 4}]]}],
        msg="$set should remove a field from documents inside nested arrays via $$REMOVE",
    ),
    StageTestCase(
        "remove_conditional_cond",
        docs=[{"_id": 1, "a": 1, "b": "keep"}, {"_id": 2, "a": 2, "b": "drop"}],
        pipeline=[{"$set": {"b": {"$cond": [{"$eq": ["$a", 2]}, "$$REMOVE", "$b"]}}}],
        expected=[{"_id": 1, "a": 1, "b": "keep"}, {"_id": 2, "a": 2}],
        msg="$set should conditionally remove a field via $cond returning $$REMOVE",
    ),
    StageTestCase(
        "remove_literal_wrapping",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"b": {"$literal": "$$REMOVE"}}}],
        expected=[{"_id": 1, "a": 1, "b": "$$REMOVE"}],
        msg=(
            "$set should produce the literal string '$$REMOVE' when"
            " wrapped in $literal, not removal"
        ),
    ),
]

# Property [System Variables]: system variables $$ROOT and $$CURRENT resolve
# to the full input document when used as field values in $set.
SET_SYSTEM_VARIABLE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "root_resolves_to_document",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$set": {"copy": "$$ROOT"}}, {"$project": {"copy": 1}}],
        expected=[{"_id": 1, "copy": {"_id": 1, "a": 10}}],
        msg="$set should resolve $$ROOT to the full input document",
    ),
    StageTestCase(
        "current_resolves_to_document",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$set": {"copy": "$$CURRENT"}}, {"$project": {"copy": 1}}],
        expected=[{"_id": 1, "copy": {"_id": 1, "a": 10}}],
        msg="$set should resolve $$CURRENT to the full input document",
    ),
    StageTestCase(
        "root_field_path",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$set": {"v": "$$ROOT.a"}}, {"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": 42}],
        msg="$set should resolve $$ROOT.a to the value of field a",
    ),
    StageTestCase(
        "current_field_path",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$set": {"v": "$$CURRENT.a"}}, {"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": 42}],
        msg="$set should resolve $$CURRENT.a to the value of field a",
    ),
    StageTestCase(
        "now_returns_date_type",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": {"$type": "$$NOW"}}}, {"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": "date"}],
        msg="$set should resolve $$NOW to a date value",
    ),
]

# Property [Empty Specification]: an empty specification is a no-op and
# documents pass through unchanged.
SET_EMPTY_SPEC_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_spec_passthrough",
        docs=[{"_id": 1, "a": 1, "b": "hello"}],
        pipeline=[{"$set": {}}],
        expected=[{"_id": 1, "a": 1, "b": "hello"}],
        msg="$set with an empty specification should pass documents through unchanged",
    ),
]

# Property [Values 0, false, 1, true]: numeric 0 and 1 and boolean false and
# true are treated as literal values in $set, not as inclusion/exclusion flags.
SET_LITERAL_VALUE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "zero_false_one_true_add",
        docs=[{"_id": 1, "a": "original"}],
        pipeline=[{"$set": {"b": 0, "c": False, "d": 1, "e": True}}],
        expected=[{"_id": 1, "a": "original", "b": 0, "c": False, "d": 1, "e": True}],
        msg="$set should treat 0, false, 1, and true as literal values when adding new fields",
    ),
    StageTestCase(
        "zero_false_one_true_overwrite",
        docs=[{"_id": 1, "b": "old_b", "c": "old_c", "d": "old_d", "e": "old_e"}],
        pipeline=[{"$set": {"b": 0, "c": False, "d": 1, "e": True}}],
        expected=[{"_id": 1, "b": 0, "c": False, "d": 1, "e": True}],
        msg=(
            "$set should treat 0, false, 1, and true as literal"
            " values when overwriting existing fields"
        ),
    ),
]

# Property [Timestamp Behavior]: Timestamp(0, 0) as a literal value in $set
# is preserved as-is, not replaced by the server unlike on insert.
SET_TIMESTAMP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "timestamp_zero_zero_preserved",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"v": Timestamp(0, 0)}}],
        expected=[{"_id": 1, "a": 1, "v": Timestamp(0, 0)}],
        msg="$set should preserve Timestamp(0, 0) as-is, not replace it with the current time",
    ),
]

SET_FIELD_VALUE_TESTS = (
    SET_NULL_MISSING_TESTS
    + SET_FIELD_ADDITION_TESTS
    + SET_FIELD_OVERWRITE_TESTS
    + SET_REMOVE_TESTS
    + SET_SYSTEM_VARIABLE_TESTS
    + SET_EMPTY_SPEC_TESTS
    + SET_LITERAL_VALUE_TESTS
    + SET_TIMESTAMP_TESTS
)


@pytest.mark.parametrize("stage_name", STAGE_NAMES)
@pytest.mark.parametrize("test_case", pytest_params(SET_FIELD_VALUE_TESTS))
def test_set_field_values(collection, stage_name: str, test_case: StageTestCase):
    """Test $set / $addFields field value cases."""
    populate_collection(collection, test_case)
    pipeline = replace_stage_name(test_case.pipeline, stage_name)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=f"{stage_name!r}: {test_case.msg!r}",
    )
