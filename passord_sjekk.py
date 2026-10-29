import hashlib
import requests

URL = "https://api.pwnedpasswords.com/range/{prefix}"

def sjekk_passord(passord: str) -> int:
    """Returnerer hvor mange ganger passordet er sett i lekkasjer (0 = aldri)."""
    sha1 = hashlib.sha1(passord.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    svar = requests.get(URL.format(prefix=prefix), headers={"Add-Padding": "true"}, timeout=15)
    svar.raise_for_status()
    for linje in svar.text.splitlines():
        hash_suffix, _, antall = linje.partition(":")
        if hash_suffix.strip() == suffix:
            return int(antall)
    return 0
