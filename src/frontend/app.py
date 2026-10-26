"""
Catch Plan - Streamlit app.

Sequential flow: language -> season -> district -> boat capacity -> results.

Reads data/processed/frontend_dataset.json (built by src/ml/build_frontend_dataset.py)
and src/i18n/species.json. Two data sources, kept honestly distinct throughout the UI:
- price: MODEL-PREDICTED, trained on SYNTHETIC mock data (see src/ml/generate_mock_price_data.py)
- catch share: REAL, Kerala Fisheries Department district-wise data (2022-23 to 2024-25)

Run locally with:  streamlit run src/frontend/app.py
Deploy on Streamlit Community Cloud by pointing it at this file in the repo.

Malayalam and Tamil text below is best-effort and has NOT been reviewed by a native
speaker yet - same caveat as src/i18n/species.json. Get a native speaker to check
before this goes in front of real fishermen.
"""

import html
import base64
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

from fishing_zones import DISTRICT_HARBOURS, fetch_kerala_pfz, offshore_points, zone_conditions, zones_near_district
from official_alerts import alerts_for_district, fetch_kerala_alerts
from sea_weather import compass, daily_summary, fetch_sea_conditions, rate_conditions, sky_kind, tide_turns
from theme import (BRAND_MARK, CSS, FISH_ICON, HERO_LAYERS, MENU_ICON, SCRIPT, SECTION_ANCHORS, SOURCE_DOTS,
                   SOURCE_INK, TOKENS, UI_EXTRA, WAVE_INTO_DARK, WAVE_OUT_OF_DARK, hex_rgb)

IST = timezone(timedelta(hours=5, minutes=30))
# Live-data failures are shown to the user as a friendly warning; the real cause goes to the server log.
log = logging.getLogger("marine_fishing_ai")


def live_data_failed(what, e, message):
    """Friendly warning for the user, plus the real cause (temporary, to debug the Render deployment)."""
    log.warning("%s failed: %r", what, e)
    st.warning(message)
    st.caption(f"Technical detail ({what}): {type(e).__name__}: {str(e)[:300]}")
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = ROOT / "data" / "processed" / "frontend_dataset.json"
SPECIES_PATH = ROOT / "src" / "i18n" / "species.json"

SEASON_MONTHS = {
    "winter": [12, 1, 2],
    "summer": [3, 4, 5],
    "monsoon": [6, 7, 8],
    "postmonsoon": [9, 10, 11],
}
MONTH_NAMES = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
               7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
DISTRICT_ORDER = ["EKM", "KLM", "KKD", "TVPM", "TCR", "ALP", "MLPM", "KNR", "KSD"]
HARBOUR_NATIVE = {
    "Vizhinjam": {"ml": "വിഴിഞ്ഞം", "ta": "விழிஞ்ஞம்"},
    "Neendakara": {"ml": "നീണ്ടകര", "ta": "நீண்டகரை"},
    "Alappuzha": {"ml": "ആലപ്പുഴ", "ta": "ஆலப்புழா"},
    "Kochi": {"ml": "കൊച്ചി", "ta": "கொச்சி"},
    "Chettuva": {"ml": "ചേറ്റുവ", "ta": "சேற்றுவா"},
    "Ponnani": {"ml": "പൊന്നാനി", "ta": "பொன்னானி"},
    "Puthiyappa": {"ml": "പുതിയാപ്പ", "ta": "புதியாப்பா"},
    "Azhikkal": {"ml": "അഴീക്കൽ", "ta": "அழீக்கல்"},
    "Kasaragod": {"ml": "കാസർകോട്", "ta": "காசர்கோடு"},
}
DISTRICT_NATIVE = {
    "EKM": {"ml": "എറണാകുളം", "ta": "எர்ணாகுளம்"},
    "KLM": {"ml": "കൊല്ലം", "ta": "கொல்லம்"},
    "KKD": {"ml": "കോഴിക്കോട്", "ta": "கோழிக்கோடு"},
    "TVPM": {"ml": "തിരുവനന്തപുരം", "ta": "திருவனந்தபுரம்"},
    "TCR": {"ml": "തൃശ്ശൂർ", "ta": "திருச்சூர்"},
    "ALP": {"ml": "ആലപ്പുഴ", "ta": "ஆலப்புழா"},
    "MLPM": {"ml": "മലപ്പുറം", "ta": "மலப்புரம்"},
    "KNR": {"ml": "കണ്ണൂർ", "ta": "கண்ணூர்"},
    "KSD": {"ml": "കാസർകോട്", "ta": "காசர்கோடு"},
}

