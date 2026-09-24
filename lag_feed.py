#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Henter de nyeste publikasjonene til forskergruppen fra OpenAlex
(sok paa ORCID) og skriver en RSS 2.0-fil (feed.xml) som GitHub
Pages serverer til Squarespace.

Sammendragene (abstract) hentes ordrett fra OpenAlex - dvs. på
artikkelens originalsprak, som for denne gruppen er engelsk.

description-feltet inneholder to linjer:
  linje 1: forfattere - tidsskrift (dato)
  linje 2: kort sammendrag av artikkelen, avkuttet med ...
Nettside-skriptet deler dette opp i to visningslinjer.
"""

import datetime as dt
import xml.etree.ElementTree as ET
from email.utils import format_datetime

import requests

# ----------------------------------------------------------------
# Innstillinger
# ----------------------------------------------------------------
MAILTO         = "stianfra@uio.no"   # BEHOLD DIN E-POST HER
ANTALL_I_FEED  = 30      # antall artikler i feeden
FRA_MND        = 24      # kun publikasjoner fra siste X maneder
MAKS_TEGN      = 240     # makslengde paa sammendraget
SIDENAVN       = "Oslo Diabetes Research Centre"
NETTSTED       = "https://oslodiabetes.no"
UTFIL          = "feed.xml"
CHUNK          = 10      # ORCID-er per API-kall

ORCIDS = [
    "0000-0002-9347-9633",  # Anne-Marie Aas
    "0000-0003-4406-2396",  # Tore Julsrud Berg
    "0000-0003-3002-6933",  # Kåre I. Birkeland
    "0000-0002-7844-2357",  # Esben Selmer Buhl
    "0000-0002-6952-9899",  # Knut Dahl-Jørgensen
    "0000-0001-9208-9791",  # Åse Ruth Eggemoen
    "0000-0001-5057-4449",  # Hanne Løvdal Gulseth
    "0000-0001-7619-8701",  # Sara Salehi Hammerstad
    "0000-0001-7807-194X",  # Martin Heier
    "0000-0003-0304-7800",  # Anne Karen Jenum
    "0000-0001-7556-8141",  # Geir Joner
    "0000-0002-6885-039X",  # Svein Olav Kolset
    "0000-0002-1057-7095",  # Lars Krogvold
    "0000-0002-0670-7555",  # Sindre Lee-Ødegård
    "0000-0002-7962-4726",  # Tove Lekva
    "0000-0002-1159-7004",  # Benedicte A. Lie
    "0000-0001-9144-1781",  # Hanna Dis Margeirsdottir
    "0000-0002-8768-0904",  # Gunn-Helen Moen
    "0000-0003-2714-0102",  # Anne Pernille Ofstad
    "0000-0002-9119-9187",  # Elisabeth Qvigstad
    "0000-0003-2755-4399",  # Hanne Scholz
    "0000-0002-4352-5929",  # Torild Skrivarhaug
    "0000-0002-5085-7366",  # Line S
