#!/usr/bin/env python3
"""Replace the GitHub username placeholder in repository text files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = "XiaoK00"
FILES = [ROOT / "README.md", ROOT / "README.en.md", ROOT / "docs" / "INSTALLATION.md"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", args.username):
        raise SystemExit("Invalid GitHub username format")
    count = 0
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        updated = text.replace(PLACEHOLDER, args.username)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            count += 1
    print(f"Updated {count} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
