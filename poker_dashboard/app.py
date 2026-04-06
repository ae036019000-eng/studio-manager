"""
דשבורד ניהול בנקרול פוקר — GG Poker
הרצה:  streamlit run app.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Ensure sibling modules are importable when launched from any cwd
sys.path.insert(0, str(Path(__file__).parent))

import database as db
import parser as hh_parser

# ── קבועים ───────────────────────────────────────────────────────────────────

HAND_HISTORY_FOLDER = Path(__file__).parent / "Poker_New_Era"

# ── הגדרת עמוד (חייב להיות הקריאה הראשונה לסטרימליט) ────────────────────────

st.set_page_config(
    page_title="דשבורד בנקרול פוקר",
    page_icon="♠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS — ערכת נושא פוקר כהה + RTL עברית ────────────────────────────────────

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
    [data-testid="stSidebar"] {
        background-color: #161b22;
        direction: rtl;
    }

    /* ── טיפוגרפיה ── */
    h1, h2, h3, h4 { color: #e6edf3; font-weight: 700; }

    /* ── כרטיס KPI ── */
    .kpi-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 24px 28px;
        text-align: center;
        transition: border-color .2s;
    }
    .kpi-card:hover { border-color: #58a6ff; }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: .04em;
        color: #8b949e;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 800;
        line-height: 1;
        direction: ltr;
        display: inline-block;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #8b949e;
        margin-top: 6px;
    }
    .kpi-profit  { color: #3fb950; }
    .kpi-loss    { color: #f85149; }
    .kpi-neutral { color: #58a6ff; }
    .kpi-white   { color: #e6edf3; }

    /* ── כותרות סעיף ── */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #8b949e;
        margin: 0 0 16px 2px;
        border-right: 3px solid #58a6ff;
        padding-right: 10px;
    }

    /* ── תגיות סטטוס ── */
    .badge-warn {
        display: inline-block;
        background: rgba(210, 153, 34, 0.18);
        border: 1px solid #d29922;
        color: #d29922;
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-ok {
        display: inline-block;
        background: rgba(63, 185, 80, 0.15);
        border: 1px solid #3fb950;
        color: #3fb950;
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* ── מפריד ── */
    .divider {
        border: none;
        border-top: 1px solid #21262d;
        margin: 28px 0;
    }

    /* ── Streamlit — עיצוב שדות קלט ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
        border-radius: 8px !important;
        direction: ltr;
    }
    .stButton > button {
        background: #238636 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 6px 20px !important;
    }
    .stButton > button:hover { background: #2ea043 !important; }
    div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
    .stAlert { border-radius: 10px; }

    /* ── גלילה ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

    /* ── טבלה — מספרים שמאל ── */
    [data-testid="stDataFrame"] td { direction: ltr; text-align: left; }
    [data-testid="stDataFrame"] th { direction: rtl; text-align: right; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── אתחול בסיס נתונים ─────────────────────────────────────────────────────────

db.init_db()

# ── פונקציות עזר ──────────────────────────────────────────────────────────────


def scan_and_import() -> tuple[int, int]:
    """סרוק את תיקיית היסטוריית הידיים ועדכן את הדאטהבייס."""
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


def fmt_money(value: float, always_sign: bool = False) -> str:
    sign = "+" if always_sign and value > 0 else ""
    return f"{sign}${value:,.2f}"


def color_class(value: float) -> str:
    if value > 0:
        return "kpi-profit"
    if value < 0:
        return "kpi-loss"
    return "kpi-neutral"


def kpi_card(label: str, value: str, sub: str = "", css_class: str = "kpi-white") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {css_class}">{value}</div>
        {"<div class='kpi-sub'>" + sub + "</div>" if sub else ""}
    </div>
    """


