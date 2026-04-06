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

HAND_HISTORY_FOLDER = Path(__file__).parent / "Poker_New_Era"

st.set_page_config(
    page_title="דשבורד בנקרול פוקר",
    page_icon="♠",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# ── CSS מינימלי — רק צבעים ורקע, ללא HTML מורכב ─────────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d1117;
    color: #e6edf3;
    direction: rtl;
}
[data-testid="stHeader"]       { background: transparent; }
[data-testid="stSidebar"]      { display: none !important; }
[data-testid="collapsedControl"]{ display: none !important; }
.block-container               { padding: 1.2rem 1rem 3rem 1rem !important; }

/* כרטיסי מדד */
[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 16px 14px !important;
    text-align: center;
}
[data-testid="stMetricLabel"] p {
    color: #8b949e !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    direction: rtl;
}
[data-testid="stMetricValue"] {
    font-size: 1.7rem !important;
    font-weight: 800 !important;
    direction: ltr;
    text-align: center;
}
[data-testid="stMetricDelta"] { justify-content: center; }

/* כפתורים */
.stButton > button {
    background: #238636 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    min-height: 48px !important;
    width: 100% !important;
    padding: 10px 20px !important;
}
.stButton > button:active { opacity: 0.85; }

/* שדות קלט */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 10px !important;
    min-height: 46px !important;
    font-size: 1rem !important;
    direction: ltr;
}

/* uploader */
[data-testid="stFileUploader"] {
    background: #161b22 !important;
    border: 2px dashed #30363d !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: #21262d !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    min-height: 44px !important;
}

/* טבלה */
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

/* divider */
hr { border-color: #21262d !important; margin: 20px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── DB + פונקציות ─────────────────────────────────────────────────────────────

db.init_db()


def scan_and_import() -> tuple[int, int]:
    if not HAND_HISTORY_FOLDER.exists():
        HAND_HISTORY_FOLDER.mkdir(parents=True, exist_ok=True)
        return 0, 0
    parsed = hh_parser.parse_folder(HAND_HISTORY_FOLDER)
    new_c = upd_c = 0
    for t in parsed:
        r = db.upsert_tournament(t)
        if r == "inserted":   new_c += 1
        elif r == "updated":  upd_c += 1
    return new_c, upd_c


def handle_uploaded_files(files) -> tuple[int, int]:
    """עיבוד קבצים מהזיכרון — לא נדרשת כתיבה לדיסק."""
    new_c = upd_c = 0
    seen: dict[str, dict] = {}

    for f in files:
        try:
            content = f.getvalue().decode("utf-8", errors="replace")
        except Exception:
            continue
        result = hh_parser.parse_content(content, f.name)
        if result is None:
            continue
        tid = result["tournament_id"]
        if tid not in seen:
            seen[tid] = result
        else:
            seen[tid]["bounties"] += result["bounties"]

    for t in seen.values():
        r = db.upsert_tournament(t)
        if r == "inserted":  new_c += 1
        elif r == "updated": upd_c += 1

    return new_c, upd_c


def fmt(v: float, sign: bool = False) -> str:
    s = "+" if sign and v > 0 else ""
    return f"{s}${v:,.2f}"


# (סרגל צד הוסר — כל הפקדים בדף הראשי)

if "scanned" not in st.session_state:
    scan_and_import()
    st.session_state["scanned"] = True

# ── נתונים ───────────────────────────────────────────────────────────────────

rows  = db.get_all_tournaments()
stats = db.get_stats()

df = pd.DataFrame(rows) if rows else pd.DataFrame(
    columns=["id","tournament_id","filename","title","date",
             "buy_in","rake","bounties","cash_out","notes","created_at","updated_at"]
)
if not df.empty:
    df["date_dt"]      = pd.to_datetime(df["date"], errors="coerce")
    df["total_cost"]   = df["buy_in"] + df["rake"]
    df["total_return"] = df["bounties"] + df["cash_out"].fillna(0)
    df["net"]          = df["total_return"] - df["total_cost"]
    df["roi_pct"]      = df.apply(
        lambda r: r["net"] / r["total_cost"] * 100 if r["total_cost"] > 0 else 0, axis=1
    )

total_inv = stats["total_invested"]
total_ret = stats["total_bounties"] + stats["total_cash"]
net_pl    = total_ret - total_inv
roi       = (net_pl / total_inv * 100) if total_inv > 0 else 0.0
missing   = stats["missing_payouts"]

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("# ♠ דשבורד בנקרול פוקר")
st.caption("GG Poker · מעקב טורנירים")

if missing > 0:
    st.warning(f"⚠️ {missing} טורנירים ללא נתוני תשלום")
elif stats["total_tournaments"] > 0:
    st.success("✓ כל התשלומים מעודכנים")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# העלאת קבצים
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("📂 העלאת קבצי GG Poker")

uploaded = st.file_uploader(
    "בחר קבצי היסטוריית ידיים (.txt מ-GG Poker)",
    type=["txt"],
    accept_multiple_files=True,
    label_visibility="visible",
)

# ייבוא אוטומטי — מעבד ברגע שיש קבצים חדשים
uploaded_key = tuple(sorted(f.name for f in uploaded)) if uploaded else ()
if uploaded and uploaded_key != st.session_state.get("last_upload_key"):
    with st.spinner(f"מעבד {len(uploaded)} קבצים…"):
        new, upd = handle_uploaded_files(uploaded)
    st.session_state["last_upload_key"] = uploaded_key
    if new + upd > 0:
        st.success(f"✅ {new} טורנירים חדשים, {upd} עודכנו")
        st.rerun()
    else:
        st.warning("לא נמצאו טורנירים בקבצים שהועלו. ודא שאלו קבצי GG Poker .txt תקינים.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# KPI — 2 עמודות (מותאם לפלאפון)
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("📊 סיכום")

r1c1, r1c2 = st.columns(2)
r2c1, r2c2 = st.columns(2)
r3c1, r3c2 = st.columns(2)

with r1c1:
    st.metric("טורנירים", stats["total_tournaments"])
with r1c2:
    st.metric("סה״כ השקעה", fmt(total_inv))
with r2c1:
    st.metric("סה״כ החזר", fmt(total_ret))
with r2c2:
    delta_color = "normal" if net_pl >= 0 else "inverse"
    st.metric("רווח / הפסד", fmt(net_pl, sign=True))
with r3c1:
    st.metric("ROI", f"{roi:+.1f}%")
with r3c2:
    st.metric("ממתינים לעדכון", missing)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# גרף
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("📈 צמיחת הבנקרול")

if df.empty:
    st.info("אין נתונים עדיין.")
else:
    df_c = df.dropna(subset=["date_dt"]).sort_values("date_dt").copy()
    if df_c.empty:
        st.info("אין טורנירים עם תאריך.")
    else:
        df_c["net_t"] = df_c["bounties"] + df_c["cash_out"].fillna(0) - df_c["buy_in"] - df_c["rake"]
        df_c["cum"]   = df_c["net_t"].cumsum()
        df_c["lbl"]   = df_c["date_dt"].dt.strftime("%d/%m")
        colors = ["#3fb950" if v >= 0 else "#f85149" for v in df_c["cum"]]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_c["lbl"], y=df_c["cum"],
            mode="lines+markers",
            line=dict(color="#58a6ff", width=2.5, shape="spline"),
            marker=dict(color=colors, size=10, line=dict(color="#0d1117", width=1.5)),
            fill="tozeroy", fillcolor="rgba(88,166,255,0.08)",
            hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>",
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="#30363d", line_width=1.5)
        fig.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            height=260,
            margin=dict(l=0, r=0, t=10, b=0),
            font=dict(color="#8b949e", size=12),
            xaxis=dict(showgrid=False, zeroline=False, tickangle=-45, tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False,
                       tickprefix="$", tickfont=dict(size=11)),
            hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d",
                            font=dict(color="#e6edf3", size=14)),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# עדכון כספים
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("💰 עדכון כספים")

