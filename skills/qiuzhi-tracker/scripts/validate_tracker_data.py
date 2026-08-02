#!/usr/bin/env python3
"""Validate company-pool and recruitment data for qiuzhi-tracker."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

COMPANY_PRIORITIES = {"重点", "关注", "储备", "排除"}
COMPANY_STATUSES = {"待核验", "已发现岗位", "已核验暂无岗位", "待复核", "不再关注"}
JOB_STATUSES = {"招募中", "即将截止", "已预告", "滚动招聘", "待确认", "已截止", "已暂停"}
HARD_REQUIREMENT_JUDGMENTS = {"满足", "待确认", "不满足"}
JOB_VALUES = {"高", "中", "低", "待确认"}
JOB_FRESHNESS_VALUES = {"新鲜", "需复核", "过期"}
CURRENT_ACTIONS = {"立即投递", "本周投递", "继续核验", "持续关注", "暂不处理"}
SOURCE_LEVELS = {"官方", "官方关联渠道", "第三方待复核"}
ACTIVE_JOB_STATUSES = {"招募中", "即将截止", "滚动招聘"}
INACTIVE_JOB_STATUSES = {"已截止", "已暂停"}
APPLY_ACTIONS = {"立即投递", "本周投递"}

SCORE_DIMENSIONS = {
    "responsibility_fit": 35,
    "skills_evidence": 25,
    "preferred_qualifications": 20,
    "conditions_fit": 20,
}

COMPANY_REQUIRED = (
    "company_name",
    "company_profile",
    "industry",
    "region",
    "job_directions",
    "priority",
    "verification_status",
    "note",
)

JOB_REQUIRED = (
    "company_name",
    "recruitment_cohort",
    "recruitment_project",
    "role_name",
    "location",
    "recruitment_status",
    "deadline",
    "job_freshness",
    "core_duties",
    "hard_requirements",
    "hard_requirement_judgment",
    "preferred_qualifications",
    "job_value",
    "job_value_basis",
    "fit_score",
    "score_breakdown",
    "current_action",
    "source_url",
    "source_level",
    "last_verified_date",
    "status_basis",
)

ALIASES = {
    "企业名称": "company_name",
    "岗位所属企业": "company_name",
    "企业性质及规模": "company_profile",
    "行业": "industry",
    "主要地区": "region",
    "适配岗位方向": "job_directions",
    "企业优先级": "priority",
    "核验状态": "verification_status",
    "招聘官网": "career_url",
    "招聘线索与风险备注": "note",
    "招募届别": "recruitment_cohort",
    "招募项目": "recruitment_project",
    "招募项目名称": "recruitment_project",
    "岗位名称": "role_name",
    "工作地点": "location",
    "招聘状态": "recruitment_status",
    "截止日期": "deadline",
    "岗位新鲜度": "job_freshness",
    "核心工作内容": "core_duties",
    "硬性要求": "hard_requirements",
    "硬性门槛": "hard_requirements",
    "硬性要求判断": "hard_requirement_judgment",
    "硬性门槛判断": "hard_requirement_judgment",
    "requirement_judgment": "hard_requirement_judgment",
    "优先条件": "preferred_qualifications",
    "岗位价值": "job_value",
    "岗位价值依据": "job_value_basis",
    "契合指数": "fit_score",
    "评分分项": "score_breakdown",
    "当前行动": "current_action",
    "招聘链接": "source_url",
    "来源等级": "source_level",
    "最后核验日期": "last_verified_date",
    "状态判断依据": "status_basis",
}


def parse_iso_date(value: Any) -> date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def parse_as_of(value: str) -> date:
    parsed = parse_iso_date(value)
    if parsed is None:
        raise argparse.ArgumentTypeError("--as-of must use YYYY-MM-DD")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate qiuzhi-tracker JSON data.")
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--min-companies", type=int, default=0)
    parser.add_argument("--min-jobs", type=int, default=0)
    parser.add_argument("--as-of", type=parse_as_of, default=date.today())
    parser.add_argument("--normalized", type=Path)
    return parser.parse_args()


def nonempty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def normalize_dict(raw: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in raw.items():
        key = ALIASES.get(key, key)
        if isinstance(value, str):
            value = value.strip()
        output[key] = value
    return output


def valid_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalized_company_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[\s（）()·•._-]+", "", text)


def make_record_id(record: dict[str, Any]) -> str:
    parts = [
        record.get("company_name", ""),
        record.get("recruitment_cohort", ""),
        record.get("recruitment_project", ""),
        record.get("role_name", ""),
        record.get("location", ""),
    ]
    return "|".join(str(part).strip() for part in parts)


def expected_freshness(verified_date: date, as_of: date) -> str | None:
    age = (as_of - verified_date).days
    if age < 0:
        return None
    if age <= 7:
        return "新鲜"
    if age <= 30:
        return "需复核"
    return "过期"


def load_payload(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ValueError("top-level JSON must be an object with 'companies' and 'jobs' lists")

    companies = payload.get("companies")
    jobs = payload.get("jobs")
    if not isinstance(companies, list) or not isinstance(jobs, list):
        raise ValueError("'companies' and 'jobs' must both be lists")

    normalized_companies: list[dict[str, Any]] = []
    normalized_jobs: list[dict[str, Any]] = []
    for index, item in enumerate(companies, 1):
        if not isinstance(item, dict):
            raise ValueError(f"company {index} is not an object")
        normalized_companies.append(normalize_dict(item))
    for index, item in enumerate(jobs, 1):
        if not isinstance(item, dict):
            raise ValueError(f"job {index} is not an object")
        normalized_jobs.append(normalize_dict(item))
    return normalized_companies, normalized_jobs


def validate_companies(companies: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seen: dict[str, int] = {}

    for row_number, company in enumerate(companies, 1):
        prefix = f"company {row_number}"
        for field in COMPANY_REQUIRED:
            if not nonempty(company.get(field)):
                errors.append(f"{prefix}: missing required field '{field}'")

        priority = str(company.get("priority", "")).strip()
        if priority and priority not in COMPANY_PRIORITIES:
            errors.append(f"{prefix}: invalid priority '{priority}'")

        status = str(company.get("verification_status", "")).strip()
        if status and status not in COMPANY_STATUSES:
            errors.append(f"{prefix}: invalid verification_status '{status}'")

        career_url = company.get("career_url")
        if nonempty(career_url) and not valid_url(career_url):
            warnings.append(f"{prefix}: career_url is not a valid http(s) URL")

        key = normalized_company_name(company.get("company_name"))
        if key:
            if key in seen:
                errors.append(
                    f"{prefix}: duplicate company name after normalization; first seen in company {seen[key]}"
                )
            else:
                seen[key] = row_number
    return errors, warnings


def validate_score_breakdown(
    job: dict[str, Any], prefix: str, score: float
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    breakdown = job.get("score_breakdown")
    if not isinstance(breakdown, dict):
        return [f"{prefix}: score_breakdown must be an object"], warnings

    total = 0.0
    for dimension, maximum in SCORE_DIMENSIONS.items():
        value = breakdown.get(dimension)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            errors.append(f"{prefix}: score_breakdown.{dimension} must be numeric")
            continue
        if not 0 <= numeric <= maximum:
            errors.append(
                f"{prefix}: score_breakdown.{dimension} must be between 0 and {maximum}"
            )
        total += numeric

    extras = sorted(set(breakdown) - set(SCORE_DIMENSIONS))
    if extras:
        warnings.append(f"{prefix}: unrecognized score_breakdown keys: {', '.join(extras)}")
    if score >= 0 and abs(total - score) > 1e-9:
        errors.append(f"{prefix}: score_breakdown total {total:g} does not equal fit_score {score:g}")
    return errors, warnings


def validate_jobs(
    jobs: list[dict[str, Any]],
    companies: list[dict[str, Any]] | None = None,
    as_of: date | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seen: dict[str, int] = {}
    as_of = as_of or date.today()
    known_companies = None
    if companies is not None:
        known_companies = {
            normalized_company_name(company.get("company_name")) for company in companies
        }

    for row_number, job in enumerate(jobs, 1):
        prefix = f"job {row_number}"
        for field in JOB_REQUIRED:
            if not nonempty(job.get(field)):
                errors.append(f"{prefix}: missing required field '{field}'")

        company_key = normalized_company_name(job.get("company_name"))
        if known_companies is not None and company_key and company_key not in known_companies:
            errors.append(f"{prefix}: company_name does not exist in companies")

        status = str(job.get("recruitment_status", "")).strip()
        if status and status not in JOB_STATUSES:
            errors.append(f"{prefix}: invalid recruitment_status '{status}'")

        judgment = str(job.get("hard_requirement_judgment", "")).strip()
        if judgment and judgment not in HARD_REQUIREMENT_JUDGMENTS:
            errors.append(f"{prefix}: invalid hard_requirement_judgment '{judgment}'")

        job_value = str(job.get("job_value", "")).strip()
        if job_value and job_value not in JOB_VALUES:
            errors.append(f"{prefix}: invalid job_value '{job_value}'")

        action = str(job.get("current_action", "")).strip()
        if action and action not in CURRENT_ACTIONS:
            errors.append(f"{prefix}: invalid current_action '{action}'")

        source_level = str(job.get("source_level", "")).strip()
        if source_level and source_level not in SOURCE_LEVELS:
            errors.append(f"{prefix}: invalid source_level '{source_level}'")

        freshness = str(job.get("job_freshness", "")).strip()
        if freshness and freshness not in JOB_FRESHNESS_VALUES:
            errors.append(f"{prefix}: invalid job_freshness '{freshness}'")

        try:
            score = float(job.get("fit_score"))
            if not 0 <= score <= 100:
                errors.append(f"{prefix}: fit_score must be between 0 and 100")
        except (TypeError, ValueError):
            score = -1
            errors.append(f"{prefix}: fit_score must be numeric")

        score_errors, score_warnings = validate_score_breakdown(job, prefix, score)
        errors.extend(score_errors)
        warnings.extend(score_warnings)

        verified = parse_iso_date(job.get("last_verified_date"))
        if verified is None:
            errors.append(f"{prefix}: last_verified_date must use YYYY-MM-DD")
        else:
            expected = expected_freshness(verified, as_of)
            if expected is None:
                errors.append(f"{prefix}: last_verified_date cannot be after as-of date")
            elif freshness in JOB_FRESHNESS_VALUES and freshness != expected:
                errors.append(
                    f"{prefix}: job_freshness '{freshness}' does not match expected '{expected}'"
                )
            if status in ACTIVE_JOB_STATUSES and expected == "过期":
                errors.append(f"{prefix}: active status cannot rely on an expired verification")
            elif status in ACTIVE_JOB_STATUSES and expected == "需复核":
                warnings.append(f"{prefix}: active status should be re-verified before delivery")

        deadline_value = job.get("deadline")
        deadline = None
        if str(deadline_value).strip() == "未披露":
            pass
        else:
            deadline = parse_iso_date(deadline_value)
            if deadline is None:
                errors.append(f"{prefix}: deadline must use YYYY-MM-DD or be '未披露'")

        if deadline is not None:
            days_left = (deadline - as_of).days
            if days_left < 0 and status not in INACTIVE_JOB_STATUSES:
                errors.append(f"{prefix}: past deadline requires an inactive recruitment status")
            if verified is not None and deadline < verified and status in ACTIVE_JOB_STATUSES:
                errors.append(f"{prefix}: active status was verified after its deadline")
            if status == "即将截止" and not 0 <= days_left <= 7:
                errors.append(f"{prefix}: '即将截止' requires a deadline within 7 days")
        elif status == "即将截止":
            errors.append(f"{prefix}: '即将截止' requires a disclosed deadline")

        source_url = job.get("source_url")
        if status in ACTIVE_JOB_STATUSES and not valid_url(source_url):
            errors.append(f"{prefix}: active status requires a valid source_url")
        elif nonempty(source_url) and not valid_url(source_url):
            warnings.append(f"{prefix}: source_url is not a valid http(s) URL")

        if status in ACTIVE_JOB_STATUSES and source_level == "第三方待复核":
            errors.append(f"{prefix}: active status requires an official or officially linked source")

        if status in INACTIVE_JOB_STATUSES and action != "暂不处理":
            errors.append(f"{prefix}: inactive status '{status}' requires current_action '暂不处理'")

        if judgment == "不满足" and action != "暂不处理":
            errors.append(f"{prefix}: unmet hard requirements require current_action '暂不处理'")
        if judgment == "待确认" and action in APPLY_ACTIONS:
            errors.append(f"{prefix}: pending hard requirements conflict with current_action '{action}'")

        if action in APPLY_ACTIONS:
            if status not in ACTIVE_JOB_STATUSES:
                errors.append(f"{prefix}: '{action}' requires an active recruitment status")
            if judgment != "满足":
                errors.append(f"{prefix}: '{action}' requires hard_requirement_judgment '满足'")
            if job_value == "低":
                warnings.append(f"{prefix}: applying to a low-value role needs an explicit strategy reason")

        if action == "立即投递" and 0 <= score < 80:
            warnings.append(f"{prefix}: '立即投递' with fit_score below 80 needs manual review")
        if action == "本周投递" and 0 <= score < 65:
            warnings.append(f"{prefix}: '本周投递' with fit_score below 65 needs manual review")

        record_id = make_record_id(job)
        if record_id.startswith("|") or record_id.endswith("|") or "||" in record_id:
            errors.append(f"{prefix}: all record-ID components must be present")
        if record_id in seen:
            errors.append(f"{prefix}: duplicate record ID; first seen in job {seen[record_id]}: {record_id}")
        else:
            seen[record_id] = row_number
        job["record_id"] = record_id

    return errors, warnings


def main() -> int:
    args = parse_args()
    try:
        companies, jobs = load_payload(args.json_file)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    if len(companies) < args.min_companies:
        errors.append(f"company count {len(companies)} is below required minimum {args.min_companies}")
    if len(jobs) < args.min_jobs:
        errors.append(f"job count {len(jobs)} is below required minimum {args.min_jobs}")

    company_errors, company_warnings = validate_companies(companies)
    job_errors, job_warnings = validate_jobs(jobs, companies, args.as_of)
    errors.extend(company_errors)
    errors.extend(job_errors)
    warnings.extend(company_warnings)
    warnings.extend(job_warnings)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1

    if args.normalized:
        args.normalized.parent.mkdir(parents=True, exist_ok=True)
        args.normalized.write_text(
            json.dumps({"companies": companies, "jobs": jobs}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Normalized data written to: {args.normalized}")

    print(f"PASSED: {len(companies)} companies, {len(jobs)} jobs, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