def build_chart(df: pd.DataFrame) -> go.Figure:
    """גרף רווח/הפסד מצטבר לאורך זמן."""
    df_sorted = df.copy().sort_values("date_dt").reset_index(drop=True)

    df_sorted["net"] = (
        df_sorted["bounties"]
        + df_sorted["cash_out"].fillna(0)
        - df_sorted["buy_in"]
        - df_sorted["rake"]
    )
    df_sorted["cumulative"] = df_sorted["net"].cumsum()
    df_sorted["label"] = df_sorted.apply(
        lambda r: (
            f"{r['date_dt'].strftime('%d/%m')}  {r['title']}"
            if pd.notna(r["date_dt"]) else f"?  {r['title']}"
        ),
        axis=1,
    )

    colors = ["#3fb950" if v >= 0 else "#f85149" for v in df_sorted["cumulative"]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_sorted["label"],
            y=df_sorted["cumulative"],
            mode="lines+markers",
            line=dict(color="#58a6ff", width=2.5, shape="spline", smoothing=0.6),
            marker=dict(color=colors, size=9, line=dict(color="#0d1117", width=1.5)),
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.08)",
            hovertemplate="<b>%{x}</b><br>רווח/הפסד מצטבר: <b>$%{y:,.2f}</b><extra></extra>",
            name="רווח/הפסד מצטבר",
        )
    )

    fig.add_hline(y=0, line_dash="dot", line_color="#30363d", line_width=1.5)

    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(family="'Segoe UI', Arial, sans-serif", color="#8b949e", size=12),
        margin=dict(l=10, r=10, t=20, b=10),
        height=360,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=10),
            tickangle=-35,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#21262d",
            gridwidth=1,
            zeroline=False,
            tickprefix="$",
            tickfont=dict(size=11),
        ),
        hoverlabel=dict(
            bgcolor="#161b22",
            bordercolor="#30363d",
            font=dict(color="#e6edf3", size=13),
        ),
        showlegend=False,
    )
    return fig


# ── סרגל צד: כפתור סריקה ─────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ♠ פקדים")
    folder_display = (
        HAND_HISTORY_FOLDER.relative_to(Path.cwd())
        if HAND_HISTORY_FOLDER.is_relative_to(Path.cwd())
        else HAND_HISTORY_FOLDER
    )
    st.markdown(f"**תיקיית היסטוריית ידיים**\n\n`{folder_display}`")

    if st.button("🔄  סרוק וייבא קבצים"):
        with st.spinner("סורק…"):
            new, upd = scan_and_import()
        st.success(f"הושלם — {new} חדשים, {upd} עודכנו")
        st.rerun()

    st.divider()
    st.caption(
        "הכנס קבצי `.txt` חדשים של GG Poker לתיקיית `Poker_New_Era`, "
        "ולחץ **סרוק וייבא קבצים**."
    )

# ── סריקה אוטומטית בטעינה הראשונה ───────────────────────────────────────────

if "scanned" not in st.session_state:
    scan_and_import()
    st.session_state["scanned"] = True

# ── טעינת נתונים ─────────────────────────────────────────────────────────────

rows = db.get_all_tournaments()
stats = db.get_stats()

df = pd.DataFrame(rows) if rows else pd.DataFrame(
    columns=[
        "id", "tournament_id", "filename", "title", "date",
        "buy_in", "rake", "bounties", "cash_out", "notes",
        "created_at", "updated_at",
    ]
)

if not df.empty:
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df["total_cost"] = df["buy_in"] + df["rake"]
    df["total_return"] = df["bounties"] + df["cash_out"].fillna(0)
    df["net"] = df["total_return"] - df["total_cost"]
    df["roi_pct"] = df.apply(
        lambda r: (r["net"] / r["total_cost"] * 100) if r["total_cost"] > 0 else 0,
        axis=1,
    )

# ── חישוב KPI ─────────────────────────────────────────────────────────────────

total_invested = stats["total_invested"]
total_returned = stats["total_bounties"] + stats["total_cash"]
net_pl = total_returned - total_invested
roi = (net_pl / total_invested * 100) if total_invested > 0 else 0.0
missing = stats["missing_payouts"]

# ─────────────────────────────────────────────────────────────────────────────
# כותרת ראשית
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:8px; direction:rtl;">
        <span style="font-size:2.6rem;">♠</span>
        <div>
            <h1 style="margin:0; font-size:2rem;">דשבורד בנקרול פוקר</h1>
            <p style="margin:0; color:#8b949e; font-size:0.9rem;">GG Poker · מעקב טורנירים</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if missing > 0:
    s = "ים" if missing != 1 else ""
    st.markdown(
        f'<span class="badge-warn">⚠ {missing} טורניר{s} ללא נתוני תשלום</span>',
        unsafe_allow_html=True,
    )
