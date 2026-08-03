"""Unit tests for markdown rendering of arbitrary test data.

Test IDs, reasons, and tracebacks embed test inputs, which can be markup in the
context they land in: table pipes, HTML in <summary>, backtick fences.
"""

import pytest

from documentdb_tests.compatibility.result_analyzer.render_markdown import (
    _failure_details,
    _fenced_block,
    _table_cell,
    render,
)


def _analysis(tests):
    """Minimal analysis dict around the given test details."""
    return {
        "reconciliation": {"collected": 1, "total": 1, "passed": 1},
        "tests": tests,
        "by_feature": {"counts": {}, "requires": set(), "children": {}},
    }


@pytest.mark.unit
class TestTableCell:
    def test_pipe_is_escaped(self):
        assert _table_cell("t[a|b]") == "t[a\\|b]"

    def test_plain_text_unchanged(self):
        assert _table_cell("core/test_x.py::t") == "core/test_x.py::t"


@pytest.mark.unit
class TestFencedBlock:
    def test_plain_traceback_gets_three_backticks(self):
        assert _fenced_block("assert 1 == 2") == ["```", "assert 1 == 2", "```"]

    def test_embedded_fence_cannot_terminate_block(self):
        fenced = _fenced_block("data = '```'")
        assert fenced[0] == "````" and fenced[-1] == "````"

    def test_fence_always_exceeds_longest_run(self):
        fenced = _fenced_block("x = '``````'")
        assert fenced[0] == "`" * 7


@pytest.mark.unit
class TestFailureDetails:
    def test_html_in_test_name_is_escaped(self):
        lines = _failure_details({"name": "test_x.py::t[a<b]", "outcome": "FAIL", "error": "boom"})
        summary = next(line for line in lines if "<summary>" in line)
        assert "t[a&lt;b]" in summary and "t[a<b]" not in summary


@pytest.mark.unit
class TestRenderedTables:
    def test_pipe_in_known_gap_does_not_split_row(self):
        report = render(
            _analysis([{"name": "test_x.py::t[p|q]", "outcome": "XFAIL", "xfail_reason": "a | b"}])
        )
        row = next(line for line in report.splitlines() if "t[p" in line)
        # 2 columns -> exactly 3 unescaped pipes; the data pipes are escaped.
        assert row.count("|") - row.count("\\|") == 3

    def test_pipe_in_skip_reason_does_not_split_row(self):
        report = render(
            _analysis([{"name": "test_x.py::t", "outcome": "SKIPPED", "skip_reason": "needs x|y"}])
        )
        row = next(line for line in report.splitlines() if "needs x" in line)
        assert row.count("|") - row.count("\\|") == 3