UI = {
    "en": {
        "lang_name": "English",
        "title": "Catch Plan",
        "brand_tag": "Kerala fishing assistant",
        "setup_header": "Plan your trip",
        "sea_now": "Sea right now",
        "subtitle": "Pick your language, season, district, and boat capacity to see fish prices and your catch plan.",
        "legend_real": "Real: catch data, Kerala Fisheries Dept 2022-25",
        "legend_pred": "Model-predicted: price, trained on synthetic data (prototype, not real market history)",
        "step0": "Choose your language",
        "step1": "Which season are you fishing in?",
        "step2": "Which district are you in?",
        "step3": "Your boat's loading capacity (kg per trip)",
        "result_header": "Market price prediction",
        "plan_header": "Your catch plan",
        "col_species": "Species", "col_price": "Rs / kg", "col_halfkg": "Rs / half-kg", "col_share": "Catch share",
        "col_district": "District",
        "plan_intro": "Based on {district}'s typical species mix and {season} prices, if you land {kg} kg this trip:",
        "plan_total": "Estimated total value",
        "plan_detail": "{share}% of typical catch  |  ~{kg} kg  |  Rs.{price}/kg",
        "all_seasons_header": "Price by season (best season highlighted)",
        "district_compare_header": "Compare districts for one fish",
        "district_compare_pick": "Pick a fish",
        "district_compare_col_share": "Typical catch share",
        "glossary_header": "Fish name glossary",
        "glossary_col_scientific": "Scientific name",
        "glossary_col_malayalam": "Malayalam",
        "glossary_col_tamil": "Tamil",
        "download_button": "Download this plan",
        "sea_header": "Live sea conditions",
        "sea_point": "Sea point ~12 km off {harbour}  |  updated {time}  |  refreshes every 15 min",
        "rating": {
            "calm": ("Calm", "Conditions look workable for going out."),
            "caution": ("Caution", "Choppy sea or strong wind. Small boats take care."),
            "rough": ("Rough", "High waves, strong wind or thunderstorm. Avoid going out."),
        },
        "dir_from": "from {d}", "dir_to": "towards {d}",
        "m_wave": "Wave height", "m_wind": "Wind", "m_gust": "Gusts", "m_swell": "Swell / period",
        "m_sst": "Sea temperature", "m_rain": "Rain now", "m_current": "Ocean current",
        "m_next_high": "Next high tide", "m_next_low": "Next low tide",
        "alerts_header": "Official alerts (IMD, INCOIS via NDMA Sachet)",
        "alerts_none": "No active official alerts for {district}. Checked {time}.",
        "alerts_error": ("Could not reach the official alert service. Check the SAMUDRA app or incois.gov.in "
                         "before going out."),
        "alerts_loading": "Checking official alerts...",
        "alert_sea": "SEA ALERT", "alert_weather": "WEATHER ALERT",
        "alert_meta": "Issued by {source}  |  valid until {until}",
        "forecast_header": "7-day forecast (worst of each day)",
        "col_day": "Day", "col_rating": "Sea", "col_wave": "Waves (m)", "col_period": "Period (s)",
        "col_wind": "Wind (km/h)", "col_max_gust": "Gusts (km/h)", "col_current": "Current (km/h)",
        "col_high_tide": "High tide", "col_low_tide": "Low tide", "col_rain": "Rain (mm)",
        "chart_waves": "Waves (m)", "chart_wind": "Wind (km/h)", "chart_tide": "Tide (m)",
        "chart_current": "Current (km/h)",
        "thunder": "thunderstorm",
        "sea_disclaimer": ("Forecast: Open-Meteo weather model, not an official warning. Tide times are approximate "
                           "(within about 30 min). Alerts are shown exactly as issued by IMD / INCOIS. Always check "
                           "official warnings before going to sea."),
        "sea_error": "Could not load live sea conditions right now. Check your connection and INCOIS / IMD warnings.",
        "zones_header": "Fish-gathering zones today",
        "zones_intro": ("Official INCOIS Potential Fishing Zones near {harbour}: where shoaling fish such as sardine "
                        "and mackerel are likely to gather. Colour shows the sea at each zone right now."),
        "zone_label": "Zone {n}: ~{km} km {dir} of {harbour}",
        "zone_detail": "Nearest point GPS {lat} N, {lon} E  |  waves {wave} m  |  wind {wind} km/h",
        "zones_date": "INCOIS advisory of {date}. Zones are not per fish species; distance is to the nearest point of each zone.",
        "zones_old": ("This is the latest advisory available ({date}). INCOIS does not issue zones on cloudy days "
                      "or during the fishing ban."),
        "zones_none": ("No fishing zone advisory near {harbour} today. INCOIS does not issue zones on cloudy days "
                       "or during the fishing ban."),
        "zones_error": "Could not load fishing zones from INCOIS right now. Check the SAMUDRA app.",
        "zones_harbour": "Your harbour",
        "sky": {"clear": "Clear sky", "clear_night": "Clear sky", "partly": "Partly cloudy",
                "partly_night": "Partly cloudy", "cloudy": "Cloudy", "fog": "Fog / haze",
                "drizzle": "Drizzle", "rain": "Rain", "storm": "Thunderstorm"},
        "sky_detail": "{sky}, {cloud}% cloud",
        "offshore_label": "{km} km out to sea from {harbour}",
        "offshore_intro": "Weather at sea right now, straight out from {harbour}:",
        "map_distance_note": "Numbers on the map are distances from the harbour.",
        "footer": ("Species matched across both datasets: 6 of 21 in the species dictionary. Catch share reflects "
                   "each species' typical proportion of a district's total landings (2022-23 to 2024-25 average). "
                   "Price is a model trained on one real week of prices scaled by a documented seasonal assumption "
                   "- a prototype, not a market guarantee. Malayalam and Tamil text has not yet been reviewed by a "
                   "native speaker."),
        "seasons": {
            "winter": ("Winter", "Dec - Feb"),
            "summer": ("Summer", "Mar - May"),
            "monsoon": ("Monsoon", "Jun - Aug (trawling ban)"),
            "postmonsoon": ("Post-Monsoon", "Sep - Nov"),
        },
    },
    "ml": {
        "lang_name": "മലയാളം",
        "title": "പിടിത്ത പദ്ധതി",
        "brand_tag": "കേരള മത്സ്യബന്ധന സഹായി",
        "setup_header": "നിങ്ങളുടെ യാത്ര ആസൂത്രണം ചെയ്യുക",
        "sea_now": "ഇപ്പോഴത്തെ കടൽ",
        "subtitle": "മത്സ്യവില അറിയാനും നിങ്ങളുടെ പിടിത്ത പദ്ധതി കാണാനും ഭാഷ, സീസൺ, ജില്ല, ബോട്ട് ശേഷി എന്നിവ തിരഞ്ഞെടുക്കുക.",
        "legend_real": "യഥാർത്ഥം: പിടിത്ത വിവരം, കേരള ഫിഷറീസ് വകുപ്പ് 2022-25",
        "legend_pred": "മാതൃക പ്രവചനം: വില, കൃത്രിമ ഡാറ്റയിൽ പരിശീലിപ്പിച്ചത് (പ്രോട്ടോടൈപ്പ്, യഥാർത്ഥ വിപണി ചരിത്രമല്ല)",
        "step0": "നിങ്ങളുടെ ഭാഷ തിരഞ്ഞെടുക്കുക",
        "step1": "ഏത് സീസണിലാണ് നിങ്ങൾ മീൻപിടിക്കുന്നത്?",
        "step2": "നിങ്ങൾ ഏത് ജില്ലയിലാണ്?",
        "step3": "നിങ്ങളുടെ ബോട്ടിന്റെ ശേഷി (കി.ഗ്രാം, ഓരോ യാത്രയ്ക്കും)",
        "result_header": "വിപണി വില പ്രവചനം",
        "plan_header": "നിങ്ങളുടെ പിടിത്ത പദ്ധതി",
        "col_species": "മത്സ്യം", "col_price": "₹ / കി.ഗ്രാം", "col_halfkg": "₹ / അര കി.ഗ്രാം", "col_share": "പിടിത്ത വിഹിതം",
        "col_district": "ജില്ല",
        "plan_intro": "{district}യിലെ സാധാരണ മത്സ്യ ഇനങ്ങളും {season} വിലയും അടിസ്ഥാനമാക്കി, ഈ യാത്രയിൽ {kg} കി.ഗ്രാം പിടിച്ചാൽ:",
        "plan_total": "കണക്കാക്കിയ ആകെ മൂല്യം",
        "plan_detail": "സാധാരണ പിടിത്തത്തിന്റെ {share}%  |  ~{kg} കി.ഗ്രാം  |  ₹{price}/കി.ഗ്രാം",
        "all_seasons_header": "സീസൺ അനുസരിച്ചുള്ള വില (മികച്ച സീസൺ ഹൈലൈറ്റ് ചെയ്തിരിക്കുന്നു)",
        "district_compare_header": "ഒരു മത്സ്യത്തിന് ജില്ലകൾ താരതമ്യം ചെയ്യുക",
        "district_compare_pick": "ഒരു മത്സ്യം തിരഞ്ഞെടുക്കുക",
        "district_compare_col_share": "സാധാരണ പിടിത്ത വിഹിതം",
        "glossary_header": "മത്സ്യങ്ങളുടെ പേര് നിഘണ്ടു",
        "glossary_col_scientific": "ശാസ്ത്രീയ നാമം",
        "glossary_col_malayalam": "മലയാളം",
        "glossary_col_tamil": "തമിഴ്",
        "download_button": "ഈ പദ്ധതി ഡൗൺലോഡ് ചെയ്യുക",
        "sea_header": "തത്സമയ കടൽ സ്ഥിതി",
        "sea_point": "{harbour} തുറമുഖത്തു നിന്ന് ~12 കി.മീ കടലിൽ  |  പുതുക്കിയത് {time}  |  ഓരോ 15 മിനിറ്റിലും പുതുക്കുന്നു",
        "rating": {
            "calm": ("ശാന്തം", "കടലിൽ പോകാൻ അനുയോജ്യമായ സാഹചര്യം."),
            "caution": ("ജാഗ്രത", "ഇളകിയ കടൽ അല്ലെങ്കിൽ ശക്തമായ കാറ്റ്. ചെറിയ ബോട്ടുകൾ ശ്രദ്ധിക്കുക."),
            "rough": ("പ്രക്ഷുബ്ധം", "ഉയർന്ന തിരമാല, ശക്തമായ കാറ്റ് അല്ലെങ്കിൽ ഇടിമിന്നൽ. കടലിൽ പോകരുത്."),
        },
        "dir_from": "{d} ദിശയിൽ നിന്ന്", "dir_to": "{d} ദിശയിലേക്ക്",
        "m_wave": "തിരമാല ഉയരം", "m_wind": "കാറ്റ്", "m_gust": "ശക്തമായ കാറ്റ്", "m_swell": "ഓളം / ഇടവേള",
        "m_sst": "കടൽ താപനില", "m_rain": "ഇപ്പോഴത്തെ മഴ", "m_current": "കടൽ പ്രവാഹം",
        "m_next_high": "അടുത്ത വേലിയേറ്റം", "m_next_low": "അടുത്ത വേലിയിറക്കം",
        "alerts_header": "ഔദ്യോഗിക മുന്നറിയിപ്പുകൾ (IMD, INCOIS - NDMA സചേത് വഴി)",
        "alerts_none": "{district} ജില്ലയ്ക്ക് നിലവിൽ ഔദ്യോഗിക മുന്നറിയിപ്പുകളില്ല. പരിശോധിച്ചത് {time}.",
        "alerts_error": ("ഔദ്യോഗിക മുന്നറിയിപ്പ് സേവനം ലഭ്യമല്ല. കടലിൽ പോകുന്നതിന് മുമ്പ് SAMUDRA ആപ്പ് "
                         "അല്ലെങ്കിൽ incois.gov.in പരിശോധിക്കുക."),
        "alerts_loading": "ഔദ്യോഗിക മുന്നറിയിപ്പുകൾ പരിശോധിക്കുന്നു...",
        "alert_sea": "കടൽ മുന്നറിയിപ്പ്", "alert_weather": "കാലാവസ്ഥ മുന്നറിയിപ്പ്",
        "alert_meta": "നൽകിയത് {source}  |  {until} വരെ സാധുത",
        "forecast_header": "7 ദിവസത്തെ പ്രവചനം (ഓരോ ദിവസത്തെയും മോശം അവസ്ഥ)",
        "col_day": "ദിവസം", "col_rating": "കടൽ", "col_wave": "തിര (മീ)", "col_period": "ഇടവേള (സെ)",
        "col_wind": "കാറ്റ് (കി.മീ/മ)", "col_max_gust": "ശക്തമായ കാറ്റ് (കി.മീ/മ)",
        "col_current": "പ്രവാഹം (കി.മീ/മ)",
        "col_high_tide": "വേലിയേറ്റം", "col_low_tide": "വേലിയിറക്കം", "col_rain": "മഴ (മി.മീ)",
        "chart_waves": "തിര (മീ)", "chart_wind": "കാറ്റ് (കി.മീ/മ)", "chart_tide": "വേലി (മീ)",
        "chart_current": "പ്രവാഹം (കി.മീ/മ)",
        "thunder": "ഇടിമിന്നൽ",
        "sea_disclaimer": ("പ്രവചനം: Open-Meteo കാലാവസ്ഥ മാതൃക, ഔദ്യോഗിക മുന്നറിയിപ്പല്ല. വേലി സമയങ്ങൾ ഏകദേശമാണ് "
                           "(ഏകദേശം 30 മിനിറ്റ് വ്യത്യാസം). മുന്നറിയിപ്പുകൾ IMD / INCOIS നൽകിയതുപോലെ തന്നെ "
                           "കാണിക്കുന്നു. കടലിൽ പോകുന്നതിന് മുമ്പ് ഔദ്യോഗിക മുന്നറിയിപ്പുകൾ എപ്പോഴും പരിശോധിക്കുക."),
        "sea_error": "തത്സമയ കടൽ സ്ഥിതി ഇപ്പോൾ ലഭ്യമല്ല. INCOIS / IMD മുന്നറിയിപ്പുകൾ പരിശോധിക്കുക.",
        "zones_header": "ഇന്നത്തെ മത്സ്യ സാന്ദ്രത മേഖലകൾ",
        "zones_intro": ("{harbour} തുറമുഖത്തിന് സമീപമുള്ള INCOIS ഔദ്യോഗിക സാധ്യതാ മത്സ്യബന്ധന മേഖലകൾ: മത്തി, അയല പോലുള്ള "
                        "കൂട്ടമായി സഞ്ചരിക്കുന്ന മത്സ്യങ്ങൾ കൂടാൻ സാധ്യതയുള്ള ഇടങ്ങൾ. നിറം ഓരോ മേഖലയിലെയും ഇപ്പോഴത്തെ "
                        "കടൽ സ്ഥിതി കാണിക്കുന്നു."),
        "zone_label": "മേഖല {n}: {harbour} തുറമുഖത്തു നിന്ന് ~{km} കി.മീ {dir}",
        "zone_detail": "ഏറ്റവും അടുത്ത GPS {lat} N, {lon} E  |  തിര {wave} മീ  |  കാറ്റ് {wind} കി.മീ/മ",
        "zones_date": ("INCOIS മുന്നറിയിപ്പ് തീയതി {date}. മേഖലകൾ ഓരോ മത്സ്യ ഇനത്തിനും പ്രത്യേകമല്ല; ദൂരം ഓരോ "
                       "മേഖലയുടെയും ഏറ്റവും അടുത്ത ബിന്ദുവിലേക്കാണ്."),
        "zones_old": ("ലഭ്യമായ ഏറ്റവും പുതിയ മുന്നറിയിപ്പ് ഇതാണ് ({date}). മേഘാവൃതമായ ദിവസങ്ങളിലും ട്രോളിംഗ് "
                      "നിരോധന കാലത്തും INCOIS മേഖലകൾ നൽകാറില്ല."),
        "zones_none": ("ഇന്ന് {harbour} തുറമുഖത്തിന് സമീപം മത്സ്യബന്ധന മേഖല മുന്നറിയിപ്പില്ല. മേഘാവൃതമായ ദിവസങ്ങളിലും ട്രോളിംഗ് "
                       "നിരോധന കാലത്തും INCOIS മേഖലകൾ നൽകാറില്ല."),
        "zones_error": "INCOIS മത്സ്യബന്ധന മേഖലകൾ ഇപ്പോൾ ലഭ്യമല്ല. SAMUDRA ആപ്പ് പരിശോധിക്കുക.",
        "zones_harbour": "നിങ്ങളുടെ തുറമുഖം",
        "sky": {"clear": "തെളിഞ്ഞ ആകാശം", "clear_night": "തെളിഞ്ഞ ആകാശം", "partly": "ഭാഗികമായി മേഘാവൃതം",
                "partly_night": "ഭാഗികമായി മേഘാവൃതം", "cloudy": "മേഘാവൃതം", "fog": "മൂടൽമഞ്ഞ്",
                "drizzle": "ചാറ്റൽമഴ", "rain": "മഴ", "storm": "ഇടിമിന്നലോടു കൂടിയ മഴ"},
        "sky_detail": "{sky}, മേഘം {cloud}%",
        "offshore_label": "{harbour} തുറമുഖത്തു നിന്ന് കടലിലേക്ക് {km} കി.മീ",
        "offshore_intro": "{harbour} തുറമുഖത്തു നിന്ന് നേരെ കടലിലേക്ക്, ഇപ്പോഴത്തെ കാലാവസ്ഥ:",
        "map_distance_note": "മാപ്പിലെ സംഖ്യകൾ തുറമുഖത്തു നിന്നുള്ള ദൂരമാണ്.",
        "footer": ("രണ്ട് ഡാറ്റാസെറ്റുകളിലും പൊരുത്തപ്പെടുന്ന മത്സ്യങ്ങൾ: 21ൽ 6. പിടിത്ത വിഹിതം ഒരു ജില്ലയുടെ മൊത്തം "
                   "പിടിത്തത്തിന്റെ സാധാരണ അനുപാതത്തെ സൂചിപ്പിക്കുന്നു (2022-23 മുതൽ 2024-25 ശരാശരി). വില ഒരു യഥാർത്ഥ "
                   "ആഴ്ചയിലെ വിലയെ അടിസ്ഥാനമാക്കിയുള്ള ഒരു മാതൃകയാണ് - ഇത് ഒരു പ്രോട്ടോടൈപ്പ് ആണ്, വിപണി ഉറപ്പല്ല. "
                   "മലയാളം, തമിഴ് പരിഭാഷകൾ ഒരു മാതൃഭാഷക്കാരൻ ഇതുവരെ പരിശോധിച്ചിട്ടില്ല."),
        "seasons": {
            "winter": ("ശീതകാലം", "ഡിസംബർ - ഫെബ്രുവരി"),
            "summer": ("വേനൽക്കാലം", "മാർച്ച് - മേയ്"),
            "monsoon": ("മഴക്കാലം", "ജൂൺ - ഓഗസ്റ്റ് (ട്രോളിംഗ് നിരോധനം)"),
            "postmonsoon": ("മഴക്കാലാനന്തരം", "സെപ്റ്റംബർ - നവംബർ"),
        },
    },
    "ta": {
        "lang_name": "தமிழ்",
        "title": "மீன்பிடி திட்டம்",
        "brand_tag": "கேரள மீன்பிடி உதவியாளர்",
        "setup_header": "உங்கள் பயணத்தைத் திட்டமிடுங்கள்",
        "sea_now": "தற்போதைய கடல்",
        "subtitle": "மீன் விலைகளையும் உங்கள் மீன்பிடி திட்டத்தையும் காண மொழி, பருவம், மாவட்டம், படகு திறன் ஆகியவற்றைத் தேர்ந்தெடுக்கவும்.",
        "legend_real": "உண்மையானது: பிடிப்பு தரவு, கேரள மீன்வள துறை 2022-25",
        "legend_pred": "மாதிரி கணிப்பு: விலை, செயற்கை தரவில் பயிற்சி பெற்றது (முன்மாதிரி, உண்மையான சந்தை வரலாறு அல்ல)",
        "step0": "உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்",
        "step1": "நீங்கள் எந்த பருவத்தில் மீன் பிடிக்கிறீர்கள்?",
        "step2": "நீங்கள் எந்த மாவட்டத்தில் இருக்கிறீர்கள்?",
        "step3": "உங்கள் படகின் ஏற்றும் திறன் (கிலோ, ஒரு பயணத்திற்கு)",
        "result_header": "சந்தை விலை கணிப்பு",
        "plan_header": "உங்கள் மீன்பிடி திட்டம்",
        "col_species": "மீன் வகை", "col_price": "₹ / கிலோ", "col_halfkg": "₹ / அரை கிலோ", "col_share": "பிடிப்பு பங்கு",
        "col_district": "மாவட்டம்",
        "plan_intro": "{district} மாவட்டத்தின் வழக்கமான மீன் கலவையும் {season} விலையும் அடிப்படையாகக் கொண்டு, இந்த பயணத்தில் {kg} கிலோ பிடித்தால்:",
        "plan_total": "மதிப்பிடப்பட்ட மொத்த மதிப்பு",
        "plan_detail": "வழக்கமான பிடிப்பில் {share}%  |  ~{kg} கிலோ  |  ₹{price}/கிலோ",
        "all_seasons_header": "பருவத்தின் அடிப்படையில் விலை (சிறந்த பருவம் தனிப்படுத்தப்பட்டுள்ளது)",
        "district_compare_header": "ஒரு மீனுக்கு மாவட்டங்களை ஒப்பிடுக",
        "district_compare_pick": "ஒரு மீனைத் தேர்ந்தெடுக்கவும்",
        "district_compare_col_share": "வழக்கமான பிடிப்பு பங்கு",
        "glossary_header": "மீன் பெயர் அகராதி",
        "glossary_col_scientific": "அறிவியல் பெயர்",
        "glossary_col_malayalam": "மலையாளம்",
        "glossary_col_tamil": "தமிழ்",
        "download_button": "இந்த திட்டத்தை பதிவிறக்கவும்",
        "sea_header": "நேரடி கடல் நிலை",
        "sea_point": "{harbour} அருகே ~12 கி.மீ கடலில்  |  புதுப்பிப்பு {time}  |  ஒவ்வொரு 15 நிமிடமும் புதுப்பிக்கப்படும்",
        "rating": {
            "calm": ("அமைதி", "கடலுக்குச் செல்ல ஏற்ற நிலை."),
            "caution": ("எச்சரிக்கை", "கொந்தளிப்பான கடல் அல்லது பலத்த காற்று. சிறிய படகுகள் கவனம்."),
            "rough": ("கொந்தளிப்பு", "உயர் அலைகள், பலத்த காற்று அல்லது இடியுடன் மழை. கடலுக்குச் செல்ல வேண்டாம்."),
        },
        "dir_from": "{d} திசையிலிருந்து", "dir_to": "{d} திசை நோக்கி",
        "m_wave": "அலை உயரம்", "m_wind": "காற்று", "m_gust": "பலத்த காற்று", "m_swell": "அலை வீச்சு / இடைவெளி",
        "m_sst": "கடல் வெப்பநிலை", "m_rain": "தற்போதைய மழை", "m_current": "கடல் நீரோட்டம்",
        "m_next_high": "அடுத்த உயர் அலை", "m_next_low": "அடுத்த தாழ் அலை",
        "alerts_header": "அதிகாரப்பூர்வ எச்சரிக்கைகள் (IMD, INCOIS - NDMA சசேத் வழியாக)",
        "alerts_none": "{district} மாவட்டத்திற்கு தற்போது அதிகாரப்பூர்வ எச்சரிக்கைகள் இல்லை. சரிபார்த்தது {time}.",
        "alerts_error": ("அதிகாரப்பூர்வ எச்சரிக்கை சேவையை அணுக முடியவில்லை. கடலுக்குச் செல்லும் முன் SAMUDRA "
                         "செயலி அல்லது incois.gov.in ஐச் சரிபார்க்கவும்."),
        "alerts_loading": "அதிகாரப்பூர்வ எச்சரிக்கைகளைச் சரிபார்க்கிறது...",
        "alert_sea": "கடல் எச்சரிக்கை", "alert_weather": "வானிலை எச்சரிக்கை",
        "alert_meta": "வெளியிட்டது {source}  |  {until} வரை செல்லுபடியாகும்",
        "forecast_header": "7 நாள் முன்னறிவிப்பு (ஒவ்வொரு நாளின் மோசமான நிலை)",
        "col_day": "நாள்", "col_rating": "கடல்", "col_wave": "அலை (மீ)", "col_period": "இடைவெளி (வி)",
        "col_wind": "காற்று (கி.மீ/ம)", "col_max_gust": "பலத்த காற்று (கி.மீ/ம)",
        "col_current": "நீரோட்டம் (கி.மீ/ம)",
        "col_high_tide": "உயர் அலை", "col_low_tide": "தாழ் அலை", "col_rain": "மழை (மி.மீ)",
        "chart_waves": "அலை (மீ)", "chart_wind": "காற்று (கி.மீ/ம)", "chart_tide": "ஓதம் (மீ)",
        "chart_current": "நீரோட்டம் (கி.மீ/ம)",
        "thunder": "இடியுடன் மழை",
        "sea_disclaimer": ("முன்னறிவிப்பு: Open-Meteo வானிலை மாதிரி, அதிகாரப்பூர்வ எச்சரிக்கை அல்ல. ஓத நேரங்கள் "
                           "தோராயமானவை (சுமார் 30 நிமிடம்). எச்சரிக்கைகள் IMD / INCOIS வெளியிட்டபடியே "
                           "காட்டப்படுகின்றன. கடலுக்குச் செல்லும் முன் அதிகாரப்பூர்வ எச்சரிக்கைகளை எப்போதும் "
                           "சரிபார்க்கவும்."),
        "sea_error": "நேரடி கடல் நிலையை இப்போது ஏற்ற முடியவில்லை. INCOIS / IMD எச்சரிக்கைகளைச் சரிபார்க்கவும்.",
        "zones_header": "இன்றைய மீன் கூடும் பகுதிகள்",
        "zones_intro": ("{harbour} அருகே INCOIS அதிகாரப்பூர்வ சாத்தியமான மீன்பிடி மண்டலங்கள்: மத்தி, கானாங்கெளுத்தி "
                        "போன்ற கூட்டமாக வாழும் மீன்கள் கூடக்கூடிய இடங்கள். நிறம் ஒவ்வொரு மண்டலத்திலும் தற்போதைய "
                        "கடல் நிலையைக் காட்டுகிறது."),
        "zone_label": "மண்டலம் {n}: {harbour} துறைமுகத்திலிருந்து ~{km} கி.மீ {dir}",
        "zone_detail": "அருகிலுள்ள GPS {lat} N, {lon} E  |  அலை {wave} மீ  |  காற்று {wind} கி.மீ/ம",
        "zones_date": ("INCOIS அறிவிப்பு தேதி {date}. மண்டலங்கள் மீன் வகை வாரியாக இல்லை; தூரம் ஒவ்வொரு மண்டலத்தின் "
                       "அருகிலுள்ள புள்ளி வரை."),
        "zones_old": ("கிடைக்கும் சமீபத்திய அறிவிப்பு இது ({date}). மேகமூட்டமான நாட்களிலும் மீன்பிடி தடைக் காலத்திலும் "
                      "INCOIS மண்டலங்களை வெளியிடுவதில்லை."),
        "zones_none": ("இன்று {harbour} அருகே மீன்பிடி மண்டல அறிவிப்பு இல்லை. மேகமூட்டமான நாட்களிலும் மீன்பிடி தடைக் "
                       "காலத்திலும் INCOIS மண்டலங்களை வெளியிடுவதில்லை."),
        "zones_error": "INCOIS மீன்பிடி மண்டலங்களை இப்போது ஏற்ற முடியவில்லை. SAMUDRA செயலியைச் சரிபார்க்கவும்.",
        "zones_harbour": "உங்கள் துறைமுகம்",
        "sky": {"clear": "தெளிவான வானம்", "clear_night": "தெளிவான வானம்", "partly": "ஓரளவு மேகமூட்டம்",
                "partly_night": "ஓரளவு மேகமூட்டம்", "cloudy": "மேகமூட்டம்", "fog": "பனிமூட்டம்",
                "drizzle": "தூறல்", "rain": "மழை", "storm": "இடியுடன் கூடிய மழை"},
        "sky_detail": "{sky}, மேகம் {cloud}%",
        "offshore_label": "{harbour} துறைமுகத்திலிருந்து கடலுக்குள் {km} கி.மீ",
        "offshore_intro": "{harbour} துறைமுகத்திலிருந்து நேராகக் கடலில், தற்போதைய வானிலை:",
        "map_distance_note": "வரைபடத்தில் உள்ள எண்கள் துறைமுகத்திலிருந்து உள்ள தூரம்.",
        "footer": ("இரு தரவுத்தொகுப்புகளிலும் பொருந்தும் மீன் வகைகள்: 21ல் 6. பிடிப்பு பங்கு ஒரு மாவட்டத்தின் மொத்த "
                   "பிடிப்பில் ஒவ்வொரு மீன் வகையின் வழக்கமான விகிதத்தைக் குறிக்கிறது (2022-23 முதல் 2024-25 சராசரி). "
                   "விலை ஒரு உண்மையான வார விலையை அடிப்படையாகக் கொண்ட ஒரு மாதிரி - இது ஒரு முன்மாதிரி, சந்தை "
                   "உத்தரவாதம் அல்ல. தமிழ், மலையாள மொழிபெயர்ப்புகள் இன்னும் ஒரு சொந்த மொழி பேசுபவரால் "
                   "சரிபார்க்கப்படவில்லை."),
        "seasons": {
            "winter": ("குளிர்காலம்", "டிசம்பர் - பிப்ரவரி"),
            "summer": ("கோடைக்காலம்", "மார்ச் - மே"),
            "monsoon": ("பருவமழைக் காலம்", "ஜூன் - ஆகஸ்ட் (இழுவலை தடை)"),
            "postmonsoon": ("பருவமழைக்குப் பின்", "செப்டம்பர் - நவம்பர்"),
        },
    },
}


