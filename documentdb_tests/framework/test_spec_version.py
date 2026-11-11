"""Unit tests for spec-version gating with the requires marker (no database needed)."""

import json
import textwrap
from pathlib import Path

import pytest

from documentdb_tests.framework.preconditions import (
    merged_requirements,
    spec_gate_folder,
    unmet_requirements,
    unmet_spec,
)

pytest_plugins = ["pytester"]


@pytest.mark.unit
class TestUnmetSpec:
    def test_ungated_test_is_in_every_spec(self):
        assert unmet_spec({}, "8.2") == {}
        assert unmet_spec({}, "8.3") == {}

    def test_spec_since_is_out_of_an_older_spec(self):
        assert unmet_spec({"spec_since": "8.3"}, "8.2") == {"spec_since": "8.3"}

    def test_spec_since_is_in_its_own_spec(self):
        assert unmet_spec({"spec_since": "8.3"}, "8.3") == {}

    def test_spec_until_is_out_of_a_newer_spec(self):
        assert unmet_spec({"spec_until": "8.2"}, "8.3") == {"spec_until": "8.2"}

    def test_spec_until_is_in_its_own_spec(self):
        assert unmet_spec({"spec_until": "8.2"}, "8.2") == {}

    def test_capability_keys_are_ignored(self):
        assert unmet_spec({"change_streams": True}, "8.2") == {}

    def test_unknown_version_raises(self):
        with pytest.raises(RuntimeError, match="unknown spec version"):
            unmet_spec({"spec_since": "8.4"}, "8.3")


@pytest.mark.unit
class TestUnmetRequirementsIgnoresSpecKeys:
    def test_spec_keys_are_not_unknown_capabilities(self):
        required = {"spec_since": "8.3", "change_streams": True}
        assert unmet_requirements(required, frozenset()) == {"change_streams": True}


class _Marker:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@pytest.mark.unit
class TestMergedRequirements:
    def test_levels_combine(self):
        merged = merged_requirements([_Marker(change_streams=True), _Marker(spec_since="8.3")])
        assert merged == {"change_streams": True, "spec_since": "8.3"}

    def test_closest_wins_on_the_same_key(self):
        merged = merged_requirements([_Marker(spec_since="8.3"), _Marker(spec_since="8.2")])
        assert merged == {"spec_since": "8.3"}


@pytest.mark.unit
class TestSpecGateFolder:
    def test_unknown_version_raises_at_import(self):
        with pytest.raises(RuntimeError, match="unknown spec version"):
            spec_gate_folder(__file__, spec_since="9.0")

    def test_unknown_key_raises_at_import(self):
        with pytest.raises(RuntimeError, match="unknown spec gate keys"):
            spec_gate_folder(__file__, since="8.3")


# A test tree run in a child pytest session, wired to the real collection hooks.
# Capability detection is stubbed so no server is needed: the target has no
# capabilities.
_ROOT_CONFTEST = """
import documentdb_tests.conftest as root

root.detect_capabilities = lambda engine, connection_string: frozenset()

pytest_addoption = root.pytest_addoption
pytest_configure = root.pytest_configure
pytest_generate_tests = root.pytest_generate_tests
pytest_collection_modifyitems = root.pytest_collection_modifyitems
"""

_FOLDER_CONFTEST = """
from documentdb_tests.framework.preconditions import spec_gate_folder

pytest_collection_modifyitems = spec_gate_folder(__file__, spec_since="8.3")
"""

_FILES = {
    "conftest.py": _ROOT_CONFTEST,
    "test_ungated.py": """
        def test_ungated(engine_client):
            pass
    """,
    "test_file_gated.py": """
        import pytest

        pytestmark = [pytest.mark.smoke, pytest.mark.requires(spec_since="8.3")]

        def test_file_gated(engine_client):
            pass
    """,
    "test_until.py": """
        import pytest

        @pytest.mark.requires(spec_until="8.2")
        def test_until(engine_client):
            pass
    """,
    "new_op/conftest.py": _FOLDER_CONFTEST,
    "new_op/test_folder_gated.py": """
        def test_folder_gated(engine_client):
            pass
    """,
    "new_op/test_folder_and_capability.py": """
        import pytest

        @pytest.mark.requires(change_streams=True)
        def test_folder_and_capability(engine_client):
            pass
    """,
}


@pytest.fixture
def run_tree(pytester, monkeypatch):
    """Write the test tree and return a runner for one spec version."""
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[2]))
    for name, source in _FILES.items():
        path = pytester.path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source))
    pytester.makeini("[pytest]\nmarkers =\n    smoke: smoke\n")

    def _run(*spec_args):
        report = pytester.path / "report.json"
        result = pytester.runpytest_subprocess(
            "--collect-only",
            "-q",
            "--connection-string=mongodb://127.0.0.1:1",
            "--engine-name=mongodb",
            "--json-report",
            f"--json-report-file={report}",
            *spec_args,
        )
        sidecar = json.loads((pytester.path / "report.json.deselected.json").read_text())
        header = json.loads(report.read_text())["run"]
        collected = {line.split("::")[1].split("[")[0] for line in result.outlines if "::" in line}
        reasons = {nodeid.split("::")[1].split("[")[0]: why for nodeid, why in sidecar.items()}
        return collected, reasons, header

    return _run


@pytest.mark.unit
class TestSpecGatingInASession:
    def test_default_spec_is_8_2(self, run_tree):
        collected, reasons, header = run_tree()
        assert header["spec_version"] == "8.2"
        assert collected == {"test_ungated", "test_until"}
        assert reasons == {
            "test_file_gated": {"spec_since": "8.3"},
            "test_folder_gated": {"spec_since": "8.3"},
            "test_folder_and_capability": {"spec_since": "8.3"},
        }

    def test_spec_8_3_runs_newer_tests_and_ungated_ones(self, run_tree):
        collected, reasons, header = run_tree("--spec-version=8.3")
        assert header["spec_version"] == "8.3"
        assert header["targets"] == [{"name": "mongodb", "engine": "mongodb", "version": None}]
        assert collected == {"test_ungated", "test_file_gated", "test_folder_gated"}
        assert reasons == {
            "test_until": {"spec_until": "8.2"},
            "test_folder_and_capability": {"change_streams": True},
        }

    def test_unknown_spec_version_is_a_usage_error(self, pytester, run_tree):
        result = pytester.runpytest_subprocess("--collect-only", "--spec-version=9.9")
        assert result.ret == pytest.ExitCode.USAGE_ERROR
        result.stderr.fnmatch_lines(["*--spec-version*invalid choice*"])
