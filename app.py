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
/* ─── Premium Typography & Font Imports ─── */
@import url('https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&f[]=clash-display@500,600,700&display=swap');

:root {
    --theme-text-primary: #0a0f18;
    --theme-text-secondary: #4a5568;
    --theme-text-weak: rgba(10, 15, 24, 0.5);
    
    --theme-bg-canvas: #f8fafc;
    --theme-bg-glass: rgba(255, 255, 255, 0.75);
    --theme-bg-glass-hover: rgba(255, 255, 255, 0.9);
    
    --theme-accent: #2563eb;
    --theme-accent-hover: #1d4ed8;
    --theme-accent-glow: rgba(37, 99, 235, 0.2);
    
    --theme-border: rgba(10, 15, 24, 0.08);
    --theme-border-glow: rgba(37, 99, 235, 0.15);
    
    --shadow-sm: 0 2px 8px -2px rgba(10, 15, 24, 0.05), inset 0 1px 0 rgba(255,255,255,0.6);
    --shadow-md: 0 4px 20px -4px rgba(10, 15, 24, 0.08), inset 0 1px 0 rgba(255,255,255,0.8);
    --shadow-lg: 0 12px 32px -8px rgba(10, 15, 24, 0.12), inset 0 1px 0 rgba(255,255,255,0.9);
    --shadow-float: 0 20px 40px -12px rgba(37, 99, 235, 0.15), 0 0 0 1px var(--theme-border-glow);
}

/* Base Styles */
html, body, [class*="st-"] {
    font-family: 'Satoshi', -apple-system, sans-serif !important;
    color: var(--theme-text-primary) !important;
    letter-spacing: 0.2px;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Clash Display', sans-serif !important;
    letter-spacing: -0.01em !important;
    color: var(--theme-text-primary) !important;
}

h1 {
    font-size: 3rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #0a0f18 0%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

/* Core App Canvas */
.stApp {
    background: var(--theme-bg-canvas) !important;
    background-image: 
        radial-gradient(circle at 10% 20%, rgba(37, 99, 235, 0.05) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(37, 99, 235, 0.08) 0%, transparent 40%) !important;
    background-attachment: fixed !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(248, 250, 252, 0.6) !important;
    backdrop-filter: blur(24px) saturate(180%) !important;
    border-right: 1px solid var(--theme-border) !important;
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    font-weight: 600;
    font-size: 1.25rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* Premium Buttons */
.stButton > button {
    background: var(--theme-bg-glass) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid var(--theme-border) !important;
    border-radius: 14px !important;
    color: var(--theme-text-primary) !important;
    font-weight: 600 !important;
    padding: 16px 28px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: var(--shadow-lg) !important;
    border-color: var(--theme-border-glow) !important;
    background: #ffffff !important;
}
.stButton > button[kind="primary"] {
    background: var(--theme-accent) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 4px 16px var(--theme-accent-glow), inset 0 1px 0 rgba(255,255,255,0.2) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--theme-accent-hover) !important;
    box-shadow: 0 8px 24px rgba(37,99,235,0.3), inset 0 1px 0 rgba(255,255,255,0.2) !important;
}

/* Glassmorphic Metrics */
[data-testid="stMetric"] {
    background: var(--theme-bg-glass) !important;
    backdrop-filter: blur(16px) saturate(180%);
    border: 1px solid var(--theme-border) !important;
    border-radius: 20px !important;
    padding: 24px !important;
    box-shadow: var(--shadow-md) !important;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) backwards;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-float) !important;
    background: #ffffff !important;
}
[data-testid="stMetricValue"] > div {
    font-family: 'Clash Display', sans-serif !important;
    font-weight: 600 !important;
    font-size: 2.5rem !important;
    color: var(--theme-accent) !important;
}
[data-testid="stMetricLabel"] > div {
    font-size: 0.9rem !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--theme-text-secondary) !important;
    font-weight: 500;
}

/* Chat Input */
.stChatInput > div {
    border-radius: 24px !important;
    border: 1px solid var(--theme-border) !important;
    background: rgba(255, 255, 255, 0.8) !important;
    backdrop-filter: blur(20px) !important;
    box-shadow: var(--shadow-lg) !important;
    transition: all 0.4s ease !important;
    padding: 4px 8px !important;
}
.stChatInput > div:focus-within {
    border-color: var(--theme-accent) !important;
    box-shadow: var(--shadow-float) !important;
    transform: translateY(-2px);
    background: #ffffff !important;
}

/* Chat Messages */
[data-testid="stChatMessage"] {
    background: var(--theme-bg-glass) !important;
    backdrop-filter: blur(16px);
    border: 1px solid var(--theme-border);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: var(--shadow-md);
    animation: messageReveal 0.6s cubic-bezier(0.16, 1, 0.3, 1) backwards;
}
[data-testid="stChatMessage"] * {
    color: var(--theme-text-primary) !important;
}

/* Expanders & DataFrames */
[data-testid="stExpander"] {
    background: var(--theme-bg-glass) !important;
    backdrop-filter: blur(16px);
    border: 1px solid var(--theme-border) !important;
    border-radius: 16px !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stDataFrame"] {
    border-radius: 12px;
    border: 1px solid var(--theme-border);
    box-shadow: var(--shadow-md);
}

/* Recommendation Cards */
.rec-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.9), rgba(248,250,252,0.8));
    border: 1px solid rgba(37,99,235,0.1);
    border-left: 4px solid var(--theme-accent);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 16px;
    font-size: 1.05rem;
    line-height: 1.6;
    box-shadow: var(--shadow-sm);
    transition: all 0.3s ease;
}
.rec-card:hover {
    transform: translateX(4px);
    box-shadow: var(--shadow-md);
    border-color: rgba(37,99,235,0.2);
}

/* Custom Selectbox */
div[data-baseweb="select"] > div {
    border-radius: 14px !important;
    border: 1px solid var(--theme-border) !important;
    background: rgba(255, 255, 255, 0.7) !important;
    backdrop-filter: blur(12px) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.3s ease !important;
}
div[data-baseweb="select"] > div:hover {
    border-color: var(--theme-accent) !important;
    background: #ffffff !important;
}

/* Animations */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(24px); filter: blur(8px); }
    to { opacity: 1; transform: translateY(0); filter: blur(0); }
}
@keyframes messageReveal {
    from { opacity: 0; transform: translateY(16px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Global Noise Overlay (Pointer-events none) */
.noise-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    pointer-events: none;
    opacity: 0.04;
    background-image: url('data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)"/%3E%3C/svg%3E');
}
</style>
<div class="noise-overlay"></div>
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