@st.cache_data
def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        frontend_data = json.load(f)
    with open(SPECIES_PATH, encoding="utf-8") as f:
        species_dict = json.load(f)
    return frontend_data, species_dict


def species_label(species_dict, key, lang):
    entry = species_dict.get(key)
    if not entry:
        return key.replace("_", " ")
    if lang == "ml":
        return entry.get("malayalam") or entry["english"]
    if lang == "ta":
        return entry.get("tamil") or entry["english"]
    return entry["english"]


def district_label(data, code, lang):
    native = DISTRICT_NATIVE.get(code, {})
    if lang != "en" and native.get(lang):
        return f"{native[lang]} ({code})"
    return f"{data['districts'][code]['name']} ({code})"


def harbour_label(name, lang):
    return HARBOUR_NATIVE.get(name, {}).get(lang) or name


def season_avg_price(species_info, season_key):
    months = SEASON_MONTHS[season_key]
    values = [species_info["monthly_prices"][MONTH_NAMES[m]]["price_inr_per_kg"] for m in months]
    return sum(values) / len(values)


def option_grid(options, selected_key, session_key, columns=4):
    """Renders a row of card-style buttons; returns the newly selected key."""
    # one st.columns row per line, so phones (where columns stack) keep the reading order
    result = selected_key
    for i, (key, label) in enumerate(options):
        if i % columns == 0:
            cols = st.columns(columns)
        with cols[i % columns]:
            is_selected = key == selected_key
            if st.button(label, key=f"{session_key}_{key}", type="primary" if is_selected else "secondary",
                         width="stretch"):
                result = key
    return result


