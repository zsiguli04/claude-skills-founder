from decimal import Decimal

import pytest

from vagyonado_app.formatting import ParseError, huf, parse_amount, parse_percent, percent

NB = " "


@pytest.mark.parametrize(
    "text, expected",
    [
        ("1500000", "1500000"),
        ("1 500 000", "1500000"),
        ("1 500 000 Ft", "1500000"),
        ("1.500.000", "1500000"),
        ("1.500.000,50", "1500000.50"),
        ("1500000,5", "1500000.5"),
        ("0,15", "0.15"),
        ("1500000.5", "1500000.5"),
        ("-250 000", "-250000"),
        ("12.5", "12.5"),
    ],
)
def test_parse_amount(text, expected):
    assert parse_amount(text) == Decimal(expected)


@pytest.mark.parametrize("text", ["", "abc", "1,2,3", "NaN", "Infinity"])
def test_parse_amount_rejects(text):
    with pytest.raises(ParseError):
        parse_amount(text)


def test_parse_percent():
    assert parse_percent("50") == Decimal("0.5")
    assert parse_percent("33,3%") == Decimal("0.333")


def test_huf():
    assert huf(Decimal("1500000000")) == f"1{NB}500{NB}000{NB}000{NB}Ft"
    assert huf("999.5") == f"1{NB}000{NB}Ft"
    assert huf("-1234") == f"-1{NB}234{NB}Ft"
    assert huf("1000.255", 2) == f"1{NB}000,26{NB}Ft"


def test_percent():
    assert percent("0.015") == f"1,5{NB}%"
    assert percent("0.01") == f"1{NB}%"
    assert percent("0.0033333", 3) == f"0,333{NB}%"


from vagyonado_app.i18n import hu


@pytest.mark.parametrize(
    "engine_text, expected",
    [
        ("purchase price (acquired within 12 months)", "vételár (12 hónapon belüli szerzés)"),
        ("exempt: art_jewelry worth at most 3000000", f"mentes: műtárgy, gyűjtemény, ékszer, legfeljebb 3{NB}000{NB}000{NB}Ft értékig"),
        ("unlisted company formula (equity + 2 x earning value) / 3; equity incl. hidden reserves; minority discount 0.25",
         f"nem tőzsdei cég képlete: (saját tőke + 2 × hozamérték) / 3; saját tőke rejtett tartalékkal; kisebbségi kedvezmény 25{NB}%"),
        ("záróárfolyam 2026.12.30.", "záróárfolyam 2026.12.30."),
    ],
)
def test_engine_texts_in_hungarian(engine_text, expected):
    assert hu(engine_text) == expected
