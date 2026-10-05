"""
Official disaster alerts for a district, from NDMA's Sachet feed.

Sachet is India's national Common Alerting Protocol (CAP) system. IMD (weather,
thunderstorm, wind), INCOIS (tsunami, high wave, swell surge, storm surge) and
others publish into it. We only READ and pass these alerts on unchanged - we
never generate or rewrite a warning ourselves.

Feed:   RSS list of recent alerts per state
Detail: each RSS item links to a CAP XML with event, severity, expiry, area
        (district name + LGD code) and headlines in English and the state language.
"""

import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

KERALA_FEED_URL = "https://sachet.ndma.gov.in/cap_public_website/rss/rss_kerala.xml"
CAP_NS = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}

# LGD (Local Government Directory) district codes, as used in CAP <geocode>.
# Kerala's are 554-567 in alphabetical order; cross-checked against live alerts
# that list district names (Kasaragod 558, Palakkad 563, Kozhikode 561,
# Malappuram 562, Thrissur 566, Kannur 557, Wayanad 567).
DISTRICT_LGD = {
    "ALP": "554", "EKM": "555", "KNR": "557", "KSD": "558", "KLM": "559",
    "KKD": "561", "MLPM": "562", "TVPM": "565", "TCR": "566",
}

# Fallback for alerts with no geocode: spellings seen in area descriptions, lowercase.
DISTRICT_NAMES = {
    "TVPM": ["thiruvananthapuram", "trivandrum"],
    "KLM": ["kollam", "quilon"],
    "ALP": ["alappuzha", "alleppey"],
    "EKM": ["ernakulam", "kochi", "cochin"],
    "TCR": ["thrissur", "trichur"],
    "MLPM": ["malappuram"],
    "KKD": ["kozhikode", "calicut"],
    "KNR": ["kannur", "cannanore"],
    "KSD": ["kasaragod", "kasargod", "kasaragode"],
}
ALL_KERALA_NAMES = [n for names in DISTRICT_NAMES.values() for n in names] + [
    "kottayam", "idukki", "pathanamthitta", "palakkad", "wayanad"]

# An alert counts as a SEA alert if it comes from INCOIS or its event text
# matches one of these.
SEA_KEYWORDS = ["tsunami", "storm surge", "high wave", "swell", "surge", "sea state",
                "rough sea", "coastal", "fishermen", "kallakkadal", "cyclone"]

SEVERITY_ORDER = ["Extreme", "Severe", "Moderate", "Minor", "Unknown"]


def _text(node, path):
    found = node.find(path, CAP_NS)
    return found.text.strip() if found is not None and found.text else ""


def _parse_cap(xml_bytes, author):
    root = ET.fromstring(xml_bytes)
    infos = root.findall("cap:info", CAP_NS)
    if not infos:
        return None
    headlines = {}
    for info in infos:
        lang = _text(info, "cap:language").lower()[:2] or "en"
        headlines[lang] = _text(info, "cap:headline") or _text(info, "cap:description")
    first = infos[0]
    areas = first.findall("cap:area", CAP_NS)
    area = " ".join(_text(a, "cap:areaDesc") for a in areas)
    lgd_codes = {_text(g, "cap:value") for a in areas for g in a.findall("cap:geocode", CAP_NS)
                 if "lgd" in _text(g, "cap:valueName").lower()}
    event = _text(first, "cap:event")
    sender = _text(root, "cap:sender")
    source = author or sender
    is_sea = "incois" in source.lower() or any(k in f"{event} {headlines.get('en', '')}".lower()
                                                for k in SEA_KEYWORDS)
    expires = _text(first, "cap:expires")
    return {
        "event": event,
        "severity": _text(first, "cap:severity") or "Unknown",
        "headlines": headlines,
        "area": area,
        "lgd_codes": lgd_codes,
        "source": source,
        "is_sea": is_sea,
        "sent": _text(root, "cap:sent"),
        "expires": datetime.fromisoformat(expires) if expires else None,
        "instruction": _text(first, "cap:instruction"),
    }


def fetch_kerala_alerts(max_items=30):
    """Downloads the Kerala feed and every linked CAP alert.

    Raises requests.RequestException / ET.ParseError if the feed itself fails;
    individual broken alerts are skipped.
    """
    resp = requests.get(KERALA_FEED_URL, timeout=15)
    resp.raise_for_status()
    items = ET.fromstring(resp.content).findall(".//item")[:max_items]

    def load(item):
        author = (item.findtext("author") or "").split("(")[-1].rstrip(")")
        try:
            cap = requests.get(item.findtext("link"), timeout=15)
            cap.raise_for_status()
            alert = _parse_cap(cap.content, author)
        except (requests.RequestException, ET.ParseError, ValueError):
            return None
        if alert and alert["expires"] is None:
            pub = item.findtext("pubDate")
            alert["expires"] = parsedate_to_datetime(pub) if pub else None
        return alert

    with ThreadPoolExecutor(max_workers=8) as pool:
        return [a for a in pool.map(load, items) if a]


def alerts_for_district(alerts, district_code, now=None):
    """Active (not yet expired) alerts that apply to this district, sea alerts first.

    An alert applies if its LGD district codes include this district, or (when it
    has no codes) its area text names this district. A sea alert that names no
    district at all (e.g. "Kerala coast") applies to every coastal district.
    """
    now = now or datetime.now(timezone.utc)
    names = DISTRICT_NAMES[district_code]
    matched = []
    for a in alerts:
        if a["expires"] and a["expires"] < now:
            continue
        area = a["area"].lower()
        if a["lgd_codes"]:
            applies = DISTRICT_LGD[district_code] in a["lgd_codes"]
        else:
            applies = any(n in area for n in names) or (
                a["is_sea"] and not any(n in area for n in ALL_KERALA_NAMES))
        if applies:
            matched.append(a)

    # Same alert is often re-issued as updates - keep one per headline.
    unique = {}
    for a in matched:
        unique.setdefault(a["headlines"].get("en") or a["event"], a)

    def sort_key(a):
        sev = a["severity"] if a["severity"] in SEVERITY_ORDER else "Unknown"
        return (not a["is_sea"], SEVERITY_ORDER.index(sev))

    return sorted(unique.values(), key=sort_key)