def section_head(title, sub=None, live=False, kicker=None, anchor_id=None):
    parts = []
    if anchor_id:
        parts.append(f'<div class="mf-anchor" id="{anchor_id}"></div>')
    if kicker:
        parts.append(f'<div class="mf-kicker">{html.escape(kicker)}</div>')
    parts.append(f'<div class="mf-h2">{html.escape(title)}</div>')
    if sub and live:
        parts.append(f'<div class="mf-live"><i></i><span>{html.escape(sub)}</span></div>')
    elif sub:
        parts.append(f'<p class="mf-sub">{html.escape(sub)}</p>')
    st.markdown("".join(parts), unsafe_allow_html=True)


def field_label(text, help_text=None):
    help_html = f'<div class="mf-help">{html.escape(help_text)}</div>' if help_text else ""
    st.markdown(f'<div class="mf-field">{html.escape(text)}</div>{help_html}', unsafe_allow_html=True)


def sub_label(text):
    st.markdown(f'<div class="sub-label">{html.escape(text)}</div>', unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner=False)
def cached_sea_conditions(district_code):
    return fetch_sea_conditions(district_code)


@st.cache_data(ttl=600, show_spinner=False)
def cached_official_alerts():
    return fetch_kerala_alerts(), datetime.now(IST)


def _fmt(value, fmt="{:.1f}"):
    return "-" if value is None else fmt.format(value)


def _dir(t, key, degrees):
    return t[key].format(d=compass(degrees)) if degrees is not None else None


def official_alerts_block(district_code, district_name, lang):
    t = UI[lang]
    sub_label(t["alerts_header"])
    try:
        with st.spinner(t["alerts_loading"]):
            all_alerts, checked_at = cached_official_alerts()
    except (requests.RequestException, ET.ParseError) as e:
        live_data_failed("official alerts", e, t["alerts_error"])
        return

    active = alerts_for_district(all_alerts, district_code)
    if not active:
        none_text = t["alerts_none"].format(district=district_name, time=checked_at.strftime("%H:%M"))
        st.markdown(f'<div class="alert-card alert-none">{html.escape(none_text)}</div>',
                    unsafe_allow_html=True)
        return

    for a in active:
        # Alert text is shown exactly as issued. Tamil falls back to English since
        # the Kerala feed only carries English and Malayalam.
        headline = a["headlines"].get(lang) or a["headlines"].get("en") or a["event"]
        kind = t["alert_sea"] if a["is_sea"] else t["alert_weather"]
        css = "alert-sea" if a["is_sea"] or a["severity"] == "Extreme" else "alert-weather"
        until = a["expires"].astimezone(IST).strftime("%H:%M, %d %b") if a["expires"] else "-"
        meta = t["alert_meta"].format(source=a["source"], until=until)
        st.markdown(
            f'<div class="alert-card {css}">'
            f'<div class="alert-kind">{kind}  |  {html.escape(a["event"])}  |  {html.escape(a["severity"])}</div>'
            f'<div class="alert-headline">{html.escape(headline)}</div>'
            f'<div class="alert-meta">{html.escape(meta)}</div>'
            f'</div>', unsafe_allow_html=True)


