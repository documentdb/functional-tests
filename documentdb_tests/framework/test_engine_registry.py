"""Unit tests for reading test targets from the compose file (no database needed)."""

import pytest

from documentdb_tests.framework.engine_registry import _host_port, load_targets


@pytest.mark.unit
class TestHostPort:
    def test_loopback_mapping(self):
        assert _host_port({"ports": ["127.0.0.1:27017:27017"]}) == "27017"

    def test_bare_mapping(self):
        assert _host_port({"ports": ["27018:27017"]}) == "27018"

    def test_no_ports(self):
        assert _host_port({}) is None


@pytest.mark.unit
def test_compose_targets_connect_to_their_host_ports():
    by_name = {t.name: t.connection_string for t in load_targets()}
    assert by_name["mongo-standalone"] == "mongodb://localhost:27017"
    assert by_name["mongo-replset"] == "mongodb://localhost:27018/?directConnection=true"
