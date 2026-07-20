"""Unit tests for the marker reason validator."""

import pytest

from documentdb_tests.framework.marker_reason_validator import validate_marker_reasons


def _write(tmp_path, source: str) -> str:
    """Write source to a temp file and return its path."""
    file_path = tmp_path / "test_sample.py"
    file_path.write_text(source)
    return str(file_path)


@pytest.mark.unit
class TestMarkerReasonValidator:
    def test_skip_with_reason_is_clean(self, tmp_path):
        src = '@pytest.mark.skip(reason="needs Atlas search")\ndef test_a():\n    pass\n'
        assert validate_marker_reasons(_write(tmp_path, src)) == []

    def test_skip_without_reason_is_flagged(self, tmp_path):
        src = "@pytest.mark.skip()\ndef test_a():\n    pass\n"
        errors = validate_marker_reasons(_write(tmp_path, src))
        assert len(errors) == 1 and "skip" in errors[0]

    def test_bare_skip_decorator_is_flagged(self, tmp_path):
        src = "@pytest.mark.skip\ndef test_a():\n    pass\n"
        errors = validate_marker_reasons(_write(tmp_path, src))
        assert len(errors) == 1 and "without a reason" in errors[0]

    def test_empty_reason_is_flagged(self, tmp_path):
        src = '@pytest.mark.xfail(reason="   ")\ndef test_a():\n    pass\n'
        errors = validate_marker_reasons(_write(tmp_path, src))
        assert len(errors) == 1 and "xfail" in errors[0]

    def test_none_reason_is_flagged(self, tmp_path):
        src = "@pytest.mark.xfail(reason=None)\ndef test_a():\n    pass\n"
        assert len(validate_marker_reasons(_write(tmp_path, src))) == 1

    def test_variable_reason_is_accepted(self, tmp_path):
        # A non-literal reason (e.g. a shared constant) can't be resolved
        # statically, so it's accepted as present.
        src = (
            "_R = 'server crashes on views'\n"
            '@pytest.mark.engine_xcrash(engine="mongodb", reason=_R)\n'
            "def test_a():\n    pass\n"
        )
        assert validate_marker_reasons(_write(tmp_path, src)) == []

    def test_engine_xfail_in_marks_with_reason_is_clean(self, tmp_path):
        src = (
            "params = [\n"
            "    pytest.param(1, marks=pytest.mark.engine_xfail(\n"
            '        engine="mongodb", reason="known incompatibility")),\n'
            "]\n"
        )
        assert validate_marker_reasons(_write(tmp_path, src)) == []

    def test_engine_xfail_in_marks_without_reason_is_flagged(self, tmp_path):
        src = (
            "params = [\n"
            '    pytest.param(1, marks=pytest.mark.engine_xfail(engine="mongodb")),\n'
            "]\n"
        )
        errors = validate_marker_reasons(_write(tmp_path, src))
        assert len(errors) == 1 and "engine_xfail" in errors[0]

    def test_module_level_constant_marker_is_checked(self, tmp_path):
        src = 'X = pytest.mark.engine_xfail(engine="mongodb")\n'
        errors = validate_marker_reasons(_write(tmp_path, src))
        assert len(errors) == 1 and "engine_xfail" in errors[0]

    def test_runtime_skip_with_literal_is_clean(self, tmp_path):
        src = 'def test_a():\n    pytest.skip("no system namespace found")\n'
        assert validate_marker_reasons(_write(tmp_path, src)) == []

    def test_runtime_skip_with_fstring_is_clean(self, tmp_path):
        # A runtime message is expected to embed dynamic context; presence is enough.
        src = 'def test_a():\n    pytest.skip(f"unrecognized {x!r}")\n'
        assert validate_marker_reasons(_write(tmp_path, src)) == []

    def test_runtime_skip_without_argument_is_flagged(self, tmp_path):
        src = "def test_a():\n    pytest.skip()\n"
        errors = validate_marker_reasons(_write(tmp_path, src))
        assert len(errors) == 1 and "pytest.skip()" in errors[0]

    def test_runtime_skip_with_empty_literal_is_flagged(self, tmp_path):
        src = 'def test_a():\n    pytest.skip("")\n'
        errors = validate_marker_reasons(_write(tmp_path, src))
        assert len(errors) == 1 and "pytest.skip()" in errors[0]

    def test_runtime_fail_and_xfail_without_argument_are_flagged(self, tmp_path):
        src = "def test_a():\n    pytest.fail()\ndef test_b():\n    pytest.xfail()\n"
        errors = validate_marker_reasons(_write(tmp_path, src))
        assert len(errors) == 2

    def test_unparseable_file_is_skipped(self, tmp_path):
        assert validate_marker_reasons(_write(tmp_path, "def (:\n")) == []
