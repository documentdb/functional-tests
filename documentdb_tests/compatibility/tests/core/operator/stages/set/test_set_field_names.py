from __future__ import annotations

import pytest

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

# Property [Field Name Acceptance]: unicode characters, emoji, spaces, tabs,
# other special characters, and long field names (up to 10,000 characters) are
# accepted in field names.
SET_FIELD_NAME_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_name_unicode",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"\u00e9\u00e8\u00ea": "accented"}}],
        expected=[{"_id": 1, "\u00e9\u00e8\u00ea": "accented"}],
        msg="$set should accept unicode characters in field names",
    ),
    StageTestCase(
        "field_name_emoji",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"\U0001f600\U0001f680": "emoji"}}],
        expected=[{"_id": 1, "\U0001f600\U0001f680": "emoji"}],
        msg="$set should accept emoji in field names",
    ),
    StageTestCase(
        "field_name_space",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"hello world": 1}}],
        expected=[{"_id": 1, "hello world": 1}],
        msg="$set should accept spaces in field names",
    ),
    StageTestCase(
        "field_name_tab",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a\tb": 1}}],
        expected=[{"_id": 1, "a\tb": 1}],
        msg="$set should accept tabs in field names",
    ),
    StageTestCase(
        "field_name_special_chars",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a!@#%^&*()=+": 1}}],
        expected=[{"_id": 1, "a!@#%^&*()=+": 1}],
        msg="$set should accept special characters in field names",
    ),
    StageTestCase(
        "field_name_numeric",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"123": 1}}],
        expected=[{"_id": 1, "123": 1}],
        msg="$set should accept numeric field names",
    ),
    StageTestCase(
        "field_name_non_leading_dollar",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a$bc": 1}}],
        expected=[{"_id": 1, "a$bc": 1}],
        msg="$set should accept non-leading $ in field names",
    ),
]

# Property [Dollar-Sign String Values]: $-prefixed strings are interpreted as
# field path references. $literal prevents interpretation. Inside an array
# literal, a missing reference produces null rather than omitting the element.
SET_DOLLAR_SIGN_STRING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dollar_field_ref",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"ref": "$a"}}],
        expected=[{"_id": 1, "a": "hello", "ref": "hello"}],
        msg="$set should interpret a $-prefixed string as a field reference",
    ),
    StageTestCase(
        "dollar_space_field_ref",
        docs=[{"_id": 1, " hello": "found"}],
        pipeline=[{"$set": {"ref": "$ hello"}}],
        expected=[{"_id": 1, " hello": "found", "ref": "found"}],
        msg="$set should interpret '$ hello' as a reference to a field named ' hello'",
    ),
    StageTestCase(
        "dollar_numeric_field_ref",
        docs=[{"_id": 1, "123": "found"}],
        pipeline=[{"$set": {"ref": "$123"}}],
        expected=[{"_id": 1, "123": "found", "ref": "found"}],
        msg="$set should interpret '$123' as a reference to a field named '123'",
    ),
    StageTestCase(
        "dollar_literal_prevents_ref",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"ref": {"$literal": "$a"}}}],
        expected=[{"_id": 1, "a": 1, "ref": "$a"}],
        msg=(
            "$set should produce the literal string '$a' when"
            " wrapped in $literal, not a field reference"
        ),
    ),
    StageTestCase(
        "dollar_missing_ref_in_array_produces_null",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"ref": [1, MISSING, 3]}}],
        expected=[{"_id": 1, "a": 1, "ref": [1, None, 3]}],
        msg=(
            "$set should produce null for a missing field reference"
            " inside an array literal, unlike at the top level where"
            " the field is omitted"
        ),
    ),
]

SET_FIELD_NAME_TESTS = SET_FIELD_NAME_ACCEPTANCE_TESTS + SET_DOLLAR_SIGN_STRING_TESTS


@pytest.mark.parametrize("stage_name", STAGE_NAMES)
@pytest.mark.parametrize("test_case", pytest_params(SET_FIELD_NAME_TESTS))
def test_set_field_names(collection, stage_name: str, test_case: StageTestCase):
    """Test $set / $addFields field name acceptance and dollar-sign string cases."""
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
