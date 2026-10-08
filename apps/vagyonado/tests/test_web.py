import json
import re
import sqlite3
from decimal import Decimal

import pytest

from conftest import PASSWORD, csrf_of, post


def test_pages_require_login(client):
    for url in ["/", "/clients/new", "/clients/1", "/calculations/1"]:
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"] == "/login"


def test_wrong_password(client):
    r = post(client, "/login", {"email": "anna@iroda.hu", "password": "wrong password!!"}, "/login")
    assert r.status_code == 401 and "Hibás" in r.text


def test_unknown_email_gets_the_same_answer(client):
    r = post(client, "/login", {"email": "nobody@iroda.hu", "password": "whatever password"}, "/login")
    assert r.status_code == 401 and "Hibás e-mail-cím vagy jelszó" in r.text


def test_login_lockout_after_five_failures(client):
    for _ in range(5):
        post(client, "/login", {"email": "anna@iroda.hu", "password": "wrong password!!"}, "/login")
    r = post(client, "/login", {"email": "anna@iroda.hu", "password": PASSWORD}, "/login")
    assert r.status_code == 429


def test_post_without_csrf_is_rejected(logged_in):
    r = logged_in.post("/clients/new", data={"name": "X", "kind": "individual", "resident": "1"})
    assert r.status_code == 403
    r = logged_in.post("/clients/new", data={"csrf": "forged", "name": "X", "kind": "individual", "resident": "1"})
    assert r.status_code == 403


def test_security_headers(client):
    r = client.get("/login")
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["cache-control"] == "no-store"


def new_client(c, name="Kovács Péter", kind="individual", resident="1"):
    r = post(c, "/clients/new", {"name": name, "kind": kind, "resident": resident, "notes": ""})
    assert r.status_code == 200, r.text
    return int(re.search(r"/clients/(\d+)/edit", r.text).group(1))


def add_asset(c, cid, **data):
    return post(c, f"/clients/{cid}/assets/new", data, f"/clients/{cid}")


def test_full_flow_matches_hand_calculation(logged_in, db):
    c = logged_in
    cid = new_client(c)

    # Flat bought 2026-03-01 for 800m: purchase price within 12 months.
    r = add_asset(c, cid, valuation_kind="real_estate_purchase", name="Budapesti lakás", category="real_estate",
                  location="HU", acquired_on="2026-03-01", purchase_price="800 000 000", ownership_share="100")
    assert r.status_code == 200 and "Budapesti lakás" in r.text

    # House bought 2020-06-01 for 400m, index 120 -> 150: 500m, half owned: 250m.
    add_asset(c, cid, valuation_kind="real_estate_purchase", name="Balatoni ház", category="real_estate",
              location="HU", acquired_on="2020-06-01", purchase_price="400.000.000", ownership_share="50",
              index_at_purchase="120", index_at_valuation="150")

    # Kft.: equity 1.5bn, profit 225m a year, 100%, no hidden reserves.
    # Earning value 225m / 0.15 = 1.5bn; (1.5bn + 2 x 1.5bn) / 3 = 1.5bn
    add_asset(c, cid, valuation_kind="unlisted_company", name="Kovács Kft.", category="company_share", location="HU",
              equity="1 500 000 000", profit_1="225 000 000", profit_2="225 000 000", profit_3="225 000 000",
              ownership_share="100", hidden_reserves="0")

    # A watch worth 2.5m (art and jewelry up to 3m are exempt) and a deposit of 300,000,000.50.
    add_asset(c, cid, valuation_kind="manual", name="Karóra", category="art_jewelry", location="HU",
              value="2 500 000", ownership_share="100", method="értékbecslés 2026.12.")
    add_asset(c, cid, valuation_kind="manual", name="Betét", category="cash", location="HU",
              value="300 000 000,50", ownership_share="100", method="bankszámla-egyenleg 2026.12.31.")

    # Mortgage 50m on the flat.
    with db.connect() as conn:
        flat_id = conn.execute("SELECT id FROM assets WHERE name = 'Budapesti lakás'").fetchone()["id"]
    r = post(c, f"/clients/{cid}/debts/new", {"name": "Jelzálog", "amount": "50 000 000",
                                              "secured_on_asset_id": str(flat_id)}, f"/clients/{cid}")
    assert r.status_code == 200

    # Gross: 800m + 250m + 1.5bn + 300,000,000.50 = 2,850,000,000.50. Net 2,800,000,000.50.
    # Base 1,800,000,000.50; tax 1% = 18,000,000.005, rounded half up to whole forints: 18,000,000.
    r = post(c, f"/clients/{cid}/calculate", {}, f"/clients/{cid}")
    assert r.status_code == 200
    assert "TERVEZET ALAPJÁN" in r.text
    calc_id = int(re.search(r"/calculations/(\d+)/export.json", r.text).group(1))

    export = c.get(f"/calculations/{calc_id}/export.json").json()
    out = export["result"]
    assert Decimal(out["gross_assets"]) == Decimal("2850000000.50")
    assert Decimal(out["net_wealth"]) == Decimal("2800000000.50")
    assert Decimal(out["tax_base"]) == Decimal("1800000000.50")
    assert Decimal(out["tax_unrounded"]) == Decimal("18000000.005")
    assert Decimal(out["tax"]) == Decimal("18000000")
    assert out["rule"]["status"] == "draft"
    watch = next(l for l in out["lines"] if l["name"] == "Karóra")
    assert watch["included"] is False and "exempt" in watch["reason"]
    assert len(export["inputs"]["assets"]) == 5

    # The client list shows the latest tax.
    assert "18 000 000 Ft" in c.get("/").text


