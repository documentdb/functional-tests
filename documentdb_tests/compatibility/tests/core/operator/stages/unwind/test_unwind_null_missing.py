"""Tests for $unwind stage — null and missing handling."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing Dropped by Default]: when preserveNullAndEmptyArrays
# is false or omitted, documents whose path value is null, missing, or an empty
# array are dropped from the output.
UNWIND_NULL_MISSING_DROPPED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dropped_null_document_form",
        docs=[{"_id": 1, "a": None, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[],
        msg="$unwind should drop document when path value is null (document form)",
    ),
    StageTestCase(
        "dropped_null_preserve_false",
        docs=[{"_id": 1, "a": None, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": False}}],
        expected=[],
        msg="$unwind should drop document when path value is null (preserve=false)",
    ),
    StageTestCase(
        "dropped_missing_document_form",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[],
        msg="$unwind should drop document when path field is missing (document form)",
    ),
    StageTestCase(
        "dropped_missing_preserve_false",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": False}}],
        expected=[],
        msg="$unwind should drop document when path field is missing (preserve=false)",
    ),
    StageTestCase(
        "dropped_empty_array_document_form",
        docs=[{"_id": 1, "a": [], "x": 10}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[],
        msg="$unwind should drop document when path value is empty array (document form)",
    ),
    StageTestCase(
        "dropped_empty_array_preserve_false",
        docs=[{"_id": 1, "a": [], "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": False}}],
        expected=[],
        msg="$unwind should drop document when path is empty array (preserve=false)",
    ),
]

# Property [Null and Missing Preserved]: when preserveNullAndEmptyArrays is
# true, documents whose path value is null are emitted with the field set to
# null, and documents whose path field is missing or an empty array are emitted
# with the field omitted.
UNWIND_NULL_MISSING_PRESERVED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "preserved_null",
        docs=[{"_id": 1, "a": None, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": None, "x": 10}],
        msg=(
            "$unwind should emit document with field set to null when path"
            " value is null and preserve=true"
        ),
    ),
    StageTestCase(
        "preserved_missing",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "x": 10}],
        msg=(
            "$unwind should emit document with field omitted when path field"
            " is missing and preserve=true"
        ),
    ),
    StageTestCase(
        "preserved_empty_array",
        docs=[{"_id": 1, "a": [], "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "x": 10}],
        msg=(
            "$unwind should emit document with field omitted when path value"
            " is empty array and preserve=true"
        ),
    ),
]

UNWIND_NULL_MISSING_TESTS = UNWIND_NULL_MISSING_DROPPED_TESTS + UNWIND_NULL_MISSING_PRESERVED_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_NULL_MISSING_TESTS))
def test_unwind_null_missing(collection, test_case: StageTestCase):
    """Test $unwind null and missing handling."""
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
