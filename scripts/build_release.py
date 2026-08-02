#!/usr/bin/env python3
"""Build the distributable .skill archive using Python's standard library."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "qiuzhi-tracker"


def version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def should_skip(path: Path) -> bool:
    return any(part in {"__pycache__", ".DS_Store"} for part in path.parts) or path.suffix == ".pyc"


def build(output_dir: Path) -> Path:
    if not (SKILL_DIR / "SKILL.md").exists():
        raise SystemExit("Missing skills/qiuzhi-tracker/SKILL.md")
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"qiuzhi-tracker-v{version()}.skill"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for source in sorted(SKILL_DIR.rglob("*")):
            if source.is_file() and not should_skip(source):
                relative = Path("qiuzhi-tracker") / source.relative_to(SKILL_DIR)
                zf.write(source, relative.as_posix())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output_dir / "SHA256SUMS.txt").write_text(
        f"{digest}  {archive.name}\n", encoding="utf-8"
    )
    return archive


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    archive = build(args.output_dir)
    print(f"Built: {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
