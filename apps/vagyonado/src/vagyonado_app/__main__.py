"""Command line: run the server or manage users.

    python -m vagyonado_app serve [--host 127.0.0.1] [--port 8000]
    python -m vagyonado_app create-user EMAIL NAME
    python -m vagyonado_app deactivate-user EMAIL
"""

from __future__ import annotations

import argparse
import getpass
import sys

from vagyonado_app.auth import hash_password
from vagyonado_app.config import ConfigError, Settings
from vagyonado_app.db import Database, now


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vagyonado")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="start the web server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    create = sub.add_parser("create-user", help="add a user (asks for the password)")
    create.add_argument("email")
    create.add_argument("name")
    deactivate = sub.add_parser("deactivate-user", help="block a user from logging in")
    deactivate.add_argument("email")
    args = parser.parse_args(argv)

    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.command == "serve":
        import uvicorn

        from vagyonado_app.web import create_app

        uvicorn.run(create_app(settings), host=args.host, port=args.port, proxy_headers=True)
        return 0

    db = Database(settings.database_path)
    if args.command == "create-user":
        password = getpass.getpass("Jelszó (legalább 12 karakter): ")
        if password != getpass.getpass("Jelszó újra: "):
            print("A két jelszó nem egyezik.", file=sys.stderr)
            return 1
        try:
            hashed = hash_password(password)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
        with db.connect() as conn:
            cur = conn.execute("INSERT INTO users (email, name, password_hash, created_at) VALUES (?, ?, ?, ?)",
                               (args.email.strip().lower(), args.name, hashed, now()))
            db.audit(conn, None, "create", "user", cur.lastrowid, {"via": "cli"})
        print(f"Felhasználó létrehozva: {args.email}")
        return 0

    if args.command == "deactivate-user":
        with db.connect() as conn:
            cur = conn.execute("UPDATE users SET active = 0 WHERE email = ?", (args.email.strip().lower(),))
            if not cur.rowcount:
                print("Nincs ilyen felhasználó.", file=sys.stderr)
                return 1
            row = conn.execute("SELECT id FROM users WHERE email = ?", (args.email.strip().lower(),)).fetchone()
            db.audit(conn, None, "deactivate", "user", row["id"], {"via": "cli"})
        print(f"Felhasználó letiltva: {args.email}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
