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

import json
from pathlib import Path

import streamlit as st

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
        "step0": "0. Choose your language",
        "step1": "1. Which season are you fishing in?",
        "step2": "2. Which district are you in?",
        "step3": "3. Your boat's loading capacity (kg per trip)",
        "result_header": "Market price prediction",
        "plan_header": "Your catch plan",
        "col_species": "Species", "col_price": "Rs / kg", "col_halfkg": "Rs / half-kg", "col_share": "Catch share",
        "plan_intro": "Based on {district}'s typical species mix and {season} prices, if you land {kg} kg this trip:",
        "plan_total": "Estimated total value",
        "plan_detail": "{share}% of typical catch  |  ~{kg} kg  |  Rs.{price}/kg",
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
        "step0": "0. നിങ്ങളുടെ ഭാഷ തിരഞ്ഞെടുക്കുക",
        "step1": "1. ഏത് സീസണിലാണ് നിങ്ങൾ മീൻപിടിക്കുന്നത്?",
        "step2": "2. നിങ്ങൾ ഏത് ജില്ലയിലാണ്?",
        "step3": "3. നിങ്ങളുടെ ബോട്ടിന്റെ ശേഷി (കി.ഗ്രാം, ഓരോ യാത്രയ്ക്കും)",
        "result_header": "വിപണി വില പ്രവചനം",
        "plan_header": "നിങ്ങളുടെ പിടിത്ത പദ്ധതി",
        "col_species": "മത്സ്യം", "col_price": "₹ / കി.ഗ്രാം", "col_halfkg": "₹ / അര കി.ഗ്രാം", "col_share": "പിടിത്ത വിഹിതം",
        "plan_intro": "{district}യിലെ സാധാരണ മത്സ്യ ഇനങ്ങളും {season} വിലയും അടിസ്ഥാനമാക്കി, ഈ യാത്രയിൽ {kg} കി.ഗ്രാം പിടിച്ചാൽ:",
        "plan_total": "കണക്കാക്കിയ ആകെ മൂല്യം",
        "plan_detail": "സാധാരണ പിടിത്തത്തിന്റെ {share}%  |  ~{kg} കി.ഗ്രാം  |  ₹{price}/കി.ഗ്രാം",
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
        "step0": "0. உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்",
        "step1": "1. நீங்கள் எந்த பருவத்தில் மீன் பிடிக்கிறீர்கள்?",
        "step2": "2. நீங்கள் எந்த மாவட்டத்தில் இருக்கிறீர்கள்?",
        "step3": "3. உங்கள் படகின் ஏற்றும் திறன் (கிலோ, ஒரு பயணத்திற்கு)",
        "result_header": "சந்தை விலை கணிப்பு",
        "plan_header": "உங்கள் மீன்பிடி திட்டம்",
        "col_species": "மீன் வகை", "col_price": "₹ / கிலோ", "col_halfkg": "₹ / அரை கிலோ", "col_share": "பிடிப்பு பங்கு",
        "plan_intro": "{district} மாவட்டத்தின் வழக்கமான மீன் கலவையும் {season} விலையும் அடிப்படையாகக் கொண்டு, இந்த பயணத்தில் {kg} கிலோ பிடித்தால்:",
        "plan_total": "மதிப்பிடப்பட்ட மொத்த மதிப்பு",
        "plan_detail": "வழக்கமான பிடிப்பில் {share}%  |  ~{kg} கிலோ  |  ₹{price}/கிலோ",
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


def season_avg_price(species_info, season_key):
    months = SEASON_MONTHS[season_key]
    values = [species_info["monthly_prices"][MONTH_NAMES[m]]["price_inr_per_kg"] for m in months]
    return sum(values) / len(values)


def main():
    st.set_page_config(page_title="Catch Plan", page_icon=":fish:", layout="centered")
    data, species_dict = load_data()

    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "season" not in st.session_state:
        st.session_state.season = "monsoon"
    if "district" not in st.session_state:
        st.session_state.district = "EKM"

    # Step 0: language - shown first, plain choice, drives every label below it
    lang_options = list(UI.keys())
    lang = st.radio(
        UI[st.session_state.lang]["step0"],
        lang_options,
        format_func=lambda code: UI[code]["lang_name"],
        index=lang_options.index(st.session_state.lang),
        horizontal=True,
        key="lang_radio",
    )
    st.session_state.lang = lang
    t = UI[lang]

    st.title(t["title"])
    st.caption(t["subtitle"])
    st.markdown(f"🟢 {t['legend_real']}  \n🟡 {t['legend_pred']}")
    st.divider()

    # Step 1: season
    st.subheader(t["step1"])
    season_keys = list(t["seasons"].keys())
    season = st.radio(
        t["step1"], season_keys,
        format_func=lambda k: f"{t['seasons'][k][0]} ({t['seasons'][k][1]})",
        index=season_keys.index(st.session_state.season),
        horizontal=True, label_visibility="collapsed", key="season_radio",
    )
    st.session_state.season = season

    # Step 2: district
    st.subheader(t["step2"])
    district = st.selectbox(
        t["step2"], DISTRICT_ORDER,
        format_func=lambda code: district_label(data, code, lang),
        index=DISTRICT_ORDER.index(st.session_state.district),
        label_visibility="collapsed", key="district_select",
    )
    st.session_state.district = district
    ports = data["districts"][district]["target_ports"]
    if ports:
        st.caption(", ".join(ports))

    # Step 3: capacity
    st.subheader(t["step3"])
    capacity = st.number_input(t["step3"], min_value=1, value=50, step=1, label_visibility="collapsed")

    st.divider()

    # Results: price table for the season
    season_name = t["seasons"][season][0]
    st.header(f"{t['result_header']} — {season_name}")

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

    # Capacity plan
    st.header(t["plan_header"])
    district_plain = district_label(data, district, lang).rsplit(" (", 1)[0]
    st.write(t["plan_intro"].format(district=district_plain, season=season_name, kg=capacity))

    plan_rows = sorted(rows, key=lambda r: -(r["_share"] * r["_price"]))
    total_value = 0.0
    for r in plan_rows:
        expected_kg = capacity * r["_share"]
        expected_value = expected_kg * r["_price"]
        total_value += expected_value
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{species_label(species_dict, r['_sp'], lang)}**")
            st.caption(t["plan_detail"].format(
                share=f"{r['_share'] * 100:.1f}", kg=f"{expected_kg:.1f}", price=f"{r['_price']:.0f}"
            ))
        with col2:
            st.markdown(f"**Rs.{expected_value:,.0f}**")

    st.divider()
    st.markdown(f"### {t['plan_total']}: Rs.{total_value:,.0f}")

    st.divider()
    st.caption(t["footer"])


if __name__ == "__main__":
    main()