@st.fragment(run_every="15m")
def live_sea_panel(district_code, district_name, lang):
    """Official alerts + live sea state for the district's offshore point. Re-runs
    on its own every 15 minutes without reloading the rest of the page."""
    with st.container(key="sec_sea"):
        _live_sea_body(district_code, district_name, lang)


def _num(value, fmt="{:.1f}", unit=""):
    """A reading for a metric tile. The number counts up on first reveal and always
    ends on exactly this formatted text."""
    unit_html = f"<small> {html.escape(unit)}</small>" if unit else ""
    text = _fmt(value, fmt)
    if value is None:
        return text + unit_html
    dec = int(fmt.split(".")[1].rstrip("f}")) if "." in fmt else 0
    return f'<span data-count="{float(value):.{dec}f}" data-dec="{dec}">{text}</span>{unit_html}'


def _metric_tile(label, value_html, delta=None, delay=0):
    delta_html = f'<div class="mf-md">{html.escape(delta)}</div>' if delta else ""
    return (f'<div class="mf-metric rv" style="--d:{delay}ms"><div class="mf-ml">{html.escape(label)}</div>'
            f'<div class="mf-mv">{value_html}</div>{delta_html}</div>')


def _live_sea_body(district_code, district_name, lang):
    t = UI[lang]
    kicker = f'02 · {t["n_sea"]}'
    try:
        sea = cached_sea_conditions(district_code)
    except (requests.RequestException, KeyError, ValueError) as e:
        section_head(t["sea_h"], t["sea_header"], live=True, kicker=kicker, anchor_id="mf-sea")
        official_alerts_block(district_code, district_name, lang)
        live_data_failed(f"sea conditions {district_code}", e, t["sea_error"])
        return

    now = sea["current"]
    rating = rate_conditions(now)
    label, advice = t["rating"][rating]
    updated = datetime.fromisoformat(now["time"]).strftime("%H:%M")
    section_head(t["sea_h"], f'{t["sea_header"]}  |  ' + t["sea_point"].format(
        harbour=harbour_label(sea["harbour"], lang), time=updated), live=True, kicker=kicker, anchor_id="mf-sea")
    # official warnings come first and are never animated
    official_alerts_block(district_code, district_name, lang)

    upcoming_tides = [x for x in tide_turns(sea["hourly"]) if x["time"] >= now["time"]]
    next_high = next((x for x in upcoming_tides if x["kind"] == "high"), None)
    next_low = next((x for x in upcoming_tides if x["kind"] == "low"), None)

    def tide_text(turn):
        if not turn:
            return "-"
        when = datetime.fromisoformat(turn["time"])
        day = "" if turn["time"][:10] == now["time"][:10] else when.strftime(" %d/%m")
        return f'{when.strftime("%H:%M")}{day}'

    swell = (f'{_fmt(now.get("swell_wave_height"))}<small> m /</small> '
             f'{_fmt(now.get("swell_wave_period"), "{:.0f}")}<small> s</small>')
    tiles = [
        (t["m_wave"], _num(now.get("wave_height"), unit="m"), _dir(t, "dir_from", now.get("wave_direction"))),
        (t["m_wind"], _num(now.get("wind_speed_10m"), "{:.0f}", "km/h"), _dir(t, "dir_from", now.get("wind_direction_10m"))),
        (t["m_gust"], _num(now.get("wind_gusts_10m"), "{:.0f}", "km/h"), None),
        (t["m_swell"], swell, _dir(t, "dir_from", now.get("swell_wave_direction"))),
        (t["m_current"], _num(now.get("ocean_current_velocity"), unit="km/h"), _dir(t, "dir_to", now.get("ocean_current_direction"))),
        (t["m_sst"], _num(now.get("sea_surface_temperature"), unit="°C"), None),
        (t["m_next_high"], html.escape(tide_text(next_high)), None),
        (t["m_next_low"], html.escape(tide_text(next_low)), None),
        (t["m_rain"], _num(now.get("precipitation"), unit="mm"), None),
    ]
    tiles_html = "".join(_metric_tile(lbl, val, delta, i * 60) for i, (lbl, val, delta) in enumerate(tiles))
    status_html = (f'<div class="mf-status {rating}"><div class="mf-status-l">{html.escape(t["sea_now"])}</div>'
                   f'<div class="mf-status-word">{html.escape(label)}</div>'
                   f'<div class="mf-status-adv">{html.escape(advice)}</div></div>')
    st.markdown(f'<div class="mf-sea-grid">{status_html}<div class="mf-metrics">{tiles_html}</div></div>',
                unsafe_allow_html=True)

    # 7-day outlook: one card per day (worst values of that day), full table on demand
    sub_label(t["forecast_header"])
    forecast_rows, day_cards = [], []
    for i, day in enumerate(daily_summary(sea["hourly"])):
        sea_label = t["rating"][day["rating"]][0]
        if day["thunderstorm"]:
            sea_label += f' ({t["thunder"]})'
        day_fmt = "%a %d %b" if lang == "en" else "%d/%m"
        row = {
            t["col_day"]: datetime.fromisoformat(day["date"]).strftime(day_fmt),
            t["col_rating"]: sea_label,
            t["col_wave"]: f'{_fmt(day["max_wave_height"])} {compass(day["wave_direction"])}',
            t["col_period"]: _fmt(day["wave_period"], "{:.0f}"),
            t["col_wind"]: f'{_fmt(day["max_wind_speed"], "{:.0f}")} {compass(day["wind_direction"])}',
            t["col_max_gust"]: _fmt(day["max_wind_gusts"], "{:.0f}"),
            t["col_current"]: f'{_fmt(day["max_current"])} {compass(day["current_direction"])}',
            t["col_high_tide"]: ", ".join(day["high_tides"]) or "-",
            t["col_low_tide"]: ", ".join(day["low_tides"]) or "-",
            t["col_rain"]: _fmt(day["total_rain_mm"]),
        }
        forecast_rows.append(row)
        facts = "".join(f'<span>{html.escape(k)} <span class="v">{html.escape(row[k])}</span></span>'
                        for k in (t["col_wave"], t["col_wind"], t["col_max_gust"], t["col_rain"]))
        day_cards.append(f'<div class="mf-day rv" style="--d:{i * 60}ms"><b>{html.escape(row[t["col_day"]])}</b>'
                         f'<span class="mf-pill {day["rating"]}">{html.escape(sea_label)}</span>{facts}</div>')
    st.markdown(f'<div class="mf-days">{"".join(day_cards)}</div>', unsafe_allow_html=True)
    with st.expander(t["show_cols"]):
        st.dataframe(forecast_rows, hide_index=True, width="stretch")

    # Hourly charts from the current hour onward
    sub_label(t["hourly_h"])
    hourly = pd.DataFrame(sea["hourly"])
    hourly["time"] = pd.to_datetime(hourly["time"])
    hourly = hourly[hourly["time"] >= pd.to_datetime(now["time"]).floor("h")].set_index("time")
    with st.container(key="mf_chartcard"):
        tab_waves, tab_wind, tab_tide, tab_current = st.tabs(
            [t["chart_waves"], t["chart_wind"], t["chart_tide"], t["chart_current"]])
        with tab_waves:
            st.line_chart(hourly[["wave_height", "swell_wave_height"]].rename(
                columns={"wave_height": t["m_wave"], "swell_wave_height": t["m_swell"].split(" /")[0]}),
                color=[TOKENS["ocean"], TOKENS["foam"]], height=220)
        with tab_wind:
            st.line_chart(hourly[["wind_speed_10m", "wind_gusts_10m"]].rename(
                columns={"wind_speed_10m": t["m_wind"], "wind_gusts_10m": t["m_gust"]}),
                color=[TOKENS["ocean"], TOKENS["caution"]], height=220)
        with tab_tide:
            st.line_chart(hourly[["sea_level_height_msl"]].rename(columns={"sea_level_height_msl": t["chart_tide"]}),
                          color=[TOKENS["teal"]], height=220)
        with tab_current:
            st.line_chart(hourly[["ocean_current_velocity"]].rename(columns={"ocean_current_velocity": t["chart_current"]}),
                          color=[TOKENS["ocean"]], height=220)

    st.caption(t["sea_disclaimer"])


@st.cache_data(ttl=3600, show_spinner=False)
def cached_pfz():
    return fetch_kerala_pfz()


@st.cache_data(ttl=900, show_spinner=False)
def cached_zone_conditions(points):
    return zone_conditions(list(points))


RATING_RGB = {k: hex_rgb(TOKENS[k]) for k in ("calm", "caution", "rough")}

# Weather pictures for the map: a white badge with the sky drawn inside (64 x 64 SVG).
_SUN = ('<circle cx="32" cy="32" r="9" fill="#F5B82E"/>'
        '<g stroke="#F5B82E" stroke-width="3" stroke-linecap="round">'
        '<path d="M32 15v5M32 44v5M15 32h5M44 32h5M20 20l3.5 3.5M40.5 40.5L44 44M20 44l3.5-3.5M40.5 23.5L44 20"/></g>')
