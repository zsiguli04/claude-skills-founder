#!/usr/bin/env python3
"""Phase 0: inspect the development environment.

Reports what is installed, what is reachable, and which environment variables
are set (names only, never values). Exits 1 if a tool needed for the current
phase is missing. Run: python3 scripts/check_env.py [--phase N]
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

PG_BIN = Path("/usr/lib/postgresql/16/bin")

# tool -> (version command, first phase that needs it, why)
TOOLS = {
    "python3": (["python3", "--version"], 0, "financial engines, API"),
    "git": (["git", "--version"], 0, "version control"),
    "uv": (["uv", "--version"], 2, "Python dependency and workspace management"),
    "node": (["node", "--version"], 12, "Next.js frontend"),
    "pnpm": (["pnpm", "--version"], 12, "frontend workspace"),
    "psql": (["psql", "--version"], 4, "PostgreSQL client"),
    "postgres": ([str(PG_BIN / "postgres"), "--version"], 4, "PostgreSQL server for local tests"),
    "redis-server": (["redis-server", "--version"], 11, "job queue broker"),
    "docker": (["docker", "--version"], 19, "containers"),
    "docker compose": (["docker", "compose", "version"], 19, "local stack"),
    "gh": (["gh", "--version"], 0, "GitHub CLI (optional)"),
    "tesseract": (["tesseract", "--version"], 14, "OCR for document intelligence"),
}

HOSTS = {
    "pypi.org": "Python packages",
    "registry.npmjs.org": "npm packages",
    "registry-1.docker.io": "container images",
    "api.anthropic.com": "AI layer",
    "njt.hu": "Nemzeti Jogszabálytár (official law texts)",
    "kormany.hu": "Government (draft bills)",
    "nav.gov.hu": "Tax authority",
    "e-beszamolo.im.gov.hu": "Company financial statements",
    "www.e-cegjegyzek.hu": "Company registry",
    "www.mnb.hu": "Central bank (FX, indices)",
}

ENV_VARS = ["ANTHROPIC_API_KEY", "DATABASE_URL", "REDIS_URL", "AUTH_JWT_SECRET", "APP_ENV"]


def version(cmd: list[str]) -> str | None:
    exe = cmd[0]
    if not (shutil.which(exe) or Path(exe).exists()):
        return None
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return (out.stdout or out.stderr).strip().splitlines()[0]


def reachable(host: str) -> str:
    try:
        req = urllib.request.Request(f"https://{host}", method="HEAD")
        with urllib.request.urlopen(req, timeout=8) as r:
            return f"yes ({r.status})"
    except urllib.error.HTTPError as e:  # the host answered
        return f"yes ({e.code})"
    except Exception as e:  # noqa: BLE001
        return f"no ({type(e).__name__})"


def docker_daemon() -> bool:
    return Path("/var/run/docker.sock").exists() and version(["docker", "info", "--format", "{{.ServerVersion}}"]) is not None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", type=int, default=0, help="fail if a tool needed by this phase is missing")
    ap.add_argument("--no-network", action="store_true")
    args = ap.parse_args()

    missing_now = []
    print("Tools")
    for name, (cmd, phase, why) in TOOLS.items():
        v = version(cmd)
        mark = "ok  " if v else "MISS"
        print(f"  {mark} {name:<15} {v or '-':<45} needed from phase {phase}: {why}")
        if not v and phase <= args.phase:
            missing_now.append(name)
    print(f"  {'ok  ' if docker_daemon() else 'off '} docker daemon")

    if not args.no_network:
        print("\nNetwork")
        for host, why in HOSTS.items():
            print(f"  {reachable(host):<28} {host:<24} {why}")

    print("\nEnvironment variables (set or not; values never printed)")
    for var in ENV_VARS:
        print(f"  {'set  ' if os.environ.get(var) else 'unset'} {var}")

    if missing_now:
        print(f"\nMissing for phase {args.phase}: {', '.join(missing_now)}")
        return 1
    print(f"\nEverything needed up to phase {args.phase} is installed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
