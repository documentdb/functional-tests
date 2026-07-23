"""Unit tests for report content decisions (verdict logic)."""

import pytest

from documentdb_tests.compatibility.result_analyzer.report_content import (
    VERDICT_FAIL,
    VERDICT_PASS,
    determine_verdict,
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
