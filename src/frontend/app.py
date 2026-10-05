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
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

from fishing_zones import DISTRICT_HARBOURS, fetch_kerala_pfz, zone_conditions, zones_near_district
from official_alerts import alerts_for_district, fetch_kerala_alerts
from sea_weather import compass, daily_summary, fetch_sea_conditions, rate_conditions, tide_turns

IST = timezone(timedelta(hours=5, minutes=30))
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


CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
h1, h2, h3, .catch-title { font-family: 'Poppins', sans-serif !important; }

.stApp {
    background: radial-gradient(ellipse at top, #0B3D5C 0%, #04141F 55%, #020B12 100%);
}

.catch-hero {
    text-align: center; padding: 28px 16px 20px; margin-bottom: 8px;
}
.catch-title {
    font-size: 2.1rem; font-weight: 700; color: #E8F4F8; margin: 0;
    letter-spacing: -0.01em;
}
.catch-subtitle {
    color: #8FB8CC; font-size: 0.95rem; margin-top: 8px; max-width: 480px;
    margin-left: auto; margin-right: auto; line-height: 1.5;
}

.legend-row {
    display: flex; justify-content: center; gap: 18px; flex-wrap: wrap;
    margin: 14px 0 6px; font-size: 0.8rem; color: #8FB8CC;
}
.legend-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }

.step-label {
    font-family: 'Poppins', sans-serif; font-weight: 600; font-size: 1.05rem;
    color: #6FE3E9; margin: 26px 0 12px;
}

/* card-style buttons for season / district / language grids */
div[data-testid="stButton"] > button {
    border-radius: 16px !important;
    border: 1.5px solid rgba(111, 227, 233, 0.25) !important;
    background: rgba(11, 61, 92, 0.35) !important;
    color: #E8F4F8 !important;
    padding: 14px 10px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease;
    white-space: pre-line !important;
    line-height: 1.4 !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: #6FE3E9 !important;
    background: rgba(111, 227, 233, 0.12) !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #00C2CB, #0B8FA3) !important;
    border-color: transparent !important;
    color: #04141F !important;
    font-weight: 700 !important;
    box-shadow: 0 0 18px rgba(0, 194, 203, 0.45);
}

