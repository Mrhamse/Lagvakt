from kilder import xposedornot, hibp, leakcheck

# Legg til nye kilder her senere - resten av koden trenger ikke endres
KILDER = [xposedornot, hibp, leakcheck]

def sjekk_alle(epost: str) -> list:
    alle = []
    for kilde in KILDER:
        alle.extend(kilde.sjekk(epost))

    # Slå sammen etter lekkasjenavn, husk hvilke kilder som fant hver
    samlet = {}
    for funn in alle:
        navn = funn["navn"]
        if not navn:
            continue
        nokkel = navn.lower()
        if nokkel not in samlet:
            samlet[nokkel] = {"navn": navn, "kilder": set()}
        samlet[nokkel]["kilder"].add(funn["kilde"])

    resultat = [{"navn": v["navn"], "kilder": sorted(v["kilder"])} for v in samlet.values()]
    resultat.sort(key=lambda x: x["navn"].lower())
    return resultat
