#!/usr/bin/env python3
"""Check repository structure, version consistency, samples and Skill resources."""

from __future__ import annotations

import compileall
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "qiuzhi-tracker"
VERSION = "1.1.0"

REQUIRED = [
    ROOT / "README.md", ROOT / "CHANGELOG.md", ROOT / "LICENSE", ROOT / "VERSION",
    SKILL / "SKILL.md", SKILL / "LICENSE.txt", SKILL / "agents" / "openai.yaml",
    SKILL / "references" / "matching-rubric.md", SKILL / "references" / "research-rules.md",
    SKILL / "references" / "workbook-schema.md", SKILL / "scripts" / "validate_tracker_data.py",
    SKILL / "assets" / "qiuzhi-tracker-template.xlsx",
    ROOT / "examples" / "example-tracker-data.json",
    ROOT / "examples" / "example-output-redacted.xlsx",
]

PROHIBITED_EXAMPLE_TERMS = ("资产评估", "估值咨询", "会计师事务所", "审计实习", "财务分析")
SCAN_FILES = [
    ROOT / "README.md", SKILL / "SKILL.md", SKILL / "references" / "matching-rubric.md",
    SKILL / "references" / "research-rules.md", SKILL / "references" / "workbook-schema.md",
    ROOT / "examples" / "example-prompts.md", ROOT / "examples" / "example-tracker-data.json",
    ROOT / "examples" / "sample-resume.md",
]


def read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise AssertionError("SKILL.md frontmatter is not closed")
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def main() -> int:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        raise SystemExit("Missing required files:\n- " + "\n- ".join(missing))

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if version != VERSION or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SystemExit(f"Unexpected VERSION: {version}")
    if f"[{VERSION}]" not in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"):
        raise SystemExit("CHANGELOG does not contain the current version")
    if f"v{VERSION}" not in (ROOT / "README.md").read_text(encoding="utf-8"):
        raise SystemExit("README does not contain the current version")

    metadata = read_frontmatter(SKILL / "SKILL.md")
    if metadata.get("name") != SKILL.name or not metadata.get("description"):
        raise SystemExit("Invalid Skill frontmatter")

    for path in SCAN_FILES:
        text = path.read_text(encoding="utf-8")
        for term in PROHIBITED_EXAMPLE_TERMS:
            if term in text:
                raise SystemExit(f"Professional-specific example remains in {path.relative_to(ROOT)}: {term}")

    for workbook in [
        SKILL / "assets" / "qiuzhi-tracker-template.xlsx",
        ROOT / "examples" / "example-output-redacted.xlsx",
    ]:
        if not zipfile.is_zipfile(workbook):
            raise SystemExit(f"Invalid XLSX: {workbook.relative_to(ROOT)}")
        with zipfile.ZipFile(workbook) as zf:
            if zf.testzip():
                raise SystemExit(f"Corrupted XLSX: {workbook.relative_to(ROOT)}")

    if not compileall.compile_dir(str(SKILL / "scripts"), quiet=1):
        raise SystemExit("Skill Python scripts failed to compile")
    if not compileall.compile_dir(str(ROOT / "scripts"), quiet=1):
        raise SystemExit("Repository Python scripts failed to compile")

    command = [
        sys.executable, str(SKILL / "scripts" / "validate_tracker_data.py"),
        str(ROOT / "examples" / "example-tracker-data.json"),
        "--min-companies", "6", "--min-jobs", "5", "--as-of", "2026-08-02",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stdout + result.stderr)
    json.loads((ROOT / "examples" / "example-tracker-data.json").read_text(encoding="utf-8"))
    print("Repository check passed.")
    print(result.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
