# Lagvakt

En enkel sikkerhetstjeneste for frivillige lag og foreninger. Lagvakt passer på
at folkene i et klubbstyre ikke har e-post eller passord på avveie, og varsler
dem på en vennlig måte hvis de har det.

Idrettslag, korps og velforeninger sitter på medlemslister med adresser og info
om barn, men styret er som regel foreldre uten datakompetanse. Den vanligste
måten de blir hacket på er gjenbrukte passord som allerede er lekket. Lagvakt
fanger akkurat det, og gjør det forståelig med et enkelt trafikklys.

## Skjermbilder

![Dashbord](bilder/dashbord.png)

![Styret](bilder/styret.png)

![Passord-sjekk](bilder/passord.png)

## Hva den gjør
- **Overvåker styret automatisk.** Sjekker hvert styremedlems e-post mot kjente
  datalekkasjer, i bakgrunnen på en tidsplan — ikke bare når noen åpner appen.
- **Sjekker passord trygt.** Et styremedlem kan teste om et passord er lekket,
  uten at passordet forlater maskinen (k-anonymitet).
- **Viser et trafikklys.** Grønn, gul eller rød status som alle forstår.
- **Lager vennlige varsler.** «Hei Ola, bytt passord…», klart til å sendes.
- **Flere klubber per bruker.** Én person kan styre mange lag, hver adskilt.

## Hvordan det fungerer
- **Flerkildes lekkasjemotor.** Hver datakilde (XposedOrNot, LeakCheck, Have I
  Been Pwned) er en egen adapter. En aggregator spør alle samtidig og slår
  sammen svarene, så én kilde fanger det en annen går glipp av.
- **Automatisk overvåking.** En bakgrunns-planlegger kjører sjekkene jevnlig og
  logger nye funn, så appen jobber mens du sover.
- **Passord-sjekk med k-anonymitet.** Passordet hashes lokalt, og bare de fem
  første tegnene av hashen sendes.
- **Innlogging og data per bruker.** Hver bruker ser kun sine egne klubber.

## Sikkerhet og personvern
Bygget for en sensitiv kontekst (lag med barn), så personvern er en del av
designet:
- Passord lagres hashet, aldri i klartekst.
- Lekkasjesjekken ser kun *om* en e-post er lekket, aldri selve passordet.
- Passord-sjekken sender aldri passordet (k-anonymitet).
- Hver bruker ser kun sine egne data.
- Kun seriøse kilder brukes, aldri tjenester som dumper passord i klartekst.

## Prosjektstruktur
| Fil | Ansvar |
|-----|--------|
| app.py | Webapp, ruter og bakgrunns-planlegger |
| db.py | Database (brukere, klubber, medlemmer, logg) |
| aggregator.py | Spør alle lekkasjekilder og slår sammen svaret |
| kilder/ | Én adapter per datakilde |
| passord_sjekk.py | Passord-sjekk med k-anonymitet |
| templates/ | Grensesnittet |

## Teknologi
Python, Flask, SQLite, APScheduler, Werkzeug (passord-hashing)

## Oppsett

python3 -m venv .venv && source .venv/bin/activate
pip install flask requests python-dotenv apscheduler
python app.py

Åpne http://127.0.0.1:5000 og opprett en konto.

## Begrensninger og videre arbeid
- Samtykke-flyt: hvert medlem bør bekrefte samtykke før de sjekkes.
- Ekte varsler: SMS/e-post via en betalt tjeneste (vises som forhåndsvisning i dag).
- Integrasjon med Spond/StyreWeb for å hente styret automatisk.
- Produksjonssikkerhet: hemmelig nøkkel i miljøvariabel, HTTPS, CSRF-vern.

## Attribusjon
Lekkasjedata brukes bl.a. fra Have I Been Pwned (haveibeenpwned.com) under deres
Creative Commons-lisens.

## Ansvarsfraskrivelse
Personlig læringsprosjekt / MVP. Skal kun brukes på e-poster og passord man selv
eier eller har fått samtykke til å sjekke.
