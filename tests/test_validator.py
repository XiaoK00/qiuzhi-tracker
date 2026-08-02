from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "qiuzhi-tracker" / "scripts" / "validate_tracker_data.py"
SPEC = importlib.util.spec_from_file_location("tracker_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(
            (ROOT / "examples" / "example-tracker-data.json").read_text(encoding="utf-8")
        )

    def test_sample_data_passes(self) -> None:
        companies = copy.deepcopy(self.payload["companies"])
        jobs = copy.deepcopy(self.payload["jobs"])
        company_errors, _ = MODULE.validate_companies(companies)
        job_errors, _ = MODULE.validate_jobs(jobs)
        self.assertEqual(company_errors, [])
        self.assertEqual(job_errors, [])

    def test_duplicate_company_fails(self) -> None:
        companies = copy.deepcopy(self.payload["companies"])
        companies.append(copy.deepcopy(companies[0]))
        errors, _ = MODULE.validate_companies(companies)
        self.assertTrue(any("duplicate company" in error for error in errors))

    def test_active_job_requires_url(self) -> None:
        jobs = copy.deepcopy(self.payload["jobs"])
        jobs[0]["source_url"] = ""
        errors, _ = MODULE.validate_jobs(jobs)
        self.assertTrue(any("requires a valid source_url" in error for error in errors))

    def test_inactive_job_cannot_be_immediate(self) -> None:
        jobs = copy.deepcopy(self.payload["jobs"])
        jobs[0]["recruitment_status"] = "已截止"
        jobs[0]["current_action"] = "立即投递"
        errors, _ = MODULE.validate_jobs(jobs)
        self.assertTrue(any("inactive status" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
