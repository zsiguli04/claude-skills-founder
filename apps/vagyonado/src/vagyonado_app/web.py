"""FastAPI app: server-rendered pages, no JavaScript build, no external resources."""

from __future__ import annotations

import json
import secrets
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from vagyonado_app import advisory, services
from vagyonado_app.auth import DUMMY_HASH, LoginThrottle, verify_password
from vagyonado_app.config import Settings
from vagyonado_app.db import Database, now
from vagyonado_app.formatting import ParseError, huf, parse_amount, parse_percent, percent
from vagyonado_app.i18n import hu

HERE = Path(__file__).parent


class LoginRequired(Exception):
    pass


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    db = Database(settings.database_path)
    rulebook = services.RuleBook(settings.rules_dir)
    throttle = LoginThrottle()
    templates = Jinja2Templates(directory=HERE / "templates")
    templates.env.filters["huf"] = huf
    templates.env.filters["percent"] = percent
    templates.env.filters["hu"] = hu
    templates.env.globals.update(
        CATEGORY_LABELS=services.CATEGORY_LABELS,
        VALUATION_KINDS=services.VALUATION_KINDS,
        KIND_LABELS=services.KIND_LABELS,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="vagyonado_session",
        max_age=settings.session_max_age,
        same_site="strict",
        https_only=settings.secure_cookies,
    )
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; img-src 'self' data:; form-action 'self'; "
            "frame-ancestors 'none'; base-uri 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(LoginRequired)
    async def to_login(request: Request, exc: LoginRequired):
        return RedirectResponse("/login", status_code=303)

    # Helpers

    def csrf_token(request: Request) -> str:
        token = request.session.get("csrf")
        if not token:
            token = secrets.token_urlsafe(32)
            request.session["csrf"] = token
        return token

    def render(request: Request, name: str, status: int = 200, **ctx: Any) -> HTMLResponse:
        ctx.update(request=request, csrf=csrf_token(request), user=request.session.get("user_name"))
        return templates.TemplateResponse(request, name, ctx, status_code=status)

    def user_id(request: Request) -> int:
        uid = request.session.get("user_id")
        if not uid:
            raise LoginRequired()
        with db.connect() as conn:
            row = conn.execute("SELECT active FROM users WHERE id = ?", (uid,)).fetchone()
        if not row or not row["active"]:
            request.session.clear()
            raise LoginRequired()
        return uid

    async def form(request: Request) -> dict[str, str]:
        data = await request.form()
        sent = data.get("csrf", "")
        expected = request.session.get("csrf", "")
        if not expected or not secrets.compare_digest(str(sent), expected):
            raise HTTPException(status_code=403, detail="Érvénytelen űrlap. Töltsd újra az oldalt.")
        return {k: str(v) for k, v in data.items()}

    def get_client(conn, client_id: int):
        row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Nincs ilyen ügyfél.")
        return row

    def growth_of(request: Request) -> Decimal:
        try:
            g = parse_percent(request.query_params.get("growth", "5"))
        except ParseError:
            return Decimal("0.05")
        return g if Decimal("-0.5") <= g <= Decimal("0.5") else Decimal("0.05")

    def client_page(request: Request, client_id: int, status: int = 200, **extra: Any) -> HTMLResponse:
        with db.connect() as conn:
            client = get_client(conn, client_id)
            assets = conn.execute("SELECT * FROM assets WHERE client_id = ? ORDER BY id", (client_id,)).fetchall()
            debts = conn.execute(
                "SELECT d.*, a.name AS secured_on FROM debts d LEFT JOIN assets a ON a.id = d.secured_on_asset_id "
                "WHERE d.client_id = ? ORDER BY d.id", (client_id,)).fetchall()
            calcs = conn.execute(
                "SELECT c.id, c.created_at, c.rule_key, c.rule_status, c.result, u.name AS by_name FROM calculations c "
                "JOIN users u ON u.id = c.created_by WHERE c.client_id = ? ORDER BY c.id DESC", (client_id,)).fetchall()
        preview, preview_error, analysis = None, None, None
        growth = growth_of(request)
        try:
            rule = rulebook.wealth_rule(client["kind"])
            calc = services.calculate(rule, client, list(assets), list(debts))
            preview = calc.output
            analysis = advisory.analysis(rule, client, list(assets), list(debts), calc, growth)
        except services.ValidationError as exc:
            preview_error = str(exc)
        history = [dict(c) | {"tax": json.loads(c["result"])["tax"]} for c in calcs]
        return render(request, "client.html", status, client=client, assets=assets, debts=debts,
                      calcs=history, preview=preview, preview_error=preview_error, analysis=analysis,
                      growth=growth, **extra)

    # Auth

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        return render(request, "login.html")

    @app.post("/login")
    async def login(request: Request):
        f = await form(request)
        email = f.get("email", "").strip().lower()
        password = f.get("password", "")
        if throttle.blocked(email):
            return render(request, "login.html", 429, error="Túl sok sikertelen próbálkozás. Próbáld újra 15 perc múlva.")
        with db.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ? AND active = 1", (email,)).fetchone()
            ok = verify_password(password, row["password_hash"] if row else DUMMY_HASH) and row is not None
            db.audit(conn, row["id"] if ok else None, "login" if ok else "login_failed", "user",
                     row["id"] if row else None)
        if not ok:
            throttle.fail(email)
            return render(request, "login.html", 401, error="Hibás e-mail-cím vagy jelszó.", email=email)
        throttle.reset(email)
        request.session.clear()  # new session on login
        request.session.update(user_id=row["id"], user_name=row["name"], csrf=secrets.token_urlsafe(32))
        return RedirectResponse("/", status_code=303)

    @app.post("/logout")
    async def logout(request: Request):
        await form(request)
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    # Clients

    @app.get("/", response_class=HTMLResponse)
    async def clients(request: Request):
        user_id(request)
        with db.connect() as conn:
            rows = conn.execute(
                "SELECT c.*, (SELECT COUNT(*) FROM assets a WHERE a.client_id = c.id) AS asset_count, "
                "(SELECT result FROM calculations k WHERE k.client_id = c.id ORDER BY k.id DESC LIMIT 1) AS last "
                "FROM clients c ORDER BY c.name COLLATE NOCASE").fetchall()
        items = [dict(r) | {"last_tax": json.loads(r["last"])["tax"] if r["last"] else None} for r in rows]
        return render(request, "clients.html", clients=items)

    def read_client_form(f: dict[str, str]) -> tuple[dict[str, Any], str | None]:
        values = {"name": f.get("name", "").strip(), "kind": f.get("kind", ""),
                  "resident": f.get("resident") == "1", "notes": f.get("notes", "").strip()}
        if not values["name"]:
            return values, "Add meg az ügyfél nevét."
        if values["kind"] not in services.KIND_LABELS:
            return values, "Válaszd ki az ügyfél típusát."
        return values, None

    @app.get("/clients/new", response_class=HTMLResponse)
    async def new_client_page(request: Request):
        user_id(request)
        return render(request, "client_form.html", values={"kind": "individual", "resident": True})

    @app.post("/clients/new")
    async def new_client(request: Request):
        uid = user_id(request)
        values, error = read_client_form(await form(request))
        if error:
            return render(request, "client_form.html", 400, values=values, error=error)
        with db.connect() as conn:
            cur = conn.execute(
                "INSERT INTO clients (name, kind, resident, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (values["name"], values["kind"], int(values["resident"]), values["notes"], now(), now()))
            db.audit(conn, uid, "create", "client", cur.lastrowid)
        return RedirectResponse(f"/clients/{cur.lastrowid}", status_code=303)

    @app.get("/clients/{client_id}", response_class=HTMLResponse)
    async def client_detail(request: Request, client_id: int):
        user_id(request)
        return client_page(request, client_id)

    @app.get("/clients/{client_id}/edit", response_class=HTMLResponse)
    async def edit_client_page(request: Request, client_id: int):
        user_id(request)
        with db.connect() as conn:
            client = get_client(conn, client_id)
        return render(request, "client_form.html", values=dict(client) | {"resident": bool(client["resident"])},
                      client_id=client_id)

    @app.post("/clients/{client_id}/edit")
    async def edit_client(request: Request, client_id: int):
        uid = user_id(request)
        values, error = read_client_form(await form(request))
        if error:
            return render(request, "client_form.html", 400, values=values, error=error, client_id=client_id)
        with db.connect() as conn:
            before = dict(get_client(conn, client_id))
            conn.execute("UPDATE clients SET name = ?, kind = ?, resident = ?, notes = ?, updated_at = ? WHERE id = ?",
                         (values["name"], values["kind"], int(values["resident"]), values["notes"], now(), client_id))
            changed = [k for k in ("name", "kind", "resident", "notes") if before[k] != (int(values[k]) if k == "resident" else values[k])]
            db.audit(conn, uid, "update", "client", client_id, {"fields": changed})
        return RedirectResponse(f"/clients/{client_id}", status_code=303)

    @app.post("/clients/{client_id}/delete")
    async def delete_client(request: Request, client_id: int):
        uid = user_id(request)
        f = await form(request)
        with db.connect() as conn:
            client = get_client(conn, client_id)
            if f.get("confirm_name", "").strip() != client["name"]:
                raise HTTPException(status_code=400, detail="A törléshez írd be pontosan az ügyfél nevét.")
            conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            db.audit(conn, uid, "delete", "client", client_id)
        return RedirectResponse("/", status_code=303)

    # Assets

    def parse_asset_form(f: dict[str, str], kind: str) -> dict[str, Any]:
        def amount(name: str, label: str, required: bool = True) -> Decimal | None:
            raw = f.get(name, "").strip()
            if not raw:
                if required:
                    raise services.ValidationError(f"Hiányzik: {label}.")
                return None
            try:
                return parse_amount(raw)
            except ParseError as exc:
                raise services.ValidationError(f"{label}: {exc}") from exc

        def share(name: str = "ownership_share") -> Decimal:
            raw = f.get(name, "").strip() or "100"
            try:
                value = parse_percent(raw)
            except ParseError as exc:
                raise services.ValidationError(f"Tulajdoni hányad: {exc}") from exc
            if not 0 < value <= 1:
                raise services.ValidationError("A tulajdoni hányad 0-nál nagyobb és legfeljebb 100% lehet.")
            return value

        out: dict[str, Any] = {}
        if kind == "manual":
            out.update(value=amount("value", "Érték"), method=f.get("method", ""), ownership_share=share())
        elif kind == "real_estate_purchase":
            try:
                out["acquired_on"] = date.fromisoformat(f.get("acquired_on", ""))
            except ValueError as exc:
                raise services.ValidationError("Add meg a szerzés dátumát.") from exc
            out.update(purchase_price=amount("purchase_price", "Vételár"),
                       index_at_purchase=amount("index_at_purchase", "MNB-index a szerzéskor", False),
                       index_at_valuation=amount("index_at_valuation", "MNB-index a fordulónapon", False),
                       ownership_share=share())
        elif kind == "unlisted_company":
            out.update(equity=amount("equity", "Saját tőke"),
                       profit_1=amount("profit_1", "Adózott eredmény (1. év)"),
                       profit_2=amount("profit_2", "Adózott eredmény (2. év)"),
                       profit_3=amount("profit_3", "Adózott eredmény (3. év)"),
                       hidden_reserves=amount("hidden_reserves", "Rejtett tartalék", False),
                       ownership_share=share())
            ratio = f.get("participations_to_assets", "").strip()
            out["participations_to_assets"] = parse_percent(ratio) if ratio else Decimal(0)
        else:
            raise services.ValidationError("Ismeretlen értékelési mód.")
        return out

    @app.get("/clients/{client_id}/assets/new", response_class=HTMLResponse)
    async def new_asset_page(request: Request, client_id: int, kind: str = "manual"):
        user_id(request)
        if kind not in services.VALUATION_KINDS:
            kind = "manual"
        with db.connect() as conn:
            client = get_client(conn, client_id)
        default_category = {"real_estate_purchase": "real_estate", "unlisted_company": "company_share"}.get(kind, "cash")
        return render(request, "asset_form.html", client=client, kind=kind,
                      values={"category": default_category, "location": "HU", "ownership_share": "100"})

    @app.post("/clients/{client_id}/assets/new")
    async def new_asset(request: Request, client_id: int):
        uid = user_id(request)
        f = await form(request)
        kind = f.get("valuation_kind", "")
        with db.connect() as conn:
            client = get_client(conn, client_id)
        try:
            name = f.get("name", "").strip()
            if not name:
                raise services.ValidationError("Add meg a vagyonelem megnevezését.")
            category = f.get("category", "")
            if category not in services.CATEGORY_LABELS:
                raise services.ValidationError("Válaszd ki a vagyonelem fajtáját.")
            location = f.get("location", "HU").strip().upper()
            if len(location) != 2 or not location.isalpha():
                raise services.ValidationError("Az ország kétbetűs ISO-kód legyen (pl. HU, AT, DE).")
            rule = rulebook.wealth_rule(client["kind"])
            valuation = services.value_asset(rule, kind, parse_asset_form(f, kind))
        except services.ValidationError as exc:
            return render(request, "asset_form.html", 400, client=client, kind=kind, values=f, error=str(exc))
        with db.connect() as conn:
            if conn.execute("SELECT 1 FROM assets WHERE client_id = ? AND name = ?", (client_id, name)).fetchone():
                return render(request, "asset_form.html", 400, client=client, kind=kind, values=f,
                              error="Ilyen nevű vagyonelem már van ennél az ügyfélnél.")
            cur = conn.execute(
                "INSERT INTO assets (client_id, name, category, location, ownership_share, value, method, "
                "valuation_kind, valuation_inputs, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (client_id, name, category, location, str(valuation.ownership_share), str(valuation.value),
                 valuation.method, kind, json.dumps(valuation.inputs), now()))
            db.audit(conn, uid, "create", "asset", cur.lastrowid, {"client_id": client_id})
        return RedirectResponse(f"/clients/{client_id}", status_code=303)

    @app.post("/clients/{client_id}/assets/{asset_id}/delete")
    async def delete_asset(request: Request, client_id: int, asset_id: int):
        uid = user_id(request)
        await form(request)
        with db.connect() as conn:
            cur = conn.execute("DELETE FROM assets WHERE id = ? AND client_id = ?", (asset_id, client_id))
            if cur.rowcount:
                db.audit(conn, uid, "delete", "asset", asset_id, {"client_id": client_id})
        return RedirectResponse(f"/clients/{client_id}", status_code=303)

    # Debts

    @app.post("/clients/{client_id}/debts/new")
    async def new_debt(request: Request, client_id: int):
        uid = user_id(request)
        f = await form(request)
        name = f.get("name", "").strip()
        try:
            if not name:
                raise services.ValidationError("Add meg a tartozás megnevezését.")
            amount = parse_amount(f.get("amount", ""))
            if amount <= 0:
                raise services.ValidationError("A tartozás összege legyen pozitív.")
        except (ParseError, services.ValidationError) as exc:
            return client_page(request, client_id, 400, debt_error=str(exc))
        secured = f.get("secured_on_asset_id") or None
        with db.connect() as conn:
            get_client(conn, client_id)
            if secured and not conn.execute("SELECT 1 FROM assets WHERE id = ? AND client_id = ?",
                                            (secured, client_id)).fetchone():
                raise HTTPException(status_code=400, detail="A fedezetként megadott vagyonelem nem ehhez az ügyfélhez tartozik.")
            cur = conn.execute(
                "INSERT INTO debts (client_id, name, amount, secured_on_asset_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (client_id, name, str(amount), secured, now()))
            db.audit(conn, uid, "create", "debt", cur.lastrowid, {"client_id": client_id})
        return RedirectResponse(f"/clients/{client_id}", status_code=303)

    @app.post("/clients/{client_id}/debts/{debt_id}/delete")
    async def delete_debt(request: Request, client_id: int, debt_id: int):
        uid = user_id(request)
        await form(request)
        with db.connect() as conn:
            cur = conn.execute("DELETE FROM debts WHERE id = ? AND client_id = ?", (debt_id, client_id))
            if cur.rowcount:
                db.audit(conn, uid, "delete", "debt", debt_id, {"client_id": client_id})
        return RedirectResponse(f"/clients/{client_id}", status_code=303)

    # Calculations and reports

    @app.post("/clients/{client_id}/calculate")
    async def save_calculation(request: Request, client_id: int):
        uid = user_id(request)
        f = await form(request)
        notes = f.get("advisor_notes", "").strip()[:10000]
        with db.connect() as conn:
            client = get_client(conn, client_id)
            assets = conn.execute("SELECT * FROM assets WHERE client_id = ? ORDER BY id", (client_id,)).fetchall()
            debts = conn.execute("SELECT * FROM debts WHERE client_id = ? ORDER BY id", (client_id,)).fetchall()
        try:
            rule = rulebook.wealth_rule(client["kind"])
            calc = services.calculate(rule, client, list(assets), list(debts))
            calc.output["analysis"] = advisory.analysis(rule, client, list(assets), list(debts), calc, growth_of(request))
        except services.ValidationError as exc:
            return client_page(request, client_id, 400, preview_error=str(exc))
        with db.connect() as conn:
            cur = conn.execute(
                "INSERT INTO calculations (client_id, rule_key, rule_status, engine_version, app_version, inputs, "
                "result, advisor_notes, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (client_id, calc.rule.key, calc.rule.status, calc.output["engine_version"], calc.output["app_version"],
                 json.dumps(calc.inputs, ensure_ascii=False), json.dumps(calc.output, ensure_ascii=False), notes, uid, now()))
            db.audit(conn, uid, "create", "calculation", cur.lastrowid, {"client_id": client_id})
        return RedirectResponse(f"/calculations/{cur.lastrowid}", status_code=303)

    @app.get("/calculations/{calc_id}", response_class=HTMLResponse)
    async def report(request: Request, calc_id: int):
        uid = user_id(request)
        with db.connect() as conn:
            row = conn.execute(
                "SELECT c.*, u.name AS by_name FROM calculations c JOIN users u ON u.id = c.created_by WHERE c.id = ?",
                (calc_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Nincs ilyen számítás.")
            db.audit(conn, uid, "view", "calculation", calc_id)
        return render(request, "report.html", calc=row, inputs=json.loads(row["inputs"]), out=json.loads(row["result"]))

    @app.get("/calculations/{calc_id}/export.json")
    async def export(request: Request, calc_id: int):
        uid = user_id(request)
        with db.connect() as conn:
            row = conn.execute("SELECT * FROM calculations WHERE id = ?", (calc_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Nincs ilyen számítás.")
            db.audit(conn, uid, "export", "calculation", calc_id)
        body = {"id": row["id"], "created_at": row["created_at"], "inputs": json.loads(row["inputs"]),
                "result": json.loads(row["result"]), "advisor_notes": row["advisor_notes"]}
        return Response(json.dumps(body, ensure_ascii=False, indent=2), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="vagyonado-{calc_id}.json"'})

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return render(request, "error.html", exc.status_code, message=exc.detail)

    return app
