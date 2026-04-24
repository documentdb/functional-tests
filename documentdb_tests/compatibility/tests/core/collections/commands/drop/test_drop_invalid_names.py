import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import INVALID_NAMESPACE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Invalid Name Type]: drop rejects non-string name values with
# INVALID_NAMESPACE_ERROR.
DROP_INVALID_NAME_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null",
        command={"drop": None},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Null collection name should fail with InvalidNamespace",
    ),
    CommandTestCase(
        "integer",
        command={"drop": 123},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Integer collection name should fail with InvalidNamespace",
    ),
    CommandTestCase(
        "boolean",
        command={"drop": True},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Boolean collection name should fail with InvalidNamespace",
    ),
    CommandTestCase(
        "double",
        command={"drop": 1.5},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Double collection name should fail with InvalidNamespace",
    ),
    CommandTestCase(
        "object",
        command={"drop": {"a": 1}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Object collection name should fail with InvalidNamespace",
    ),
    CommandTestCase(
        "array",
        command={"drop": [1, 2]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Array collection name should fail with InvalidNamespace",
    ),
]

# Property [Invalid Name Value]: drop rejects invalid string name values
# with INVALID_NAMESPACE_ERROR.
DROP_INVALID_NAME_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_string",
        command={"drop": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Empty string name should fail with InvalidNamespace",
    ),
    CommandTestCase(
        "null_byte",
        command={"drop": "test\x00coll"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Name with null byte should fail with InvalidNamespace",
    ),
    CommandTestCase(
        "just_dot",
        command={"drop": "."},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Single dot name should fail with InvalidNamespace",
    ),
    CommandTestCase(
        "leading_dot",
        command={"drop": ".test"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Leading dot name should fail with InvalidNamespace",
    ),
]

DROP_INVALID_NAME_TESTS: list[CommandTestCase] = (
    DROP_INVALID_NAME_TYPE_TESTS + DROP_INVALID_NAME_VALUE_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DROP_INVALID_NAME_TESTS))
def test_drop_invalid_names(database_client, collection, test):
    """Test drop command rejects invalid collection names."""
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
