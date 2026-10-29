import os
import requests
from dotenv import load_dotenv

load_dotenv()

NAVN = "HaveIBeenPwned"
API_KEY = os.getenv("HIBP_API_KEY")
URL = "https://haveibeenpwned.com/api/v3/breachedaccount/{epost}"

def sjekk(epost: str) -> list:
    if not API_KEY:
        print(f"[i] {NAVN}: ingen API-nøkkel i .env - hopper over denne kilden.")
        return []

    headers = {"hibp-api-key": API_KEY, "user-agent": "Lagvakt-lekkasjesjekk"}
    try:
        svar = requests.get(
            URL.format(epost=epost),
            headers=headers,
            params={"truncateResponse": "false"},
            timeout=15,
        )
    except requests.RequestException as e:
        print(f"[!] {NAVN}: nettverksfeil ({e})")
        return []

    if svar.status_code == 404:
        return []
    if svar.status_code == 401:
        print(f"[!] {NAVN}: ugyldig API-nøkkel.")
        return []
    if svar.status_code != 200:
        print(f"[!] {NAVN}: uventet svar {svar.status_code}")
        return []

    data = svar.json()
    return [{"kilde": NAVN, "navn": b.get("Name", "")} for b in data]