.plan-card {
    background: rgba(11, 44, 61, 0.55); border: 1px solid rgba(111, 227, 233, 0.18);
    border-radius: 18px; padding: 18px 20px; margin-bottom: 10px;
    backdrop-filter: blur(6px);
}
.plan-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.06);
}
.plan-row:last-child { border-bottom: none; }
.plan-name { font-weight: 600; color: #E8F4F8; }
.plan-detail { font-size: 0.78rem; color: #8FB8CC; margin-top: 2px; }
.plan-value { font-family: 'Poppins', sans-serif; font-weight: 700; color: #6FE3E9; font-size: 1.05rem; white-space: nowrap; }

.total-card {
    background: linear-gradient(135deg, rgba(0,194,203,0.18), rgba(11,143,163,0.10));
    border: 1px solid rgba(111, 227, 233, 0.4); border-radius: 18px;
    padding: 20px; text-align: center; margin: 18px 0;
}
.total-label { color: #8FB8CC; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.04em; }
.total-value { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 2.2rem; color: #E8F4F8; margin-top: 4px; }

.sea-status {
    border-radius: 18px; padding: 16px 20px; margin: 4px 0 14px;
    border: 1px solid; display: flex; align-items: center; gap: 16px;
}
.sea-status-label { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 1.5rem; white-space: nowrap; }
.sea-status-advice { color: #E8F4F8; font-size: 0.92rem; line-height: 1.4; }
.sea-calm { background: rgba(62, 207, 142, 0.12); border-color: rgba(62, 207, 142, 0.5); }
.sea-calm .sea-status-label { color: #3ECF8E; }
.sea-caution { background: rgba(224, 177, 92, 0.12); border-color: rgba(224, 177, 92, 0.5); }
.sea-caution .sea-status-label { color: #E0B15C; }
.sea-rough { background: rgba(229, 72, 77, 0.14); border-color: rgba(229, 72, 77, 0.6); }
.sea-rough .sea-status-label { color: #FF6B6F; }
.live-dot {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #3ECF8E;
    margin-right: 8px; animation: pulse 1.6s ease-in-out infinite;
}
.alert-card {
    border-radius: 14px; padding: 12px 16px; margin: 6px 0 10px; border: 1px solid;
}
.alert-none {
    background: rgba(62, 207, 142, 0.08); border-color: rgba(62, 207, 142, 0.35);
    color: #B8E8D2; font-size: 0.9rem;
}
.alert-sea { background: rgba(229, 72, 77, 0.16); border-color: rgba(229, 72, 77, 0.7); }
.alert-weather { background: rgba(224, 177, 92, 0.12); border-color: rgba(224, 177, 92, 0.55); }
.alert-kind { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.04em; color: #FFD0A8; }
.alert-sea .alert-kind { color: #FF9EA1; }
.alert-headline { color: #E8F4F8; font-weight: 600; margin: 4px 0; line-height: 1.45; }
.alert-meta { color: #8FB8CC; font-size: 0.78rem; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.25; } }

footer, #MainMenu { visibility: hidden; }
</style>
"""


def option_grid(options, selected_key, session_key, columns=4):
    """Renders a row of card-style buttons; returns the newly selected key."""
    cols = st.columns(columns)
    result = selected_key
    for i, (key, label) in enumerate(options):
        with cols[i % columns]:
            is_selected = key == selected_key
            if st.button(label, key=f"{session_key}_{key}", type="primary" if is_selected else "secondary",
                         use_container_width=True):
                result = key
    return result


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
    st.markdown(f'**{t["alerts_header"]}**')
    try:
        with st.spinner(t["alerts_loading"]):
            all_alerts, checked_at = cached_official_alerts()
    except (requests.RequestException, ET.ParseError):
        st.warning(t["alerts_error"])
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
    t = UI[lang]
    st.markdown(f'<div class="step-label"><span class="live-dot"></span>{t["sea_header"]}</div>',
                unsafe_allow_html=True)

    official_alerts_block(district_code, district_name, lang)

    try:
        sea = cached_sea_conditions(district_code)
    except (requests.RequestException, KeyError, ValueError):
        st.warning(t["sea_error"])
        return

    now = sea["current"]
    rating = rate_conditions(now)
    label, advice = t["rating"][rating]
    updated = datetime.fromisoformat(now["time"]).strftime("%H:%M")
    st.caption(t["sea_point"].format(harbour=harbour_label(sea["harbour"], lang), time=updated))
    st.markdown(
        f'<div class="sea-status sea-{rating}">'
        f'<div class="sea-status-label">{label}</div>'
        f'<div class="sea-status-advice">{advice}</div>'
        f'</div>', unsafe_allow_html=True)

    upcoming_tides = [x for x in tide_turns(sea["hourly"]) if x["time"] >= now["time"]]
    next_high = next((x for x in upcoming_tides if x["kind"] == "high"), None)
    next_low = next((x for x in upcoming_tides if x["kind"] == "low"), None)

    def tide_text(turn):
        if not turn:
            return "-"
        when = datetime.fromisoformat(turn["time"])
        day = "" if turn["time"][:10] == now["time"][:10] else when.strftime(" %d/%m")
        return f'{when.strftime("%H:%M")}{day}'

    # delta slot is used only to show direction text, so colour is switched off
    c1, c2, c3 = st.columns(3)
    c1.metric(t["m_wave"], f'{_fmt(now.get("wave_height"))} m',
              _dir(t, "dir_from", now.get("wave_direction")), delta_color="off", delta_arrow="off")
    c2.metric(t["m_wind"], f'{_fmt(now.get("wind_speed_10m"), "{:.0f}")} km/h',
              _dir(t, "dir_from", now.get("wind_direction_10m")), delta_color="off", delta_arrow="off")
    c3.metric(t["m_gust"], f'{_fmt(now.get("wind_gusts_10m"), "{:.0f}")} km/h')
    c4, c5, c6 = st.columns(3)
    c4.metric(t["m_swell"], f'{_fmt(now.get("swell_wave_height"))} m / '
                            f'{_fmt(now.get("swell_wave_period"), "{:.0f}")} s',
              _dir(t, "dir_from", now.get("swell_wave_direction")), delta_color="off", delta_arrow="off")
    c5.metric(t["m_current"], f'{_fmt(now.get("ocean_current_velocity"))} km/h',
              _dir(t, "dir_to", now.get("ocean_current_direction")), delta_color="off", delta_arrow="off")
    c6.metric(t["m_sst"], f'{_fmt(now.get("sea_surface_temperature"))} °C')
    c7, c8, c9 = st.columns(3)
    c7.metric(t["m_next_high"], tide_text(next_high))
    c8.metric(t["m_next_low"], tide_text(next_low))
    c9.metric(t["m_rain"], f'{_fmt(now.get("precipitation"))} mm')

    # 7-day outlook: one row per day, worst values of that day
    st.markdown(f'**{t["forecast_header"]}**')
    forecast_rows = []
    for day in daily_summary(sea["hourly"]):
        sea_label = t["rating"][day["rating"]][0]
        if day["thunderstorm"]:
            sea_label += f' ({t["thunder"]})'
        day_fmt = "%a %d %b" if lang == "en" else "%d/%m"
        forecast_rows.append({
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
        })
    st.dataframe(forecast_rows, hide_index=True, use_container_width=True)

    # Hourly charts from the current hour onward
    hourly = pd.DataFrame(sea["hourly"])
    hourly["time"] = pd.to_datetime(hourly["time"])
    hourly = hourly[hourly["time"] >= pd.to_datetime(now["time"]).floor("h")].set_index("time")
    tab_waves, tab_wind, tab_tide, tab_current = st.tabs(
        [t["chart_waves"], t["chart_wind"], t["chart_tide"], t["chart_current"]])
    with tab_waves:
        st.line_chart(hourly[["wave_height", "swell_wave_height"]], color=["#6FE3E9", "#3ECF8E"], height=220)
    with tab_wind:
        st.line_chart(hourly[["wind_speed_10m", "wind_gusts_10m"]], color=["#6FE3E9", "#E0B15C"], height=220)
    with tab_tide:
        st.line_chart(hourly[["sea_level_height_msl"]], color=["#6FE3E9"], height=220)
    with tab_current:
        st.line_chart(hourly[["ocean_current_velocity"]], color=["#6FE3E9"], height=220)

    st.caption(t["sea_disclaimer"])


@st.cache_data(ttl=3600, show_spinner=False)
def cached_pfz():
    return fetch_kerala_pfz()


@st.cache_data(ttl=900, show_spinner=False)
def cached_zone_conditions(points):
    return zone_conditions(list(points))


RATING_RGB = {"calm": [62, 207, 142], "caution": [224, 177, 92], "rough": [255, 107, 111]}


@st.fragment(run_every="15m")
def fishing_zones_panel(district_code, lang):
    """Official INCOIS fishing zones near the district harbour, on a map, coloured
    by the sea conditions at each zone right now."""
    t = UI[lang]
    harbour_en, h_lat, h_lon = DISTRICT_HARBOURS[district_code]
    harbour = harbour_label(harbour_en, lang)
    st.markdown(f'<div class="step-label"><span class="live-dot"></span>{t["zones_header"]}</div>',
                unsafe_allow_html=True)
    try:
        pfz = cached_pfz()
        zones = zones_near_district(pfz, district_code)
        readings = cached_zone_conditions(tuple(z["mid"] for z in zones))
    except (requests.RequestException, KeyError, ValueError):
        st.warning(t["zones_error"])
        return

    if not zones:
        st.info(t["zones_none"].format(harbour=harbour))
        return

    st.caption(t["zones_intro"].format(harbour=harbour))

    rows = []
    for n, (z, r) in enumerate(zip(zones, readings), start=1):
        label = t["zone_label"].format(n=n, km=round(z["nearest_km"]), dir=compass(z["bearing"]), harbour=harbour)
        detail = t["zone_detail"].format(
            lat=f'{z["nearest_point"][0]:.3f}', lon=f'{z["nearest_point"][1]:.3f}',
            wave=_fmt(r.get("wave_height")), wind=_fmt(r.get("wind_speed_10m"), "{:.0f}"))
        rows.append({
            "n": str(n), "path": z["path"], "mid_lon": z["mid"][1], "mid_lat": z["mid"][0],
            "near_lon": z["nearest_point"][1], "near_lat": z["nearest_point"][0],
            "h_lon": h_lon, "h_lat": h_lat,
            "color": RATING_RGB[r["rating"]], "rating": r["rating"],
            "label": label, "detail": detail, "status": t["rating"][r["rating"]][0],
        })

    layers = [
        # route from harbour to the nearest point of each zone
        pdk.Layer("LineLayer", rows, get_source_position=["h_lon", "h_lat"],
                  get_target_position=["near_lon", "near_lat"], get_color=[143, 184, 204, 110], get_width=1.5),
        pdk.Layer("PathLayer", rows, get_path="path", get_color="color", width_min_pixels=5,
                  pickable=True, cap_rounded=True, joint_rounded=True),
        pdk.Layer("TextLayer", rows, get_position=["mid_lon", "mid_lat"], get_text="n", get_size=16,
                  get_color=[232, 244, 248], get_pixel_offset=[14, 0], font_weight=700),
        pdk.Layer("ScatterplotLayer", [{"lon": h_lon, "lat": h_lat, "label": t["zones_harbour"], "detail": harbour,
                                        "status": ""}],
                  get_position=["lon", "lat"], get_fill_color=[232, 244, 248], get_radius=1800,
                  radius_min_pixels=6, pickable=True),
    ]
    all_lats = [p[1] for row in rows for p in row["path"]] + [h_lat]
    all_lons = [p[0] for row in rows for p in row["path"]] + [h_lon]
    view = pdk.ViewState(latitude=(min(all_lats) + max(all_lats)) / 2,
                         longitude=(min(all_lons) + max(all_lons)) / 2, zoom=7.6)
    st.pydeck_chart(pdk.Deck(
        layers=layers, initial_view_state=view, map_style="dark",
        tooltip={"html": "<b>{label}</b><br/>{status}<br/>{detail}",
                 "style": {"backgroundColor": "#0B2C3D", "color": "#E8F4F8", "fontSize": "12px"}},
    ), height=380)

    legend = "".join(
        f'<span><span class="legend-dot" style="background:rgb({",".join(map(str, RATING_RGB[k]))})"></span>'
        f'{t["rating"][k][0]}</span>' for k in ["calm", "caution", "rough"])
    st.markdown(f'<div class="legend-row">{legend}</div>', unsafe_allow_html=True)

    cards = '<div class="plan-card">'
    for row in rows:
        cards += (
            f'<div class="plan-row"><div>'
            f'<div class="plan-name">{html.escape(row["label"])}</div>'
            f'<div class="plan-detail">{html.escape(row["detail"])}</div>'
            f'</div><div class="plan-value" style="color:rgb({",".join(map(str, row["color"]))})">'
            f'{html.escape(row["status"])}</div></div>')
    st.markdown(cards + "</div>", unsafe_allow_html=True)

    adv_date = pfz["date"]
    if adv_date and (datetime.now(IST).date() - adv_date).days > 2:
        st.caption(t["zones_old"].format(date=adv_date.strftime("%d %b %Y")))
    else:
        st.caption(t["zones_date"].format(date=adv_date.strftime("%d %b %Y") if adv_date else "-"))


def main():
    st.set_page_config(page_title="Catch Plan", layout="centered")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    data, species_dict = load_data()

    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "season" not in st.session_state:
        st.session_state.season = "monsoon"
    if "district" not in st.session_state:
        st.session_state.district = "EKM"

    t = UI[st.session_state.lang]

    st.markdown(
        f'<div class="catch-hero">'
        f'<div class="catch-title">{t["title"]}</div>'
        f'<div class="catch-subtitle">{t["subtitle"]}</div>'
        f'</div>', unsafe_allow_html=True)

    # Step 0: language
    st.markdown(f'<div class="step-label">{t["step0"]}</div>', unsafe_allow_html=True)
    lang_options = [(code, UI[code]["lang_name"]) for code in UI]
    new_lang = option_grid(lang_options, st.session_state.lang, "lang", columns=3)
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()
    t = UI[st.session_state.lang]

    st.markdown(
        f'<div class="legend-row">'
        f'<span><span class="legend-dot" style="background:#3ECF8E"></span>{t["legend_real"]}</span>'
        f'<span><span class="legend-dot" style="background:#E0B15C"></span>{t["legend_pred"]}</span>'
        f'</div>', unsafe_allow_html=True)

    # Step 1: season
    st.markdown(f'<div class="step-label">{t["step1"]}</div>', unsafe_allow_html=True)
    season_options = [(k, f"{v[0]}\n{v[1]}") for k, v in t["seasons"].items()]
    new_season = option_grid(season_options, st.session_state.season, "season", columns=4)
    if new_season != st.session_state.season:
        st.session_state.season = new_season
        st.rerun()

    # Step 2: district
    st.markdown(f'<div class="step-label">{t["step2"]}</div>', unsafe_allow_html=True)
    district_options = [(code, district_label(data, code, st.session_state.lang)) for code in DISTRICT_ORDER]
    new_district = option_grid(district_options, st.session_state.district, "district", columns=3)
    if new_district != st.session_state.district:
        st.session_state.district = new_district
        st.rerun()
    ports = data["districts"][st.session_state.district]["target_ports"]
    if ports:
        st.caption(", ".join(ports))

    live_sea_panel(st.session_state.district,
                   district_label(data, st.session_state.district, st.session_state.lang).rsplit(" (", 1)[0],
                   st.session_state.lang)
    fishing_zones_panel(st.session_state.district, st.session_state.lang)

    # Step 3: capacity
    st.markdown(f'<div class="step-label">{t["step3"]}</div>', unsafe_allow_html=True)
    capacity = st.number_input(t["step3"], min_value=1, value=50, step=1, label_visibility="collapsed")

    lang = st.session_state.lang
    season = st.session_state.season
    district = st.session_state.district
    season_name = t["seasons"][season][0]

    # Results: price table for the season
    st.markdown(f'<div class="step-label">{t["result_header"]} — {season_name}</div>', unsafe_allow_html=True)

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
    st.dataframe(
        [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows],
        hide_index=True, use_container_width=True,
    )

    # All-season comparison: same species, every season's price side by side,
    # with the best (highest) season highlighted per row - built entirely from
    # data already loaded above, no new data source needed.
    st.markdown(f'<div class="step-label">{t["all_seasons_header"]}</div>', unsafe_allow_html=True)
    season_keys_list = list(t["seasons"].keys())
    season_col_names = [t["seasons"][sk][0] for sk in season_keys_list]
    all_season_rows = []
    for sp, info in district_species.items():
        row = {t["col_species"]: species_label(species_dict, sp, lang)}
        for sk, col_name in zip(season_keys_list, season_col_names):
            row[col_name] = round(season_avg_price(info, sk), 1)
        all_season_rows.append(row)
    df_all_seasons = pd.DataFrame(all_season_rows).set_index(t["col_species"])
    st.dataframe(
        df_all_seasons.style.highlight_max(axis=1, subset=season_col_names, color="#0B8FA3"),
        use_container_width=True,
    )

    # Capacity plan
    st.markdown(f'<div class="step-label">{t["plan_header"]}</div>', unsafe_allow_html=True)
    district_plain = district_label(data, district, lang).rsplit(" (", 1)[0]
    st.caption(t["plan_intro"].format(district=district_plain, season=season_name, kg=capacity))

    plan_rows = sorted(rows, key=lambda r: -(r["_share"] * r["_price"]))
    total_value = sum(r["_share"] * capacity * r["_price"] for r in plan_rows)

    plan_html = '<div class="plan-card">'
    plan_text_lines = [f"{t['title']} - {district_plain}, {season_name}", ""]
    for r in plan_rows:
        expected_kg = capacity * r["_share"]
        expected_value = expected_kg * r["_price"]
        r["_expected_kg"] = expected_kg
        r["_expected_value"] = expected_value
        species_name = species_label(species_dict, r["_sp"], lang)
        detail = t["plan_detail"].format(
            share=f"{r['_share'] * 100:.1f}", kg=f"{expected_kg:.1f}", price=f"{r['_price']:.0f}"
        )
        plan_html += (
            f'<div class="plan-row">'
            f'<div>'
            f'<div class="plan-name">{species_name}</div>'
            f'<div class="plan-detail">{detail}</div>'
            f'</div>'
            f'<div class="plan-value">₹{expected_value:,.0f}</div>'
            f'</div>'
        )
        plan_text_lines.append(f"{species_name}: {expected_kg:.1f} kg x Rs.{r['_price']:.0f}/kg = Rs.{expected_value:,.0f}")
    plan_html += "</div>"
    st.markdown(plan_html, unsafe_allow_html=True)

    st.markdown(
        f'<div class="total-card">'
        f'<div class="total-label">{t["plan_total"]}</div>'
        f'<div class="total-value">₹{total_value:,.0f}</div>'
        f'</div>', unsafe_allow_html=True)

    plan_text_lines += ["", f"{t['plan_total']}: Rs.{total_value:,.0f}"]
    st.download_button(
        t["download_button"], data="\n".join(plan_text_lines),
        file_name="catch_plan.txt", mime="text/plain",
    )

    # District comparison: how does one species' typical catch SHARE (not
    # price, which is the same everywhere by design) vary across districts.
    st.markdown(f'<div class="step-label">{t["district_compare_header"]}</div>', unsafe_allow_html=True)
    compare_species = st.selectbox(
        t["district_compare_pick"], data["species_in_both"],
        format_func=lambda sp: species_label(species_dict, sp, lang),
        label_visibility="collapsed", key="compare_species_select",
    )
    compare_rows = []
    for code in DISTRICT_ORDER:
        sp_info = data["districts"][code]["species"].get(compare_species)
        share = sp_info["catch_share_in_district"] if sp_info else 0.0
        compare_rows.append({
            t["col_district"]: district_label(data, code, lang),
            t["district_compare_col_share"]: share,
        })
    compare_rows.sort(key=lambda r: -r[t["district_compare_col_share"]])
    for r in compare_rows:
        r[t["district_compare_col_share"]] = f"{r[t['district_compare_col_share']] * 100:.1f}%"
    st.dataframe(compare_rows, hide_index=True, use_container_width=True)

    # Fish name glossary: static reference from the species dictionary,
    # independent of the season/district picked above.
    with st.expander(t["glossary_header"]):
        glossary_rows = [
            {
                t["col_species"]: entry["english"],
                t["glossary_col_scientific"]: entry.get("scientific_name", ""),
                t["glossary_col_malayalam"]: entry.get("malayalam", ""),
                t["glossary_col_tamil"]: entry.get("tamil", ""),
            }
            for entry in species_dict.values()
        ]
        st.dataframe(glossary_rows, hide_index=True, use_container_width=True)

    st.caption(t["footer"])


if __name__ == "__main__":
    main()
