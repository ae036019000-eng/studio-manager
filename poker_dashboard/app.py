"""
דשבורד ניהול בנקרול פוקר — GG Poker
הרצה:  streamlit run app.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

import database as db
import parser as hh_parser

# ── קבועים ───────────────────────────────────────────────────────────────────

HAND_HISTORY_FOLDER = Path(__file__).parent / "Poker_New_Era"

# ── הגדרת עמוד ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="דשבורד בנקרול פוקר",
    page_icon="♠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS — מותאם אייפון + RTL עברית ───────────────────────────────────────────

st.markdown(
    """
    <style>
    /* ── בסיס RTL ── */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0d1117;
        color: #e6edf3;
        direction: rtl;
        font-family: 'Segoe UI', 'Arial Hebrew', Arial, system-ui, sans-serif;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background-color: #161b22; direction: rtl; }

    /* ── ריפוד ראשי — צר יותר במובייל ── */
    .block-container {
        padding: 1rem 1rem 2rem 1rem !important;
        max-width: 100% !important;
    }

    /* ── טיפוגרפיה ── */
    h1, h2, h3, h4 { color: #e6edf3; font-weight: 700; }

    /* ── רשת KPI — רספונסיבית ── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-bottom: 4px;
    }
    @media (min-width: 768px) {
        .kpi-grid { grid-template-columns: repeat(5, 1fr); }
        .block-container { padding: 2rem 3rem 3rem 3rem !important; }
    }

    /* ── כרטיס KPI ── */
    .kpi-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 18px 12px;
        text-align: center;
        transition: border-color .2s;
        -webkit-tap-highlight-color: transparent;
    }
    .kpi-card:active { border-color: #58a6ff; transform: scale(0.98); }
    @media (min-width: 768px) {
        .kpi-card { padding: 24px 20px; }
        .kpi-card:hover { border-color: #58a6ff; }
    }
    .kpi-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #8b949e;
        margin-bottom: 8px;
        line-height: 1.3;
    }
    @media (min-width: 768px) { .kpi-label { font-size: 0.78rem; } }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        line-height: 1;
        direction: ltr;
        display: inline-block;
    }
    @media (min-width: 768px) { .kpi-value { font-size: 2.1rem; } }
    .kpi-sub {
        font-size: 0.68rem;
        color: #8b949e;
        margin-top: 5px;
        line-height: 1.3;
    }
    .kpi-profit  { color: #3fb950; }
    .kpi-loss    { color: #f85149; }
    .kpi-neutral { color: #58a6ff; }
    .kpi-white   { color: #e6edf3; }

    /* ── כרטיס ROI — מלא ברוחב במובייל ── */
    .kpi-full {
        grid-column: 1 / -1;
    }
    @media (min-width: 768px) { .kpi-full { grid-column: auto; } }

    /* ── כותרות סעיף ── */
    .section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #8b949e;
        margin: 0 0 14px 2px;
        border-right: 3px solid #58a6ff;
        padding-right: 10px;
    }
    @media (min-width: 768px) { .section-title { font-size: 1.1rem; } }

    /* ── תגיות סטטוס ── */
    .badge-warn {
        display: inline-block;
        background: rgba(210, 153, 34, 0.18);
        border: 1px solid #d29922;
        color: #d29922;
        border-radius: 6px;
        padding: 3px 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-ok {
        display: inline-block;
        background: rgba(63, 185, 80, 0.15);
        border: 1px solid #3fb950;
        color: #3fb950;
        border-radius: 6px;
        padding: 3px 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* ── מפריד ── */
    .divider { border: none; border-top: 1px solid #21262d; margin: 22px 0; }

    /* ── כרטיס טורניר ממתין (במקום expander) ── */
    .pending-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .pending-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #e6edf3;
        margin-bottom: 4px;
    }
    .pending-sub {
        font-size: 0.75rem;
        color: #8b949e;
        margin-bottom: 12px;
    }

    /* ── שדות קלט — גדולים יותר לאצבע ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: #0d1117 !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        padding: 12px 14px !important;
        height: 48px !important;
        direction: ltr;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 3px rgba(88,166,255,0.15) !important;
    }

    /* ── כפתורים — גדולים לאצבע ── */
    .stButton > button {
        background: #238636 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 12px 24px !important;
        min-height: 48px !important;
        width: 100% !important;
        -webkit-tap-highlight-color: transparent;
    }
    .stButton > button:active { background: #2ea043 !important; transform: scale(0.97); }
    @media (min-width: 768px) {
        .stButton > button { width: auto !important; }
    }

    /* ── Checkbox — גדול יותר ── */
    .stCheckbox > label { font-size: 0.95rem; }

    /* ── טבלה ── */
    div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
    [data-testid="stDataFrame"] td { direction: ltr; text-align: left; font-size: 0.85rem; }
    [data-testid="stDataFrame"] th { direction: rtl; text-align: right; font-size: 0.85rem; }

    /* ── גלילה חלקה ── */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

    /* ── סרגל צד — נגיש יותר במובייל ── */
    [data-testid="stSidebarContent"] { padding: 1.5rem 1rem; }

    /* ── אזור העלאת קבצים ── */
    [data-testid="stFileUploader"] {
        background: #161b22 !important;
        border: 2px dashed #30363d !important;
        border-radius: 14px !important;
        padding: 8px !important;
        transition: border-color .2s;
    }
    [data-testid="stFileUploader"]:hover,
    [data-testid="stFileUploader"]:focus-within {
        border-color: #58a6ff !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: transparent !important;
        padding: 20px 12px !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] {
        color: #8b949e !important;
        font-size: 0.9rem !important;
    }
    /* כפתור Browse בתוך ה-uploader */
    [data-testid="stFileUploaderDropzone"] button {
        background: #21262d !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        min-height: 44px !important;
        padding: 10px 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── אתחול בסיס נתונים ─────────────────────────────────────────────────────────

db.init_db()

# ── פונקציות עזר ──────────────────────────────────────────────────────────────


def scan_and_import() -> tuple[int, int]:
    if not HAND_HISTORY_FOLDER.exists():
        HAND_HISTORY_FOLDER.mkdir(parents=True, exist_ok=True)
        return 0, 0
    parsed = hh_parser.parse_folder(HAND_HISTORY_FOLDER)
    new_count = updated_count = 0
    for t in parsed:
        outcome = db.upsert_tournament(t)
        if outcome == "inserted":
            new_count += 1
        elif outcome == "updated":
            updated_count += 1
    return new_count, updated_count


def handle_uploaded_files(uploaded_files) -> tuple[int, int]:
    """שמור קבצים שהועלו לתיקייה ועבד אותם."""
    HAND_HISTORY_FOLDER.mkdir(parents=True, exist_ok=True)
    saved = 0
    for f in uploaded_files:
        dest = HAND_HISTORY_FOLDER / f.name
        dest.write_bytes(f.getvalue())
        saved += 1
    if saved == 0:
        return 0, 0
    return scan_and_import()


def fmt_money(value: float, always_sign: bool = False) -> str:
    sign = "+" if always_sign and value > 0 else ""
    return f"{sign}${value:,.2f}"


def color_class(value: float) -> str:
    if value > 0:
        return "kpi-profit"
    if value < 0:
        return "kpi-loss"
    return "kpi-neutral"


def kpi_card(label: str, value: str, sub: str = "", css_class: str = "kpi-white", full: bool = False) -> str:
    extra = " kpi-full" if full else ""
    return (
        f'<div class="kpi-card{extra}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value {css_class}">{value}</div>'
        + (f'<div class="kpi-sub">{sub}</div>' if sub else "")
        + "</div>"
    )


def build_chart(df: pd.DataFrame) -> go.Figure:
    df_sorted = df.copy().sort_values("date_dt").reset_index(drop=True)
    df_sorted["net"] = (
        df_sorted["bounties"] + df_sorted["cash_out"].fillna(0)
        - df_sorted["buy_in"] - df_sorted["rake"]
    )
    df_sorted["cumulative"] = df_sorted["net"].cumsum()
    df_sorted["label"] = df_sorted.apply(
        lambda r: (
            r["date_dt"].strftime("%d/%m") if pd.notna(r["date_dt"]) else "?"
        ),
        axis=1,
    )
    colors = ["#3fb950" if v >= 0 else "#f85149" for v in df_sorted["cumulative"]]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sorted["label"],
        y=df_sorted["cumulative"],
        mode="lines+markers",
        line=dict(color="#58a6ff", width=2.5, shape="spline", smoothing=0.6),
        marker=dict(color=colors, size=10, line=dict(color="#0d1117", width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(88,166,255,0.08)",
        hovertemplate="<b>%{x}</b><br>רווח מצטבר: <b>$%{y:,.2f}</b><extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="#30363d", line_width=1.5)
    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(family="Arial, sans-serif", color="#8b949e", size=12),
        margin=dict(l=0, r=0, t=16, b=0),
        height=280,
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=11), tickangle=-45),
        yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False, tickprefix="$", tickfont=dict(size=11)),
        hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d", font=dict(color="#e6edf3", size=14)),
        showlegend=False,
    )
    return fig


# ── סרגל צד ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ♠ פקדים")
    if st.button("🔄  סרוק וייבא קבצים"):
        with st.spinner("סורק…"):
            new, upd = scan_and_import()
        st.success(f"הושלם — {new} חדשים, {upd} עודכנו")
        st.rerun()
    st.divider()
    st.caption("הכנס קבצי `.txt` של GG Poker לתיקיית `Poker_New_Era`, ולחץ סרוק.")

# ── סריקה אוטומטית בטעינה ראשונה ─────────────────────────────────────────────

if "scanned" not in st.session_state:
    scan_and_import()
    st.session_state["scanned"] = True

# ── טעינת נתונים ─────────────────────────────────────────────────────────────

rows = db.get_all_tournaments()
stats = db.get_stats()

df = pd.DataFrame(rows) if rows else pd.DataFrame(
    columns=["id","tournament_id","filename","title","date",
             "buy_in","rake","bounties","cash_out","notes","created_at","updated_at"]
)

if not df.empty:
    df["date_dt"]     = pd.to_datetime(df["date"], errors="coerce")
    df["total_cost"]  = df["buy_in"] + df["rake"]
    df["total_return"]= df["bounties"] + df["cash_out"].fillna(0)
    df["net"]         = df["total_return"] - df["total_cost"]
    df["roi_pct"]     = df.apply(
        lambda r: (r["net"] / r["total_cost"] * 100) if r["total_cost"] > 0 else 0, axis=1
    )

total_invested = stats["total_invested"]
total_returned = stats["total_bounties"] + stats["total_cash"]
net_pl  = total_returned - total_invested
roi     = (net_pl / total_invested * 100) if total_invested > 0 else 0.0
missing = stats["missing_payouts"]

# ─────────────────────────────────────────────────────────────────────────────
# כותרת
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;direction:rtl;">
        <span style="font-size:2.2rem;">♠</span>
        <div>
            <h1 style="margin:0;font-size:1.6rem;">דשבורד בנקרול פוקר</h1>
            <p style="margin:0;color:#8b949e;font-size:0.82rem;">GG Poker · מעקב טורנירים</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if missing > 0:
    s = "ים" if missing != 1 else ""
    st.markdown(
        f'<span class="badge-warn">⚠ {missing} טורניר{s} ללא תשלום</span>',
        unsafe_allow_html=True,
    )
elif stats["total_tournaments"] > 0:
    st.markdown('<span class="badge-ok">✓ כל התשלומים מעודכנים</span>', unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# העלאת קבצי GG Poker
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">📂 העלאת היסטוריית ידיים</div>', unsafe_allow_html=True)

uploaded = st.file_uploader(
    "בחר קבצי GG Poker",
    type=["txt"],
    accept_multiple_files=True,
    label_visibility="collapsed",
    help="קבצי .txt מ-GG Poker — אפשר לבחור כמה קבצים ביחד",
)

if uploaded:
    if st.button(f"📥  ייבא {len(uploaded)} קוב{'צים' if len(uploaded) != 1 else 'ץ'}"):
        with st.spinner("שומר ומעבד…"):
            new, upd = handle_uploaded_files(uploaded)
        st.success(f"✅ הושלם — {new} טורנירים חדשים, {upd} עודכנו")
        st.rerun()

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# כרטיסי KPI — גריד רספונסיבי (2 עמודות במובייל, 5 בדסקטופ)
# ─────────────────────────────────────────────────────────────────────────────

roi_sub = f"על {fmt_money(total_invested)}"

st.markdown(
    f"""
    <div class="kpi-grid">
        {kpi_card("טורנירים", str(stats["total_tournaments"]), "שיחקתי", "kpi-white")}
        {kpi_card("סה״כ השקעה", fmt_money(total_invested), "buy-in + עמלה", "kpi-white")}
        {kpi_card("סה״כ החזר", fmt_money(total_returned), "באונטי + כסף", "kpi-neutral")}
        {kpi_card("רווח / הפסד", fmt_money(net_pl, always_sign=True), "נטו", color_class(net_pl))}
        {kpi_card("ROI", f"{'+' if roi > 0 else ''}{roi:.1f}%", roi_sub, color_class(roi), full=True)}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# גרף
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">צמיחת הבנקרול</div>', unsafe_allow_html=True)

if df.empty:
    st.info("אין נתונים. הכנס קבצי GG Poker ולחץ סרוק בתפריט הצד.")
else:
    df_chart = df.dropna(subset=["date_dt"])
    if not df_chart.empty:
        st.plotly_chart(
            build_chart(df_chart),
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
        )

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# עדכון כספים
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">עדכון כספים</div>', unsafe_allow_html=True)

missing_rows = db.get_missing_payouts()

if not missing_rows:
    st.markdown(
        '<p style="color:#3fb950;font-size:0.9rem;">✓ הכל מעודכן!</p>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<p style="color:#8b949e;font-size:0.85rem;">הכנס $0 אם יצאת ללא כסף, או הסכום שקיבלת.</p>',
        unsafe_allow_html=True,
    )
    for t in missing_rows:
        date_display  = t["date"][:10] if t["date"] else "תאריך לא ידוע"
        title_display = t["title"] or t["tournament_id"]
        cost_display  = fmt_money(t["buy_in"] + t["rake"])

        st.markdown(
            f'<div class="pending-card">'
            f'<div class="pending-title">🟡 {title_display}</div>'
            f'<div class="pending-sub">{date_display} · עלות: {cost_display}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns([1, 1])
        with col_a:
            payout_input = st.number_input(
                "סכום תשלום ($)",
                min_value=0.0, step=0.01, format="%.2f",
                key=f"payout_{t['tournament_id']}",
            )
        with col_b:
            notes_input = st.text_input(
                "הערות",
                key=f"notes_{t['tournament_id']}",
                placeholder="לדוגמה: מקום 3",
            )
        if st.button("💾  שמור", key=f"save_{t['tournament_id']}"):
            db.set_cash_out(t["tournament_id"], payout_input, notes_input)
            st.success(f"נשמר: {fmt_money(payout_input)}")
            st.rerun()

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# טבלת היסטוריה
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">היסטוריית טורנירים</div>', unsafe_allow_html=True)

if df.empty:
    st.info("לא נרשמו טורנירים עדיין.")
else:
    # פקדי סינון
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        search = st.text_input("חיפוש", placeholder="שם טורניר…", label_visibility="collapsed")
    with col_f2:
        show_pending = st.checkbox("ממתינים", value=False)

    display_df = df[["date_dt","title","buy_in","rake","bounties","cash_out","net","roi_pct","notes"]].copy()
    display_df.columns = ["תאריך","טורניר","Buy-in","עמלה","באונטי","תשלום","רווח/הפסד","ROI %","הערות"]

    display_df["תאריך"]      = display_df["תאריך"].dt.strftime("%d/%m/%y").fillna("—")
    display_df["Buy-in"]     = display_df["Buy-in"].map(lambda x: f"${x:,.2f}")
    display_df["עמלה"]       = display_df["עמלה"].map(lambda x: f"${x:,.2f}")
    display_df["באונטי"]     = display_df["באונטי"].map(lambda x: f"${x:,.2f}")
    display_df["תשלום"]      = display_df["תשלום"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "⏳")
    display_df["רווח/הפסד"]  = display_df["רווח/הפסד"].map(lambda x: f"+${x:,.2f}" if x > 0 else f"-${abs(x):,.2f}")
    display_df["ROI %"]      = display_df["ROI %"].map(lambda x: f"{x:+.1f}%")
    display_df["הערות"]      = display_df["הערות"].fillna("")

    if search:
        display_df = display_df[display_df["טורניר"].str.contains(search, case=False, na=False)]
    if show_pending:
        display_df = display_df[display_df["תשלום"] == "⏳"]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=min(60 + len(display_df) * 38, 520),
        column_config={
            "תאריך":     st.column_config.TextColumn("תאריך", width=75),
            "טורניר":    st.column_config.TextColumn("טורניר", width=180),
            "Buy-in":    st.column_config.TextColumn("Buy-in", width=70),
            "עמלה":      st.column_config.TextColumn("עמלה", width=60),
            "באונטי":    st.column_config.TextColumn("באונטי", width=70),
            "תשלום":     st.column_config.TextColumn("תשלום", width=70),
            "רווח/הפסד": st.column_config.TextColumn("רווח/הפסד", width=90),
            "ROI %":     st.column_config.TextColumn("ROI %", width=65),
            "הערות":     st.column_config.TextColumn("הערות", width=120),
        },
    )

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── ניהול רשומות ──────────────────────────────────────────────────────────────

with st.expander("⚙ ניהול רשומות", expanded=False):
    st.markdown('<p style="color:#8b949e;font-size:0.85rem;">מחק טורניר לפי מזהה.</p>', unsafe_allow_html=True)
    del_id = st.text_input("מזהה טורניר", label_visibility="collapsed", placeholder="מזהה טורניר למחיקה")
    if st.button("🗑  מחק", key="del_btn"):
        if del_id.strip():
            db.delete_tournament(del_id.strip())
            st.warning(f"נמחק: {del_id}")
            st.rerun()

st.markdown(
    '<p style="text-align:center;color:#30363d;font-size:0.7rem;margin-top:32px;">'
    "♠ דשבורד בנקרול פוקר · נתונים ב־bankroll.db</p>",
    unsafe_allow_html=True,
)
