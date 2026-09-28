"""Tests for dropConnections command comment field acceptance.

Verifies that the optional comment field accepts any valid BSON type.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.test_constants import BsonType

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]

# Property [Comment Acceptance]: dropConnections accepts any BSON type for the
# optional comment field.
_COMMENT_PARAMS = [
    BsonTypeTestCase(
        id="comment",
        msg="dropConnections should accept all BSON types for comment field",
        keyword="comment",
        valid_types=list(BsonType),
    ),
]

_COMMENT_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(_COMMENT_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", _COMMENT_ACCEPTANCE_CASES)
def test_dropConnections_comment_accepts_type(collection, bson_type, sample_value, spec):
    """Test dropConnections accepts any BSON type for comment field."""
    result = execute_admin_command(
        collection,
        {"dropConnections": 1, "hostAndPort": [], "comment": sample_value},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg=f"dropConnections should accept {bson_type.value} for comment field.",
    )
