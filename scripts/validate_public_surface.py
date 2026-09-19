#!/usr/bin/env python3
"""Fail closed if the public wallboard exposes known internal-only content."""
from pathlib import Path
import re

html = Path("public-wallboard.html").read_text(encoding="utf-8")
visible = re.sub(r"<(?:style|script)\b.*?</(?:style|script)>", "", html, flags=re.S | re.I)
visible = re.sub(r"<[^>]+>", " ", visible)
checks = {
    "no personal names": not re.search(
        r"\b(?:Aarav|Nisha|Kabir|Ira|Dev|Rhea|Arjun)\s+[A-Z][a-z]+\b", visible
    ),
    "no Monday identifiers": not re.search(r"\b(?:Monday|board_id|item_id|pulse_id)\b", visible, re.I),
    "no billing or financial values": not re.search(
        r"\b(?:billing|invoice|revenue|margin|₹|INR|USD|cost)\b", visible, re.I
    ),
    "no credentials": not re.search(
        r"\b(?:api[_-]?key|api[_-]?token|password|secret|oauth|connection[_-]?string)\b",
        visible,
        re.I,
    ),
    "fixed wallboard screens": len(re.findall(r'<section\s+class=["\']screen(?:\s|["\'])', html, re.I)) == 6,
    "no scrollable wallboard layouts": not re.search(r"overflow\s*:\s*(?:auto|scroll)", html, re.I),
}
failed = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}: {name}")
if failed:
    raise SystemExit("Public surface validation failed: " + ", ".join(failed))
