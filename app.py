"""
Schedule Advisor — Streamlit Chatbot
=====================================
A premium chatbot UI powered by Gemini 2.5 Flash that analyses
class-schedule CSVs from the ``out/`` directory and answers
natural-language queries about availability, conflicts, and
attendance.
"""

import glob
import json
import os

import pandas as pd
import streamlit as st

from advisor import ask_advisor, init_gemini_client
from query_engine import execute_query
from schedule_parser import (
    DAYS,
    TIME_SLOTS,
    build_schedule_context,
    entries_to_dicts,
    load_csv,
    parse_with_gemini,
)

# ── Page configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="Schedule Advisor",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium CSS ─────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap');

:root {
    --accent: #1b61c9;
    --accent-light: #254fad;
    --surface: #ffffff;
    --surface2: #f8fafc;
    --card-bg: #ffffff;
    --card-border: #e0e2e6;
    --text-primary: #181d26;
    --text-muted: #333333;
    --text-weak: rgba(4,14,32,0.69);
    --shadow-blue: rgba(0,0,0,0.32) 0px 0px 1px, rgba(0,0,0,0.08) 0px 0px 2px, rgba(45,127,249,0.28) 0px 1px 3px, rgba(0,0,0,0.06) 0px 0px 0px 0.5px inset;
    --shadow-soft: rgba(15,48,106,0.05) 0px 0px 20px;
}

html, body, [class*="st-"] {
    font-family: 'Haas', -apple-system, system-ui, 'Segoe UI', Roboto, sans-serif !important;
    letter-spacing: 0.18px;
}

/* Force Light Mode / Airtable canvas */
.stApp {
    background: var(--surface) !important;
}
.stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp span, .stApp div {
    color: var(--text-primary);
}

/* ─── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: var(--surface2) !important;
    border-right: 1px solid var(--card-border);
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    background: none;
    -webkit-text-fill-color: var(--text-primary);
    color: var(--text-primary) !important;
    font-weight: 700;
    letter-spacing: 0.12px;
}
section[data-testid="stSidebar"] .stMarkdown p {
    color: var(--text-muted) !important;
}

/* ─── Metric cards ─── */
[data-testid="stMetric"] {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: var(--shadow-soft);
    transition: box-shadow .2s, border-color .2s;
}
[data-testid="stMetric"]:hover {
    border-color: var(--accent);
    box-shadow: var(--shadow-blue);
}
[data-testid="stMetricLabel"] > div {
    color: var(--text-muted) !important;
    font-size: 14px !important;
    letter-spacing: 0.28px !important;
}
[data-testid="stMetricValue"] > div {
    font-weight: 700;
    font-size: 1.8rem !important;
    background: none;
    -webkit-text-fill-color: var(--text-primary);
    color: var(--text-primary) !important;
    letter-spacing: normal !important;
}
[data-testid="stMetricDelta"] > div {
    color: var(--text-weak) !important;
}

/* ─── Header ─── */
h1 {
    background: none;
    -webkit-text-fill-color: var(--text-primary);
    color: var(--text-primary) !important;
    font-weight: 900 !important;
    letter-spacing: normal !important;
}

/* ─── Chat input ─── */
.stChatInput > div {
    border: 1px solid var(--card-border) !important;
    border-radius: 12px !important;
    background: var(--card-bg) !important;
    box-shadow: var(--shadow-soft) !important;
    transition: border-color .2s, box-shadow .2s;
}
.stChatInput > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: var(--shadow-blue) !important;
}

/* ─── Chat messages ─── */
[data-testid="stChatMessage"] {
    border-radius: 16px;
    border: 1px solid var(--card-border);
    background: var(--card-bg) !important;
    box-shadow: var(--shadow-soft);
    padding: 16px 20px;
    margin-bottom: 8px;
    animation: fadeSlideIn .35s ease-out;
}
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ─── Buttons ─── */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 500;
    letter-spacing: 0.08px;
    padding: 16px 24px !important;
    box-shadow: var(--shadow-soft) !important;
    transition: transform .15s, box-shadow .2s;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-blue) !important;
}

