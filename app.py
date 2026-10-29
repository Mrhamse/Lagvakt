import os
import time
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
import db
from aggregator import sjekk_alle
from passord_sjekk import sjekk_passord

app = Flask(__name__)
app.secret_key = "lagvakt-dev-noekkel-bytt-i-produksjon"
db.init()

# --- Lekkasjesjekk-kjoering ---
def kjor_sjekk_for_klubb(klubb_id):
    ms = db.hent_medlemmer(klubb_id)
    nye = []
    for m in ms:
        gamle_navn = {l["navn"] for l in m["lekkasjer"]}
        ferske = sjekk_alle(m["epost"])
        # Slaa sammen gamle og ferske (en lekkasje forsvinner ikke)
        samlet = {}
        for l in m["lekkasjer"] + ferske:
            n = l["navn"]
            s = set(l.get("kilder", []))
            if n in samlet:
                samlet[n]["kilder"].update(s)
            else:
                samlet[n] = {"navn": n, "kilder": s}
        samlet_liste = [{"navn": v["navn"], "kilder": sorted(v["kilder"])} for v in samlet.values()]
        if {l["navn"] for l in ferske} - gamle_navn:
            nye.append(m["navn"])
        db.oppdater_lekkasjer(m["id"], samlet_liste)
        time.sleep(1)   # spar API-ene
    db.logg_sjekk(klubb_id, len(ms), len(nye), ", ".join(nye))

def kjor_automatisk_sjekk():
    for kid in db.alle_klubb_ider():
        kjor_sjekk_for_klubb(kid)

scheduler = BackgroundScheduler(daemon=True)

def start_planlegger():
    scheduler.add_job(kjor_automatisk_sjekk, "interval", minutes=30, id="auto")
    scheduler.start()

# --- Innlogging ---
def login_kreves(f):
    @wraps(f)
    def innpakning(*a, **kw):
        if "bruker_id" not in session:
            return redirect(url_for("logg_inn"))
        return f(*a, **kw)
    return innpakning

def aktiv_klubb():
    bid = session.get("bruker_id")
    if not bid:
        return None
    klubber = db.hent_klubber(bid)
    if not klubber:
        return None
    kid = session.get("klubb_id")
    if kid not in {k["id"] for k in klubber}:
        kid = klubber[0]["id"]; session["klubb_id"] = kid
    return db.hent_klubb(kid, bid)

@app.context_processor
def inject():
    bid = session.get("bruker_id")
    if not bid:
        return {"alle_klubber": [], "aktiv_klubb_id": None, "bruker": None}
    k = aktiv_klubb()
    return {"alle_klubber": db.hent_klubber(bid),
            "aktiv_klubb_id": k["id"] if k else None, "bruker": db.hent_bruker(bid)}

@app.route("/registrer", methods=["GET", "POST"])
def registrer():
    if request.method == "POST":
        navn = request.form.get("navn", "").strip()
        epost = request.form.get("epost", "").strip().lower()
        passord = request.form.get("passord", "")
        if not epost or len(passord) < 6:
            return render_template("registrer.html", feil="Fyll inn e-post og et passord på minst 6 tegn.")
        bid = db.opprett_bruker(epost, generate_password_hash(passord), navn)
        if bid is None:
            return render_template("registrer.html", feil="Denne e-posten er allerede registrert.")
        session["bruker_id"] = bid
        return redirect(url_for("klubber"))
    return render_template("registrer.html")

@app.route("/logg-inn", methods=["GET", "POST"])
def logg_inn():
    if request.method == "POST":
        epost = request.form.get("epost", "").strip().lower()
        passord = request.form.get("passord", "")
        bruker = db.hent_bruker_med_epost(epost)
        if bruker and check_password_hash(bruker["passord_hash"], passord):
            session["bruker_id"] = bruker["id"]; session.pop("klubb_id", None)
            return redirect(url_for("dashbord"))
        return render_template("login.html", feil="Feil e-post eller passord.")
    return render_template("login.html")

@app.route("/logg-ut")
def logg_ut():
    session.clear()
    return redirect(url_for("logg_inn"))

@app.route("/")
@login_kreves
def dashbord():
    klubb = aktiv_klubb()
    if not klubb:
        return redirect(url_for("klubber"))
    ms = db.hent_medlemmer(klubb["id"])
    antall = len(ms)
    antall_lekket = sum(1 for m in ms if m["lekket"])
    tofaktor_pa = sum(1 for m in ms if m["tofaktor"])
    tofaktor_mangler = antall - tofaktor_pa

    if antall == 0:
        status = {"farge": "GUL", "ord": "TOMT", "tittel": "Ingen medlemmer ennå",
                  "tekst": "Legg til styremedlemmene under Styret for å komme i gang."}
    elif antall_lekket == 0 and tofaktor_mangler == 0:
        status = {"farge": "GRONN", "ord": "TRYGG", "tittel": "Alt ser bra ut",
                  "tekst": "Ingen lekkasjer funnet, og alle har to-faktor på."}
    else:
        status = {"farge": "GUL", "ord": "VÆR OBS", "tittel": "Klubben er nesten i grønt",
                  "tekst": "Noen ting bør fikses under, så er alle klubbens kontoer trygge igjen."}

    oppgaver = []
    for m in ms:
        if m["lekket"]:
            navn = ", ".join(l["navn"] for l in m["lekkasjer"])
            oppgaver.append({"farge": "ROD", "tittel": f'{m["navn"]} ({m["rolle"]}) — e-post på avveie',
                             "tekst": f'Funnet i: {navn}. Bør bytte passord og skru på to-faktor.',
                             "knapp": "Send påminnelse", "primar": True})
    for m in ms:
        if not m["tofaktor"]:
            oppgaver.append({"farge": "GUL", "tittel": f'{m["navn"]} ({m["rolle"]}) — mangler to-faktor',
                             "tekst": "To-faktor gjør kontoen mye vanskeligere å hacke. Tar to minutter.",
                             "knapp": "Send veiledning", "primar": False})

    return render_template("dashboard.html", side="oversikt", klubb=klubb["navn"], status=status,
                           antall=antall, antall_lekket=antall_lekket, tofaktor_pa=tofaktor_pa,
                           tofaktor_total=antall, tofaktor_mangler=tofaktor_mangler,
                           siste_sjekk=db.sist_sjekk(klubb["id"]) or "aldri",
                           aktivitet=db.hent_logg(klubb["id"], 5), oppgaver=oppgaver)

