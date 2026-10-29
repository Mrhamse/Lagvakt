import requests

NAVN = "XposedOrNot"
URL = "https://api.xposedornot.com/v1/check-email/{epost}"

def sjekk(epost: str) -> list:
    """Returnerer en liste med lekkasjer for en e-post, eller tom liste."""
    try:
        svar = requests.get(URL.format(epost=epost), timeout=15)
    except requests.RequestException as e:
        print(f"[!] {NAVN}: nettverksfeil ({e})")
        return []

    # 404 = e-posten er ikke funnet i noen lekkasje
    if svar.status_code == 404:
        return []
    if svar.status_code != 200:
        print(f"[!] {NAVN}: uventet svar {svar.status_code}")
        return []

    data = svar.json()
    # Formatet er {"breaches": [["Navn1", "Navn2", ...]]}
    breaches = data.get("breaches") or []
    if not breaches or not breaches[0]:
        return []

    return [{"kilde": NAVN, "navn": navn} for navn in breaches[0]]
