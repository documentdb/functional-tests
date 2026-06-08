"""Tests for $merge into collection-name and database-name rejection."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    INVALID_NAMESPACE_ERROR,
    MERGE_INTO_EMPTY_STRING_ERROR,
    MERGE_RESERVED_DATABASE_ERROR,
    MERGE_SYSTEM_COLLECTION_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)

# Property [into Collection Name $merge-Specific Rejection]: $merge rejects
# invalid collection names with $merge-specific errors distinct from generic
# namespace validation.
MERGE_INTO_NAME_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "into_name_empty_string_document_form",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": ""}}],
        error_code=MERGE_INTO_EMPTY_STRING_ERROR,
        msg="$merge should reject empty string in document form into field",
    ),
    MergeTestCase(
        "into_name_empty_string_simplified",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": ""}],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$merge should reject empty string in simplified form",
    ),
    MergeTestCase(
        "into_name_system_prefix",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": "system.test"}}],
        error_code=MERGE_SYSTEM_COLLECTION_ERROR,
        msg="$merge should reject 'system.' prefix in collection name",
    ),
]

# Property [into Database Name $merge-Specific Rejection]: $merge rejects the
# reserved database names admin, config, and local with a $merge-specific
# error. Generic namespace character/length rules are covered by the shared
# namespace tests.
MERGE_DB_NAME_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "db_name_reserved_admin",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": {"db": "admin", "coll": "target"}}}],
        error_code=MERGE_RESERVED_DATABASE_ERROR,
        msg="$merge should reject reserved database name 'admin'",
    ),
    MergeTestCase(
        "db_name_reserved_config",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": {"db": "config", "coll": "target"}}}],
        error_code=MERGE_RESERVED_DATABASE_ERROR,
        msg="$merge should reject reserved database name 'config'",
    ),
    MergeTestCase(
        "db_name_reserved_local",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": {"db": "local", "coll": "target"}}}],
        error_code=MERGE_RESERVED_DATABASE_ERROR,
        msg="$merge should reject reserved database name 'local'",
    ),
]

MERGE_INTO_NAME_CASES = MERGE_INTO_NAME_ERROR_TESTS + MERGE_DB_NAME_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_INTO_NAME_CASES))
def test_stages_merge_into_name_error(collection, test_case: MergeTestCase):
    """Test $merge into collection and database name validation errors."""
    target = test_case.prepare(collection)
    result = execute_command(collection, test_case.build_command(collection, target))
    if test_case.error_code is None:
        result = execute_command(collection, {"find": target, "filter": {}, "sort": {"_id": 1}})
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
