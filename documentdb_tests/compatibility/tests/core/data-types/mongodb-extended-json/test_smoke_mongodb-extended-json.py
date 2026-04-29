"""
Smoke test for mongodb-extended-json.

Tests basic MongoDB Extended JSON support for special types.
"""

from datetime import datetime

import pytest
from bson import Decimal128

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_mongodb_extended_json(collection):
    """Test basic Extended JSON type support."""
    test_date = datetime(2024, 1, 1, 12, 0, 0)
    test_decimal = Decimal128("123.45")

    collection.insert_many(
        [{"_id": 1, "date": test_date, "decimal": test_decimal, "int64": 9223372036854775807.0}]
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})

    expected = [
        {"_id": 1, "date": test_date, "decimal": test_decimal, "int64": 9223372036854775807.0}
    ]
    assertSuccess(result, expected, msg="Should support MongoDB Extended JSON types")