.stButton > button[kind="secondary"],
.stButton > button[data-testid="stBaseButton-secondary"] {
    background: #ffffff !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 12px !important;
    font-weight: 500;
    letter-spacing: 0.08px;
    transition: border-color .15s, box-shadow .2s;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button[data-testid="stBaseButton-secondary"]:hover {
    border-color: var(--accent) !important;
    box-shadow: var(--shadow-blue) !important;
}

/* ─── Expanders ─── */
[data-testid="stExpander"] {
    border: 1px solid var(--card-border) !important;
    border-radius: 16px !important;
    background: var(--card-bg) !important;
    box-shadow: var(--shadow-soft) !important;
}
[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

/* ─── Dataframes ─── */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    border: 1px solid var(--card-border);
    overflow: hidden;
}

/* ─── Divider ─── */
hr {
    border-color: var(--card-border) !important;
}

/* ─── Info / success / warning banners ─── */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid var(--card-border) !important;
    color: var(--text-primary) !important;
}

/* ─── Badge pill (used in sidebar) ─── */
.badge-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 500;
    background: var(--accent);
    color: #ffffff;
    letter-spacing: 0.08px;
}

/* ─── Recommendation cards ─── */
.rec-card {
    background: var(--surface2);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 12px;
    font-size: 16px;
    line-height: 1.30;
    letter-spacing: 0.08px;
    box-shadow: var(--shadow-soft);
    color: var(--text-primary);
}
.rec-card::before {
    content: "💡 ";
}