_MOON = '<path d="M38 18a14 14 0 1 0 8 25a11 11 0 0 1-8-25z" fill="#8A9BB5"/>'
_SMALL_SUN = ('<circle cx="24" cy="25" r="7" fill="#F5B82E"/><g stroke="#F5B82E" stroke-width="2.5" '
              'stroke-linecap="round"><path d="M24 12v3M11 25h3M15 16l2 2M33 16l-2 2"/></g>')
_SMALL_MOON = '<path d="M27 15a9 9 0 1 0 5 16a7 7 0 0 1-5-16z" fill="#8A9BB5"/>'


def _cloud(fill="#C9D6E6", y=0):
    return (f'<path transform="translate(0 {y})" d="M20 42a8 8 0 0 1 1-16a11 11 0 0 1 21-2a9 9 0 0 1 2 18z" '
            f'fill="{fill}" stroke="#FFFFFF" stroke-width="1.5"/>')


_RAIN = '<g stroke="#1E78D6" stroke-width="3" stroke-linecap="round"><path d="M24 44l-2 6M32 44l-2 6M40 44l-2 6"/></g>'
_DRIZZLE = ('<g fill="#1E78D6"><circle cx="24" cy="48" r="1.8"/><circle cx="32" cy="50" r="1.8"/>'
            '<circle cx="40" cy="48" r="1.8"/></g>')
_BOLT = '<path d="M33 40l-6 9h5l-3 8l9-11h-5l3-6z" fill="#F5B82E"/>'
_FOG = '<g stroke="#8A9BB5" stroke-width="3" stroke-linecap="round"><path d="M17 26h30M14 33h36M19 40h26"/></g>'

SKY_GLYPHS = {
    "clear": _SUN, "clear_night": _MOON,
    "partly": _SMALL_SUN + _cloud(y=4), "partly_night": _SMALL_MOON + _cloud(y=4),
    "cloudy": _cloud("#AFC0D4"), "fog": _FOG,
    "drizzle": _cloud("#AFC0D4", -4) + _DRIZZLE, "rain": _cloud("#93A7BF", -4) + _RAIN,
    "storm": _cloud("#6E819A", -6) + _BOLT,
}


def _sky_svg(kind, size=64):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true">'
            '<circle cx="32" cy="32" r="30" fill="#FFFFFF" stroke="#DCE8F4" stroke-width="2"/>'
            f'{SKY_GLYPHS.get(kind, _cloud())}</svg>')


def _sky_icon(kind):
    svg = _sky_svg(kind)
    url = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    return {"url": url, "width": 64, "height": 64, "anchorY": 64}


def _sky_text(reading, t):
    kind = sky_kind(reading.get("weather_code"), reading.get("is_day", 1))
    if kind is None:
        return kind, ""
    return kind, t["sky_detail"].format(sky=t["sky"][kind], cloud=_fmt(reading.get("cloud_cover"), "{:.0f}"))


def _harbour_layer(h_lat, h_lon, harbour, t):
    return pdk.Layer("ScatterplotLayer", [{"lon": h_lon, "lat": h_lat, "label": t["zones_harbour"],
                                           "detail": harbour, "status": "", "sky": ""}],
                     get_position=["lon", "lat"], get_fill_color=hex_rgb(TOKENS["foam"]),
                     get_line_color=hex_rgb(TOKENS["deep"]), stroked=True, line_width_min_pixels=3, get_radius=1800,
                     radius_min_pixels=7, pickable=True)


def _sky_layer(rows, lon_key, lat_key):
    return pdk.Layer("IconLayer", rows, get_icon="icon", get_position=[lon_key, lat_key],
                     get_size=38, size_units="pixels", get_pixel_offset=[0, -8], pickable=True)


def _km_layer(rows, lon_key, lat_key, offset=(0, 0)):
    # distance badges ("42 km"); map text stays ASCII so it renders in every language
    return pdk.Layer("TextLayer", rows, get_position=[lon_key, lat_key], get_text="km_text", get_size=13,
                     get_color=[232, 243, 247], font_weight=700, background=True,
                     get_background_color=hex_rgb(TOKENS["deep"]) + [235], background_padding=[6, 3, 6, 3],
                     get_border_color=hex_rgb(TOKENS["foam"]) + [140], get_border_width=1, get_pixel_offset=list(offset))


def _route_color():
    return hex_rgb(TOKENS["foam"]) + [130]


def _zones_map(layers, view):
    st.pydeck_chart(pdk.Deck(
        layers=layers, initial_view_state=view, map_style="dark",
        tooltip={"html": "<b>{label}</b><br/>{status}<br/>{sky}<br/>{detail}",
                 "style": {"backgroundColor": TOKENS["deep"], "color": "#E8F3F7", "fontSize": "12px",
                           "border": "1px solid rgba(72,214,200,0.4)", "borderRadius": "10px",
                           "boxShadow": "0 12px 30px -12px rgba(0,0,0,0.6)"}},
    ), height=440)


def _zone_cards(rows, t):
    cards = ""
    for i, row in enumerate(rows):
        detail = "  |  ".join(x for x in (row["sky"], row["detail"]) if x)
        cards += (
            f'<div class="mf-zcard rv" style="--d:{i * 80}ms">{_sky_svg(row["kind"], 40)}'
            f'<div><b>{html.escape(row["label"])}</b><div class="d">{html.escape(detail)}</div></div>'
            f'<div class="st" style="color:rgb({",".join(map(str, row["color"]))})">{html.escape(row["status"])}</div></div>')
    return f'<div class="mf-zcards">{cards}</div>'


def _zones_layout(layers, view, rows, t, intro=None):
    """Map on the left, legend under it, one card per zone or offshore point on the right."""
    map_col, card_col = st.columns([1.7, 1], gap="medium")
    with map_col:
        _zones_map(layers, view)
        legend = "".join(
            f'<span><span class="legend-dot" style="background:rgb({",".join(map(str, RATING_RGB[k]))})"></span>'
            f'{t["rating"][k][0]}</span>' for k in ["calm", "caution", "rough"])
        legend += f'<span>{html.escape(t["map_distance_note"])}</span>'
        st.markdown(f'<div class="map-legend">{legend}</div>', unsafe_allow_html=True)
    with card_col:
        intro_html = f'<div class="mf-zintro">{html.escape(intro)}</div>' if intro else ""
        st.markdown(intro_html + _zone_cards(rows, t), unsafe_allow_html=True)


@st.fragment(run_every="15m")
def fishing_zones_panel(district_code, lang):
    """Official INCOIS fishing zones near the district harbour, on a map, coloured
    by the sea conditions at each zone right now, with the weather and distance."""
    with st.container(key="sec_zones"):
        _fishing_zones_body(district_code, lang)


def _offshore_weather(district_code, harbour, h_lat, h_lon, t):
    """No advisory for this coast today: show the weather at points straight out to sea."""
    points = offshore_points(district_code)
    readings = cached_zone_conditions(tuple(p["point"] for p in points))
    rows = []
    for p, r in zip(points, readings):
        kind, sky = _sky_text(r, t)
        rows.append({
            "lat": p["point"][0], "lon": p["point"][1], "km_text": f'{p["km"]} km', "kind": kind,
            "icon": _sky_icon(kind), "color": RATING_RGB[r["rating"]], "status": t["rating"][r["rating"]][0],
            "label": t["offshore_label"].format(km=p["km"], harbour=harbour), "sky": sky,
            "detail": t["zone_detail"].format(lat=f'{p["point"][0]:.3f}', lon=f'{p["point"][1]:.3f}',
                                              wave=_fmt(r.get("wave_height")),
                                              wind=_fmt(r.get("wind_speed_10m"), "{:.0f}")),
        })
    far = rows[-1]
    layers = [
        pdk.Layer("LineLayer", [{"h_lon": h_lon, "h_lat": h_lat, "lon": far["lon"], "lat": far["lat"]}],
                  get_source_position=["h_lon", "h_lat"], get_target_position=["lon", "lat"],
                  get_color=_route_color(), get_width=2),
        pdk.Layer("ScatterplotLayer", rows, get_position=["lon", "lat"], get_fill_color="color",
                  get_line_color=[255, 255, 255], stroked=True, line_width_min_pixels=2,
                  radius_min_pixels=6, get_radius=1500, pickable=True),
        _km_layer(rows, "lon", "lat", offset=(0, 18)),
        _sky_layer(rows, "lon", "lat"),
        _harbour_layer(h_lat, h_lon, harbour, t),
    ]
    view = pdk.ViewState(latitude=(h_lat + far["lat"]) / 2, longitude=(h_lon + far["lon"]) / 2, zoom=8)
    _zones_layout(layers, view, rows, t, intro=t["offshore_intro"].format(harbour=harbour))


