from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "qiuzhi-tracker" / "scripts" / "validate_tracker_data.py"
SPEC = importlib.util.spec_from_file_location("tracker_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
AS_OF = date(2026, 8, 2)


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads((ROOT / "examples" / "example-tracker-data.json").read_text(encoding="utf-8"))

    def validate(self, jobs):
        return MODULE.validate_jobs(jobs, copy.deepcopy(self.payload["companies"]), AS_OF)

    def test_sample_data_passes(self) -> None:
        company_errors, _ = MODULE.validate_companies(copy.deepcopy(self.payload["companies"]))
        job_errors, _ = self.validate(copy.deepcopy(self.payload["jobs"]))
        self.assertEqual(company_errors, [])
        self.assertEqual(job_errors, [])

    def test_duplicate_company_fails(self) -> None:
        companies = copy.deepcopy(self.payload["companies"])
        companies.append(copy.deepcopy(companies[0]))
        errors, _ = MODULE.validate_companies(companies)
        self.assertTrue(any("duplicate company" in error for error in errors))

    def test_job_company_must_exist(self) -> None:
        jobs = copy.deepcopy(self.payload["jobs"])
        jobs[0]["company_name"] = "不存在的企业（虚构）"
        errors, _ = self.validate(jobs)
        self.assertTrue(any("does not exist" in error for error in errors))

    def test_past_deadline_cannot_be_active(self) -> None:
        jobs = copy.deepcopy(self.payload["jobs"])
        jobs[0]["deadline"] = "2026-08-01"
        jobs[0]["recruitment_status"] = "招募中"
        errors, _ = self.validate(jobs)
        self.assertTrue(any("past deadline" in error for error in errors))

    def test_freshness_must_match_dates(self) -> None:
        jobs = copy.deepcopy(self.payload["jobs"])
        jobs[0]["job_freshness"] = "过期"
        errors, _ = self.validate(jobs)
        self.assertTrue(any("does not match expected" in error for error in errors))

    def test_active_job_rejects_third_party_source(self) -> None:
        jobs = copy.deepcopy(self.payload["jobs"])
        jobs[0]["source_level"] = "第三方待复核"
        errors, _ = self.validate(jobs)
        self.assertTrue(any("official or officially linked" in error for error in errors))

    def test_score_component_range_is_checked(self) -> None:
        jobs = copy.deepcopy(self.payload["jobs"])
        jobs[0]["score_breakdown"]["responsibility_fit"] = 36
        jobs[0]["fit_score"] = 90
        errors, _ = self.validate(jobs)
        self.assertTrue(any("between 0 and 35" in error for error in errors))

    def test_score_components_must_equal_total(self) -> None:
        jobs = copy.deepcopy(self.payload["jobs"])
        jobs[0]["fit_score"] = 82
        errors, _ = self.validate(jobs)
        self.assertTrue(any("does not equal fit_score" in error for error in errors))

    def test_pending_hard_requirement_blocks_apply_action(self) -> None:
        jobs = copy.deepcopy(self.payload["jobs"])
        jobs[0]["hard_requirement_judgment"] = "待确认"
        errors, _ = self.validate(jobs)
        self.assertTrue(any("pending hard requirements" in error for error in errors))

    def test_low_score_apply_is_warning(self) -> None:
        jobs = copy.deepcopy(self.payload["jobs"])
        jobs[0]["fit_score"] = 79
        jobs[0]["score_breakdown"]["responsibility_fit"] = 25
        errors, warnings = self.validate(jobs)
        self.assertEqual(errors, [])
        self.assertTrue(any("manual review" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