/* Custom Selectbox styling for Airtable feel */
div[data-baseweb="select"] > div {
    border-radius: 12px !important;
    border-color: var(--card-border) !important;
    background-color: var(--card-bg) !important;
    color: var(--text-primary) !important;
}
div[data-baseweb="select"] > div:hover {
    border-color: var(--accent) !important;
}
div[data-baseweb="popover"] * {
    color: var(--text-primary) !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Environment loader ──────────────────────────────────────────────
def _load_env() -> None:
    """Load .env from the project root into os.environ."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value


_load_env()


# ── Session-state defaults ──────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "schedule_entries" not in st.session_state:
    st.session_state.schedule_entries = None
if "schedule_context" not in st.session_state:
    st.session_state.schedule_context = ""
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = None


# ── Gemini client init ──────────────────────────────────────────────
def _ensure_client() -> bool:
    """Try to initialise the Gemini client. Returns True on success."""
    if st.session_state.gemini_client is not None:
        return True
    try:
        st.session_state.gemini_client = init_gemini_client()
        return True
    except ValueError as exc:
        st.error(f"⚠️ {exc}")
        return False


# ── Discover CSVs in out/ ───────────────────────────────────────────
OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT_DIR, exist_ok=True)
csv_files = sorted(glob.glob(os.path.join(OUT_DIR, "*.csv")))


# ══════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 📅 Schedule Advisor")
    st.caption("Powered by Gemini 2.5 Flash")
    st.markdown("---")

    # CSV selector ────────────────────────────────────────────────────
    if not csv_files:
        st.warning(
            "No CSV files found in **out/**.\n\n"
            "Run `python main.py` first to generate the schedule CSV."
        )
        st.stop()

    selected_csv = st.selectbox(
        "📂 Schedule CSV",
        csv_files,
        format_func=lambda p: os.path.basename(p),
    )

    # Load / parse button ────────────────────────────────────────────
    load_clicked = st.button("⚡ Load & Parse Schedule", type="primary", use_container_width=True)

    if load_clicked or st.session_state.schedule_entries is not None:
        if st.session_state.schedule_entries is None:
            # ── Caching logic ───────────────────────────────────────
            cache_file = selected_csv.replace(".csv", ".parsed.json")
            cached_data = None
            
            # Check if cache exists and is newer than CSV
            if os.path.exists(cache_file) and os.path.getmtime(cache_file) >= os.path.getmtime(selected_csv):
                try:
                    with open(cache_file, "r") as f:
                        cached_data = json.load(f)
                except Exception:
                    pass

            if cached_data:
                st.session_state.schedule_entries = [
                    from_dict(ScheduleEntry, item) if 'from_dict' in globals() else ScheduleEntry(**item)
                    for item in cached_data
                ]
                st.session_state.schedule_context = build_schedule_context(st.session_state.schedule_entries)
                st.toast("✅ Loaded from cache!", icon="💾")
            else:
                if not _ensure_client():
                    st.stop()
                with st.spinner("🔄 Parsing schedule with Gemini…"):
                    raw_rows = load_csv(selected_csv)
                    entries = parse_with_gemini(
                        st.session_state.gemini_client, raw_rows
                    )
                    if not entries:
                        st.error("❌ Failed to parse schedule. Gemini might be down (503). Try again later.")
                        st.stop()
                    
                    st.session_state.schedule_entries = entries
                    st.session_state.schedule_context = build_schedule_context(entries)
                    
                    # Save to cache
                    try:
                        with open(cache_file, "w") as f:
                            json.dump(entries_to_dicts(entries), f, indent=2)
                    except Exception:
                        pass
                    
                    st.toast("✅ Schedule parsed and cached!", icon="📅")

        entries = st.session_state.schedule_entries
        persons = sorted(set(e.person for e in entries))

        # Summary metrics ────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📊 Overview")

        col1, col2 = st.columns(2)
        col1.metric("People", len(persons))
        col2.metric("Classes", len(entries))

        # Per-person breakdown ────────────────────────────────────────
        st.markdown("#### 👥 Per Person")
        for person in persons:
            person_count = sum(1 for e in entries if e.person == person)
            busy_days = len(set(e.day for e in entries if e.person == person))
            st.metric(
                label=f"{person}",
                value=f"{person_count} classes",
                delta=f"{busy_days} active days",
            )

        # Reload action ──────────────────────────────────────────────
        st.markdown("---")
        if st.button("🔄 Reload Data", use_container_width=True):
            st.session_state.schedule_entries = None
            st.session_state.schedule_context = ""
            st.session_state.messages = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════
#  MAIN CHAT AREA
# ══════════════════════════════════════════════════════════════════════
st.title("📅 Schedule Advisor")
st.caption(
    "Ask me about free slots, class conflicts, attendance, and scheduling recommendations."
)

# Guard: schedule must be loaded ──────────────────────────────────────
if st.session_state.schedule_entries is None:
    st.info(
        "👈 **Load a schedule CSV** from the sidebar to get started.",
        icon="📂",
    )
    st.stop()


# ── Helper: render a single assistant message ───────────────────────
def _render_assistant_msg(msg: dict) -> None:
    """Display explanation, query params, results table, and recs."""
    # Explanation text
    st.markdown(msg["content"])

    # Query parameters expander
    qp = msg.get("query_params")
    if qp:
        with st.expander("🔍 Structured Query Parameters", expanded=False):
            st.json(qp)

    # Results table
    results = msg.get("results")
    if results:
        with st.expander(f"📋 Results ({len(results)} rows)", expanded=True):
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # Recommendations
    recs = msg.get("recommendations")
    if recs:
        st.markdown("**Recommendations**")
        for rec in recs:
            st.markdown(
                f'<div class="rec-card">{rec}</div>',
                unsafe_allow_html=True,
            )


# ── Render chat history ─────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            _render_assistant_msg(msg)
        else:
            st.markdown(msg["content"])


# ── Chat input / response loop ──────────────────────────────────────
if prompt := st.chat_input("Ask about the schedule …"):
    if not _ensure_client():
        st.stop()

    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate advisor response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing schedule …"):
            advisor_resp = ask_advisor(
                st.session_state.gemini_client,
                # Only send role+content for the LLM history
                [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                st.session_state.schedule_context,
            )

            query_params = advisor_resp.get("query_params", {})
            explanation = advisor_resp.get("explanation", "")
            recommendations = advisor_resp.get("recommendations", [])

            # Execute the structured query against the data engine
            query_result = execute_query(
                st.session_state.schedule_entries, query_params
            )
            results = query_result.get("results", [])

            # Build the message dict for history
            assistant_msg = {
                "role": "assistant",
                "content": explanation,
                "query_params": query_params,
                "results": results,
                "recommendations": recommendations,
            }
            st.session_state.messages.append(assistant_msg)

        # Render the response
        _render_assistant_msg(assistant_msg)