def _fishing_zones_body(district_code, lang):
    t = UI[lang]
    harbour_en, h_lat, h_lon = DISTRICT_HARBOURS[district_code]
    harbour = harbour_label(harbour_en, lang)
    section_head(t["zones_h"], t["zones_intro"].format(harbour=harbour), kicker=f'03 · {t["n_zones"]}',
                 anchor_id="mf-zones")
    try:
        pfz = cached_pfz()
        zones = zones_near_district(pfz, district_code)
        readings = cached_zone_conditions(tuple(z["mid"] for z in zones))
    except (requests.RequestException, KeyError, ValueError) as e:
        live_data_failed(f"fishing zones {district_code}", e, t["zones_error"])
        return

    if not zones:
        st.markdown(f'<div class="mf-note">{html.escape(t["zones_none"].format(harbour=harbour))}</div>',
                    unsafe_allow_html=True)
        try:
            _offshore_weather(district_code, harbour, h_lat, h_lon, t)
        except (requests.RequestException, KeyError, ValueError) as e:
            live_data_failed(f"offshore weather {district_code}", e, t["sea_error"])
        return

    rows = []
    for n, (z, r) in enumerate(zip(zones, readings), start=1):
        kind, sky = _sky_text(r, t)
        label = t["zone_label"].format(n=n, km=round(z["nearest_km"]), dir=compass(z["bearing"]), harbour=harbour)
        detail = t["zone_detail"].format(
            lat=f'{z["nearest_point"][0]:.3f}', lon=f'{z["nearest_point"][1]:.3f}',
            wave=_fmt(r.get("wave_height")), wind=_fmt(r.get("wind_speed_10m"), "{:.0f}"))
        rows.append({
            "n": str(n), "path": z["path"], "mid_lon": z["mid"][1], "mid_lat": z["mid"][0],
            "near_lon": z["nearest_point"][1], "near_lat": z["nearest_point"][0],
            "h_lon": h_lon, "h_lat": h_lat,
            "line_lon": (h_lon + z["nearest_point"][1]) / 2, "line_lat": (h_lat + z["nearest_point"][0]) / 2,
            "km_text": f'{n}: {round(z["nearest_km"])} km', "icon": _sky_icon(kind), "kind": kind,
            "color": RATING_RGB[r["rating"]], "rating": r["rating"],
            "label": label, "detail": detail, "sky": sky, "status": t["rating"][r["rating"]][0],
        })

    layers = [
        # route from harbour to the nearest point of each zone, with its distance halfway along
        pdk.Layer("LineLayer", rows, get_source_position=["h_lon", "h_lat"],
                  get_target_position=["near_lon", "near_lat"], get_color=_route_color(), get_width=1.5),
        pdk.Layer("PathLayer", rows, get_path="path", get_color="color", width_min_pixels=5,
                  pickable=True, cap_rounded=True, joint_rounded=True),
        _km_layer(rows, "line_lon", "line_lat"),
        _sky_layer(rows, "mid_lon", "mid_lat"),
        _harbour_layer(h_lat, h_lon, harbour, t),
    ]
    all_lats = [p[1] for row in rows for p in row["path"]] + [h_lat]
    all_lons = [p[0] for row in rows for p in row["path"]] + [h_lon]
    view = pdk.ViewState(latitude=(min(all_lats) + max(all_lats)) / 2,
                         longitude=(min(all_lons) + max(all_lons)) / 2, zoom=7.6)
    _zones_layout(layers, view, rows, t)

    adv_date = pfz["date"]
    if adv_date and (datetime.now(IST).date() - adv_date).days > 2:
        st.caption(t["zones_old"].format(date=adv_date.strftime("%d %b %Y")))
    else:
        st.caption(t["zones_date"].format(date=adv_date.strftime("%d %b %Y") if adv_date else "-"))


def _keep_lang():
    # clicking the active language would clear the control; keep the current one instead
    if st.session_state.lang_picker is None:
        st.session_state.lang_picker = st.session_state.lang
    else:
        st.session_state.lang = st.session_state.lang_picker


def _nav_html(t, lang):
    links = "".join(f'<a href="#{aid}" data-mf-link="{aid}">{html.escape(t[key])}</a>' for aid, key, _ in SECTION_ANCHORS)
    return (
        f'<div class="mf-navrow mf-l-{lang}">'
        f'<a class="mf-brand" href="#mf-home"><span class="mf-mark">{BRAND_MARK}</span>'
        f'<span class="mf-bname">{html.escape(t["brand"])}<small>{html.escape(t["brand_tag"])}</small></span></a>'
        f'<nav class="mf-links" aria-label="{html.escape(t["menu"])}">{links}</nav>'
        f'<details class="mf-menu"><summary aria-label="{html.escape(t["menu"])}">{MENU_ICON}</summary>'
        f'<div class="mf-drawer">{links}</div></details>'
        f'</div>'
    )


def _hero_html(t):
    facts = (f'<div><b>IMD · INCOIS</b>{html.escape(t["fact1"])}</div>'
             f'<div><b>15 min</b>{html.escape(t["fact2"])}</div>'
             f'<div><b>2022-25</b>{html.escape(t["fact3"])}</div>')
    pills = (f'<span class="mf-hpill"><i style="background:{TOKENS["calm"]}"></i>{html.escape(t["legend_real"])}</span>'
             f'<span class="mf-hpill"><i style="background:{TOKENS["caution"]}"></i>{html.escape(t["legend_pred"])}</span>')
    return (
        f'<section class="mf-hero" id="mf-home">{HERO_LAYERS}<div class="mf-hero-copy">'
        f'<div class="mf-eyebrow rv">{html.escape(t["hero_eyebrow"])}</div>'
        f'<div class="mf-h1 rv" style="--d:80ms">{html.escape(t["hero_h1"])}</div>'
        f'<p class="mf-lead rv" style="--d:160ms">{html.escape(t["hero_lead"])}</p>'
        f'<div class="mf-ctas rv" style="--d:240ms">'
        f'<a class="mf-btn mf-btn-primary" href="#mf-plan">{html.escape(t["cta_plan"])}</a>'
        f'<a class="mf-btn mf-btn-ghost" href="#mf-sea">{html.escape(t["cta_sea"])}</a></div>'
        f'<div class="mf-facts rv" style="--d:320ms">{facts}</div>'
        f'<div class="mf-hpills rv" style="--d:400ms">{pills}</div>'
        f'</div></section>'
    )


def _sea_rating_now(district_code):
    """Rating for the trip summary; uses the same cached reading as the sea panel."""
    try:
        return rate_conditions(cached_sea_conditions(district_code)["current"])
    except (requests.RequestException, KeyError, ValueError):
        return None