elif stats["total_tournaments"] > 0:
    st.markdown('<span class="badge-ok">✓ כל התשלומים מעודכנים</span>', unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# כרטיסי KPI
# ─────────────────────────────────────────────────────────────────────────────

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(
        kpi_card("טורנירים", str(stats["total_tournaments"]), "", "kpi-white"),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        kpi_card("סה״כ השקעה", fmt_money(total_invested), "buy-in + עמלה", "kpi-white"),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        kpi_card("סה״כ החזר", fmt_money(total_returned), "באונטי + כסף", "kpi-neutral"),
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        kpi_card(
            "רווח / הפסד נטו",
            fmt_money(net_pl, always_sign=True),
            "כולל הכל",
            color_class(net_pl),
        ),
        unsafe_allow_html=True,
    )
with c5:
    roi_sub = f"על {fmt_money(total_invested)} השקועים"
    st.markdown(
        kpi_card(
            "ROI",
            f"{'+' if roi > 0 else ''}{roi:.1f}%",
            roi_sub,
            color_class(roi),
        ),
        unsafe_allow_html=True,
    )

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# גרף צמיחת הבנקרול
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">צמיחת הבנקרול לאורך זמן</div>', unsafe_allow_html=True)

if df.empty:
    st.info("אין נתונים עדיין. הכנס קבצי היסטוריית ידיים לתיקייה `Poker_New_Era` ולחץ **סרוק וייבא קבצים** בסרגל הצד.")
else:
    df_chart = df.dropna(subset=["date_dt"])
    if df_chart.empty:
        st.warning("אין טורנירים עם תאריך ידוע לצורך הצגת הגרף.")
    else:
        fig = build_chart(df_chart)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# עדכון כספים — טורנירים עם תשלום חסר
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">עדכון כספים (Cashes)</div>', unsafe_allow_html=True)

missing_rows = db.get_missing_payouts()

if not missing_rows:
    st.markdown(
        '<p style="color:#3fb950; font-size:0.9rem;">✓ אין תשלומים חסרים — הכל מעודכן!</p>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<p style="color:#8b949e; font-size:0.88rem;">'
        'הכנס $0 אם לא קיבלת תשלום (יצאת ללא כסף), או את הסכום המדויק שקיבלת.</p>',
        unsafe_allow_html=True,
    )

    for t in missing_rows:
        date_display = t["date"][:10] if t["date"] else "תאריך לא ידוע"
        title_display = t["title"] or t["tournament_id"]
        cost_display = fmt_money(t["buy_in"] + t["rake"])

        with st.expander(f"🟡  {date_display} — {title_display}  [{cost_display}]", expanded=False):
            col_a, col_b, col_c = st.columns([3, 3, 2])

            with col_a:
                payout_input = st.number_input(
                    "סכום תשלום ($)",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    key=f"payout_{t['tournament_id']}",
                )
            with col_b:
                notes_input = st.text_input(
                    "הערות (אופציונלי)",
                    key=f"notes_{t['tournament_id']}",
                    placeholder="לדוגמה: שולחן פינאל, מקום 3",
                )
            with col_c:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("שמור", key=f"save_{t['tournament_id']}"):
                    db.set_cash_out(t["tournament_id"], payout_input, notes_input)
                    st.success(f"נשמר: {fmt_money(payout_input)}")
                    st.rerun()

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# טבלת היסטוריית טורנירים
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">היסטוריית טורנירים</div>', unsafe_allow_html=True)

if df.empty:
    st.info("לא נרשמו טורנירים עדיין.")
else:
    display_df = df[[
        "date_dt", "title", "buy_in", "rake", "bounties", "cash_out", "net", "roi_pct", "notes"
    ]].copy()

    display_df.columns = [
        "תאריך", "טורניר", "Buy-in", "עמלה", "באונטי", "תשלום", "רווח/הפסד", "ROI %", "הערות"
    ]

    display_df["תאריך"] = display_df["תאריך"].dt.strftime("%Y-%m-%d").fillna("—")
    display_df["Buy-in"]     = display_df["Buy-in"].map(lambda x: f"${x:,.2f}")
    display_df["עמלה"]       = display_df["עמלה"].map(lambda x: f"${x:,.2f}")
    display_df["באונטי"]     = display_df["באונטי"].map(lambda x: f"${x:,.2f}")
    display_df["תשלום"]      = display_df["תשלום"].map(
        lambda x: f"${x:,.2f}" if pd.notna(x) else "⏳ ממתין"
    )
    display_df["רווח/הפסד"]  = display_df["רווח/הפסד"].map(
        lambda x: f"+${x:,.2f}" if x > 0 else f"-${abs(x):,.2f}"
    )
    display_df["ROI %"]      = display_df["ROI %"].map(lambda x: f"{x:+.1f}%")
    display_df["הערות"]      = display_df["הערות"].fillna("")

    # פקדי סינון
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        search = st.text_input(
            "חיפוש טורנירים",
            placeholder="סנן לפי שם…",
            label_visibility="collapsed",
        )
    with col_f2:
        show_pending = st.checkbox("ממתינים בלבד", value=False)

    if search:
        display_df = display_df[
            display_df["טורניר"].str.contains(search, case=False, na=False)
        ]
    if show_pending:
        display_df = display_df[display_df["תשלום"] == "⏳ ממתין"]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=min(60 + len(display_df) * 36, 600),
        column_config={
            "תאריך":      st.column_config.TextColumn("תאריך", width=95),
            "טורניר":     st.column_config.TextColumn("טורניר", width=220),
            "Buy-in":     st.column_config.TextColumn("Buy-in", width=80),
            "עמלה":       st.column_config.TextColumn("עמלה", width=70),
            "באונטי":     st.column_config.TextColumn("באונטי", width=80),
            "תשלום":      st.column_config.TextColumn("תשלום", width=95),
            "רווח/הפסד":  st.column_config.TextColumn("רווח/הפסד", width=100),
            "ROI %":      st.column_config.TextColumn("ROI %", width=75),
            "הערות":      st.column_config.TextColumn("הערות", width=160),
        },
    )

    # שורת סיכום תחתית
    total_buyin     = df["buy_in"].sum()
    total_rake      = df["rake"].sum()
    total_bounties  = df["bounties"].sum()
    total_cash      = df["cash_out"].sum(skipna=True)
    total_net       = df["net"].sum()

    cols = st.columns([95/720, 220/720, 80/720, 70/720, 80/720, 95/720, 100/720, 75/720, 160/720])
    footer_style = "color:#8b949e; font-size:0.8rem; font-weight:600; padding-top:4px; direction:ltr;"
    with cols[0]:
        st.markdown(f'<div style="{footer_style}">סה״כ</div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f'<div style="{footer_style}">${total_buyin:,.2f}</div>', unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f'<div style="{footer_style}">${total_rake:,.2f}</div>', unsafe_allow_html=True)
    with cols[4]:
        st.markdown(f'<div style="{footer_style}">${total_bounties:,.2f}</div>', unsafe_allow_html=True)
    with cols[5]:
        st.markdown(f'<div style="{footer_style}">${total_cash:,.2f}</div>', unsafe_allow_html=True)
    with cols[6]:
        color = "#3fb950" if total_net >= 0 else "#f85149"
        st.markdown(
            f'<div style="{footer_style} color:{color};">'
            f'{"+$" if total_net >= 0 else "-$"}{abs(total_net):,.2f}</div>',
            unsafe_allow_html=True,
        )

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ניהול רשומות — מחיקה ידנית
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("⚙ ניהול רשומות", expanded=False):
    st.markdown(
        '<p style="color:#8b949e; font-size:0.85rem;">'
        'מחק טורניר לפי מזהה (הקובץ המקורי לא יימחק).</p>',
        unsafe_allow_html=True,
    )
    del_col1, del_col2 = st.columns([3, 1])
    with del_col1:
        del_id = st.text_input(
            "מזהה טורניר למחיקה",
            label_visibility="collapsed",
            placeholder="מזהה טורניר",
        )
    with del_col2:
        if st.button("מחק", key="del_btn"):
            if del_id.strip():
                db.delete_tournament(del_id.strip())
                st.warning(f"נמחק טורניר {del_id}")
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# כותרת תחתית
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    '<p style="text-align:center; color:#30363d; font-size:0.75rem; margin-top:40px;">'
    "דשבורד בנקרול פוקר · אפליקציה מקומית · הנתונים שמורים ב־bankroll.db"
    "</p>",
    unsafe_allow_html=True,
)
