# Vagyonadó-iroda

Belső webes eszköz vagyonadó-tanácsadáshoz. Az iroda munkatársai ügyfeleket vesznek fel, rögzítik a vagyonelemeket és tartozásokat, a program kiszámolja a becsült vagyonadót, és nyomtatható jelentést készít az ügyfélnek.

Minden számot a [`finengine`](../../engine/README.md) motor számol; a szabályok az [`engine/rules/hu/`](../../engine/rules/hu/) fájlokban vannak, forrással együtt.

> **A vagyonadó jelenleg törvénytervezet** (társadalmi egyeztetés 2026. október 6. és 14. között). A program a tervezetnek a sajtóban és tanácsadói összefoglalókban közölt szabályait használja, a tervezet szövegét még nem vetettük össze vele. Minden képernyőn és jelentésben figyelmeztetés jelzi ezt. A nyitott kérdések listája: [`engine/rules/hu/RESEARCH.md`](../../engine/rules/hu/RESEARCH.md).

## Mit tud

- **Ügyfelek:** magánszemély vagy vagyonkezelési adóalany (bizalmi vagyonkezelés, magánalapítvány), belföldi vagy külföldi illetőség.
- **Vagyonelemek három módon:**
  - ingatlan vételár alapján (12 hónapon belüli szerzés: vételár; 1-10 év: MNB lakásárindexszel korrigált vételár);
  - nem tőzsdei cégrészesedés a tervezet képletével (rejtett tartalék, holdingtársaság, kisebbségi kedvezmény);
  - megadott érték a módszer megnevezésével (záróárfolyam, egyenleg, NAV-modell, értékbecslés).
- **Mentességek:** személyes ingóság 1 millió, gépkocsi 10 millió, műtárgy és ékszer 3 millió Ft-ig automatikusan kimarad.
- **Tartozások**, fedezetként megjelölt vagyonelemmel.
- **Élő előnézet** az ügyfél oldalán, **mentett számítások** teljes bemenettel és eredménnyel (később is pontosan visszakereshető), **nyomtatható jelentés** (Ctrl+P, PDF-be is) és JSON-export.
- **Elemzés a tanácsadáshoz** az ügyfél oldalán és a jelentésben:
  - *megállapítások* (teendő, kockázat, figyelem): 1 milliárdos határ közelében lévő nettó vagyon, likviditási kockázat (a becsült adó több, mint a pénz, betét, értékpapír és kripto), alátámasztandó nulla rejtett tartalék, kedvezményhatár közeli tulajdoni hányad, mentességi határ közeli ingóság, dokumentálandó ingatlanérték-módszer, külföldi vagyon árfolyama és be nem számítható külföldi adója, külföldi illetőség, házastársak és családtagok, határidők;
  - *érzékenységvizsgálat*: az adó, ha az ingatlanok, cégrészesedések vagy értékpapírok értéke -20% és +20% között változik;
  - *ötéves kitekintés* állítható hozammal, változatlan szabályt feltételezve.
- **Tanácsadói javaslatok:** a mentéskor beírt szöveg a jelentésbe kerül. A javaslatot mindig a tanácsadó fogalmazza meg; a program csak az anyagot készíti elő hozzá. A „határ közelében” sávok (10%, 20%, 3 százalékpont) a program saját ellenőrzési szabályai, nem a törvény részei.
- **Biztonság:** belépés jelszóval, CSRF-védelem minden űrlapon, belépési próbálkozások korlátozása, szigorú biztonsági fejlécek, csak hozzáfűzhető napló minden módosításról és megtekintésről.

Házastársakat és nagykorú családtagokat külön ügyfélként kell felvenni (mindenkinek saját 1 milliárdos határa van). Az egymással kapcsolatban álló vagyonkezelési konstrukciókat egy ügyfélként (közösen egy határ).

## Telepítés

Python 3.11 vagy újabb kell.

```bash
cd apps/vagyonado
python -m venv .venv && . .venv/bin/activate
pip install -e ../../engine -e .

# Titkos kulcs a munkamenet-sütikhez (egyszer generáld, és tartsd titokban)
export VAGYONADO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export VAGYONADO_DB=/var/lib/vagyonado/vagyonado.sqlite3

# Első felhasználó (jelszót kér, legalább 12 karakter)
vagyonado create-user anna@iroda.hu "Kiss Anna"

vagyonado serve --host 127.0.0.1 --port 8000
```

| Környezeti változó | Jelentés |
|:--|:--|
| `VAGYONADO_SECRET_KEY` | Kötelező, legalább 32 karakter. Ha megváltozik, mindenkit kiléptet. |
| `VAGYONADO_DB` | Az SQLite-adatbázis útvonala. Alapértelmezés: `vagyonado.sqlite3` a munkakönyvtárban. |
| `VAGYONADO_RULES_DIR` | A szabályfájlok mappája. Alapértelmezés: `engine/rules/hu`. |
| `VAGYONADO_INSECURE_COOKIES` | `1` esetén a süti HTTP-n is működik. Csak helyi kipróbáláshoz. |

Felhasználó letiltása: `vagyonado deactivate-user anna@iroda.hu`. A letiltott felhasználó a következő kattintásnál kilép.

## Üzemeltetés

- **Csak HTTPS mögött** futtasd, fordított proxyval (például Caddy vagy nginx), és a proxy csak az iroda hálózatából vagy VPN-ről legyen elérhető. A szerver alapból csak a `127.0.0.1` címen figyel.
- **Az adatbázis érzékeny adatokat tartalmaz** (ügyfelek vagyona). Titkosított lemezen tárold, a fájlhoz csak a szolgáltatás felhasználója férjen hozzá (`chmod 600`), és készíts rendszeres, titkosított mentést (`sqlite3 vagyonado.sqlite3 ".backup mentes.sqlite3"`).
- Adóazonosító jelet és más személyes azonosítót a program nem kér és nem tárol; a megjegyzés mezőbe se írd.
- Az e-mail-címenkénti belépési korlát (15 percen belül 5 hibás próbálkozás) a memóriában van, újraindításkor nullázódik.
- Minden belépett felhasználó minden ügyfelet lát: a program egy iroda belső eszköze, nem ügyfélportál.

## Ha változik a törvény

A számítás a szabályfájlból jön, nem a programkódból. Ha a végleges törvény más kulcsot, értékhatárt vagy mentességet tartalmaz, az `engine/rules/hu/vagyonado-2026.yaml` fájlban új verziót kell felvenni (`supersedes` mezővel), elfogadás után `status: enacted` értékkel. A régi mentett számítások változatlanok maradnak, az újak az új szabállyal készülnek.

## Fejlesztés

```bash
pip install -e ../../engine -e ".[dev]"
pytest -q
```

A tesztek a teljes folyamatot végigviszik (belépés, ügyfél, mindhárom értékelési mód, tartozás, számítás, jelentés), és kézzel kiszámolt értékekhez hasonlítanak.
