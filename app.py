"""
Schedule Advisor — Streamlit Landing Page + Chatbot
=====================================================
A premium landing-page-first experience powered by Gemini 2.5 Flash
that analyses class-schedule CSVs and answers natural-language queries.
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
    page_title="Schedule Advisor · 1000 JAY",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Premium CSS ─────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ─── Font Import ─── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --navy: #181d26;
    --navy-soft: rgba(24,29,38,0.72);
    --navy-weak: rgba(24,29,38,0.48);
    --blue: #1b61c9;
    --blue-hover: #1550a8;
    --blue-glow: rgba(27,97,201,0.12);
    --blue-tint: rgba(27,97,201,0.06);
    --white: #ffffff;
    --surface: #f8fafc;
    --border: #e0e2e6;
    --border-hover: #c8ccd2;
    --green: #006400;

    --shadow-card: 0 0 1px rgba(0,0,0,0.32), 0 0 2px rgba(0,0,0,0.08), 0 1px 3px rgba(45,127,249,0.28), 0 0 0 0.5px rgba(0,0,0,0.06) inset;
    --shadow-soft: 0 0 20px rgba(15,48,106,0.05);
    --shadow-hover: 0 4px 16px rgba(27,97,201,0.18), 0 0 1px rgba(0,0,0,0.2);
    --shadow-float: 0 12px 32px rgba(27,97,201,0.14), 0 0 0 1px rgba(27,97,201,0.08);

    --radius-sm: 2px;
    --radius-btn: 12px;
    --radius-card: 16px;
    --radius-section: 24px;
    --radius-lg: 32px;
}

/* ─── Base Reset ─── */
html, body, [class*="st-"] {
    font-family: 'DM Sans', -apple-system, system-ui, 'Segoe UI', sans-serif !important;
    color: var(--navy) !important;
    letter-spacing: 0.12px;
}
h1, h2, h3, h4, h5, h6,
[data-testid="stMetricLabel"] > div {
    font-family: 'Space Grotesk', 'DM Sans', sans-serif !important;
    color: var(--navy) !important;
}

/* ─── App Canvas ─── */
.stApp {
    background: var(--white) !important;
}

/* ─── Hide default header & footer ─── */
header[data-testid="stHeader"] { background: transparent !important; }
footer { display: none !important; }
#MainMenu { visibility: hidden; }

/* ─── Hero Section ─── */
.hero-wrapper {
    padding: 80px 0 64px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero-wrapper::before {
    content: '';
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse 70% 50% at 50% 0%, var(--blue-tint) 0%, transparent 70%),
        radial-gradient(circle at 80% 90%, rgba(27,97,201,0.04) 0%, transparent 50%);
    pointer-events: none;
}
.hero-badge {
    display: inline-block;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 100px;
    padding: 6px 18px;
    font-size: 13px;
    font-weight: 500;
    color: var(--blue);
    letter-spacing: 0.4px;
    margin-bottom: 28px;
    animation: fadeUp 0.6s ease-out both;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 56px;
    font-weight: 700;
    line-height: 1.1;
    color: var(--navy);
    margin: 0 0 20px;
    animation: fadeUp 0.7s ease-out 0.1s both;
}
.hero-title span {
    color: var(--blue);
}
.hero-subtitle {
    font-size: 19px;
    line-height: 1.55;
    color: var(--navy-soft);
    width: 100%;
    font-weight: 400;
    animation: fadeUp 0.7s ease-out 0.2s both;
}
.hero-cta-row {
    display: flex;
    justify-content: center;
    gap: 14px;
    animation: fadeUp 0.7s ease-out 0.3s both;
}

/* ─── Feature Cards ─── */
.features-section {
    padding: 48px 0 64px;
}
.features-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}
.feature-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--radius-card);
    padding: 32px 28px;
    transition: all 0.35s cubic-bezier(0.16,1,0.3,1);
    box-shadow: var(--shadow-soft);
    animation: fadeUp 0.7s ease-out both;
}
.feature-card:nth-child(1) { animation-delay: 0.15s; }
.feature-card:nth-child(2) { animation-delay: 0.25s; }
.feature-card:nth-child(3) { animation-delay: 0.35s; }
.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-hover);
    border-color: var(--border-hover);
}
.feature-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: var(--blue-tint);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    margin-bottom: 20px;
}
.feature-card h4 {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 10px;
    letter-spacing: 0.08px;
}
.feature-card p {
    font-size: 15px;
    line-height: 1.55;
    color: var(--navy-soft);
    margin: 0;
    letter-spacing: 0.08px;
}

/* ─── Stats Row ─── */
.stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 16px;
    padding: 20px 0;
}
.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-card);
    padding: 24px 20px;
    text-align: center;
    transition: all 0.3s ease;
}
.stat-card:hover {
    border-color: var(--blue);
    box-shadow: var(--shadow-card);
}
.stat-value {
    font-family: 'Space Grotesk', monospace;
    font-size: 32px;
    font-weight: 700;
    color: var(--blue);
    line-height: 1;
    margin-bottom: 6px;
}
.stat-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--navy-weak);
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ─── Divider ─── */
.section-divider {
    width: 100%;
    height: 1px;
    background: var(--border);
    margin: 32px 0;
}

/* ─── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 15px;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: var(--navy-weak);
}

/* ─── Buttons ─── */
.stButton > button {
    border-radius: var(--radius-btn) !important;
    font-weight: 500 !important;
    letter-spacing: 0.08px !important;
    padding: 12px 24px !important;
    transition: all 0.3s cubic-bezier(0.16,1,0.3,1) !important;
    border: 1px solid var(--border) !important;
    background: var(--white) !important;
    color: var(--navy) !important;
    box-shadow: var(--shadow-soft) !important;
}
.stButton > button:hover {
    border-color: var(--blue) !important;
    box-shadow: var(--shadow-card) !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"] {
    background: var(--blue) !important;
    color: var(--white) !important;
    border: none !important;
    box-shadow: 0 2px 8px var(--blue-glow) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--blue-hover) !important;
    box-shadow: 0 6px 20px rgba(27,97,201,0.25) !important;
}

/* ─── Metrics ─── */
[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-card) !important;
    padding: 20px !important;
    transition: all 0.3s ease !important;
}
[data-testid="stMetric"]:hover {
    border-color: var(--blue) !important;
    box-shadow: var(--shadow-card) !important;
}
[data-testid="stMetricValue"] > div {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 2rem !important;
    color: var(--blue) !important;
}
[data-testid="stMetricLabel"] > div {
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--navy-weak) !important;
    font-weight: 500;
}

/* ─── Chat Input ─── */
.stChatInput > div {
    border-radius: var(--radius-btn) !important;
    border: 1px solid var(--border) !important;
    background: var(--white) !important;
    box-shadow: var(--shadow-soft) !important;
    transition: all 0.3s ease !important;
}
.stChatInput > div:focus-within {
    border-color: var(--blue) !important;
    box-shadow: var(--shadow-card) !important;
}

/* ─── Chat Messages ─── */
[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border);
    border-radius: var(--radius-card);
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-soft);
    animation: messageIn 0.4s ease-out backwards;
}
[data-testid="stChatMessage"] * {
    color: var(--navy) !important;
}

/* ─── Expanders & DataFrames ─── */
[data-testid="stExpander"] {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-btn) !important;
    box-shadow: var(--shadow-soft) !important;
}
[data-testid="stDataFrame"] {
    border-radius: var(--radius-btn);
    border: 1px solid var(--border);
}

/* ─── Recommendation Cards ─── */
.rec-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--blue);
    border-radius: var(--radius-btn);
    padding: 16px 20px;
    margin-bottom: 12px;
    font-size: 15px;
    line-height: 1.55;
    letter-spacing: 0.08px;
    transition: all 0.25s ease;
}
.rec-card:hover {
    border-color: var(--border-hover);
    border-left-color: var(--blue);
    box-shadow: var(--shadow-card);
    transform: translateX(3px);
}

/* ─── Selectbox ─── */
div[data-baseweb="select"] > div {
    border-radius: var(--radius-btn) !important;
    border: 1px solid var(--border) !important;
    background: var(--white) !important;
    transition: all 0.25s ease !important;
}
div[data-baseweb="select"] > div:hover {
    border-color: var(--blue) !important;
}

/* ─── Animations ─── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes messageIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ─── Chat Section Header ─── */
.chat-header {
    padding: 32px 0 8px;
}
.chat-header h2 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 28px;
    font-weight: 600;
    color: var(--navy);
    margin: 0;
}
.chat-header p {
    font-size: 15px;
    color: var(--navy-soft);
    margin: 6px 0 0;
    letter-spacing: 0.08px;
}

/* ─── Footer ─── */
.app-footer {
    text-align: center;
    padding: 40px 0 24px;
    color: var(--navy-weak);
    font-size: 13px;
    letter-spacing: 0.2px;
    border-top: 1px solid var(--border);
    margin-top: 48px;
}
.app-footer a {
    color: var(--blue);
    text-decoration: none;
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
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False


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
    st.markdown("### Schedule Advisor")
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
        "Schedule CSV",
        csv_files,
        format_func=lambda p: os.path.basename(p),
    )

    # Load / parse button ────────────────────────────────────────────
    load_clicked = st.button("Load & Parse Schedule", type="primary", use_container_width=True)

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
                from schedule_parser import ScheduleEntry
                st.session_state.schedule_entries = [
                    ScheduleEntry(**item) for item in cached_data
                ]
                st.session_state.schedule_context = build_schedule_context(st.session_state.schedule_entries)
                st.session_state.show_chat = True
                st.toast("Loaded from cache!", icon="✅")
            else:
                if not _ensure_client():
                    st.stop()
                with st.spinner("Parsing schedule with Gemini…"):
                    raw_rows = load_csv(selected_csv)
                    entries = parse_with_gemini(
                        st.session_state.gemini_client, raw_rows
                    )
                    if not entries:
                        st.error("Failed to parse schedule. Gemini might be down (503). Try again later.")
                        st.stop()

                    st.session_state.schedule_entries = entries
                    st.session_state.schedule_context = build_schedule_context(entries)
                    st.session_state.show_chat = True

                    # Save to cache
                    try:
                        with open(cache_file, "w") as f:
                            json.dump(entries_to_dicts(entries), f, indent=2)
                    except Exception:
                        pass

                    st.toast("Schedule parsed and cached!", icon="✅")

        entries = st.session_state.schedule_entries
        persons = sorted(set(e.person for e in entries))

        # Summary metrics ────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### Overview")

        col1, col2 = st.columns(2)
        col1.metric("People", len(persons))
        col2.metric("Classes", len(entries))

        # Per-person breakdown ────────────────────────────────────────
        st.markdown("#### Per Person")
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
        if st.button("Reload Data", use_container_width=True):
            st.session_state.schedule_entries = None
            st.session_state.schedule_context = ""
            st.session_state.messages = []
            st.session_state.show_chat = False
            st.rerun()


# ══════════════════════════════════════════════════════════════════════
#  LANDING PAGE (shown when no schedule is loaded)
# ══════════════════════════════════════════════════════════════════════
if not st.session_state.show_chat or st.session_state.schedule_entries is None:
    # Hero
    st.markdown("""
    <div class="hero-wrapper">
        <div class="hero-badge">AI-Powered Scheduling · Built with Gemini 2.5 Flash</div>
        <h1 class="hero-title">Your schedule,<br><span>intelligently organized.</span></h1>
        <p class="hero-subtitle">
            Upload class schedules, ask natural-language questions, and get instant
            insights about availability, conflicts, and the best times to meet.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature Cards
    st.markdown("""
    <div class="features-section">
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <h4>Smart Queries</h4>
                <p>Ask questions in plain English. Find free slots, check conflicts, or discover common availability across your entire group.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h4>Schedule Analytics</h4>
                <p>See attendance heatmaps, busiest time slots, and per-person breakdowns — all derived automatically from your data.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h4>Instant Parsing</h4>
                <p>OCR-extracted schedule images are parsed by Gemini into structured data, cached locally for lightning-fast reloads.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CTA
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.info(
            "**Get started →** Open the sidebar and load a schedule CSV to begin chatting with your advisor.",
            icon="📂",
        )

    # Footer
    st.markdown("""
    <div class="app-footer">
        Schedule Advisor · 1000 JAY &nbsp;·&nbsp; Powered by <a href="https://deepmind.google/technologies/gemini/">Gemini 2.5 Flash</a>
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ══════════════════════════════════════════════════════════════════════
#  CHAT AREA (shown after schedule is loaded)
# ══════════════════════════════════════════════════════════════════════

entries = st.session_state.schedule_entries
persons = sorted(set(e.person for e in entries))

# Stats bar
st.markdown(f"""
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-value">{len(persons)}</div>
        <div class="stat-label">People</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{len(entries)}</div>
        <div class="stat-label">Classes</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{len(set(e.course for e in entries))}</div>
        <div class="stat-label">Courses</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{len(set(e.day for e in entries))}</div>
        <div class="stat-label">Active Days</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="chat-header">
    <h2>Schedule Advisor</h2>
    <p>Ask about free slots, class conflicts, attendance, and scheduling recommendations.</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


# ── Helper: render a single assistant message ───────────────────────
def _render_assistant_msg(msg: dict) -> None:
    """Display explanation, query params, results table, and recs."""
    # Explanation text
    st.markdown(msg["content"])

    # Query parameters expander
    qp = msg.get("query_params")
    if qp:
        with st.expander("Structured Query Parameters", expanded=False):
            st.json(qp)

    # Results table
    results = msg.get("results")
    if results:
        with st.expander(f"Results ({len(results)} rows)", expanded=True):
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