missing_rows = db.get_missing_payouts()

if not missing_rows:
    st.success("✓ הכל מעודכן!")
else:
    st.caption("הכנס $0 אם יצאת ללא כסף, או הסכום שקיבלת.")
    for t in missing_rows:
        date_str  = t["date"][:10] if t["date"] else "תאריך לא ידוע"
        title_str = t["title"] or t["tournament_id"]
        cost_str  = fmt(t["buy_in"] + t["rake"])

        with st.expander(f"🟡 {date_str}  |  {title_str}  |  {cost_str}"):
            ca, cb = st.columns(2)
            with ca:
                payout = st.number_input("סכום ($)", min_value=0.0, step=0.01,
                                         format="%.2f", key=f"p_{t['tournament_id']}")
            with cb:
                notes = st.text_input("הערות", key=f"n_{t['tournament_id']}",
                                      placeholder="מקום 3, FT...")
            if st.button("💾 שמור", key=f"s_{t['tournament_id']}"):
                db.set_cash_out(t["tournament_id"], payout, notes)
                st.success(f"נשמר: {fmt(payout)}")
                st.rerun()

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# טבלת היסטוריה
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("🗂 היסטוריית טורנירים")

if df.empty:
    st.info("לא נרשמו טורנירים עדיין.")
else:
    fc1, fc2 = st.columns([3, 1])
    with fc1:
        search = st.text_input("חיפוש", placeholder="שם טורניר...", label_visibility="collapsed")
    with fc2:
        only_pending = st.checkbox("ממתינים", value=False)

    disp = df[["date_dt","title","buy_in","rake","bounties","cash_out","net","roi_pct"]].copy()
    disp.columns = ["תאריך","טורניר","Buy-in","עמלה","באונטי","תשלום","רווח/הפסד","ROI %"]

    disp["תאריך"]     = disp["תאריך"].dt.strftime("%d/%m/%y").fillna("—")
    disp["Buy-in"]    = disp["Buy-in"].map(lambda x: f"${x:,.2f}")
    disp["עמלה"]      = disp["עמלה"].map(lambda x: f"${x:,.2f}")
    disp["באונטי"]    = disp["באונטי"].map(lambda x: f"${x:,.2f}")
    disp["תשלום"]     = disp["תשלום"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "⏳")
    disp["רווח/הפסד"] = disp["רווח/הפסד"].map(lambda x: f"+${x:,.2f}" if x > 0 else f"-${abs(x):,.2f}")
    disp["ROI %"]     = disp["ROI %"].map(lambda x: f"{x:+.1f}%")

    if search:
        disp = disp[disp["טורניר"].str.contains(search, case=False, na=False)]
    if only_pending:
        disp = disp[disp["תשלום"] == "⏳"]

    st.dataframe(disp, use_container_width=True, hide_index=True,
                 height=min(60 + len(disp) * 38, 500))

st.divider()

with st.expander("⚙️ ניהול רשומות"):
    del_id = st.text_input("מזהה טורניר למחיקה", label_visibility="collapsed",
                           placeholder="Tournament ID")
    if st.button("🗑 מחק"):
        if del_id.strip():
            db.delete_tournament(del_id.strip())
            st.warning(f"נמחק: {del_id}")
            st.rerun()

st.caption("♠ דשבורד בנקרול פוקר · נתונים נשמרים ב־bankroll.db")
