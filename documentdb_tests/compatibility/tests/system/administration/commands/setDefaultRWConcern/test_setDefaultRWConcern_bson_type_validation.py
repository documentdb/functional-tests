"""BSON type validation tests for setDefaultRWConcern."""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]


# NULL is skipped from rejection: a null concern is treated as omitted, not rejected.
# The null-as-omitted behavior is covered in test_setDefaultRWConcern_valid_inputs.py.
FIELD_SPECS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="setDefaultRWConcern_value",
        msg="setDefaultRWConcern command value is type-agnostic (any BSON type accepted)",
        keyword="setDefaultRWConcern",
        valid_types=list(BsonType),
        requires={"defaultReadConcern": {"level": "local"}},
    ),
    BsonTypeTestCase(
        id="defaultReadConcern",
        msg="defaultReadConcern should accept object types only",
        keyword="defaultReadConcern",
        valid_types=[BsonType.OBJECT],
        skip_rejection_types=[BsonType.NULL],
        valid_inputs={BsonType.OBJECT: {"level": "local"}},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="defaultWriteConcern",
        msg="defaultWriteConcern should accept object types only",
        keyword="defaultWriteConcern",
        valid_types=[BsonType.OBJECT],
        skip_rejection_types=[BsonType.NULL],
        valid_inputs={BsonType.OBJECT: {"w": 1}},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="writeConcern",
        msg="writeConcern should accept object types only",
        keyword="writeConcern",
        valid_types=[BsonType.OBJECT],
        skip_rejection_types=[BsonType.NULL],
        valid_inputs={BsonType.OBJECT: {"w": 1}},
        requires={"defaultReadConcern": {"level": "local"}},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(FIELD_SPECS)
REJECTION_CASES = generate_bson_rejection_test_cases(FIELD_SPECS)


def _build_command(spec: BsonTypeTestCase, sample_value):
    """Build a setDefaultRWConcern command with ``sample_value`` in ``spec.keyword``."""
    keyword = spec.keyword
    assert keyword is not None, "BsonTypeTestCase must define a keyword"
    if keyword == "setDefaultRWConcern":
        command = {"setDefaultRWConcern": sample_value}
    else:
        command = {"setDefaultRWConcern": 1, keyword: sample_value}
    if spec.requires:
        command.update(spec.requires)
    return command


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_setDefaultRWConcern_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test each field accepts the BSON types declared valid for it."""
    result = execute_admin_command(collection, _build_command(spec, sample_value))
    assertProperties(result, {"ok": Eq(1.0)}, msg=spec.msg, raw_res=True)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_setDefaultRWConcern_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test each field rejects BSON types outside its declared valid set."""
    result = execute_admin_command(collection, _build_command(spec, sample_value))
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)
