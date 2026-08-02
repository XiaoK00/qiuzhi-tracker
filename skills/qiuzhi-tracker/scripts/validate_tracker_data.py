#!/usr/bin/env python3
"""Validate concise company-pool and recruitment data for qiuzhi-tracker."""

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
REQUIREMENT_JUDGMENTS = {"满足", "待确认", "不满足"}
CURRENT_ACTIONS = {"立即投递", "本周投递", "继续核验", "持续关注", "暂不处理"}
SOURCE_LEVELS = {"官方", "官方关联渠道", "第三方待复核"}
ACTIVE_JOB_STATUSES = {"招募中", "即将截止", "滚动招聘"}
INACTIVE_JOB_STATUSES = {"已截止", "已暂停"}

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
    "core_duties",
    "hard_requirements",
    "requirement_judgment",
    "fit_score",
    "match_and_barriers",
    "current_action",
    "source_url",
    "source_level",
    "last_verified_date",
    "status_basis",
)

ALIASES = {
    "企业名称": "company_name",
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
    "核心工作内容": "core_duties",
    "硬性要求": "hard_requirements",
    "硬性要求判断": "requirement_judgment",
    "薪资福利或岗位质量": "job_quality",
    "契合指数": "fit_score",
    "匹配点与主要门槛": "match_and_barriers",
    "当前行动": "current_action",
    "招聘链接": "source_url",
    "来源等级": "source_level",
    "最后核验日期": "last_verified_date",
    "状态判断依据": "status_basis",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate qiuzhi-tracker JSON data.")
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--min-companies", type=int, default=0)
    parser.add_argument("--min-jobs", type=int, default=0)
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


def valid_iso_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def normalized_company_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s（）()·•._-]+", "", text)
    return text


def make_record_id(record: dict[str, Any]) -> str:
    parts = [
        record.get("company_name", ""),
        record.get("recruitment_cohort", ""),
        record.get("recruitment_project", ""),
        record.get("role_name", ""),
        record.get("location", ""),
    ]
    return "|".join(str(part).strip() for part in parts)


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
        if not key:
            continue
        if key in seen:
            errors.append(
                f"{prefix}: duplicate company name after normalization; first seen in company {seen[key]}"
            )
        else:
            seen[key] = row_number

    return errors, warnings


def validate_jobs(jobs: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seen: dict[str, int] = {}

    for row_number, job in enumerate(jobs, 1):
        prefix = f"job {row_number}"
        for field in JOB_REQUIRED:
            if not nonempty(job.get(field)):
                errors.append(f"{prefix}: missing required field '{field}'")

        status = str(job.get("recruitment_status", "")).strip()
        if status and status not in JOB_STATUSES:
            errors.append(f"{prefix}: invalid recruitment_status '{status}'")

        judgment = str(job.get("requirement_judgment", "")).strip()
        if judgment and judgment not in REQUIREMENT_JUDGMENTS:
            errors.append(f"{prefix}: invalid requirement_judgment '{judgment}'")

        action = str(job.get("current_action", "")).strip()
        if action and action not in CURRENT_ACTIONS:
            errors.append(f"{prefix}: invalid current_action '{action}'")

        source_level = str(job.get("source_level", "")).strip()
        if source_level and source_level not in SOURCE_LEVELS:
            errors.append(f"{prefix}: invalid source_level '{source_level}'")

        try:
            score = float(job.get("fit_score"))
            if not 0 <= score <= 100:
                errors.append(f"{prefix}: fit_score must be between 0 and 100")
        except (TypeError, ValueError):
            score = -1
            errors.append(f"{prefix}: fit_score must be numeric")

        verified = job.get("last_verified_date")
        if nonempty(verified) and not valid_iso_date(verified):
            errors.append(f"{prefix}: last_verified_date must use YYYY-MM-DD")

        deadline = job.get("deadline")
        if nonempty(deadline) and str(deadline).strip() != "未披露" and not valid_iso_date(deadline):
            errors.append(f"{prefix}: deadline must use YYYY-MM-DD, be '未披露', or be empty")

        source_url = job.get("source_url")
        if status in ACTIVE_JOB_STATUSES and not valid_url(source_url):
            errors.append(f"{prefix}: active status requires a valid source_url")
        elif nonempty(source_url) and not valid_url(source_url):
            warnings.append(f"{prefix}: source_url is not a valid http(s) URL")

        if status in ACTIVE_JOB_STATUSES and source_level == "第三方待复核":
            warnings.append(f"{prefix}: active status relies on a third-party source and needs higher-priority verification")

        if status in INACTIVE_JOB_STATUSES and action != "暂不处理":
            errors.append(f"{prefix}: inactive status '{status}' requires current_action '暂不处理'")

        if judgment == "不满足" and action in {"立即投递", "本周投递"}:
            errors.append(f"{prefix}: unmet hard requirements conflict with current_action '{action}'")

        if action == "立即投递":
            if status not in ACTIVE_JOB_STATUSES:
                errors.append(f"{prefix}: '立即投递' requires an active recruitment status")
            if judgment != "满足":
                errors.append(f"{prefix}: '立即投递' requires requirement_judgment '满足'")
            if score >= 0 and score < 80:
                errors.append(f"{prefix}: '立即投递' normally requires fit_score >= 80")

        if action == "本周投递":
            if status not in ACTIVE_JOB_STATUSES:
                errors.append(f"{prefix}: '本周投递' requires an active recruitment status")
            if judgment != "满足":
                errors.append(f"{prefix}: '本周投递' requires requirement_judgment '满足'")
            if score >= 0 and score < 65:
                errors.append(f"{prefix}: '本周投递' normally requires fit_score >= 65")

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
    job_errors, job_warnings = validate_jobs(jobs)
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
