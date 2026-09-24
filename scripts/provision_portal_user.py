#!/usr/bin/env python3
"""Provision a Manager Vault account without storing the password in source or logs."""
from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import portal_server

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("username")
parser.add_argument("--role", choices=["manager", "editor", "read_only"], default="manager")
parser.add_argument("--db", type=Path, default=Path(os.environ.get("PORTAL_AUTH_DB", ROOT / "data" / "portal_auth.sqlite3")))
args = parser.parse_args()
password = getpass.getpass("Password (12+ characters): ")
confirmation = getpass.getpass("Confirm password: ")
if password != confirmation:
    raise SystemExit("Passwords do not match")
portal_server.provision_user(args.db, args.username, password, args.role)
print(f"Provisioned account {args.username.strip().casefold()} with role {args.role} in {args.db}")
