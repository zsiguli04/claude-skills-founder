import re
import sqlite3
from decimal import Decimal

from conftest import post
from test_web import add_asset, new_client

from vagyonado_app.advisory import projection
from vagyonado_app.config import DEFAULT_RULES_DIR
from vagyonado_app.db import Database
from vagyonado_app.services import RuleBook

D = Decimal


def rule():
    return RuleBook(DEFAULT_RULES_DIR).wealth_rule("individual")


def test_projection_hand_calculation():
    # 2bn, no growth: tax 10m, then (2bn - 10m) = 1.99bn -> 9.9m, then 1.9801bn -> 9.801m
    rows = projection(rule(), D("2000000000"), D("0"), years=3)
    assert [D(r["tax"]) for r in rows] == [D("10000000"), D("9900000"), D("9801000")]
    assert D(rows[-1]["cumulative"]) == D("29701000")
    assert [r["year"] for r in rows] == ["2026", "2027", "2028"]


def save(c, cid, notes="", growth="5"):
    r = post(c, f"/clients/{cid}/calculate?growth={growth}", {"advisor_notes": notes}, f"/clients/{cid}")
    calc_id = int(re.search(r"/calculations/(\d+)/export.json", r.text).group(1))
    return r, c.get(f"/calculations/{calc_id}/export.json").json()


def titles(export):
    return [f["title"] for f in export["result"]["analysis"]["findings"]]


def test_scenarios_and_notes_in_report(logged_in):
    c = logged_in
    cid = new_client(c, "Szabó Éva")
    add_asset(c, cid, valuation_kind="manual", name="Villa", category="real_estate", location="HU",
              value="2 000 000 000", method="értékbecslés")
    r, export = save(c, cid, notes="A villa értékbecslését 2026 decemberében frissíteni kell.")
    scen = export["result"]["analysis"]["scenarios"]
    # Only real estate present. 1.6bn, 1.8bn, 2bn, 2.2bn, 2.4bn -> 6m, 8m, 10m, 12m, 14m
    assert scen == [{"group": "Ingatlanok", "taxes": ["6000000", "8000000", "10000000", "12000000", "14000000"]}]
    assert export["advisor_notes"].startswith("A villa")
    assert "Tanácsadói javaslatok" in r.text and "A villa értékbecslését" in r.text
    assert "Érzékenységvizsgálat" in r.text and "Ötéves kitekintés" in r.text
    # No cash at all against a 10m tax: liquidity risk. Manual HU real estate: method reminder.
    t = titles(export)
    assert "Likviditási kockázat" in t
    assert "Villa: megadott értékű magyar ingatlan" in t
    assert "Házastárs és családtagok" in t


def test_findings_for_threshold_hidden_reserves_and_limits(logged_in):
    c = logged_in
    cid = new_client(c, "Tóth Gábor")
    # Company: equity 900m, no profit, hidden reserves 0, 100%: 300m. Car 11m (near the 10m limit). Deposit 650m.
    add_asset(c, cid, valuation_kind="unlisted_company", name="Tóth Zrt.", category="company_share", location="HU",
              equity="900 000 000", profit_1="0", profit_2="0", profit_3="0", ownership_share="100", hidden_reserves="0")
    add_asset(c, cid, valuation_kind="manual", name="Autó", category="car", location="HU", value="11 000 000", method="x")
    add_asset(c, cid, valuation_kind="manual", name="Betét", category="cash", location="HU", value="650 000 000", method="x")
    _, export = save(c, cid)
    # Net 961m: within 10% under the 1bn threshold, no tax.
    assert D(export["result"]["tax"]) == 0
    t = titles(export)
    assert "A nettó vagyon az 1 milliárdos határ közelében van (alatta)" in t
    assert "Tóth Zrt.: rejtett tartalék nulla" in t
    assert "Autó: érték a mentességi határ közelében" in t
    assert "Likviditási kockázat" not in t
    # Actions come first.
    assert export["result"]["analysis"]["findings"][0]["level"] in ("action", "warning")


def test_non_resident_and_foreign_findings(logged_in):
    c = logged_in
    resident = new_client(c, "Nagy Ilona")
    add_asset(c, resident, valuation_kind="manual", name="Párizsi lakás", category="real_estate", location="FR",
              value="3 000 000 000", method="értékbecslés, EUR árfolyam MNB")
    _, export = save(c, resident)
    assert "Párizsi lakás: külföldi vagyonelem" in titles(export)

    foreign = new_client(c, "John Smith", resident="0")
    add_asset(c, foreign, valuation_kind="manual", name="Budai lakás", category="real_estate", location="HU",
              value="1 200 000 000", method="x")
    post(c, f"/clients/{foreign}/debts/new", {"name": "UK hitel", "amount": "100 000 000"}, f"/clients/{foreign}")
    _, export = save(c, foreign)
    t = titles(export)
    assert "Külföldi illetőség" in t and "Nem levont tartozás" in t


def test_growth_input_is_bounded(logged_in):
    cid = new_client(logged_in, "Kis Anna")
    add_asset(logged_in, cid, valuation_kind="manual", name="Betét", category="cash", location="HU", value="2 000 000 000", method="x")
    _, export = save(logged_in, cid, growth="900")  # nonsense falls back to 5%
    assert export["result"]["analysis"]["projection_growth"] == "0.05"
    _, export = save(logged_in, cid, growth="3")
    assert export["result"]["analysis"]["projection_growth"] == "0.03"


def test_old_database_gets_the_notes_column(tmp_path):
    path = tmp_path / "old.sqlite3"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, name TEXT, password_hash TEXT, active INTEGER, created_at TEXT);
        CREATE TABLE calculations (id INTEGER PRIMARY KEY, client_id INTEGER, rule_key TEXT, rule_status TEXT,
            engine_version TEXT, app_version TEXT, inputs TEXT, result TEXT, created_by INTEGER, created_at TEXT);
    """)
    conn.close()
    Database(path)
    with sqlite3.connect(path) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(calculations)")]
    assert "advisor_notes" in cols