@app.route("/oppdater")
@login_kreves
def oppdater_rute():
    klubb = aktiv_klubb()
    if klubb:
        kjor_sjekk_for_klubb(klubb["id"])
    return redirect(url_for("dashbord"))

@app.route("/styret")
@login_kreves
def styret():
    klubb = aktiv_klubb()
    if not klubb:
        return redirect(url_for("klubber"))
    return render_template("styret.html", side="styret", klubb=klubb["navn"],
                           medlemmer=db.hent_medlemmer(klubb["id"]))

@app.route("/legg-til", methods=["POST"])
@login_kreves
def legg_til_medlem():
    klubb = aktiv_klubb()
    navn = request.form.get("navn", "").strip()
    rolle = request.form.get("rolle", "").strip()
    epost = request.form.get("epost", "").strip()
    tofaktor = request.form.get("tofaktor") == "on"
    if klubb and navn and epost:
        db.legg_til(klubb["id"], navn, rolle, epost, tofaktor, sjekk_alle(epost))
    return redirect(url_for("styret"))

@app.route("/slett/<int:medlem_id>", methods=["POST"])
@login_kreves
def slett_medlem(medlem_id):
    bid = session["bruker_id"]
    m = db.hent_medlem(medlem_id)
    if m and db.hent_klubb(m["klubb_id"], bid):
        db.slett(medlem_id)
    return redirect(url_for("styret"))

@app.route("/passord", methods=["GET", "POST"])
@login_kreves
def passord():
    resultat = None
    if request.method == "POST":
        p = request.form.get("passord", "")
        if p:
            antall = sjekk_passord(p)
            resultat = {"antall": antall, "lekket": antall > 0}
    klubb = aktiv_klubb()
    return render_template("passord.html", side="passord",
                           klubb=(klubb or {}).get("navn", "Lagvakt"), resultat=resultat)

@app.route("/varsler")
@login_kreves
def varsler():
    klubb = aktiv_klubb()
    if not klubb:
        return redirect(url_for("klubber"))
    meldinger = []
    for m in db.hent_medlemmer(klubb["id"]):
        fornavn = m["navn"].split()[0]
        if m["lekket"]:
            meldinger.append({"til": m["navn"], "type": "Lekkasje",
                "tekst": f"Hei {fornavn}! Du er {m['rolle'].lower()} i {klubb['navn']}. E-posten din er funnet i en datalekkasje, så passordet ditt kan være på avveie. Bytt passord og skru på to-faktor, så er klubbens konto trygg igjen."})
        elif not m["tofaktor"]:
            meldinger.append({"til": m["navn"], "type": "To-faktor",
                "tekst": f"Hei {fornavn}! Skru på to-faktor på kontoen din i {klubb['navn']}, så blir den mye vanskeligere å hacke. Det tar to minutter — her er veiledningen."})
    return render_template("varsler.html", side="varsler", klubb=klubb["navn"], meldinger=meldinger)

@app.route("/klubber")
@login_kreves
def klubber():
    bid = session["bruker_id"]
    return render_template("klubber.html", side="innstillinger",
                           klubb=(aktiv_klubb() or {}).get("navn", "Lagvakt"),
                           klubber=db.hent_klubber(bid))

@app.route("/klubb/velg/<int:klubb_id>")
@login_kreves
def velg_klubb(klubb_id):
    bid = session["bruker_id"]
    if db.hent_klubb(klubb_id, bid):
        session["klubb_id"] = klubb_id
    return redirect(url_for("dashbord"))

@app.route("/klubb/ny", methods=["POST"])
@login_kreves
def ny_klubb():
    bid = session["bruker_id"]
    navn = request.form.get("navn", "").strip()
    if navn:
        session["klubb_id"] = db.legg_til_klubb(navn, bid)
        return redirect(url_for("styret"))
    return redirect(url_for("klubber"))

@app.route("/klubb/navn/<int:klubb_id>", methods=["POST"])
@login_kreves
def endre_klubb_navn(klubb_id):
    navn = request.form.get("navn", "").strip()
    if navn:
        db.endre_klubb(klubb_id, navn, session["bruker_id"])
    return redirect(url_for("klubber"))

@app.route("/klubb/slett/<int:klubb_id>", methods=["POST"])
@login_kreves
def slett_klubb_rute(klubb_id):
    db.slett_klubb(klubb_id, session["bruker_id"])
    if session.get("klubb_id") == klubb_id:
        session.pop("klubb_id", None)
    return redirect(url_for("klubber"))

@app.route("/innstillinger")
@login_kreves
def innstillinger():
    return redirect(url_for("klubber"))

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_planlegger()
    app.run(debug=True, port=5000)
