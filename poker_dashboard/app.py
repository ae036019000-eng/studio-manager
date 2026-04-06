"""
דשבורד ניהול בנקרול פוקר — GG Poker
מותאם לאייפון ראשית — ללא סרגל צד, פריסה אנכית מלאה
הרצה:  streamlit run app.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# הוספת תיקיית הפרויקט ל-PATH
sys.path.insert(0, str(Path(__file__).parent))

import database as db
import parser as hh_parser

# ── תיקיית קבצי היסטוריית ידיים המקומית (אופציונלי) ──────────────────────────
HAND_HISTORY_FOLDER = Path(__file__).parent / "Poker_New_Era"

# ── הגדרות עמוד ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="דשבורד בנקרול פוקר",
    page_icon="♠",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# ── CSS מינימלי — מותאם לאייפון, ללא HTML מורכב ─────────────────────────────
st.markdown("""
<style>
/* הסתרת סרגל צד לחלוטין */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* רקע כהה וכיוון RTL */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d1117; color: #e6edf3; direction: rtl;
}
[data-testid="stHeader"] { background: transparent; }

/* ריפוד בטוח לאייפון */
.block-container { padding: 1rem 0.8rem 3rem 0.8rem !important; }

/* כרטיסי מדד */
[data-testid="stMetric"] {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 12px; padding: 14px 10px !important; text-align: center;
}
[data-testid="stMetricLabel"] p { color: #8b949e !important; font-size: 0.78rem !important; font-weight: 600 !important; }
[data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 800 !important; direction: ltr; }

/* כפתורים — גדולים וידידותיים למגע */
.stButton > button {
    background: #238636 !important; color: #fff !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    min-height: 50px !important; width: 100% !important; font-size: 1rem !important;
}

/* שדות קלט */
.stTextInput > div > div > input, .stNumberInput > div > div > input {
    background: #161b22 !important; border: 1px solid #30363d !important;
    color: #e6edf3 !important; border-radius: 10px !important;
    min-height: 46px !important; font-size: 1rem !important; direction: ltr;
}

/* אזור העלאת קבצים */
[data-testid="stFileUploader"] { background: #161b22 !important; border: 2px dashed #30363d !important; border-radius: 12px !important; }

/* טבלת נתונים */
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

/* פס גלילה דק */
::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

hr { border-color: #21262d !important; margin: 18px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── אתחול DB ─────────────────────────────────────────────────────────────────
db.init_db()


# ─────────────────────────────────────────────────────────────────────────────
# פונקציות עזר
# ─────────────────────────────────────────────────────────────────────────────

def fmt(v: float, sign: bool = False) -> str:
    """פורמט ערך כסף: $1,234.56 או +$1,234.56"""
    prefix = "+" if sign and v > 0 else ""
    return f"{prefix}${v:,.2f}"


def scan_and_import() -> tuple[int, int]:
    """סריקת תיקיית Hand History המקומית וייבוא לDB."""
    if not HAND_HISTORY_FOLDER.exists():
        HAND_HISTORY_FOLDER.mkdir(parents=True, exist_ok=True)
        return 0, 0
    parsed = hh_parser.parse_folder(HAND_HISTORY_FOLDER)
    new_c = upd_c = 0
    for t in parsed:
        r = db.upsert_tournament(t)
        if r == "inserted":  new_c += 1
        elif r == "updated": upd_c += 1
    return new_c, upd_c


def handle_uploaded_files(files) -> tuple[int, int, list[str]]:
    """עיבוד קבצים מהזיכרון — מחזיר (חדשים, עודכנו, לוג_שורות)"""
    new_c = upd_c = 0
    seen: dict[str, dict] = {}
    log: list[str] = []

    for f in files:
        try:
            content = f.getvalue().decode("utf-8", errors="replace")
        except Exception as e:
            log.append(f"❌ {f.name}: {e}")
            continue

        result = hh_parser.parse_content(content, f.name)
        if result is None:
            first_line = content.strip().splitlines()[0][:80] if content.strip() else "(ריק)"
            log.append(f"⚠️ {f.name}: לא זוהה — {first_line}")
            continue

        tid = result["tournament_id"]
        log.append(
            f"✅ {f.name} → #{tid} | ${result['buy_in']:.2f} | bounty:${result['bounties']:.2f}"
        )
        if tid not in seen:
            seen[tid] = result
        else:
            # צבירת באונטי ממספר קבצים לאותו טורניר
            seen[tid]["bounties"] += result["bounties"]

    for t in seen.values():
        r = db.upsert_tournament(t)
        if r == "inserted": new_c += 1
        elif r == "updated": upd_c += 1

    # שורת סיכום תמיד ראשונה בלוג
    log.insert(0, f"📊 {len(files)} קבצים → {len(seen)} טורנירים ייחודיים | {new_c} חדשים | {upd_c} עודכנו")
    return new_c, upd_c, log


# ── סריקה אוטומטית בטעינה ראשונה ────────────────────────────────────────────
if "scanned" not in st.session_state:
    scan_and_import()
    st.session_state["scanned"] = True

# ── טעינת נתונים מה-DB ───────────────────────────────────────────────────────
rows  = db.get_all_tournaments()
stats = db.get_stats()

df = pd.DataFrame(rows) if rows else pd.DataFrame(
    columns=["id", "tournament_id", "filename", "title", "date",
             "buy_in", "rake", "bounties", "cash_out", "notes", "created_at", "updated_at"]
)

if not df.empty:
    df["date_dt"]      = pd.to_datetime(df["date"], errors="coerce")
    df["total_cost"]   = df["buy_in"] + df["rake"]
    df["total_return"] = df["bounties"] + df["cash_out"].fillna(0)
    df["net"]          = df["total_return"] - df["total_cost"]
    df["roi_pct"]      = df.apply(
        lambda r: r["net"] / r["total_cost"] * 100 if r["total_cost"] > 0 else 0, axis=1
    )

# ── חישובי KPI ───────────────────────────────────────────────────────────────
total_inv = stats["total_invested"]
total_ret = stats["total_bounties"] + stats["total_cash"]
net_pl    = total_ret - total_inv
roi       = (net_pl / total_inv * 100) if total_inv > 0 else 0.0
missing   = stats["missing_payouts"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("# ♠ דשבורד בנקרול פוקר")
st.caption("GG Poker · מעקב טורנירים")

# תג סטטוס — אזהרה / הצלחה
if missing > 0:
    st.warning(f"⚠️ {missing} טורנירים ללא נתוני תשלום")
elif stats["total_tournaments"] > 0:
    st.success("✓ כל התשלומים מעודכנים")

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# 2. העלאת קבצים
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("📂 העלאת קבצים")

uploaded = st.file_uploader(
    "בחר קבצי היסטוריית ידיים (.txt מ-GG Poker)",
    type=["txt"],
    accept_multiple_files=True,
    label_visibility="visible",
)

if uploaded:
    st.info(f"📁 {len(uploaded)} קבצים נבחרו")
    if st.button(f"📥 ייבא {len(uploaded)} קבצים", type="primary", use_container_width=True):
        with st.spinner(f"מעבד {len(uploaded)} קבצים…"):
            new, upd, parse_log = handle_uploaded_files(uploaded)
        st.session_state["parse_log"] = parse_log
        if new + upd > 0:
            st.success(f"✅ {new} טורנירים חדשים · {upd} עודכנו")
            st.rerun()
        else:
            st.error("❌ לא נמצאו טורנירים — בדוק לוג למטה")

# לוג אבחון מהייבוא האחרון
if st.session_state.get("parse_log"):
    with st.expander("🔍 פירוט ייבוא אחרון"):
        for line in st.session_state["parse_log"][:30]:
            st.caption(line)

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# 3. KPI — 3 שורות × 2 עמודות
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
    # delta מציג ROI% כמדד שינוי
    st.metric("רווח / הפסד", fmt(net_pl, sign=True), delta=f"{roi:+.1f}%")
with r3c1:
    st.metric("ROI", f"{roi:+.1f}%")
with r3c2:
    st.metric("ממתינים לעדכון", missing)

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# 4. גרף צמיחת בנקרול
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("📈 צמיחת הבנקרול")

if df.empty:
    st.info("אין נתונים עדיין — העלה קבצים כדי להתחיל.")
else:
    df_c = df.dropna(subset=["date_dt"]).sort_values("date_dt").copy()
    if df_c.empty:
        st.info("אין טורנירים עם תאריך תקין.")
    else:
        # חישוב רווח/הפסד מצטבר
        df_c["net_t"] = (
            df_c["bounties"] + df_c["cash_out"].fillna(0)
            - df_c["buy_in"] - df_c["rake"]
        )
        df_c["cum"] = df_c["net_t"].cumsum()
        df_c["lbl"] = df_c["date_dt"].dt.strftime("%d/%m")

        # צבע מרקר: ירוק ברווח, אדום בהפסד
        colors = ["#3fb950" if v >= 0 else "#f85149" for v in df_c["cum"]]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_c["lbl"],
            y=df_c["cum"],
            mode="lines+markers",
            line=dict(color="#58a6ff", width=2.5, shape="spline"),
            marker=dict(color=colors, size=10, line=dict(color="#0d1117", width=1.5)),
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.08)",
            hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>",
        ))
        # קו אפס
        fig.add_hline(y=0, line_dash="dot", line_color="#30363d", line_width=1.5)

        fig.update_layout(
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            font=dict(color="#8b949e", size=12),
            xaxis=dict(
                showgrid=False, zeroline=False,
                tickangle=-45, tickfont=dict(size=11),
            ),
            yaxis=dict(
                showgrid=True, gridcolor="#21262d", zeroline=False,
                tickprefix="$", tickfont=dict(size=11),
            ),
            hoverlabel=dict(
                bgcolor="#161b22", bordercolor="#30363d",
                font=dict(color="#e6edf3", size=14),
            ),
            showlegend=False,
        )

        # config: ללא toolbar, scrollZoom=False — מניע גלילה טבעית באייפון
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "scrollZoom": False,
                "responsive": True,
            },
        )

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# 5. עדכון כספים
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
            payout = st.number_input(
                "סכום תשלום ($)", min_value=0.0, step=0.01, format="%.2f",
                key=f"p_{t['tournament_id']}",
            )
            notes = st.text_input(
                "הערות", key=f"n_{t['tournament_id']}",
                placeholder="מקום 3, FT...",
            )
            if st.button("💾 שמור", key=f"s_{t['tournament_id']}"):
                db.set_cash_out(t["tournament_id"], payout, notes)
                st.success(f"נשמר: {fmt(payout)}")
                st.rerun()

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# 6. היסטוריית טורנירים
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("🗂 היסטוריית טורנירים")

