import sqlite3
import json
from datetime import datetime

DB = "lagvakt.db"

def koble():
    konn = sqlite3.connect(DB)
    konn.row_factory = sqlite3.Row
    return konn

def init():
    konn = koble()
    konn.execute("""CREATE TABLE IF NOT EXISTS brukere (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        epost TEXT UNIQUE NOT NULL, passord_hash TEXT NOT NULL, navn TEXT
    )""")
    konn.execute("""CREATE TABLE IF NOT EXISTS klubber (
        id INTEGER PRIMARY KEY AUTOINCREMENT, eier_id INTEGER NOT NULL, navn TEXT NOT NULL
    )""")
    konn.execute("""CREATE TABLE IF NOT EXISTS medlemmer (
        id INTEGER PRIMARY KEY AUTOINCREMENT, klubb_id INTEGER NOT NULL,
        navn TEXT NOT NULL, rolle TEXT, epost TEXT NOT NULL,
        tofaktor INTEGER DEFAULT 0, lekkasjer TEXT DEFAULT '[]'
    )""")
    konn.execute("""CREATE TABLE IF NOT EXISTS sjekk_logg (
        id INTEGER PRIMARY KEY AUTOINCREMENT, klubb_id INTEGER NOT NULL,
        tidspunkt TEXT, antall_sjekket INTEGER, nye_funn INTEGER, detaljer TEXT
    )""")
    konn.commit(); konn.close()

# --- Brukere ---
def opprett_bruker(epost, passord_hash, navn):
    konn = koble()
    try:
        cur = konn.execute("INSERT INTO brukere (epost, passord_hash, navn) VALUES (?,?,?)",
                           (epost, passord_hash, navn))
        konn.commit(); ny = cur.lastrowid
    except sqlite3.IntegrityError:
        ny = None
    konn.close(); return ny

def hent_bruker_med_epost(epost):
    konn = koble()
    r = konn.execute("SELECT * FROM brukere WHERE epost = ?", (epost,)).fetchone()
    konn.close(); return dict(r) if r else None

def hent_bruker(bruker_id):
    konn = koble()
    r = konn.execute("SELECT * FROM brukere WHERE id = ?", (bruker_id,)).fetchone()
    konn.close(); return dict(r) if r else None

# --- Klubber ---
def hent_klubber(eier_id):
    konn = koble()
    rader = konn.execute("SELECT * FROM klubber WHERE eier_id = ? ORDER BY id", (eier_id,)).fetchall()
    konn.close(); return [{"id": r["id"], "navn": r["navn"]} for r in rader]

def hent_klubb(klubb_id, eier_id):
    konn = koble()
    r = konn.execute("SELECT * FROM klubber WHERE id = ? AND eier_id = ?", (klubb_id, eier_id)).fetchone()
    konn.close(); return {"id": r["id"], "navn": r["navn"]} if r else None

def alle_klubb_ider():
    konn = koble()
    rader = konn.execute("SELECT id FROM klubber").fetchall()
    konn.close(); return [r["id"] for r in rader]

def legg_til_klubb(navn, eier_id):
    konn = koble()
    cur = konn.execute("INSERT INTO klubber (eier_id, navn) VALUES (?,?)", (eier_id, navn))
    konn.commit(); ny = cur.lastrowid; konn.close(); return ny

def endre_klubb(klubb_id, navn, eier_id):
    konn = koble()
    konn.execute("UPDATE klubber SET navn = ? WHERE id = ? AND eier_id = ?", (navn, klubb_id, eier_id))
    konn.commit(); konn.close()

def slett_klubb(klubb_id, eier_id):
    konn = koble()
    if konn.execute("SELECT 1 FROM klubber WHERE id = ? AND eier_id = ?", (klubb_id, eier_id)).fetchone():
        konn.execute("DELETE FROM medlemmer WHERE klubb_id = ?", (klubb_id,))
        konn.execute("DELETE FROM sjekk_logg WHERE klubb_id = ?", (klubb_id,))
        konn.execute("DELETE FROM klubber WHERE id = ?", (klubb_id,))
        konn.commit()
    konn.close()

# --- Medlemmer ---
def hent_medlemmer(klubb_id):
    konn = koble()
    rader = konn.execute("SELECT * FROM medlemmer WHERE klubb_id = ? ORDER BY id", (klubb_id,)).fetchall()
    konn.close()
    medlemmer = []
    for r in rader:
        lekkasjer = json.loads(r["lekkasjer"])
        medlemmer.append({"id": r["id"], "navn": r["navn"], "rolle": r["rolle"],
                          "epost": r["epost"], "tofaktor": bool(r["tofaktor"]),
                          "lekkasjer": lekkasjer, "lekket": len(lekkasjer) > 0})
    return medlemmer

def hent_medlem(medlem_id):
    konn = koble()
    r = konn.execute("SELECT id, klubb_id FROM medlemmer WHERE id = ?", (medlem_id,)).fetchone()
    konn.close(); return {"id": r["id"], "klubb_id": r["klubb_id"]} if r else None

def legg_til(klubb_id, navn, rolle, epost, tofaktor, lekkasjer):
    konn = koble()
    konn.execute("INSERT INTO medlemmer (klubb_id, navn, rolle, epost, tofaktor, lekkasjer) VALUES (?,?,?,?,?,?)",
                 (klubb_id, navn, rolle, epost, 1 if tofaktor else 0, json.dumps(lekkasjer)))
    konn.commit(); konn.close()

def oppdater_lekkasjer(medlem_id, lekkasjer):
    konn = koble()
    konn.execute("UPDATE medlemmer SET lekkasjer = ? WHERE id = ?", (json.dumps(lekkasjer), medlem_id))
    konn.commit(); konn.close()

def slett(medlem_id):
    konn = koble()
    konn.execute("DELETE FROM medlemmer WHERE id = ?", (medlem_id,))
    konn.commit(); konn.close()

# --- Sjekk-logg ---
def logg_sjekk(klubb_id, antall, nye_funn, detaljer):
    konn = koble()
    tid = datetime.now().strftime("%d.%m kl. %H:%M")
    konn.execute("INSERT INTO sjekk_logg (klubb_id, tidspunkt, antall_sjekket, nye_funn, detaljer) VALUES (?,?,?,?,?)",
                 (klubb_id, tid, antall, nye_funn, detaljer))
    konn.commit(); konn.close()

def hent_logg(klubb_id, grense=5):
    konn = koble()
    rader = konn.execute("SELECT * FROM sjekk_logg WHERE klubb_id = ? ORDER BY id DESC LIMIT ?",
                         (klubb_id, grense)).fetchall()
    konn.close()
    return [{"tidspunkt": r["tidspunkt"], "antall_sjekket": r["antall_sjekket"],
             "nye_funn": r["nye_funn"], "detaljer": r["detaljer"]} for r in rader]

def sist_sjekk(klubb_id):
    konn = koble()
    r = konn.execute("SELECT tidspunkt FROM sjekk_logg WHERE klubb_id = ? ORDER BY id DESC LIMIT 1",
                     (klubb_id,)).fetchone()
    konn.close(); return r["tidspunkt"] if r else None
