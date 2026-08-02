#!/usr/bin/env python3
"""Check repository structure, Skill metadata, archive resources and sample data."""

from __future__ import annotations

import compileall
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "qiuzhi-tracker"

REQUIRED = [
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / "VERSION",
    SKILL / "SKILL.md",
    SKILL / "LICENSE.txt",
    SKILL / "agents" / "openai.yaml",
    SKILL / "references" / "matching-rubric.md",
    SKILL / "references" / "research-rules.md",
    SKILL / "references" / "workbook-schema.md",
    SKILL / "scripts" / "validate_tracker_data.py",
    SKILL / "assets" / "qiuzhi-tracker-template.xlsx",
    ROOT / "examples" / "example-tracker-data.json",
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

    metadata = read_frontmatter(SKILL / "SKILL.md")
    if metadata.get("name") != SKILL.name:
        raise SystemExit(
            f"Skill folder/name mismatch: folder={SKILL.name!r}, name={metadata.get('name')!r}"
        )
    if not metadata.get("description"):
        raise SystemExit("SKILL.md description is missing")

    template = SKILL / "assets" / "qiuzhi-tracker-template.xlsx"
    if not zipfile.is_zipfile(template):
        raise SystemExit("Excel template is not a valid XLSX/ZIP file")
    with zipfile.ZipFile(template) as zf:
        bad = zf.testzip()
        if bad:
            raise SystemExit(f"Corrupted XLSX member: {bad}")

    if not compileall.compile_dir(str(SKILL / "scripts"), quiet=1):
        raise SystemExit("Skill Python scripts failed to compile")
    if not compileall.compile_dir(str(ROOT / "scripts"), quiet=1):
        raise SystemExit("Repository Python scripts failed to compile")

    command = [
        sys.executable,
        str(SKILL / "scripts" / "validate_tracker_data.py"),
        str(ROOT / "examples" / "example-tracker-data.json"),
        "--min-companies",
        "6",
        "--min-jobs",
        "4",
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
