import requests

NAVN = "LeakCheck"
URL = "https://leakcheck.io/api/public"

def sjekk(epost: str) -> list:
    try:
        svar = requests.get(URL, params={"check": epost}, timeout=15)
    except requests.RequestException as e:
        print(f"[!] {NAVN}: nettverksfeil ({e})")
        return []

    if svar.status_code == 429:
        print(f"[!] {NAVN}: for mange forespørsler - vent et minutt.")
        return []
    if svar.status_code != 200:
        print(f"[!] {NAVN}: uventet svar {svar.status_code}")
        return []

    data = svar.json()
    # success=false betyr som regel "ikke funnet"
    if not data.get("success"):
        return []

    kilder_liste = data.get("sources") or []
    return [{"kilde": NAVN, "navn": s.get("name", "")} for s in kilder_liste]
