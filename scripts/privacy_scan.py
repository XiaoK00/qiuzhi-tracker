#!/usr/bin/env python3
"""Best-effort scan for accidental personal data, local paths and common secrets."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THIS_FILE = Path(__file__).resolve()
TEXT_SUFFIXES = {".md", ".txt", ".py", ".yml", ".yaml", ".json", ".cff", ""}
SKIP_DIRS = {".git", "dist", "dist-ci", "__pycache__"}

PATTERNS = {
    "Chinese mobile number": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "local /mnt path": re.compile(r"/mnt/data/"),
    "Windows drive path": re.compile(r"[A-Za-z]:\\(?:Users|Documents|Desktop)\\"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "OpenAI key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "non-example email": re.compile(
        r"\b[A-Z0-9._%+-]+@(?!example\.com\b)[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I
    ),
}


def main() -> int:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if path.resolve() == THIS_FILE:
            continue
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(ROOT)}:{line}: {label}")
    if findings:
        print("Potential privacy or secret findings:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Privacy scan passed. Manual review is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
