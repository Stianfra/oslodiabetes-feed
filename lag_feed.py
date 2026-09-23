#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Henter de nyeste publikasjonene til forskergruppen fra OpenAlex
(sok paa ORCID) og skriver en RSS 2.0-fil (feed.xml) som GitHub
Pages serverer til Squarespace.
"""

import datetime as dt
import xml.etree.ElementTree as ET
from email.utils import format_datetime

import requests

# ----------------------------------------------------------------
# Innstillinger
# ----------------------------------------------------------------
MAILTO         = "stianfra@uio.no"   # BYTT TIL DIN E-POST
ANTALL_I_FEED  = 30      # antall artikler i feeden
FRA_MND        = 24      # kun publikasjoner fra siste X maneder
SIDENAVN       = "Oslo Diabetes Research Centre"
NETTSTED       = "https://oslodiabetes.no"
UTFIL          = "feed.xml"
CHUNK          = 10      # ORCID-er per API-kall

ORCIDS = [
    "0000-0002-9347-9633",  # Anne-Marie Aas
    "0000-0003-4406-2396",  # Tore Julsrud Berg
    "0000-0003-3002-6933",  # Kaare I. Birkeland
    "0000-0002-7844-2357",  # Esben Selmer Buhl
    "0000-0002-6952-9899",  # Knut Dahl-Jorgensen
    "0000-0001-9208-9791",  # Ase Ruth Eggemoen
    "0000-0001-5057-4449",  # Hanne Loevdal Gulseth
    "0000-0001-7619-8701",  # Sara Salehi Hammerstad
    "0000-0001-7807-194X",  # Martin Heier
    "0000-0003-0304-7800",  # Anne Karen Jenum
    "0000-0001-7556-8141",  # Geir Joner
    "0000-0002-6885-039X",  # Svein Olav Kolset
    "0000-0002-1057-7095",  # Lars Krogvold
    "0000-0002-0670-7555",  # Sindre Lee-Oedegaard
    "0000-0002-7962-4726",  # Tove Lekva
    "0000-0002-1159-7004",  # Benedicte A. Lie
    "0000-0001-9144-1781",  # Hanna Dis Margeirsdottir
    "0000-0002-8768-0904",  # Gunn-Helen Moen
    "0000-0003-2714-0102",  # Anne Pernille Ofstad
    "0000-0002-9119-9187",  # Elisabeth Qvigstad
    "0000-0003-2755-4399",  # Hanne Scholz
    "0000-0002-4352-5929",  # Torild Skrivarhaug
    "0000-0002-5085-7366",  # Line Sletner
    "0000-0002-7370-8988",  # Christine Sommer
    "0000-0002-8434-119X",  # Lars Christian Moech Stene
    "0000-0002-1034-9965",  # Kari Anne Sveen
    "0000-0002-9615-1035",  # Per M. Thorsby
    "0000-0002-3917-9269",  # Marte K. Viken
    "0000-0002-5424-7290",  # Line Wisting
    "0000-0001-9917-4825",  # Christin Wiegels Waage
]

API = "https://api.openalex.org/works"


def rfc822(dato):
    """Gjoer '2026-09-08' om til 'Tue, 08 Sep 2026 00:00:00 +0000'."""
    if not dato:
        return None
    try:
        d = dt.date.fromisoformat(str(dato)[:10])
    except ValueError:
        return None
    return format_datetime(dt.datetime(d.year, d.month, d.day,
                                       tzinfo=dt.timezone.utc))


def hent_verk():
    samlet = {}
    fra_dato = (dt.date.today() - dt.timedelta(days=FRA_MND * 31)).isoformat()

    for i in range(0, len(ORCIDS), CHUNK):
        chunk = ORCIDS[i:i + CHUNK]

        # OpenAlex har brukt litt ulik ORCID-syntaks - proev begge.
        for verdier in (["https://orcid.org/" + o for o in chunk], chunk):
            f = "author.orcid:" + "|".join(verdier)
            f += ",from_publication_date:" + fra_dato
            r = requests.get(
                API,
                params={
                    "filter": f,
                    "sort": "publication_date:desc",
                    "per-page": 200,
                    "mailto": MAILTO,
                },
                timeout=60,
            )
            if r.status_code == 200:
                break
        r.raise_for_status()

        data = r.json()
        print(f"Gruppe {i // CHUNK + 1}: {data['meta']['count']} treff")
        for w in data["results"]:
            samlet[w["id"]] = w

    if not samlet:
        raise RuntimeError("OpenAlex returnerte ingen treff - ingen feed skrevet.")

    sortert = sorted(samlet.values(),
                     key=lambda w: str(w.get("publication_date") or ""),
                     reverse=True)
    return sortert[:ANTALL_I_FEED]


def lag_rss(verk):
    rss = ET.Element("rss", {"version": "2.0"})
    kanal = ET.SubElement(rss, "channel")
    ET.SubElement(kanal, "title").text = f"{SIDENAVN} - siste publikasjoner"
    ET.SubElement(kanal, "link").text = NETTSTED
    ET.SubElement(kanal, "description").text = (
        f"Nyere vitenskapelige artikler fra forskere ved {SIDENAVN}.")
    ET.SubElement(kanal, "language").text = "no"
    ET.SubElement(kanal, "lastBuildDate").text = format_datetime(
        dt.datetime.now(dt.timezone.utc))

    for w in verk:
        tittel = w.get("title") or "Uten tittel"
        lenke = w.get("doi") or w.get("id") or NETTSTED

        forfattere = [a.get("author", {}).get("display_name")
                      for a in (w.get("authorships") or [])]
        forfattere = [navn for navn in forfattere if navn]
        tekst = ", ".join(forfattere[:8])
        if len(forfattere) > 8:
            tekst += " m.fl."

        kilde = ((w.get("primary_location") or {})
                 .get("source") or {}).get("display_name")
        if kilde:
            tekst += f" - {kilde}"
        if w.get("publication_date"):
            tekst += f" ({w['publication_date']})"

        item = ET.SubElement(kanal, "item")
        ET.SubElement(item, "title").text = tittel
        ET.SubElement(item, "link").text = lenke
        ET.SubElement(item, "description").text = tekst
        ET.SubElement(item, "guid").text = w["id"]
        ET.SubElement(item, "pubDate").text = (
            rfc822(w.get("publication_date"))
            or format_datetime(dt.datetime.now(dt.timezone.utc)))

    tre = ET.ElementTree(rss)
    ET.indent(tre, space="  ")
    tre.write(UTFIL, encoding="utf-8", xml_declaration=True)


def main():
    verk = hent_verk()
    lag_rss(verk)
    print(f"ferdig: {UTFIL} med {len(verk)} artikler")


if __name__ == "__main__":
    main()