def test_non_resident_scope_in_app(logged_in):
    c = logged_in
    cid = new_client(c, "Müller Hans", resident="0")
    add_asset(c, cid, valuation_kind="manual", name="Budai villa", category="real_estate", location="HU",
              value="1 500 000 000", method="értékbecslés")
    add_asset(c, cid, valuation_kind="manual", name="Bécsi lakás", category="real_estate", location="AT",
              value="5 000 000 000", method="értékbecslés")
    r = post(c, f"/clients/{cid}/calculate", {}, f"/clients/{cid}")
    calc_id = int(re.search(r"/calculations/(\d+)/export.json", r.text).group(1))
    out = c.get(f"/calculations/{calc_id}/export.json").json()["result"]
    # Only the Hungarian villa: 1.5bn, base 500m, tax 5m.
    assert Decimal(out["tax"]) == Decimal("5000000")


def test_trust_uses_trust_rule(logged_in):
    c = logged_in
    cid = new_client(c, "Családi Alapítvány", kind="trust")
    add_asset(c, cid, valuation_kind="manual", name="Portfólió", category="listed_security", location="HU",
              value="2 000 000 000", method="záróárfolyam")
    r = post(c, f"/clients/{cid}/calculate", {}, f"/clients/{cid}")
    assert "hu-vagyonado-trust@1" in r.text


@pytest.mark.parametrize(
    "data, message",
    [
        ({"valuation_kind": "manual", "name": "", "category": "cash", "location": "HU", "value": "1", "method": "x"}, "megnevezés"),
        ({"valuation_kind": "manual", "name": "A", "category": "cash", "location": "HU", "value": "1", "method": ""}, "hogyan"),
        ({"valuation_kind": "manual", "name": "A", "category": "cash", "location": "HU", "value": "sok", "method": "x"}, "Érvénytelen"),
        ({"valuation_kind": "manual", "name": "A", "category": "cash", "location": "HUN", "value": "1", "method": "x"}, "ISO"),
        ({"valuation_kind": "manual", "name": "A", "category": "cash", "location": "HU", "value": "1", "method": "x",
          "ownership_share": "150"}, "hányad"),
        ({"valuation_kind": "real_estate_purchase", "name": "A", "category": "real_estate", "location": "HU",
          "acquired_on": "2010-01-01", "purchase_price": "1"}, "NAV"),
        ({"valuation_kind": "real_estate_purchase", "name": "A", "category": "real_estate", "location": "HU",
          "acquired_on": "2020-01-01", "purchase_price": "1"}, "MNB"),
        ({"valuation_kind": "unlisted_company", "name": "A", "category": "company_share", "location": "HU",
          "equity": "600 000 000", "profit_1": "0", "profit_2": "0", "profit_3": "0", "ownership_share": "100"}, "rejtett tartalék"),
    ],
)
def test_asset_validation_messages(logged_in, data, message):
    cid = new_client(logged_in)
    r = add_asset(logged_in, cid, **data)
    assert r.status_code == 400
    assert message in r.text


def test_duplicate_asset_name(logged_in):
    cid = new_client(logged_in)
    data = dict(valuation_kind="manual", name="Betét", category="cash", location="HU", value="1", method="x")
    add_asset(logged_in, cid, **data)
    r = add_asset(logged_in, cid, **data)
    assert r.status_code == 400 and "már van" in r.text


def test_debt_cannot_point_at_another_clients_asset(logged_in, db):
    a = new_client(logged_in, "A")
    b = new_client(logged_in, "B")
    add_asset(logged_in, a, valuation_kind="manual", name="Ház", category="real_estate", location="HU", value="1", method="x")
    with db.connect() as conn:
        asset_id = conn.execute("SELECT id FROM assets WHERE client_id = ?", (a,)).fetchone()["id"]
    r = post(logged_in, f"/clients/{b}/debts/new", {"name": "Hitel", "amount": "5", "secured_on_asset_id": str(asset_id)},
             f"/clients/{b}")
    assert r.status_code == 400


def test_delete_client_needs_exact_name(logged_in):
    cid = new_client(logged_in, "Törlendő Ügyfél")
    r = post(logged_in, f"/clients/{cid}/delete", {"confirm_name": "rossz"}, f"/clients/{cid}")
    assert r.status_code == 400
    r = post(logged_in, f"/clients/{cid}/delete", {"confirm_name": "Törlendő Ügyfél"}, f"/clients/{cid}")
    assert r.status_code == 200 and "Törlendő Ügyfél" not in r.text


def test_audit_log_records_and_is_append_only(logged_in, db):
    new_client(logged_in, "Naplózott")
    with db.connect() as conn:
        actions = [r["action"] for r in conn.execute("SELECT action FROM audit_log ORDER BY id")]
    assert actions[:2] == ["login", "create"]
    with pytest.raises(sqlite3.IntegrityError):
        with db.connect() as conn:
            conn.execute("DELETE FROM audit_log")
    with pytest.raises(sqlite3.IntegrityError):
        with db.connect() as conn:
            conn.execute("UPDATE audit_log SET action = 'x'")


def test_deactivated_user_is_logged_out(logged_in, db):
    with db.connect() as conn:
        conn.execute("UPDATE users SET active = 0")
    r = logged_in.get("/", follow_redirects=False)
    assert r.status_code == 303


def test_html_is_escaped(logged_in):
    cid = new_client(logged_in, "<script>alert(1)</script>")
    page = logged_in.get(f"/clients/{cid}").text
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_logout(logged_in):
    r = post(logged_in, "/logout", {})
    assert "Belépés" in r.text
    assert logged_in.get("/", follow_redirects=False).status_code == 303