def main():
    st.set_page_config(page_title="Marine Fishing AI · Catch Plan", page_icon=":material/sailing:", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.html(SCRIPT, unsafe_allow_javascript=True)
    data, species_dict = load_data()
    for code, extra in UI_EXTRA.items():
        for key, value in extra.items():
            UI[code].setdefault(key, value)

    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "season" not in st.session_state:
        st.session_state.season = "monsoon"
    if "district" not in st.session_state:
        st.session_state.district = "EKM"

    # Top bar: brand + section links + language switch (sticky)
    with st.container(key="mf_nav"):
        nav_col, lang_col = st.columns([5, 2], vertical_alignment="center")
        with lang_col:
            st.segmented_control(
                UI[st.session_state.lang]["step0"], list(UI), format_func=lambda c: UI[c]["lang_name"],
                default=st.session_state.lang, key="lang_picker", on_change=_keep_lang,
                label_visibility="collapsed", width="stretch",
            )
        lang = st.session_state.lang
        t = UI[lang]
        with nav_col:
            st.markdown(_nav_html(t, lang), unsafe_allow_html=True)

    st.markdown(_hero_html(t), unsafe_allow_html=True)

    # Trip setup: season, district, boat capacity, with a live summary beside it
    with st.container(key="sec_setup"):
        section_head(t["plan_h"], kicker=f'01 · {t["n_plan"]}', anchor_id="mf-plan")
        form_col, summary_col = st.columns([1.55, 1], gap="large")
        with form_col:
            field_label(t["step1"])
            season_options = [(k, f"{v[0]}\n{v[1]}") for k, v in t["seasons"].items()]
            new_season = option_grid(season_options, st.session_state.season, "season", columns=4)
            if new_season != st.session_state.season:
                st.session_state.season = new_season
                st.rerun()

            field_label(t["step2"])
            district_options = [(code, district_label(data, code, lang)) for code in DISTRICT_ORDER]
            new_district = option_grid(district_options, st.session_state.district, "district", columns=3)
            if new_district != st.session_state.district:
                st.session_state.district = new_district
                st.rerun()
            ports = data["districts"][st.session_state.district]["target_ports"]
            if ports:
                chips = "".join(f'<span class="mf-chip">{html.escape(p)}</span>' for p in ports)
                st.markdown(f'<div class="mf-chips"><span>{html.escape(t["landing"])}</span>{chips}</div>',
                            unsafe_allow_html=True)

            field_label(t["step3"], t["cap_help"])
            capacity = st.number_input(t["step3"], min_value=1, value=50, step=1, label_visibility="collapsed")

        season = st.session_state.season
        district = st.session_state.district
        season_name = t["seasons"][season][0]
        district_plain = district_label(data, district, lang).rsplit(" (", 1)[0]
        harbour = harbour_label(DISTRICT_HARBOURS[district][0], lang)

        # Market prices for the season (sorted by price), and the capacity plan
        district_species = data["districts"][district]["species"]
        rows = []
        for sp, info in district_species.items():
            price = season_avg_price(info, season)
            rows.append({
                t["col_species"]: species_label(species_dict, sp, lang),
                t["col_price"]: round(price, 1),
                t["col_halfkg"]: round(price / 2, 1),
                "_sp": sp, "_price": price, "_share": info["catch_share_in_district"],
            })
        rows.sort(key=lambda r: -r["_price"])
        plan_rows = sorted(rows, key=lambda r: -(r["_share"] * r["_price"]))
        total_value = sum(r["_share"] * capacity * r["_price"] for r in plan_rows)
        max_share = max((r["_share"] for r in plan_rows), default=0) or 1
        coverage_pct = sum(r["_share"] for r in plan_rows) * 100

        with summary_col:
            rating = _sea_rating_now(district)
            pill = (f'<span class="mf-pill {rating}">{html.escape(t["rating"][rating][0])}</span>' if rating
                    else '<span class="mf-pill none">-</span>')
            st.markdown(
                f'<div class="mf-summary rv" style="--d:150ms">'
                f'<div class="mf-kicker" style="color:var(--foam)">{html.escape(t["sum_k"])}</div>'
                f'<div class="mf-sum-row"><span>{html.escape(t["sum_district"])}</span>'
                f'<b>{html.escape(district_plain)} · {html.escape(harbour)}</b></div>'
                f'<div class="mf-sum-row"><span>{html.escape(t["sum_season"])}</span><b>{html.escape(season_name)}</b></div>'
                f'<div class="mf-sum-row"><span>{html.escape(t["sum_capacity"])}</span><b>{capacity} kg</b></div>'
                f'<div class="mf-sum-row"><span>{html.escape(t["sum_sea"])}</span>{pill}</div>'
                f'<div><div class="mf-sum-note">{html.escape(t["sum_value"])}</div>'
                f'<div class="mf-sum-total">₹{total_value:,.0f}</div>'
                f'<div class="mf-sum-note">{html.escape(t["sum_cov"].format(pct=f"{coverage_pct:.1f}"))}</div></div>'
                f'<a class="mf-btn mf-btn-primary" href="#mf-catch">{html.escape(t["sum_btn"])}</a>'
                f'</div>', unsafe_allow_html=True)

    st.markdown(WAVE_INTO_DARK, unsafe_allow_html=True)
    live_sea_panel(district, district_plain, lang)
    fishing_zones_panel(district, lang)
    st.markdown(WAVE_OUT_OF_DARK, unsafe_allow_html=True)

    season_keys_list = list(t["seasons"].keys())
    season_col_names = [t["seasons"][sk][0] for sk in season_keys_list]

    with st.container(key="sec_prices"):
        section_head(t["prices_h"].format(season=season_name), kicker=f'04 · {t["n_prices"]}', anchor_id="mf-prices")
        st.markdown(
            f'<div class="mf-badges"><span class="mf-src"><i style="background:{TOKENS["caution"]}"></i>'
            f'{html.escape(t["legend_pred"])}</span><span class="mf-src">{html.escape(t["same_price"])}</span></div>',
            unsafe_allow_html=True)
        cards = ""
        for i, r in enumerate(rows):
            info = district_species[r["_sp"]]
            by_season = [season_avg_price(info, sk) for sk in season_keys_list]
            top = max(by_season) or 1
            bars = "".join(f'<span class="{"hi" if p == top else ""}" style="height:{p / top * 100:.0f}%"></span>'
                           for p in by_season)
            bar_labels = "".join(f'<span>{html.escape(name)}</span>' for name in season_col_names)
            sci = species_dict.get(r["_sp"], {}).get("scientific_name", "")
            cards += (
                f'<div class="mf-pcard rv" style="--d:{i * 70}ms">'
                f'<div class="sp">{html.escape(r[t["col_species"]])}</div><div class="sci">{html.escape(sci)}</div>'
                f'<div class="pr"><span data-count="{r[t["col_price"]]:.1f}" data-dec="1">{r[t["col_price"]]:.1f}</span>'
                f'<small> {html.escape(t["col_price"])}</small></div>'
                f'<div class="half">{r[t["col_halfkg"]]:.1f} {html.escape(t["col_halfkg"])}</div>'
                f'<div class="mf-spark">{bars}</div><div class="mf-spark-l">{bar_labels}</div></div>')
        st.markdown(f'<div class="mf-price-grid mf-grow">{cards}</div>', unsafe_allow_html=True)
        st.caption(t["season_bars"])

        sub_label(t["all_seasons_header"])
        all_season_rows = []
        for sp, info in district_species.items():
            row = {t["col_species"]: species_label(species_dict, sp, lang)}
            for sk, col_name in zip(season_keys_list, season_col_names):
                row[col_name] = round(season_avg_price(info, sk), 1)
            all_season_rows.append(row)
        df_all_seasons = pd.DataFrame(all_season_rows).set_index(t["col_species"])
        st.dataframe(
            df_all_seasons.style.highlight_max(axis=1, subset=season_col_names, color="#CDEDEE")
            .format("{:.1f}", subset=season_col_names),
            width="stretch",
        )

    with st.container(key="sec_plan"):
        section_head(t["plan_header"], t["plan_intro"].format(district=district_plain, season=season_name, kg=capacity),
                     kicker=f'05 · {t["n_catch"]}', anchor_id="mf-catch")
        total_col, list_col = st.columns([1, 1.7], gap="large")

        plan_html = ""
        plan_text_lines = [f"{t['title']} - {district_plain}, {season_name}", ""]
        for i, r in enumerate(plan_rows):
            expected_kg = capacity * r["_share"]
            expected_value = expected_kg * r["_price"]
            species_name = species_label(species_dict, r["_sp"], lang)
            detail = t["plan_detail"].format(
                share=f"{r['_share'] * 100:.1f}", kg=f"{expected_kg:.1f}", price=f"{r['_price']:.0f}"
            )
            plan_html += (
                f'<div class="mf-scard rv" style="--d:{i * 70}ms"><span class="mf-fish">{FISH_ICON}</span>'
                f'<div><b>{html.escape(species_name)}</b><div class="d">{html.escape(detail)}</div>'
                f'<div class="mf-sbar"><span style="width:{r["_share"] / max_share * 100:.0f}%"></span></div></div>'
                f'<div class="v">₹{expected_value:,.0f}</div></div>'
            )
            plan_text_lines.append(
                f"{species_name}: {expected_kg:.1f} kg x Rs.{r['_price']:.0f}/kg = Rs.{expected_value:,.0f}")
        plan_text_lines += ["", f"{t['plan_total']}: Rs.{total_value:,.0f}"]

        with total_col:
            coverage = t["catch_cov"].format(n=len(plan_rows), pct=f"{coverage_pct:.1f}", district=district_plain)
            st.markdown(
                f'<div class="mf-total rv mf-grow">'
                f'<div class="tl">{html.escape(t["plan_total"])}</div>'
                f'<div class="tv">₹<span data-count="{total_value:.0f}">{total_value:,.0f}</span></div>'
                f'<div class="tm">{html.escape(district_plain)} · {html.escape(season_name)} · {capacity} kg</div>'
                f'<div class="mf-cov">{html.escape(coverage)}'
                f'<div class="mf-cov-bar"><span style="width:{min(coverage_pct, 100):.1f}%"></span></div></div>'
                f'</div>', unsafe_allow_html=True)
            st.download_button(
                t["download_button"], data="\n".join(plan_text_lines),
                file_name="catch_plan.txt", mime="text/plain", icon=":material/download:",
            )
        with list_col:
            st.markdown(f'<div class="mf-species mf-grow">{plan_html}</div>', unsafe_allow_html=True)

    # District comparison: how does one species' typical catch SHARE (not
    # price, which is the same everywhere by design) vary across districts.
    with st.container(key="sec_compare"):
        section_head(t["cmp_h"], t["cmp_sub"], kicker=f'06 · {t["n_compare"]}', anchor_id="mf-compare")
        compare_species = st.selectbox(
            t["district_compare_pick"], data["species_in_both"],
            format_func=lambda sp: species_label(species_dict, sp, lang),
            label_visibility="collapsed", key="compare_species_select",
        )
        compare_rows = []
        for code in DISTRICT_ORDER:
            sp_info = data["districts"][code]["species"].get(compare_species)
            share = sp_info["catch_share_in_district"] if sp_info else 0.0
            compare_rows.append({t["col_district"]: district_label(data, code, lang), "_share": share, "_code": code})
        compare_rows.sort(key=lambda r: -r["_share"])
        top_share = max(r["_share"] for r in compare_rows) or 1
        bars = "".join(
            f'<div class="mf-bar{" me" if r["_code"] == district else ""}"><span>{html.escape(r[t["col_district"]])}</span>'
            f'<div class="track"><span style="width:{r["_share"] / top_share * 100:.1f}%"></span></div>'
            f'<span class="pct">{r["_share"] * 100:.1f}%</span></div>' for r in compare_rows)
        st.markdown(
            f'<div class="mf-bars mf-grow rv" aria-label="{html.escape(t["district_compare_col_share"])}">{bars}</div>'
            f'<div class="mf-badges" style="margin-top:10px"><span class="mf-src"><i style="background:{TOKENS["calm"]}"></i>'
            f'{html.escape(t["real_catch"])}</span></div>', unsafe_allow_html=True)

    # Fish name glossary (static, from the species dictionary) and the data sources
    with st.container(key="sec_ref"):
        section_head(t["ref_h"], kicker=f'07 · {t["n_ref"]}', anchor_id="mf-reference")
        gloss_col, src_col = st.columns([1.5, 1], gap="large")
        with gloss_col:
            sub_label(t["glossary_header"])
            glossary_rows = [
                {
                    t["col_species"]: entry["english"],
                    t["glossary_col_scientific"]: entry.get("scientific_name", ""),
                    t["glossary_col_malayalam"]: entry.get("malayalam", ""),
                    t["glossary_col_tamil"]: entry.get("tamil", ""),
                }
                for entry in species_dict.values()
            ]
            st.dataframe(glossary_rows, hide_index=True, width="stretch")
        with src_col:
            sub_label(t["sources_h"])
            sources = "".join(
                f'<div class="mf-source rv" style="--d:{i * 70}ms"><i style="background:{SOURCE_DOTS[i]}"></i><div>'
                f'<em style="color:{SOURCE_INK[i]}">{html.escape(tag)}</em><b>{html.escape(name)}</b>'
                f'<span>{html.escape(desc)}</span></div></div>' for i, (tag, name, desc) in enumerate(t["sources"]))
            st.markdown(f'<div class="mf-sources">{sources}</div>', unsafe_allow_html=True)

    links = "".join(f'<a href="#{aid}">{html.escape(t[key])}</a>' for aid, key, _ in SECTION_ANCHORS)
    st.markdown(
        f'{WAVE_INTO_DARK}<div class="mf-footer"><div class="mf-foot-grid">'
        f'<div><h4>{html.escape(t["brand"])}</h4><p>{html.escape(t["foot_about"])}</p></div>'
        f'<div><h4>{html.escape(t["foot_sections"])}</h4>{links}<a href="#mf-home">{html.escape(t["back_top"])} ↑</a></div>'
        f'</div><div class="mf-foot-note">{html.escape(t["footer"])}</div></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
