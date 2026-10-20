"""
Presentation layer for the Streamlit app: design tokens, CSS, the scroll/animation
script, the hero illustration and the extra interface text the redesigned layout needs.

Nothing here fetches or computes data. app.py decides what to show; this module only
decides how it looks. Malayalam and Tamil strings below have NOT been reviewed by a
native speaker yet (same caveat as the rest of the UI text).
"""

# Design tokens. Python-side colours (map layers, charts) read from here too, so the
# palette is defined once.
TOKENS = {
    "deep": "#0C2438",
    "deep_2": "#10304A",
    "ocean": "#145A7A",
    "teal": "#087E8B",
    "foam": "#48D6C8",
    "mist": "#F3F8FA",
    "white": "#FFFFFF",
    "ink": "#173348",
    "ink_2": "#597487",
    "line": "#D7E5EC",
    "calm": "#1E9E6A",
    "caution": "#E3A132",
    "rough": "#E0565D",
}


def hex_rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


SECTION_ANCHORS = [
    # (anchor id, nav text key, streamlit container key)
    ("mf-plan", "n_plan", "sec_setup"),
    ("mf-sea", "n_sea", "sec_sea"),
    ("mf-zones", "n_zones", "sec_zones"),
    ("mf-prices", "n_prices", "sec_prices"),
    ("mf-catch", "n_catch", "sec_plan"),
    ("mf-compare", "n_compare", "sec_compare"),
    ("mf-reference", "n_ref", "sec_ref"),
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@112,600;112,700;112,800&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&family=Noto+Sans+Malayalam:wght@400;500;600;700&family=Noto+Sans+Tamil:wght@400;500;600;700&display=swap');

:root {
    --deep: #0C2438; --deep-2: #10304A; --ocean: #145A7A; --teal: #087E8B; --foam: #48D6C8;
    --mist: #F3F8FA; --white: #FFFFFF; --ink: #173348; --ink-2: #597487; --line: #D7E5EC;
    --line-dark: rgba(170, 215, 230, 0.16); --on-dark: #E8F3F7; --on-dark-2: #A3BDCD;
    --calm: #1E9E6A; --caution: #E3A132; --rough: #E0565D;
    --calm-soft: #5FE0A8; --caution-soft: #F3C06A; --rough-soft: #F68A90;
    --calm-ink: #12754D; --caution-ink: #8F5D07; --rough-ink: #B3323A;
    --font-display: 'Archivo', 'Noto Sans Malayalam', 'Noto Sans Tamil', 'Segoe UI', sans-serif;
    --font-body: 'Geist', 'Noto Sans Malayalam', 'Noto Sans Tamil', -apple-system, 'Segoe UI', sans-serif;
    --font-data: 'Geist Mono', ui-monospace, Consolas, monospace;
    --wrap: 1120px;
    --pad-x: max(16px, calc((100% - var(--wrap)) / 2));
    --nav-h: 64px;
}

/* ---------- base ---------- */
html, body, .stApp, .stMarkdown, button, input, label, textarea, [data-testid="stCaptionContainer"] {
    font-family: var(--font-body) !important;
}
.stApp { background: var(--mist); color: var(--ink); }
[data-testid="stHeader"] { display: none; }
.block-container, [data-testid="stMainBlockContainer"] {
    max-width: none !important; padding: 0 !important;
}
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap: 0 !important; }
footer, #MainMenu { visibility: hidden; }
:focus-visible { outline: 2px solid var(--foam) !important; outline-offset: 2px; }
.mf-anchor { position: relative; top: calc(-1 * var(--nav-h) - 8px); height: 0; scroll-margin-top: calc(var(--nav-h) + 8px); }

