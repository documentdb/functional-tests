"""Tests for connectionStatus showPrivileges parameter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Exists, NotExists
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


@dataclass(frozen=True)
class ShowPrivTruthyTest(BaseTestCase):
    show_priv: Any = None


@dataclass(frozen=True)
class ShowPrivFalsyTest(BaseTestCase):
    show_priv: Any = None


TRUTHY_TESTS: list[ShowPrivTruthyTest] = [
    ShowPrivTruthyTest("true", show_priv=True, msg="true should show privileges"),
    ShowPrivTruthyTest("int_1", show_priv=1, msg="int 1 (truthy) should show privileges"),
    ShowPrivTruthyTest("double_1", show_priv=1.0, msg="double 1.0 (truthy) should show"),
    ShowPrivTruthyTest("long_1", show_priv=Int64(1), msg="long 1 (truthy) should show"),
    ShowPrivTruthyTest("decimal128_1", show_priv=Decimal128("1"), msg="decimal128 1 should show"),
]

FALSY_TESTS: list[ShowPrivFalsyTest] = [
    ShowPrivFalsyTest("false", show_priv=False, msg="false should hide privileges"),
    ShowPrivFalsyTest("int_0", show_priv=0, msg="int 0 (falsy) should hide privileges"),
    ShowPrivFalsyTest("double_0", show_priv=0.0, msg="double 0.0 (falsy) should hide"),
    ShowPrivFalsyTest("long_0", show_priv=Int64(0), msg="long 0 (falsy) should hide"),
    ShowPrivFalsyTest("decimal128_0", show_priv=Decimal128("0"), msg="decimal128 0 should hide"),
    ShowPrivFalsyTest("null", show_priv=None, msg="null (falsy) should hide privileges"),
]


@pytest.mark.parametrize("test", pytest_params(TRUTHY_TESTS))
def test_connectionStatus_show_privileges_truthy(collection, test):
    """Test connectionStatus showPrivileges truthy values return privileges."""
    result = execute_admin_command(
        collection, {"connectionStatus": 1, "showPrivileges": test.show_priv}
    )
    assertResult(
        result,
        expected={"authInfo": {"authenticatedUserPrivileges": Exists()}},
        raw_res=True,
        msg=test.msg,
    )


@pytest.mark.parametrize("test", pytest_params(FALSY_TESTS))
def test_connectionStatus_show_privileges_falsy(collection, test):
    """Test connectionStatus showPrivileges falsy values hide privileges."""
    result = execute_admin_command(
        collection, {"connectionStatus": 1, "showPrivileges": test.show_priv}
    )
    assertResult(
        result,
        expected={"authInfo": {"authenticatedUserPrivileges": NotExists()}},
        raw_res=True,
        msg=test.msg,
    )


def test_connectionStatus_omit_showPrivileges(collection):
    """Test omitting showPrivileges behaves same as showPrivileges: false."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertResult(
        result,
        expected={"authInfo": {"authenticatedUserPrivileges": NotExists()}},
        raw_res=True,
        msg="Omitting showPrivileges should not return privileges",
    )
