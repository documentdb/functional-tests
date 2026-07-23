"""Unit tests for report content decisions (verdict logic)."""

import pytest

from documentdb_tests.compatibility.result_analyzer.report_content import (
    NEEDS_ATTENTION_CAP,
    VERDICT_FAIL,
    VERDICT_PASS,
    cap_items,
    determine_verdict,
    group_needs_attention,
    needs_attention,
)


@pytest.mark.unit
class TestDetermineVerdict:
    def test_clean_pass(self):
        recon = {"passed": 10, "failed": 0, "error": 0, "xpassed": 0}
        verdict, reason = determine_verdict(recon)
        assert verdict == VERDICT_PASS and reason == ""

    def test_failure_is_fail(self):
        recon = {"passed": 8, "failed": 2, "error": 0, "xpassed": 0}
        verdict, _ = determine_verdict(recon)
        assert verdict == VERDICT_FAIL

    def test_error_is_fail(self):
        recon = {"passed": 9, "failed": 0, "error": 1, "xpassed": 0}
        verdict, _ = determine_verdict(recon)
        assert verdict == VERDICT_FAIL

    def test_raw_xpass_is_fail_and_takes_priority(self):
        # A raw xpassed means strict wasn't applied; results are untrustworthy.
        recon = {"passed": 10, "failed": 0, "error": 0, "xpassed": 1}
        verdict, reason = determine_verdict(recon)
        assert verdict == VERDICT_FAIL and "invalid" in reason

    def test_no_tests_executed_is_fail(self):
        # Everything deselected/skipped: nothing ran, so the run has no value.
        recon = {"passed": 0, "failed": 0, "error": 0, "xpassed": 0, "skipped": 3}
        verdict, reason = determine_verdict(recon)
        assert verdict == VERDICT_FAIL and "no tests ran" in reason

    def test_skipped_and_xfailed_do_not_block_pass(self):
        # A run that passed everything it ran is PASS even with skips/known gaps.
        recon = {"passed": 5, "failed": 0, "error": 0, "xpassed": 0, "skipped": 2, "xfailed": 3}
        verdict, _ = determine_verdict(recon)
        assert verdict == VERDICT_PASS

    def test_missing_keys_treated_as_zero_is_fail(self):
        # Empty reconciliation -> nothing executed -> FAIL.
        verdict, reason = determine_verdict({})
        assert verdict == VERDICT_FAIL and "no tests ran" in reason


@pytest.mark.unit
class TestNeedsAttention:
    def _analysis(self):
        return {
            "tests": [
                {"name": "a", "outcome": "PASS"},
                {"name": "b", "outcome": "FAIL", "failure_type": "RESULT_MISMATCH"},
                {"name": "c", "outcome": "ERROR", "failure_type": "UNKNOWN"},
                {"name": "d", "outcome": "SKIPPED"},
                {"name": "e", "outcome": "XFAIL"},
            ]
        }

    def test_includes_failures_and_errors_only(self):
        names = {t["name"] for t in needs_attention(self._analysis())}
        # b (FAIL) and c (ERROR); not the pass/skip/xfail.
        assert names == {"b", "c"}

    def test_grouped_by_failure_type(self):
        grouped = group_needs_attention(self._analysis())
        assert set(grouped) == {"RESULT_MISMATCH", "UNKNOWN"}
        assert grouped["RESULT_MISMATCH"][0]["name"] == "b"
        assert grouped["UNKNOWN"][0]["name"] == "c"


@pytest.mark.unit
class TestCapItems:
    def test_under_cap_keeps_all(self):
        kept, omitted = cap_items([1, 2, 3], cap=5)
        assert kept == [1, 2, 3] and omitted == 0

    def test_over_cap_trims_and_counts(self):
        kept, omitted = cap_items(list(range(30)), cap=25)
        assert len(kept) == 25 and omitted == 5

    def test_default_cap(self):
        kept, omitted = cap_items(list(range(NEEDS_ATTENTION_CAP + 3)))
        assert len(kept) == NEEDS_ATTENTION_CAP and omitted == 3
