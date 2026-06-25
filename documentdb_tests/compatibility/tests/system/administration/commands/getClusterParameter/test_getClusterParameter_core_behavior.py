"""Tests for getClusterParameter core retrieval behavior.

Covers read coherence and idempotency that hold on any single deployment:
repeated reads are stable, a single-name read agrees with the same parameter's
entry in the wildcard result, and every parameter advertised by '*' is
individually retrievable.

DEFERRED (require a sharded cluster or controlled concurrency, not available on
a single mongod target):
- mongos durable value vs mongod cached value divergence and eventual
  convergence (#13). On a sharded cluster mongos reads the config-server
  durable value while mongod reads a cached snapshot; this needs a mongos +
  shard topology to observe.
- Concurrent getClusterParameter during a setClusterParameter must observe a
  coherent (old or new) snapshot, never partial (#14). Needs deterministic
  interleaving with a writer and is inherently racy on a single node.
"""

import pytest

from documentdb_tests.compatibility.tests.system.administration.commands.getClusterParameter.utils import (  # noqa: E501
    all_cluster_parameters,
    valid_parameter_names,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


def test_getClusterParameter_repeated_wildcard_returns_same_parameter_set(collection):
    """Test repeated '*' calls return the same set of parameter names (idempotent)."""
    first = execute_admin_command(collection, {"getClusterParameter": "*"})["clusterParameters"]
    second = execute_admin_command(collection, {"getClusterParameter": "*"})["clusterParameters"]
    names_first = sorted(p["_id"] for p in first)
    names_second = sorted(p["_id"] for p in second)
    assertProperties(
        {"names": names_second},
        {"names": Eq(names_first)},
        msg="Repeated '*' reads should return the same set of parameter names.",
        raw_res=True,
    )


def test_getClusterParameter_repeated_single_read_is_consistent(collection):
    """Test reading the same parameter twice returns an identical entry."""
    (name,) = valid_parameter_names(collection, 1)
    first = execute_admin_command(collection, {"getClusterParameter": name})["clusterParameters"][0]
    second = execute_admin_command(collection, {"getClusterParameter": name})["clusterParameters"][
        0
    ]
    assertProperties(
        {"entry": second},
        {"entry": Eq(first)},
        msg=f"Repeated single read of '{name}' should be consistent.",
        raw_res=True,
    )


def test_getClusterParameter_single_name_matches_wildcard_entry(collection):
    """Test a single-name read agrees with that parameter's entry under '*'."""
    (name,) = valid_parameter_names(collection, 1)
    single = execute_admin_command(collection, {"getClusterParameter": name})["clusterParameters"][
        0
    ]
    wildcard_entry = next(p for p in all_cluster_parameters(collection) if p["_id"] == name)
    assertProperties(
        {"entry": single},
        {"entry": Eq(wildcard_entry)},
        msg=f"Single read of '{name}' should match its '*' entry.",
        raw_res=True,
    )


def test_getClusterParameter_wildcard_names_individually_retrievable(collection):
    """Test parameters advertised by '*' are each retrievable by name."""
    names = [p["_id"] for p in all_cluster_parameters(collection)][:5]
    retrieved = {}
    for name in names:
        params = execute_admin_command(collection, {"getClusterParameter": name})[
            "clusterParameters"
        ]
        retrieved[name] = [len(params), params[0]["_id"] if params else None]
    expected = {name: [1, name] for name in names}
    assertProperties(
        {"retrieved": retrieved},
        {"retrieved": Eq(expected)},
        msg="Each parameter from '*' should be individually retrievable by name.",
        raw_res=True,
    )