/* ---------- navigation ---------- */
.st-key-mf_nav {
    position: sticky; top: 0; z-index: 999990;
    background: rgba(12, 36, 56, 0.9); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--line-dark); padding: 10px max(16px, calc((100% - 1300px) / 2)) !important;
}
.st-key-mf_nav [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; align-items: center; gap: 12px !important; }
.st-key-mf_nav [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-mf_nav [data-testid="stColumn"]:last-child { flex: 0 0 auto !important; width: auto !important; }
.mf-navrow { display: flex; align-items: center; gap: 18px; min-height: 44px; }
.mf-brand { display: flex; align-items: center; gap: 10px; text-decoration: none !important; color: var(--on-dark) !important; flex: none; }
.mf-mark { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; flex: none;
    background: linear-gradient(150deg, var(--foam), var(--teal) 55%, var(--ocean)); }
.mf-bname { font-family: var(--font-display); font-weight: 700; font-stretch: 112%; font-size: 1rem; line-height: 1.1; color: var(--on-dark); }
.mf-bname small { display: block; font-family: var(--font-body); font-weight: 400; font-stretch: 100%; font-size: .7rem; color: var(--on-dark-2); }
.mf-links { display: flex; gap: 2px; margin-left: auto; overflow-x: auto; scrollbar-width: none; min-width: 0; }
.mf-links::-webkit-scrollbar { display: none; }
.mf-links a, .mf-drawer a {
    text-decoration: none !important; color: var(--on-dark-2) !important; font-size: 13.5px; padding: 7px 9px;
    border-radius: 8px; white-space: nowrap; transition: color .2s, background .2s;
}
.mf-links a:hover { color: var(--on-dark) !important; background: rgba(255,255,255,.07); }
.mf-links a.active, .mf-drawer a.active { color: var(--deep) !important; background: var(--foam); font-weight: 600; }
.mf-menu { display: none; margin-left: auto; position: relative; }
.mf-menu summary { list-style: none; cursor: pointer; width: 40px; height: 40px; border-radius: 10px; display: grid; place-items: center;
    background: rgba(255,255,255,.08); border: 1px solid var(--line-dark); color: var(--on-dark); }
.mf-menu summary::-webkit-details-marker { display: none; }
.mf-drawer { position: absolute; right: 0; top: 48px; width: min(300px, 86vw); background: var(--deep); border: 1px solid var(--line-dark);
    border-radius: 14px; padding: 8px; display: grid; gap: 2px; box-shadow: 0 24px 50px -20px rgba(0,0,0,.6); }
.mf-drawer a { display: block; color: var(--on-dark) !important; padding: 10px 12px; font-size: 14px; }
@media (max-width: 1240px) { .mf-links { display: none; } .mf-menu { display: block; } }
@media (max-width: 1600px) {
    .mf-navrow.mf-l-ml .mf-links, .mf-navrow.mf-l-ta .mf-links { display: none; }
    .mf-navrow.mf-l-ml .mf-menu, .mf-navrow.mf-l-ta .mf-menu { display: block; }
}
@media (max-width: 520px) { .mf-bname small { display: none; } }
@media (max-width: 640px) {
    .mf-bname { display: none; }
    .mf-navrow { gap: 10px; }
    .mf-menu { margin-left: 0; order: 3; }
    .st-key-mf_nav [data-testid="stColumn"]:first-child { flex: 0 0 auto !important; width: auto !important; }
    .st-key-mf_nav [data-testid="stHorizontalBlock"] { justify-content: space-between; }
    /* season / district cards two per row instead of one */
    .st-key-sec_setup [data-testid="stColumn"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 8px !important; }
    .st-key-sec_setup [data-testid="stColumn"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: calc(50% - 4px) !important; flex: 1 1 calc(50% - 4px) !important; width: calc(50% - 4px) !important; }
}
/* language switch on the dark bar */
.st-key-mf_nav [data-testid="stButtonGroup"] { background: rgba(255,255,255,.07); border-radius: 10px; padding: 3px; border: 1px solid var(--line-dark); }
.st-key-mf_nav [data-testid="stButtonGroup"] button {
    background: transparent !important; color: var(--on-dark-2) !important; border: 0 !important; border-radius: 7px !important;
    min-height: 32px; padding: 4px 10px !important; box-shadow: none !important;
}
.st-key-mf_nav [data-testid="stButtonGroup"] button p { font-size: 13px !important; }
.st-key-mf_nav [data-testid="stButtonGroup"] button[aria-checked="true"],
.st-key-mf_nav [data-testid="stButtonGroup"] button[kind$="Active"] { background: var(--white) !important; color: var(--deep) !important; }
.st-key-mf_nav [data-testid="stButtonGroup"] button[aria-checked="true"] p,
.st-key-mf_nav [data-testid="stButtonGroup"] button[kind$="Active"] p { font-weight: 600; color: var(--deep) !important; }
@media (max-width: 520px) { .st-key-mf_nav [data-testid="stButtonGroup"] button { padding: 4px 6px !important; } .st-key-mf_nav [data-testid="stButtonGroup"] button p { font-size: 12px !important; } }

/* ---------- hero ---------- */
.mf-hero { position: relative; min-height: min(86vh, 820px); padding-bottom: 190px !important; overflow: hidden; isolation: isolate; color: var(--on-dark);
    background: linear-gradient(180deg, #071A2B 0%, #0C2438 38%, #12405C 62%, #145A7A 78%, #0E3D58 100%); padding-left: var(--pad-x); padding-right: var(--pad-x); }
.mf-layer { position: absolute; left: 0; right: 0; will-change: transform; pointer-events: none; }
.mf-layer svg { display: block; width: 100%; height: 100%; }
.mf-l-glow { top: 0; height: 70%; background: radial-gradient(520px 260px at 72% 58%, rgba(72,214,200,.22), transparent 70%), radial-gradient(900px 400px at 20% 10%, rgba(20,90,122,.45), transparent 70%); }
.mf-l-stars { top: 0; height: 55%; opacity: .55; }
.mf-l-far { bottom: 24%; height: 22%; }
.mf-l-boat { bottom: 21%; height: 26%; }
.mf-l-mid { bottom: 9%; height: 22%; }
.mf-l-near { bottom: 0; height: 22%; }
.mf-hero-copy { position: relative; z-index: 2; padding-top: clamp(56px, 11vh, 120px); max-width: 760px; }
.mf-eyebrow { display: inline-flex; align-items: center; gap: 8px; font: 500 12px var(--font-data); letter-spacing: .08em; text-transform: uppercase; color: var(--foam); }
.mf-eyebrow::before { content: ""; width: 22px; height: 1px; background: var(--foam); }
.mf-h1 { font-family: var(--font-display); font-weight: 800; font-stretch: 112%; font-size: clamp(2.1rem, 5.4vw, 4.2rem); line-height: 1.04;
    letter-spacing: -0.035em; margin: 16px 0 18px; max-width: 16ch; text-wrap: balance; color: var(--on-dark); }
.mf-lead { font-size: clamp(1rem, 1.6vw, 1.15rem); color: var(--on-dark-2); max-width: 46ch; margin: 0; line-height: 1.55; }
.mf-ctas { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 28px; }
.mf-btn { display: inline-flex; align-items: center; gap: 9px; font: 600 15px var(--font-body); text-decoration: none !important; border-radius: 12px;
    padding: 13px 20px; transition: transform .2s ease, box-shadow .2s ease, background .2s; }
.mf-btn-primary { background: var(--foam); color: var(--deep) !important; box-shadow: 0 10px 30px -12px rgba(72,214,200,.7); }
.mf-btn-primary:hover { transform: translateY(-2px); }
.mf-btn-ghost { background: rgba(255,255,255,.08); color: var(--on-dark) !important; border: 1px solid rgba(255,255,255,.22); }
.mf-btn-ghost:hover { background: rgba(255,255,255,.14); }
.mf-facts { display: flex; gap: 28px; flex-wrap: wrap; margin-top: 40px; font-size: 13px; color: var(--on-dark-2); }
.mf-facts b { display: block; font: 600 1.05rem var(--font-display); color: var(--on-dark); }
.mf-hpills { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 22px; }
.mf-hpill { display: inline-flex; align-items: center; gap: 7px; font-size: 12.5px; color: var(--on-dark); line-height: 1.35;
    background: rgba(255,255,255,.07); border: 1px solid var(--line-dark); border-radius: 8px; padding: 5px 10px; max-width: 100%; }
.mf-hpill i { width: 7px; height: 7px; border-radius: 50%; flex: none; display: inline-block; }
@media (max-width: 640px) { .mf-hero { min-height: 640px; padding-bottom: 210px !important; } .mf-facts { gap: 18px; } }

/* ---------- section bands ---------- */
[class*="st-key-sec_"] { padding: 72px var(--pad-x) !important; gap: 0.9rem !important; }
.st-key-sec_sea, .st-key-sec_zones { background: var(--deep); color: var(--on-dark); }
.st-key-sec_sea { padding-top: 40px !important; }
.st-key-sec_zones { border-top: 1px solid var(--line-dark); padding-top: 48px !important; }
.st-key-sec_prices, .st-key-sec_plan, .st-key-sec_compare, .st-key-sec_ref { background: var(--mist); }
.st-key-sec_plan, .st-key-sec_compare, .st-key-sec_ref { padding-top: 28px !important; }
.mf-wave { display: block; width: 100%; height: 64px; margin: 0; }
.mf-wavewrap { line-height: 0; margin: 0; }
.mf-wavewrap + .mf-footer { margin-top: -1px; }
.mf-kicker { font: 500 12px var(--font-data); letter-spacing: .09em; text-transform: uppercase; color: var(--teal); }
.mf-dark .mf-kicker, [class*="st-key-sec_sea"] .mf-kicker, [class*="st-key-sec_zones"] .mf-kicker { color: var(--foam); }
.mf-h2 { font-family: var(--font-display); font-weight: 700; font-stretch: 112%; font-size: clamp(1.6rem, 3.1vw, 2.25rem); letter-spacing: -0.025em;
    line-height: 1.12; margin: 6px 0 8px; text-wrap: balance; color: inherit; }
.mf-sub { color: var(--ink-2); max-width: 64ch; margin: 0; font-size: 15px; line-height: 1.55; }
.st-key-sec_sea .mf-sub, .st-key-sec_zones .mf-sub { color: var(--on-dark-2); }
.mf-live { display: inline-flex; align-items: center; gap: 8px; font: 500 12.5px var(--font-data); color: var(--on-dark-2); margin-top: 4px; }
.mf-live i { width: 8px; height: 8px; border-radius: 50%; background: var(--foam); box-shadow: 0 0 0 4px rgba(72,214,200,.18); flex: none; }
@media (prefers-reduced-motion: no-preference) { .mf-live i { animation: mfpulse 1.8s ease-in-out infinite; } }
@keyframes mfpulse { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
.mf-subh { font: 600 1.05rem var(--font-display); margin: 22px 0 4px; display: flex; justify-content: space-between; gap: 12px; align-items: baseline; flex-wrap: wrap; }
.mf-subh small { font: 400 12px var(--font-data); color: var(--ink-2); }
.st-key-sec_sea .mf-subh small, .st-key-sec_zones .mf-subh small { color: var(--on-dark-2); }
.st-key-sec_sea [data-testid="stCaptionContainer"], .st-key-sec_zones [data-testid="stCaptionContainer"] { color: var(--on-dark-2) !important; }
.st-key-sec_sea [data-testid="stCaptionContainer"] p, .st-key-sec_zones [data-testid="stCaptionContainer"] p { color: var(--on-dark-2) !important; }

/* ---------- trip planner ---------- */
.st-key-sec_setup {
    background: var(--white); border: 1px solid var(--line); border-radius: 22px;
    box-shadow: 0 30px 70px -30px rgba(12,36,56,.45), 0 2px 6px rgba(12,36,56,.05);
    width: min(var(--wrap), calc(100% - 32px)) !important; margin: -130px auto 40px !important;
    padding: clamp(20px, 3vw, 34px) !important; position: relative; z-index: 5;
}
.mf-field { font-weight: 600; font-size: 14px; color: var(--ink); margin: 14px 0 2px; }
.mf-help { font-size: 12.5px; color: var(--ink-2); margin-top: -2px; }
.mf-chips { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; font-size: 12.5px; color: var(--ink-2); }
.mf-chip { background: rgba(8,126,139,.1); color: var(--teal); border-radius: 6px; padding: 3px 9px; font-weight: 500; }
.st-key-sec_setup div[data-testid="stButton"] > button {
    border-radius: 12px !important; border: 1px solid var(--line) !important; background: var(--mist) !important; color: var(--ink) !important;
    padding: 10px 10px !important; min-height: 3.1rem; white-space: pre-line !important; line-height: 1.35 !important;
    transition: border-color .2s, transform .2s, background .2s; box-shadow: none !important;
}
.st-key-sec_setup div[data-testid="stButton"] > button p { white-space: pre-line !important; font-size: .88rem; line-height: 1.35; overflow: visible !important; text-overflow: clip !important; }
.st-key-sec_setup div[data-testid="stButton"] > button:hover { border-color: var(--teal) !important; transform: translateY(-1px); }
.st-key-sec_setup div[data-testid="stButton"] > button[kind="primary"] { background: var(--deep) !important; border-color: var(--deep) !important; color: var(--white) !important; }
.st-key-sec_setup div[data-testid="stButton"] > button[kind="primary"] p { color: var(--white) !important; font-weight: 600; }
.st-key-sec_setup [data-testid="stNumberInput"] { max-width: 280px; }
.st-key-sec_setup [data-testid="stNumberInput"] input { font-family: var(--font-data) !important; font-size: 1.05rem; font-weight: 600; }
.mf-summary { background: linear-gradient(165deg, var(--deep) 0%, #123A55 100%); color: var(--on-dark); border-radius: 18px; padding: 24px;
    display: flex; flex-direction: column; gap: 14px; position: relative; overflow: hidden; }
.mf-summary::after { content: ""; position: absolute; right: -40px; bottom: -60px; width: 220px; height: 220px; border-radius: 50%;
    background: radial-gradient(circle, rgba(72,214,200,.25), transparent 70%); pointer-events: none; }
.mf-sum-row { display: flex; justify-content: space-between; gap: 12px; font-size: 13.5px; color: var(--on-dark-2); border-bottom: 1px solid var(--line-dark); padding-bottom: 10px; }
.mf-sum-row b { color: var(--on-dark); font-weight: 600; text-align: right; }
.mf-sum-total { font: 700 2.2rem var(--font-display); font-stretch: 112%; letter-spacing: -0.03em; line-height: 1.05; font-variant-numeric: tabular-nums; color: var(--on-dark); }
.mf-sum-note { font-size: 12.5px; color: var(--on-dark-2); line-height: 1.45; }
.mf-summary .mf-btn { justify-content: center; position: relative; z-index: 1; }
.mf-pill { display: inline-flex; align-items: center; gap: 6px; font-weight: 600; font-size: 12.5px; padding: 3px 10px; border-radius: 999px; white-space: nowrap; }
.mf-pill::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.mf-pill.calm { color: var(--calm-soft); background: rgba(30,158,106,.16); }
.mf-pill.caution { color: var(--caution-soft); background: rgba(227,161,50,.16); }
.mf-pill.rough { color: var(--rough-soft); background: rgba(224,86,93,.16); }
.mf-pill.none { color: var(--on-dark-2); background: rgba(255,255,255,.06); }

/* ---------- sea conditions ---------- */
.alert-card { border-radius: 14px; padding: 13px 16px; border: 1px solid; font-size: 14px; }
.alert-none { background: rgba(30,158,106,.12); border-color: rgba(95,224,168,.32); color: #C4F1DC; }
.alert-sea { background: rgba(224,86,93,.14); border-color: rgba(246,138,144,.45); }
.alert-weather { background: rgba(227,161,50,.13); border-color: rgba(243,192,106,.45); }
.alert-kind { font: 600 11.5px var(--font-data); letter-spacing: .04em; color: var(--caution-soft); }
.alert-sea .alert-kind { color: var(--rough-soft); }
.alert-headline { color: var(--on-dark); font-weight: 600; margin: 5px 0; line-height: 1.5; font-size: 15px; }
.alert-meta { color: var(--on-dark-2); font-size: 12.5px; }
.sub-label { font: 600 1.02rem var(--font-display); margin: 14px 0 2px; }
.st-key-sec_sea .sub-label { color: var(--on-dark); }
.mf-sea-grid { display: grid; grid-template-columns: minmax(0, 300px) minmax(0, 1fr); gap: 14px; margin-top: 4px; }
@media (max-width: 860px) { .mf-sea-grid { grid-template-columns: minmax(0, 1fr); } }
.mf-status { border-radius: 18px; padding: 22px; border: 1px solid; display: flex; flex-direction: column; gap: 10px; }
.mf-status.calm { background: linear-gradient(170deg, rgba(30,158,106,.24), rgba(30,158,106,.06)); border-color: rgba(95,224,168,.32); }
.mf-status.caution { background: linear-gradient(170deg, rgba(227,161,50,.24), rgba(227,161,50,.06)); border-color: rgba(243,192,106,.4); }
.mf-status.rough { background: linear-gradient(170deg, rgba(224,86,93,.26), rgba(224,86,93,.07)); border-color: rgba(246,138,144,.45); }
.mf-status-l { font-size: 12.5px; color: var(--on-dark-2); }
.mf-status-word { font: 800 2.6rem var(--font-display); font-stretch: 112%; letter-spacing: -0.03em; line-height: 1; }
.mf-status.calm .mf-status-word { color: var(--calm-soft); }
.mf-status.caution .mf-status-word { color: var(--caution-soft); }
.mf-status.rough .mf-status-word { color: var(--rough-soft); }
.mf-status-adv { color: var(--on-dark); font-size: 15px; line-height: 1.45; }
.mf-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
@media (max-width: 560px) { .mf-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.mf-metric { background: rgba(255,255,255,.045); border: 1px solid var(--line-dark); border-radius: 14px; padding: 13px 15px; min-width: 0; transition: transform .25s, background .25s; }
.mf-metric:hover { background: rgba(255,255,255,.075); transform: translateY(-2px); }
.mf-ml { font-size: 12px; color: var(--on-dark-2); }
.mf-mv { font: 600 1.4rem var(--font-display); font-variant-numeric: tabular-nums; letter-spacing: -0.02em; margin-top: 2px; color: var(--on-dark); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mf-md { font-size: 12px; color: var(--foam); margin-top: 2px; }
.mf-mv small { font: 500 .78rem var(--font-body); color: var(--on-dark-2); letter-spacing: 0; }
.mf-days { display: grid; grid-template-columns: repeat(7, minmax(112px, 1fr)); gap: 8px; overflow-x: auto; padding-bottom: 6px; }
.mf-day { border-radius: 14px; padding: 12px; background: rgba(255,255,255,.045); border: 1px solid var(--line-dark); font-size: 12.5px; color: var(--on-dark-2); display: grid; gap: 5px; align-content: start; }
.mf-day b { color: var(--on-dark); font: 600 13.5px var(--font-body); }
.mf-day .mf-pill { justify-self: start; padding: 2px 8px; font-size: 11.5px; white-space: normal; }
.mf-day .v { font-family: var(--font-data); color: var(--on-dark); font-variant-numeric: tabular-nums; }
.st-key-sec_sea [data-testid="stExpander"] details, .st-key-sec_zones [data-testid="stExpander"] details {
    background: rgba(255,255,255,.04); border: 1px solid var(--line-dark) !important; border-radius: 14px;
}
.st-key-sec_sea [data-testid="stExpander"] summary p, .st-key-sec_sea [data-testid="stExpander"] summary svg { color: var(--on-dark) !important; }
.st-key-mf_chartcard { background: var(--white); border-radius: 16px; padding: 10px 16px 6px !important; }
.st-key-mf_chartcard [data-baseweb="tab"] p { font-size: 13px; }

/* ---------- fishing zones ---------- */
.mf-note { border-radius: 14px; padding: 13px 15px; background: rgba(72,214,200,.08); border: 1px solid rgba(72,214,200,.25); color: var(--on-dark); font-size: 14px; }
.st-key-sec_zones [data-testid="stDeckGlJsonChart"] { border-radius: 18px; overflow: hidden; border: 1px solid var(--line-dark);
    box-shadow: 0 40px 80px -40px rgba(0,0,0,.7); transform-origin: 50% 100%; }
.map-legend { display: flex; gap: 14px; flex-wrap: wrap; font-size: 12.5px; color: var(--on-dark-2); margin-top: 4px; }
.map-legend span { display: inline-flex; align-items: center; gap: 6px; }
.legend-dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; flex: none; }
.mf-zcards { display: grid; gap: 10px; }
.mf-zcard { border-radius: 14px; padding: 13px 15px; background: rgba(255,255,255,.045); border: 1px solid var(--line-dark);
    display: grid; grid-template-columns: 40px minmax(0, 1fr) auto; gap: 12px; align-items: center; }
.mf-zcard img { width: 40px; height: 40px; display: block; }
.mf-zcard b { display: block; font-size: 14px; color: var(--on-dark); line-height: 1.35; }
.mf-zcard .d { font: 12px var(--font-data); color: var(--on-dark-2); line-height: 1.55; margin-top: 2px; }
.mf-zcard .st { font: 700 .95rem var(--font-display); text-align: right; white-space: nowrap; }
.mf-zintro { font-size: 13.5px; color: var(--on-dark-2); margin-bottom: 2px; }

/* ---------- prices ---------- */
.mf-badges { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 2px; }
.mf-src { display: inline-flex; gap: 7px; align-items: center; font-size: 12.5px; padding: 4px 10px; border-radius: 8px; background: var(--white); border: 1px solid var(--line); color: var(--ink-2); }
.mf-src i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; flex: none; }
.mf-price-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 6px; }
@media (max-width: 860px) { .mf-price-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 480px) { .mf-price-grid { grid-template-columns: minmax(0, 1fr); } }
.mf-pcard { background: var(--white); border: 1px solid var(--line); border-radius: 16px; padding: 16px 18px; transition: transform .3s ease, box-shadow .3s ease; min-width: 0; }
.mf-pcard:hover { transform: perspective(800px) rotateX(3deg) translateY(-3px); box-shadow: 0 20px 36px -24px rgba(12,36,56,.4); }
.mf-pcard .sp { font-weight: 600; font-size: 14.5px; color: var(--ink); }
.mf-pcard .sci { font-size: 12px; color: var(--ink-2); font-style: italic; min-height: 1.2em; }
.mf-pcard .pr { font: 700 1.75rem var(--font-display); font-stretch: 112%; letter-spacing: -0.03em; margin-top: 10px; font-variant-numeric: tabular-nums; color: var(--ink); }
.mf-pcard .pr small { font: 500 .78rem var(--font-body); color: var(--ink-2); letter-spacing: 0; font-stretch: 100%; }
.mf-pcard .half { font-size: 12.5px; color: var(--ink-2); font-variant-numeric: tabular-nums; }
.mf-spark { display: flex; align-items: flex-end; gap: 5px; height: 44px; margin-top: 12px; }
.mf-spark span { flex: 1; background: #CFE3EA; border-radius: 4px 4px 0 0; transform-origin: bottom; }
.mf-spark span.hi { background: var(--teal); }
.mf-spark-l { display: flex; gap: 5px; font-size: 10.5px; color: var(--ink-2); margin-top: 4px; }
.mf-spark-l span { flex: 1; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }

/* ---------- catch plan ---------- */
.mf-total { background: linear-gradient(160deg, var(--teal), var(--ocean) 60%, var(--deep)); color: var(--white); border-radius: 20px; padding: 26px;
    box-shadow: 0 30px 60px -30px rgba(8,126,139,.7); }
.mf-total .tl { font-size: 14px; opacity: .88; }
.mf-total .tv { font: 800 2.9rem var(--font-display); font-stretch: 112%; letter-spacing: -0.04em; line-height: 1.05; margin-top: 6px; font-variant-numeric: tabular-nums; }
.mf-total .tm { font-size: 13px; opacity: .82; margin-top: 4px; }
.mf-cov { margin-top: 18px; background: rgba(255,255,255,.12); border-radius: 12px; padding: 12px 14px; font-size: 13px; line-height: 1.45; }
.mf-cov-bar { height: 6px; background: rgba(255,255,255,.22); border-radius: 6px; margin-top: 9px; overflow: hidden; }
.mf-cov-bar span { display: block; height: 100%; background: var(--foam); border-radius: 6px; }
.st-key-sec_plan div[data-testid="stDownloadButton"] > button {
    width: 100%; border-radius: 12px !important; background: var(--deep) !important; color: var(--white) !important; border: 0 !important;
    padding: 12px 16px !important; font-weight: 600 !important; transition: transform .2s;
}
.st-key-sec_plan div[data-testid="stDownloadButton"] > button p { color: var(--white) !important; font-weight: 600; }
.st-key-sec_plan div[data-testid="stDownloadButton"] > button:hover { transform: translateY(-1px); }
.mf-species { display: grid; gap: 10px; }
.mf-scard { background: var(--white); border: 1px solid var(--line); border-radius: 16px; padding: 15px 18px; display: grid;
    grid-template-columns: 44px minmax(0, 1fr) auto; gap: 14px; align-items: center; transition: transform .3s ease, box-shadow .3s ease; }
.mf-scard:hover { transform: translateY(-2px); box-shadow: 0 18px 30px -22px rgba(12,36,56,.4); }
.mf-fish { width: 44px; height: 44px; border-radius: 12px; background: var(--mist); display: grid; place-items: center; }
.mf-scard b { font-size: 14.5px; color: var(--ink); }
.mf-scard .d { font: 12px var(--font-data); color: var(--ink-2); margin-top: 2px; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.mf-sbar { height: 5px; background: #E3EEF2; border-radius: 5px; margin-top: 8px; max-width: 220px; overflow: hidden; }
.mf-sbar span { display: block; height: 100%; background: linear-gradient(90deg, var(--foam), var(--teal)); border-radius: 5px; transform-origin: left; }
.mf-scard .v { font: 700 1.2rem var(--font-display); font-stretch: 112%; text-align: right; font-variant-numeric: tabular-nums; color: var(--ink); white-space: nowrap; }

/* ---------- compare ---------- */
.st-key-sec_compare [data-testid="stSelectbox"] { max-width: 360px; }
.mf-bars { display: grid; gap: 9px; background: var(--white); border: 1px solid var(--line); border-radius: 18px; padding: clamp(16px, 3vw, 26px); }
.mf-bar { display: grid; grid-template-columns: minmax(0, 220px) minmax(0, 1fr) 60px; gap: 12px; align-items: center; font-size: 13.5px; color: var(--ink); }
@media (max-width: 560px) { .mf-bar { grid-template-columns: minmax(0, 1fr) 56px; } .mf-bar .track { grid-column: 1 / -1; grid-row: 2; } }
.mf-bar.me { font-weight: 600; }
.mf-bar .track { height: 12px; background: var(--mist); border-radius: 6px; overflow: hidden; }
.mf-bar .track span { display: block; height: 100%; background: var(--ocean); border-radius: 6px; transform-origin: left; }
.mf-bar.me .track span { background: var(--teal); }
.mf-bar .pct { font-family: var(--font-data); text-align: right; font-variant-numeric: tabular-nums; }

/* ---------- reference + footer ---------- */
.mf-sources { display: grid; gap: 10px; }
.mf-source { background: var(--white); border: 1px solid var(--line); border-radius: 14px; padding: 14px 16px; display: grid; grid-template-columns: 10px minmax(0, 1fr); gap: 12px; }
.mf-source i { width: 10px; height: 10px; border-radius: 50%; margin-top: 6px; }
.mf-source em { font-style: normal; font: 500 11px var(--font-data); letter-spacing: .05em; text-transform: uppercase; }
.mf-source b { display: block; font-size: 14px; color: var(--ink); }
.mf-source span { font-size: 13px; color: var(--ink-2); }
.mf-footer { background: var(--deep); color: var(--on-dark-2); padding: 10px var(--pad-x) 44px; font-size: 13.5px; }
.mf-foot-grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 30px; padding-top: 30px; }
@media (max-width: 760px) { .mf-foot-grid { grid-template-columns: minmax(0, 1fr); } }
.mf-footer h4 { color: var(--on-dark); font: 600 14px var(--font-display); margin: 0 0 10px; padding: 0; }
.mf-footer a { color: var(--on-dark-2) !important; text-decoration: none !important; display: block; padding: 3px 0; }
.mf-footer a:hover { color: var(--foam) !important; }
.mf-footer p { color: var(--on-dark-2); margin: 0; }
.mf-foot-note { border-top: 1px solid var(--line-dark); margin-top: 28px; padding-top: 18px; font-size: 12.5px; line-height: 1.6; max-width: 90ch; }

/* ---------- reveal system (only active once the script has loaded) ---------- */
.mf-anim .rv:not(.in) { opacity: 0; transform: translateY(24px); }
.mf-anim .rv.in { transition: opacity .8s ease, transform .8s cubic-bezier(.2,.7,.2,1); transition-delay: var(--d, 0ms); }
.mf-anim .st-key-sec_setup:not(.in) { opacity: 0; transform: perspective(900px) rotateX(9deg) translateY(40px); }
.mf-anim .st-key-sec_setup.in { transition: opacity .9s ease, transform 1s cubic-bezier(.2,.7,.2,1); }
/* the map is revealed with a wipe, never a transform: deck.gl measures its box while drawing */
.mf-anim .mf-mapwrap:not(.in) { opacity: .2; clip-path: inset(0 0 100% 0 round 18px); }
.mf-anim .mf-mapwrap.in { clip-path: inset(0 0 0 0 round 18px); transition: opacity .9s ease, clip-path 1.2s cubic-bezier(.2,.7,.2,1); }
.mf-anim .mf-grow:not(.in) .mf-spark span { transform: scaleY(0); }
.mf-anim .mf-grow:not(.in) .mf-sbar span, .mf-anim .mf-grow:not(.in) .track span, .mf-anim .mf-grow:not(.in) .mf-cov-bar span { transform: scaleX(0); }
.mf-anim .mf-grow .mf-spark span, .mf-anim .mf-grow .mf-sbar span, .mf-anim .mf-grow .track span, .mf-anim .mf-grow .mf-cov-bar span { transition: transform 1s cubic-bezier(.2,.7,.2,1); }
@media (prefers-reduced-motion: reduce) {
    .mf-anim .rv, .mf-anim .st-key-sec_setup, .mf-anim .mf-mapwrap, .mf-anim .mf-grow * { opacity: 1 !important; transform: none !important; clip-path: none !important; transition: none !important; }
    .mf-pcard:hover, .mf-scard:hover, .mf-metric:hover { transform: none; }
}
</style>
"""

# Scroll behaviour. Runs once per browser tab; re-scans the page after every Streamlit
# rerun or fragment refresh so new elements show immediately (no replayed animations,
# and refreshed live numbers are never re-counted as if they were new).
SCRIPT = """
<script>
(function () {
  if (window.__mfai) { window.__mfai.scan(); return; }
  var doc = document, root = doc.documentElement;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var canIO = 'IntersectionObserver' in window;
  var seen = new WeakSet(), shownSections = {}, firstPass = true;

  function sectionOf(el) {
    var s = el.closest('[class*="st-key-sec_"]');
    if (!s) return el.closest('.mf-hero') ? 'hero' : 'page';
    var m = s.className.match(/st-key-(sec_[a-z_]+)/); return m ? m[1] : 'page';
  }
  function countUp(el) {
    if (el.dataset.done || reduce) return; el.dataset.done = '1';
    var end = parseFloat(el.dataset.count); if (isNaN(end)) return;
    var dec = parseInt(el.dataset.dec || '0', 10), finalText = el.textContent, t0 = null, dur = 1000;
    function step(t) {
      if (!t0) t0 = t; var p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = (end * e).toLocaleString('en-IN', { minimumFractionDigits: dec, maximumFractionDigits: dec });
      if (p < 1) requestAnimationFrame(step); else el.textContent = finalText;
    }
    requestAnimationFrame(step);
  }
  function show(el, animate) {
    el.classList.add('in'); shownSections[sectionOf(el)] = true;
    if (animate) el.querySelectorAll('[data-count]').forEach(countUp);
    if (el.classList.contains('mf-mapwrap')) setTimeout(function () { window.dispatchEvent(new Event('resize')); }, 1300);
  }
  var io = canIO && !reduce ? new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { show(e.target, true); io.unobserve(e.target); } });
  }, { threshold: 0.12, rootMargin: '0px 0px -30px 0px' }) : null;
  if (io) root.classList.add('mf-anim');

  /* active link in the nav */
  var nio = canIO ? new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      var id = e.target.getAttribute('data-mf-sec');
      doc.querySelectorAll('[data-mf-link]').forEach(function (a) {
        var on = a.getAttribute('data-mf-link') === id;
        a.classList.toggle('active', on);
        if (on) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
      });
    });
  }, { rootMargin: '-40% 0px -55% 0px' }) : null;

  /* hero parallax: far layers move slower than near ones */
  var scroller = null;
  function findScroller(el) {
    var p = el.parentElement;
    while (p && p !== doc.body) {
      var oy = getComputedStyle(p).overflowY;
      if ((oy === 'auto' || oy === 'scroll') && p.scrollHeight > p.clientHeight + 4) return p;
      p = p.parentElement;
    }
    return window;
  }
  function parallax() {
    var y = scroller === window ? window.scrollY : scroller.scrollTop;
    if (y > 1400) return;
    doc.querySelectorAll('.mf-layer[data-depth]').forEach(function (l) {
      l.style.transform = 'translate3d(0,' + (y * parseFloat(l.dataset.depth) * 0.5).toFixed(1) + 'px,0)';
    });
    var copy = doc.querySelector('.mf-hero-copy');
    if (copy) { copy.style.transform = 'translate3d(0,' + (y * 0.22).toFixed(1) + 'px,0)'; copy.style.opacity = Math.max(0, 1 - y / 650).toFixed(2); }
  }
  function bindParallax() {
    var hero = doc.querySelector('.mf-hero');
    if (!hero || scroller || reduce || window.innerWidth < 700) return;
    scroller = findScroller(hero);
    var ticking = false;
    (scroller === window ? window : scroller).addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(function () { parallax(); ticking = false; }); }
    }, { passive: true });
  }

  /* nav links: smooth scroll to the section, close the phone menu */
  doc.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href^="#mf-"]');
    if (!a) return;
    var target = doc.getElementById(a.getAttribute('href').slice(1));
    if (!target) return;
    ev.preventDefault();
    target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    var menu = a.closest('details'); if (menu) menu.removeAttribute('open');
  });

  function scan() {
    doc.querySelectorAll('.st-key-sec_zones [data-testid="stDeckGlJsonChart"]').forEach(function (m) { m.classList.add('mf-mapwrap'); });
    doc.querySelectorAll('.rv, .st-key-sec_setup, .mf-mapwrap, .mf-grow').forEach(function (el) {
      if (seen.has(el)) return; seen.add(el);
      if (!io) { el.classList.add('in'); return; }
      // elements rebuilt by a rerun or a 15-minute refresh appear at once, without replaying
      if (!firstPass && shownSections[sectionOf(el)]) { show(el, false); return; }
      io.observe(el);
    });
    if (nio) doc.querySelectorAll('.mf-anchor[id]').forEach(function (anc) {
      var sec = anc.closest('[class*="st-key-sec_"]');
      if (!sec || seen.has(sec)) return; seen.add(sec);
      sec.setAttribute('data-mf-sec', anc.id); nio.observe(sec);
    });
    bindParallax();
    firstPass = false;
  }

  var pending = false;
  new MutationObserver(function () {
    if (pending) return; pending = true;
    requestAnimationFrame(function () { pending = false; scan(); });
  }).observe(doc.body, { childList: true, subtree: true });

  // safety net: never leave visible content hidden if an observer misses it
  setInterval(function () {
    if (!io) return;
    doc.querySelectorAll('.rv:not(.in), .mf-grow:not(.in), .mf-mapwrap:not(.in), .st-key-sec_setup:not(.in)').forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0) show(el, false);
    });
  }, 2500);

  window.__mfai = { scan: scan };
  scan();
})();
</script>
"""

BRAND_MARK = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0C2438" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="M2 16c2.5 0 2.5-2 5-2s2.5 2 5 2 2.5-2 5-2 2.5 2 5 2"/>'
    '<path d="M6 9c2.2-2.6 6.6-2.6 9 0-2.4 2.6-6.8 2.6-9 0Z"/><path d="M15 9l3-2.2v4.4Z"/></svg>'
)
MENU_ICON = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>')
FISH_ICON = ('<svg width="26" height="26" viewBox="0 0 32 32" fill="none" stroke="#087E8B" stroke-width="1.8" aria-hidden="true">'
             '<path d="M4 16c4-6 14-7 20-1l4-3v8l-4-3c-6 6-16 5-20-1z"/><circle cx="10" cy="15" r="1" fill="#087E8B"/></svg>')

# Hero illustration: drawn here (no photo licensing needed). data-depth sets parallax speed.
HERO_LAYERS = (
    '<div class="mf-layer mf-l-glow" data-depth="0.1"></div>'
    '<div class="mf-layer mf-l-stars" data-depth="0.15"><svg viewBox="0 0 1440 400" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
    '<g fill="#CFEFF2"><circle cx="120" cy="60" r="1.2"/><circle cx="260" cy="140" r="1"/><circle cx="410" cy="40" r="1.4"/>'
    '<circle cx="520" cy="190" r=".9"/><circle cx="690" cy="80" r="1.1"/><circle cx="830" cy="30" r="1.3"/><circle cx="960" cy="150" r="1"/>'
    '<circle cx="1100" cy="70" r="1.2"/><circle cx="1240" cy="120" r="1"/><circle cx="1360" cy="50" r="1.4"/><circle cx="1010" cy="250" r=".8"/>'
    '<circle cx="330" cy="260" r=".8"/></g><circle cx="1040" cy="300" r="46" fill="#E9F7F4" opacity=".12"/>'
    '<circle cx="1040" cy="300" r="24" fill="#E9F7F4" opacity=".35"/></svg></div>'
    '<div class="mf-layer mf-l-far" data-depth="0.25"><svg viewBox="0 0 1440 160" preserveAspectRatio="none" aria-hidden="true">'
    '<path d="M0 60 Q 180 40 360 58 T 720 54 T 1080 60 T 1440 52 V160 H0Z" fill="#1A5574" opacity=".9"/>'
    '<path d="M0 64 H1440" stroke="#48D6C8" stroke-opacity=".25"/></svg></div>'
    '<div class="mf-layer mf-l-boat" data-depth="0.4"><svg viewBox="0 0 1440 200" preserveAspectRatio="xMidYMax meet" aria-hidden="true">'
    '<g transform="translate(980 40)"><path d="M60 18 V112" stroke="#071A2B" stroke-width="4"/>'
    '<path d="M64 24 L120 98 H64Z" fill="#0A2236" opacity=".9"/><path d="M62 22 L30 30" stroke="#071A2B" stroke-width="2"/>'
    '<path d="M58 20 l-22 -8 v14z" fill="#48D6C8" opacity=".9"/><rect x="84" y="88" width="46" height="26" rx="3" fill="#0A2236"/>'
    '<rect x="92" y="94" width="10" height="8" rx="1" fill="#48D6C8" opacity=".7"/><path d="M-10 112 H190 L168 146 H18Z" fill="#071A2B"/>'
    '<path d="M-4 118 H184" stroke="#48D6C8" stroke-opacity=".5" stroke-width="2"/>'
    '<path d="M-30 150 Q 80 140 210 150" stroke="#48D6C8" stroke-opacity=".3" stroke-width="2" fill="none"/></g></svg></div>'
    '<div class="mf-layer mf-l-mid" data-depth="0.6"><svg viewBox="0 0 1440 180" preserveAspectRatio="none" aria-hidden="true">'
    '<path d="M0 70 C 120 40, 240 40, 360 66 S 600 100, 720 70 S 960 36, 1080 64 S 1320 96, 1440 66 V180 H0Z" fill="#145A7A"/>'
    '<path d="M0 70 C 120 40, 240 40, 360 66 S 600 100, 720 70 S 960 36, 1080 64 S 1320 96, 1440 66" fill="none" stroke="#48D6C8" '
    'stroke-opacity=".35" stroke-width="2"/></svg></div>'
    '<div class="mf-layer mf-l-near" data-depth="0.9"><svg viewBox="0 0 1440 160" preserveAspectRatio="none" aria-hidden="true">'
    '<path d="M0 60 C 160 20, 300 30, 460 56 S 760 92, 920 58 S 1240 22, 1440 54 V160 H0Z" fill="#F3F8FA"/>'
    '<path d="M0 60 C 160 20, 300 30, 460 56 S 760 92, 920 58 S 1240 22, 1440 54" fill="none" stroke="#48D6C8" '
    'stroke-opacity=".6" stroke-width="2.5"/></svg></div>'
)

WAVE_INTO_DARK = ('<div class="mf-wavewrap"><svg class="mf-wave" viewBox="0 0 1440 64" preserveAspectRatio="none" aria-hidden="true" style="background:#F3F8FA">'
                  '<path d="M0 36 C 240 0, 480 64, 720 32 S 1200 0, 1440 30 V64 H0Z" fill="#0C2438"/></svg></div>')
WAVE_OUT_OF_DARK = ('<div class="mf-wavewrap"><svg class="mf-wave" viewBox="0 0 1440 64" preserveAspectRatio="none" aria-hidden="true" style="background:#F3F8FA">'
                    '<path d="M0 0 H1440 V28 C 1200 64, 960 0, 720 32 S 240 64, 0 26Z" fill="#0C2438"/></svg></div>')


# Extra interface text for the redesigned layout. Merged into app.UI per language;
# existing keys are never overwritten.
UI_EXTRA = {
    "en": {
        "brand": "Marine Fishing AI",
        "menu": "Sections",
        "n_plan": "Plan your trip", "n_sea": "Sea conditions", "n_zones": "Fishing zones", "n_prices": "Market prices",
        "n_catch": "Catch plan", "n_compare": "Compare districts", "n_ref": "Glossary & sources",
        "hero_eyebrow": "Kerala · 9 coastal districts",
        "hero_h1": "Smarter decisions for safer, more profitable fishing",
        "hero_lead": "Explore sea conditions, fishing zones, official advisories and catch-planning insights in one place.",
        "cta_plan": "Plan your trip", "cta_sea": "Check sea conditions",
        "fact1": "official alerts", "fact2": "live sea refresh", "fact3": "Kerala catch records",
        "plan_h": "Tell us about this trip",
        "cap_help": "Kilograms you can land in one trip",
        "landing": "Landing centres:",
        "sum_k": "Your trip at a glance",
        "sum_district": "District", "sum_season": "Season", "sum_capacity": "Capacity", "sum_sea": "Sea right now",
        "sum_value": "Estimated catch value",
        "sum_cov": "Prices cover {pct}% of the usual catch · price is a prototype estimate",
        "sum_btn": "See my catch plan",
        "sea_h": "Is it safe to go out?",
        "show_cols": "Show all forecast columns",
        "hourly_h": "Hour by hour",
        "zones_h": "Where are the fish gathering today?",
        "prices_h": "What fish is worth this {season}",
        "same_price": "Same predicted price in every district",
        "season_bars": "Bars show the four seasons; the highest predicted season is filled.",
        "catch_cov": "These {n} species are {pct}% of {district}'s usual catch. The rest has no price data and is not counted.",
        "cmp_h": "Where is each fish most common?",
        "cmp_sub": "Share of each district's typical landings. Your district is highlighted.",
        "real_catch": "Real catch data, Kerala Fisheries Dept 2022-25",
        "ref_h": "Fish names and where the data comes from",
        "sources_h": "Data sources",
        "sources": [
            ("Real · historical", "Kerala Fisheries Department", "District catch reports, 2022-23 to 2024-25. Used for catch shares."),
            ("Model · prototype", "Price model (FMPIS anchor)", "Trained on synthetic data built around one real FMPIS week (24-30 Mar 2025)."),
            ("Live · official", "IMD and INCOIS alerts via NDMA Sachet", "Shown exactly as issued; checked every 10 minutes."),
            ("Live · official", "INCOIS Potential Fishing Zones", "Daily advisory lines from the INCOIS GeoServer."),
            ("Live · forecast model", "Open-Meteo marine and weather", "Waves, wind, tide, current and sky. Not an official warning."),
        ],
        "foot_about": ("A decision-support prototype for Kerala fishermen: sea safety, official alerts, fishing zones and "
                       "catch planning in English, Malayalam and Tamil."),
        "foot_sections": "Sections", "back_top": "Back to top",
    },
    "ml": {
        "brand": "Marine Fishing AI",
        "menu": "വിഭാഗങ്ങൾ",
        "n_plan": "യാത്ര ആസൂത്രണം", "n_sea": "കടൽ സ്ഥിതി", "n_zones": "മത്സ്യ മേഖലകൾ", "n_prices": "വിപണി വില",
        "n_catch": "പിടിത്ത പദ്ധതി", "n_compare": "ജില്ലാ താരതമ്യം", "n_ref": "പദാവലി, ഉറവിടങ്ങൾ",
        "hero_eyebrow": "കേരളം · 9 തീരദേശ ജില്ലകൾ",
        "hero_h1": "സുരക്ഷിതവും ലാഭകരവുമായ മത്സ്യബന്ധനത്തിന് മികച്ച തീരുമാനങ്ങൾ",
        "hero_lead": "കടൽ സ്ഥിതി, മത്സ്യ മേഖലകൾ, ഔദ്യോഗിക മുന്നറിയിപ്പുകൾ, പിടിത്ത പദ്ധതി എന്നിവ ഒരിടത്ത്.",
        "cta_plan": "യാത്ര ആസൂത്രണം ചെയ്യുക", "cta_sea": "കടൽ സ്ഥിതി നോക്കുക",
        "fact1": "ഔദ്യോഗിക മുന്നറിയിപ്പുകൾ", "fact2": "തത്സമയ കടൽ വിവരം", "fact3": "കേരള മത്സ്യ ലഭ്യത രേഖകൾ",
        "plan_h": "ഈ യാത്രയെക്കുറിച്ച് പറയൂ",
        "cap_help": "ഒരു യാത്രയിൽ കരയ്ക്കെത്തിക്കാവുന്ന കിലോഗ്രാം",
        "landing": "ലാൻഡിംഗ് കേന്ദ്രങ്ങൾ:",
        "sum_k": "നിങ്ങളുടെ യാത്ര ഒറ്റനോട്ടത്തിൽ",
        "sum_district": "ജില്ല", "sum_season": "സീസൺ", "sum_capacity": "ശേഷി", "sum_sea": "ഇപ്പോഴത്തെ കടൽ",
        "sum_value": "പ്രതീക്ഷിക്കുന്ന പിടിത്ത മൂല്യം",
        "sum_cov": "സാധാരണ പിടിത്തത്തിന്റെ {pct}% നു മാത്രം വില ലഭ്യം · വില ഒരു പ്രാഥമിക കണക്ക്",
        "sum_btn": "പിടിത്ത പദ്ധതി കാണുക",
        "sea_h": "കടലിൽ പോകാൻ സുരക്ഷിതമാണോ?",
        "show_cols": "എല്ലാ പ്രവചന കോളങ്ങളും കാണുക",
        "hourly_h": "മണിക്കൂർ തോറും",
        "zones_h": "ഇന്ന് മീൻ എവിടെ കൂടുന്നു?",
        "prices_h": "ഈ {season} കാലത്ത് മീനിന്റെ വില",
        "same_price": "എല്ലാ ജില്ലയിലും ഒരേ പ്രവചിത വില",
        "season_bars": "നാല് സീസണുകളുടെ വില; ഏറ്റവും ഉയർന്ന സീസൺ നിറം നൽകിയിരിക്കുന്നു.",
        "catch_cov": "ഈ {n} ഇനങ്ങൾ {district} ജില്ലയുടെ സാധാരണ പിടിത്തത്തിന്റെ {pct}% ആണ്. ബാക്കിക്ക് വില വിവരം ഇല്ല, അത് കണക്കാക്കിയിട്ടില്ല.",
        "cmp_h": "ഓരോ മീനും കൂടുതൽ എവിടെ?",
        "cmp_sub": "ഓരോ ജില്ലയുടെയും സാധാരണ പിടിത്തത്തിലെ പങ്ക്. നിങ്ങളുടെ ജില്ല എടുത്തുകാണിച്ചിരിക്കുന്നു.",
        "real_catch": "യഥാർത്ഥ പിടിത്ത വിവരം, കേരള ഫിഷറീസ് വകുപ്പ് 2022-25",
        "ref_h": "മീനുകളുടെ പേരുകളും വിവരങ്ങളുടെ ഉറവിടവും",
        "sources_h": "വിവര ഉറവിടങ്ങൾ",
        "sources": [
            ("യഥാർത്ഥം · മുൻകാല", "കേരള ഫിഷറീസ് വകുപ്പ്", "ജില്ലാതല പിടിത്ത റിപ്പോർട്ടുകൾ, 2022-23 മുതൽ 2024-25 വരെ. പിടിത്ത പങ്കിന് ഉപയോഗിക്കുന്നു."),
            ("മോഡൽ · പ്രാഥമികം", "വില മോഡൽ (FMPIS അടിസ്ഥാനം)", "ഒരു യഥാർത്ഥ FMPIS ആഴ്ചയെ (24-30 മാർച്ച് 2025) അടിസ്ഥാനമാക്കിയ കൃത്രിമ വിവരത്തിൽ പരിശീലിപ്പിച്ചത്."),
            ("തത്സമയം · ഔദ്യോഗികം", "NDMA സചേത് വഴി IMD, INCOIS മുന്നറിയിപ്പുകൾ", "നൽകിയതുപോലെ തന്നെ കാണിക്കുന്നു; ഓരോ 10 മിനിറ്റിലും പരിശോധിക്കുന്നു."),
            ("തത്സമയം · ഔദ്യോഗികം", "INCOIS സാധ്യതാ മത്സ്യബന്ധന മേഖലകൾ", "INCOIS ജിയോസെർവറിൽ നിന്നുള്ള ദിവസേനയുള്ള മുന്നറിയിപ്പ് രേഖകൾ."),
            ("തത്സമയം · പ്രവചന മോഡൽ", "Open-Meteo കടൽ, കാലാവസ്ഥ", "തിര, കാറ്റ്, വേലിയേറ്റം, ഒഴുക്ക്, ആകാശം. ഔദ്യോഗിക മുന്നറിയിപ്പ് അല്ല."),
        ],
        "foot_about": ("കേരളത്തിലെ മത്സ്യത്തൊഴിലാളികൾക്കുള്ള ഒരു പ്രാഥമിക സഹായ ഉപകരണം: കടൽ സുരക്ഷ, ഔദ്യോഗിക മുന്നറിയിപ്പുകൾ, "
                       "മത്സ്യ മേഖലകൾ, പിടിത്ത പദ്ധതി - ഇംഗ്ലീഷ്, മലയാളം, തമിഴ് ഭാഷകളിൽ."),
        "foot_sections": "വിഭാഗങ്ങൾ", "back_top": "മുകളിലേക്ക്",
    },
    "ta": {
        "brand": "Marine Fishing AI",
        "menu": "பிரிவுகள்",
        "n_plan": "பயணத் திட்டம்", "n_sea": "கடல் நிலை", "n_zones": "மீன் மண்டலங்கள்", "n_prices": "சந்தை விலை",
        "n_catch": "மீன்பிடி திட்டம்", "n_compare": "மாவட்ட ஒப்பீடு", "n_ref": "சொல்லகராதி, ஆதாரங்கள்",
        "hero_eyebrow": "கேரளா · 9 கடலோர மாவட்டங்கள்",
        "hero_h1": "பாதுகாப்பான, லாபகரமான மீன்பிடிக்கு சிறந்த முடிவுகள்",
        "hero_lead": "கடல் நிலை, மீன் மண்டலங்கள், அதிகாரப்பூர்வ எச்சரிக்கைகள், மீன்பிடி திட்டம் அனைத்தும் ஒரே இடத்தில்.",
        "cta_plan": "பயணத்தைத் திட்டமிடுங்கள்", "cta_sea": "கடல் நிலையைப் பாருங்கள்",
        "fact1": "அதிகாரப்பூர்வ எச்சரிக்கைகள்", "fact2": "நேரடி கடல் தகவல்", "fact3": "கேரள மீன்பிடி பதிவுகள்",
        "plan_h": "இந்தப் பயணம் பற்றி சொல்லுங்கள்",
        "cap_help": "ஒரு பயணத்தில் கரைக்குக் கொண்டுவரக்கூடிய கிலோகிராம்",
        "landing": "இறங்கு மையங்கள்:",
        "sum_k": "உங்கள் பயணம் ஒரே பார்வையில்",
        "sum_district": "மாவட்டம்", "sum_season": "பருவம்", "sum_capacity": "கொள்ளளவு", "sum_sea": "இப்போதைய கடல்",
        "sum_value": "மதிப்பிடப்பட்ட மீன் மதிப்பு",
        "sum_cov": "வழக்கமான பிடிப்பில் {pct}% க்கு மட்டுமே விலை உள்ளது · விலை ஒரு முன்மாதிரி மதிப்பீடு",
        "sum_btn": "மீன்பிடி திட்டத்தைப் பாருங்கள்",
        "sea_h": "கடலுக்குச் செல்வது பாதுகாப்பானதா?",
        "show_cols": "அனைத்து முன்னறிவிப்பு நெடுவரிசைகளையும் காட்டு",
        "hourly_h": "மணி வாரியாக",
        "zones_h": "இன்று மீன்கள் எங்கே கூடுகின்றன?",
        "prices_h": "இந்த {season} பருவத்தில் மீன் விலை",
        "same_price": "எல்லா மாவட்டங்களிலும் ஒரே கணிக்கப்பட்ட விலை",
        "season_bars": "நான்கு பருவங்களின் விலை; அதிகபட்ச பருவம் நிரப்பப்பட்டுள்ளது.",
        "catch_cov": "இந்த {n} வகைகள் {district} மாவட்டத்தின் வழக்கமான பிடிப்பில் {pct}%. மீதிக்கு விலை தகவல் இல்லை, அது கணக்கிடப்படவில்லை.",
        "cmp_h": "ஒவ்வொரு மீனும் அதிகம் எங்கே?",
        "cmp_sub": "ஒவ்வொரு மாவட்டத்தின் வழக்கமான பிடிப்பில் பங்கு. உங்கள் மாவட்டம் முன்னிலைப்படுத்தப்பட்டுள்ளது.",
        "real_catch": "உண்மையான பிடிப்பு தகவல், கேரள மீன்வளத் துறை 2022-25",
        "ref_h": "மீன் பெயர்களும் தகவல் ஆதாரங்களும்",
        "sources_h": "தகவல் ஆதாரங்கள்",
        "sources": [
            ("உண்மை · வரலாற்று", "கேரள மீன்வளத் துறை", "மாவட்ட பிடிப்பு அறிக்கைகள், 2022-23 முதல் 2024-25 வரை. பிடிப்பு பங்கிற்குப் பயன்படுகிறது."),
            ("மாதிரி · முன்மாதிரி", "விலை மாதிரி (FMPIS அடிப்படை)", "ஒரு உண்மையான FMPIS வாரத்தை (24-30 மார்ச் 2025) அடிப்படையாகக் கொண்ட செயற்கை தரவில் பயிற்சி பெற்றது."),
            ("நேரடி · அதிகாரப்பூர்வ", "NDMA சசேத் வழியாக IMD, INCOIS எச்சரிக்கைகள்", "வெளியிட்டபடியே காட்டப்படுகிறது; ஒவ்வொரு 10 நிமிடமும் சரிபார்க்கப்படுகிறது."),
            ("நேரடி · அதிகாரப்பூர்வ", "INCOIS சாத்தியமான மீன்பிடி மண்டலங்கள்", "INCOIS ஜியோசர்வரிலிருந்து தினசரி அறிவிப்பு கோடுகள்."),
            ("நேரடி · முன்னறிவிப்பு மாதிரி", "Open-Meteo கடல், வானிலை", "அலை, காற்று, ஓதம், நீரோட்டம், வானம். அதிகாரப்பூர்வ எச்சரிக்கை அல்ல."),
        ],
        "foot_about": ("கேரள மீனவர்களுக்கான ஒரு முன்மாதிரி உதவிக் கருவி: கடல் பாதுகாப்பு, அதிகாரப்பூர்வ எச்சரிக்கைகள், "
                       "மீன் மண்டலங்கள், மீன்பிடி திட்டம் - ஆங்கிலம், மலையாளம், தமிழில்."),
        "foot_sections": "பிரிவுகள்", "back_top": "மேலே செல்ல",
    },
}

SOURCE_DOTS = ["#1E9E6A", "#E3A132", "#48D6C8", "#48D6C8", "#5A9FC0"]
SOURCE_INK = ["var(--calm-ink)", "var(--caution-ink)", "var(--teal)", "var(--teal)", "var(--ocean)"]
