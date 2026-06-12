"""Tests for collation interaction with document schema validation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import DOCUMENT_VALIDATION_FAILURE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Validator Enum Ignores Collection Collation]: $jsonSchema enum
# validation always uses binary comparison regardless of the collection's default
# collation, so case-variant values are rejected.
COLLATION_VALIDATOR_ENUM_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "enum_case_insensitive_rejects_case_variant",
        target_collection=CustomCollection(
            options={
                "collation": {"locale": "en", "strength": 2},
                "validator": {
                    "$jsonSchema": {
                        "properties": {"status": {"enum": ["active", "inactive"]}},
                    }
                },
            }
        ),
        docs=[],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "status": "Active"}],
        },
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="$jsonSchema enum should reject case-variant even with case-insensitive collation",
    ),
    CommandTestCase(
        "enum_exact_match_accepts",
        target_collection=CustomCollection(
            options={
                "collation": {"locale": "en", "strength": 2},
                "validator": {
                    "$jsonSchema": {
                        "properties": {"status": {"enum": ["active", "inactive"]}},
                    }
                },
            }
        ),
        docs=[],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "status": "active"}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="$jsonSchema enum should accept exact match value",
    ),
    CommandTestCase(
        "enum_rejects_non_match",
        target_collection=CustomCollection(
            options={
                "collation": {"locale": "en", "strength": 2},
                "validator": {
                    "$jsonSchema": {
                        "properties": {"status": {"enum": ["active", "inactive"]}},
                    }
                },
            }
        ),
        docs=[],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "status": "pending"}],
        },
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="$jsonSchema enum should reject non-matching value",
    ),
]

# Property [Validator Comparison with Collection Collation]: validator
# expressions using comparison operators respect the collection's default
# collation.
COLLATION_VALIDATOR_COMPARISON_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "validator_expr_eq_case_insensitive",
        target_collection=CustomCollection(
            options={
                "collation": {"locale": "en", "strength": 2},
                "validator": {"status": {"$in": ["active", "inactive"]}},
            }
        ),
        docs=[],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "status": "ACTIVE"}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="validator $in should use collection collation for case-insensitive matching",
    ),
    CommandTestCase(
        "validator_expr_eq_rejects",
        target_collection=CustomCollection(
            options={
                "collation": {"locale": "en", "strength": 2},
                "validator": {"status": {"$in": ["active", "inactive"]}},
            }
        ),
        docs=[],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "status": "pending"}],
        },
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="validator $in should reject non-matching values even with collation",
    ),
]

COLLATION_SCHEMA_VALIDATION_TESTS: list[CommandTestCase] = (
    COLLATION_VALIDATOR_ENUM_TESTS + COLLATION_VALIDATOR_COMPARISON_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_SCHEMA_VALIDATION_TESTS))
def test_collation_schema_validation(database_client, collection, test):
    """Test collation interaction with document schema validation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
