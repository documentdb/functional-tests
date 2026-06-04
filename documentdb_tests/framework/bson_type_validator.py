"""BSON type test harness.

Generates parametrized test cases that verify operators correctly reject
invalid BSON types and accept valid BSON types.
"""

from dataclasses import dataclass
from typing import Optional

from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import BSON_TYPE_SAMPLES, BsonType


@dataclass(frozen=True)
class BsonTypeTestCase(BaseTestCase):
    """Test case for verifying an operator keyword's BSON type handling.

    Each case defines a keyword and its accepted types. The test framework
    generates rejection tests for every BSON type not in valid_types, and
    acceptance tests for every type in valid_types.

    Attributes:
        keyword: The operator keyword being tested (e.g. "minimum", "required").
        valid_types: List of BsonType values the keyword accepts.
            All other BSON types will be tested as rejections.
        skip_rejection_types: Optional list of BsonType values to exclude from
            rejection test generation. USE SPARINGLY — only for types that have
            documented quirky behavior. If a type cleanly errors
            or cleanly succeeds, it belongs in valid_types or as a rejection — not here.
        requires: Optional sibling fields needed alongside the keyword
            (e.g. {"minimum": 0} for exclusiveMinimum).
        default_error_code: Expected error code for rejected types.
        error_code_overrides: Custom error code for a specific BSON type that
            differs from default_error_code, as {BsonType: code}.
        valid_inputs: Optional per-type sample overrides for acceptance tests,
            used when the generic BSON_TYPE_SAMPLES value is not semantically
            valid for the keyword (e.g. {"bsonType": "string"} for properties).
    """

    keyword: Optional[str] = None
    valid_types: Optional[list] = None
    skip_rejection_types: Optional[list] = None
    requires: Optional[dict] = None
    default_error_code: int = TYPE_MISMATCH_ERROR
    error_code_overrides: Optional[dict] = None
    valid_inputs: Optional[dict] = None

    def expected_code(self, bson_type):
        """Return the expected error code for a rejected BsonType."""
        if self.error_code_overrides:
            return self.error_code_overrides.get(bson_type, self.default_error_code)
        return self.default_error_code


def generate_bson_rejection_test_cases(params):
    """Generate pytest.param tuples for rejected BSON types."""
    import pytest

    cases = []
    for spec in params:
        accepted = set(spec.valid_types)
        skipped = set(spec.skip_rejection_types or [])
        for bson_type in BsonType:
            if bson_type in accepted or bson_type in skipped:
                continue
            sample_value = BSON_TYPE_SAMPLES[bson_type]
            test_id = f"reject_{bson_type.value}_for_{spec.id}"
            cases.append(pytest.param(bson_type, sample_value, spec, id=test_id))
    return cases


def generate_bson_acceptance_test_cases(params):
    """Generate pytest.param tuples for valid types that should be accepted."""
    import pytest

    cases = []
    for spec in params:
        for bson_type in spec.valid_types:
            if spec.valid_inputs and bson_type in spec.valid_inputs:
                sample_value = spec.valid_inputs[bson_type]
            else:
                sample_value = BSON_TYPE_SAMPLES[bson_type]
            test_id = f"accept_{bson_type.value}_for_{spec.id}"
            cases.append(pytest.param(bson_type, sample_value, spec, id=test_id))
    return cases