if df.empty:
    st.info("לא נרשמו טורנירים עדיין.")
else:
    # שורת חיפוש + סינון ממתינים
    fc1, fc2 = st.columns([3, 1])
    with fc1:
        search = st.text_input(
            "חיפוש", placeholder="שם טורניר...", label_visibility="collapsed"
        )
    with fc2:
        only_pending = st.checkbox("ממתינים", value=False)

    # בניית DataFrame לתצוגה — עמודות לפי הסדר המבוקש
    disp = df[["date_dt", "title", "buy_in", "rake", "bounties", "cash_out", "net", "roi_pct"]].copy()
    disp.columns = ["תאריך", "טורניר", "Buy-in", "עמלה", "באונטי", "תשלום", "רווח/הפסד", "ROI%"]

    disp["תאריך"]      = disp["תאריך"].dt.strftime("%d/%m/%y").fillna("—")
    disp["Buy-in"]     = disp["Buy-in"].map(lambda x: f"${x:,.2f}")
    disp["עמלה"]       = disp["עמלה"].map(lambda x: f"${x:,.2f}")
    disp["באונטי"]     = disp["באונטי"].map(lambda x: f"${x:,.2f}")
    disp["תשלום"]      = disp["תשלום"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "⏳")
    disp["רווח/הפסד"]  = disp["רווח/הפסד"].map(
        lambda x: f"+${x:,.2f}" if x > 0 else f"-${abs(x):,.2f}"
    )
    disp["ROI%"]       = disp["ROI%"].map(lambda x: f"{x:+.1f}%")

    # פילטרים — חיפוש טקסט וסינון ממתינים
    if search:
        disp = disp[disp["טורניר"].str.contains(search, case=False, na=False)]
    if only_pending:
        disp = disp[disp["תשלום"] == "⏳"]

    st.dataframe(
        disp,
        use_container_width=True,
        hide_index=True,
        height=min(60 + len(disp) * 38, 500),
    )

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# 7. ניהול רשומות
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("⚙️ ניהול רשומות"):
    del_id = st.text_input(
        "מזהה טורניר למחיקה",
        label_visibility="collapsed",
        placeholder="Tournament ID",
    )
    if st.button("🗑 מחק", key="delete_btn"):
        if del_id.strip():
            db.delete_tournament(del_id.strip())
            st.warning(f"נמחק: {del_id.strip()}")
            st.rerun()
        else:
            st.error("יש להזין מזהה טורניר תקין")

# ── כותרת תחתונה ─────────────────────────────────────────────────────────────
st.caption("♠ דשבורד בנקרול פוקר · נתונים נשמרים ב-/tmp/bankroll.db")
