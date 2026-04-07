"""
דשבורד בנקרול פוקר — GG Poker
מותאם לאייפון | נתונים ב-session_state (אמין ב-Streamlit Cloud)
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

import database as db
import parser as hh_parser
import analyzer as hh_analyzer

# ── הגדרות עמוד ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="דשבורד בנקרול פוקר",
    page_icon="♠",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# ── CSS — מינימלי, בטוח ל-iOS ─────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d1117;
    color: #e6edf3;
    direction: rtl;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding: 1rem 0.75rem 4rem 0.75rem !important; max-width: 480px !important; }

[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 14px 8px !important;
    text-align: center;
}
[data-testid="stMetricLabel"] p  { color: #8b949e !important; font-size: 0.75rem !important; font-weight: 600 !important; }
[data-testid="stMetricValue"]    { font-size: 1.45rem !important; font-weight: 800 !important; direction: ltr; }
[data-testid="stMetricDelta"]    { justify-content: center; }

/* כפתורים — גדולים ובולטים */
.stButton > button, button[kind="primary"], button[kind="secondary"] {
    min-height: 52px !important;
    width: 100% !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    border: none !important;
}
button[kind="primary"] { background: #238636 !important; color: #fff !important; }
button[kind="secondary"] { background: #21262d !important; color: #e6edf3 !important; }
.stButton > button { background: #238636 !important; color: #fff !important; }

/* שדות קלט */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    font-size: 1rem !important;
    direction: ltr;
}

/* uploader */
[data-testid="stFileUploader"] {
    background: #161b22 !important;
    border: 2px dashed #58a6ff !important;
    border-radius: 14px !important;
    padding: 4px !important;
}

/* submit button בתוך form */
[data-testid="stFormSubmitButton"] > button {
    background: #238636 !important;
    color: #fff !important;
    min-height: 56px !important;
    font-size: 1.1rem !important;
    width: 100% !important;
    border-radius: 12px !important;
    border: none !important;
    font-weight: 700 !important;
    margin-top: 10px;
}

div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
hr { border-color: #21262d !important; margin: 16px 0 !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── אתחול DB ─────────────────────────────────────────────────────────────────
db.init_db()


# ─────────────────────────────────────────────────────────────────────────────
# session_state — מקור הנתונים הראשי (אמין ב-Streamlit Cloud)
# ─────────────────────────────────────────────────────────────────────────────

def _ss_tournaments() -> dict[str, dict]:
    """מחזיר את כל הטורנירים מה-session_state."""
    return st.session_state.setdefault("tournaments", {})


def _ss_load_from_db():
    """טוען מה-DB ל-session_state (פעם אחת בלבד)."""
    if st.session_state.get("db_loaded"):
        return
    for row in db.get_all_tournaments():
        tid = row["tournament_id"]
        _ss_tournaments()[tid] = row
    st.session_state["db_loaded"] = True


def _ss_upsert(t: dict):
    """שומר טורניר ב-session_state וגם מנסה ב-DB."""
    tid = t["tournament_id"]
    existing = _ss_tournaments().get(tid)
    if existing:
        # שמור cash_out / notes אם כבר הוכנסו ידנית
        t.setdefault("cash_out", existing.get("cash_out"))
        t.setdefault("notes", existing.get("notes"))
    _ss_tournaments()[tid] = t
    try:
        db.upsert_tournament(t)
    except Exception:
        pass


def _ss_set_cash_out(tid: str, amount: float, notes: str):
    """עדכון תשלום ב-session_state וב-DB."""
    if tid in _ss_tournaments():
        _ss_tournaments()[tid]["cash_out"] = amount
        _ss_tournaments()[tid]["notes"] = notes
    try:
        db.set_cash_out(tid, amount, notes)
    except Exception:
        pass


def _ss_delete(tid: str):
    _ss_tournaments().pop(tid, None)
    try:
        db.delete_tournament(tid)
    except Exception:
        pass


# ── פונקציות עזר ─────────────────────────────────────────────────────────────

def fmt(v: float, sign: bool = False) -> str:
    p = "+" if sign and v > 0 else ""
    return f"{p}${v:,.2f}"


def _ss_game_stats() -> dict[str, dict]:
    return st.session_state.setdefault("game_stats", {})


def handle_uploaded_files(files) -> tuple[int, int, list[str]]:
    """מנתח קבצים מהזיכרון, שומר ב-session_state + מריץ ניתוח משחק."""
    new_c = upd_c = 0
    # tid → (tournament_dict, raw_text)
    seen_with_content: dict[str, list] = {}
    log: list[str] = []

    for f in files:
        try:
            content = f.getvalue().decode("utf-8", errors="replace")
        except Exception as e:
            log.append(f"❌ {f.name}: {e}")
            continue

        result = hh_parser.parse_content(content, f.name)
        if result is None:
            first = content.strip().splitlines()[0][:80] if content.strip() else "(ריק)"
            log.append(f"⚠️ {f.name}: לא זוהה — {first}")
            continue

        tid = result["tournament_id"]
        log.append(f"✅ {f.name[:40]} → #{tid} | buy-in:${result['buy_in']:.2f} | bounty:${result['bounties']:.2f}")
        if tid not in seen_with_content:
            seen_with_content[tid] = [result, content]
        else:
            seen_with_content[tid][0]["bounties"] += result["bounties"]
            seen_with_content[tid][1] += "\n\n" + content

    # ── שמור טורנירים + הרץ ניתוח משחק ─────────────────────────────────────
    for tid, (t, raw_content) in seen_with_content.items():
        tid = t["tournament_id"]
        if tid in _ss_tournaments():
            upd_c += 1
        else:
            new_c += 1
        _ss_upsert(t)

        # ניתוח משחק — מנתח כל יד בקובץ
        try:
            game_stats = hh_analyzer.analyze_tournament(raw_content)
            if game_stats.get("hands_played", 0) > 0:
                _ss_game_stats()[tid] = {"tournament_id": tid, "date": t.get("date"), "title": t.get("title"), **game_stats}
                try:
                    db.upsert_game_stats(tid, game_stats)
                except Exception:
                    pass
        except Exception as e:
            log.append(f"⚠️ ניתוח משחק נכשל עבור {tid}: {e}")

    log.insert(0, f"📊 {len(files)} קבצים | {len(seen_with_content)} טורנירים ייחודיים | ✅ {new_c} חדשים | 🔄 {upd_c} עודכנו")
    return new_c, upd_c, log


# ── טעינת נתונים ─────────────────────────────────────────────────────────────
_ss_load_from_db()

tournaments = _ss_tournaments()
rows = list(tournaments.values())

df = pd.DataFrame(rows) if rows else pd.DataFrame(
    columns=["id","tournament_id","filename","title","date",
             "buy_in","rake","bounties","cash_out","notes","created_at","updated_at"]
)

if not df.empty:
    df["date_dt"]      = pd.to_datetime(df["date"], errors="coerce")
    df["total_cost"]   = df["buy_in"].fillna(0) + df["rake"].fillna(0)
    df["total_return"] = df["bounties"].fillna(0) + df["cash_out"].fillna(0)
    df["net"]          = df["total_return"] - df["total_cost"]
    df["roi_pct"]      = df.apply(
        lambda r: r["net"] / r["total_cost"] * 100 if r["total_cost"] > 0 else 0, axis=1
    )

total_inv = df["total_cost"].sum()   if not df.empty else 0.0
total_ret = df["total_return"].sum() if not df.empty else 0.0
net_pl    = total_ret - total_inv
roi       = (net_pl / total_inv * 100) if total_inv > 0 else 0.0
n_total   = len(df)
missing   = int(df["cash_out"].isna().sum()) if not df.empty else 0


# ═════════════════════════════════════════════════════════════════════════════
# ממשק משתמש
# ═════════════════════════════════════════════════════════════════════════════

# ── 1. כותרת ─────────────────────────────────────────────────────────────────
st.markdown("# ♠ דשבורד בנקרול")
st.caption("GG Poker · מעקב טורנירים")

if missing > 0:
    st.warning(f"⚠️ {missing} טורנירים ללא נתוני תשלום")
elif n_total > 0:
    st.success("✓ כל התשלומים מעודכנים")

st.divider()

# ── 2. העלאת קבצים — form עם כפתור תמיד גלוי ───────────────────────────────
st.subheader("📂 העלאת קבצים")

with st.form("upload_form", clear_on_submit=True):
    uploaded = st.file_uploader(
        "בחר קבצי GG Poker (.txt) — אפשר לבחור כמה שרוצה",
        accept_multiple_files=True,
        label_visibility="visible",
    )
    submitted = st.form_submit_button(
        "📥 ייבא קבצים עכשיו",
        use_container_width=True,
    )

if submitted:
    if uploaded:
        with st.spinner(f"מעבד {len(uploaded)} קבצים…"):
            new, upd, parse_log = handle_uploaded_files(uploaded)
        st.session_state["parse_log"] = parse_log
        if new + upd > 0:
            st.success(f"✅ {new} חדשים · {upd} עודכנו — רואים את הנתונים למטה!")
            st.rerun()
        else:
            st.error("❌ לא זוהו טורנירים. פתח 'פירוט' למטה.")
    else:
        st.warning("⬆️ בחר קבצים תחילה, ואז לחץ ייבא")

if st.session_state.get("parse_log"):
    with st.expander("🔍 פירוט ייבוא אחרון"):
        for line in st.session_state["parse_log"][:40]:
            st.caption(line)

st.divider()

# ── 3. KPI ────────────────────────────────────────────────────────────────────
st.subheader("📊 סיכום")

c1, c2 = st.columns(2)
with c1: st.metric("טורנירים", n_total)
with c2: st.metric("סה״כ השקעה", fmt(total_inv))

c3, c4 = st.columns(2)
with c3: st.metric("סה״כ החזר", fmt(total_ret))
with c4: st.metric("רווח / הפסד", fmt(net_pl, sign=True), delta=f"{roi:+.1f}%")

c5, c6 = st.columns(2)
with c5: st.metric("ROI", f"{roi:+.1f}%")
with c6: st.metric("ממתינים", missing)

st.divider()

# ── 4. גרף ───────────────────────────────────────────────────────────────────
st.subheader("📈 צמיחת הבנקרול")

if df.empty:
    st.info("העלה קבצים כדי לראות את הגרף.")
else:
    df_c = df.dropna(subset=["date_dt"]).sort_values("date_dt").copy()
    if not df_c.empty:
        df_c["net_t"] = df_c["bounties"].fillna(0) + df_c["cash_out"].fillna(0) - df_c["buy_in"].fillna(0) - df_c["rake"].fillna(0)
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
            height=280, margin=dict(l=0, r=0, t=10, b=0),
            font=dict(color="#8b949e", size=11),
            xaxis=dict(showgrid=False, zeroline=False, tickangle=-45, tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False, tickprefix="$", tickfont=dict(size=11)),
            hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d", font=dict(color="#e6edf3", size=14)),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
    else:
        st.info("אין טורנירים עם תאריך לגרף.")

st.divider()

# ── 5. עדכון כספים ────────────────────────────────────────────────────────────
st.subheader("💰 עדכון כספים")

missing_list = [t for t in rows if t.get("cash_out") is None]

if not missing_list:
    st.success("✓ הכל מעודכן!")
else:
    st.caption(f"{len(missing_list)} טורנירים ממתינים. הכנס $0 אם לא קיבלת תשלום.")
    for t in missing_list:
        date_str  = str(t.get("date", ""))[:10] or "—"
        title_str = t.get("title") or t["tournament_id"]
        cost      = (t.get("buy_in") or 0) + (t.get("rake") or 0)

        with st.expander(f"🟡 {date_str}  {title_str[:35]}  [{fmt(cost)}]"):
            ca, cb = st.columns(2)
            with ca:
                payout = st.number_input("סכום ($)", min_value=0.0, step=0.01,
                                         format="%.2f", key=f"p_{t['tournament_id']}")
            with cb:
                notes = st.text_input("הערות", key=f"n_{t['tournament_id']}",
                                      placeholder="מקום 3, FT...")
            if st.button("💾 שמור", key=f"s_{t['tournament_id']}"):
                _ss_set_cash_out(t["tournament_id"], payout, notes)
                st.success(f"נשמר: {fmt(payout)}")
                st.rerun()

st.divider()

# ── 6. טבלת היסטוריה ─────────────────────────────────────────────────────────
st.subheader("🗂 היסטוריית טורנירים")

if df.empty:
    st.info("לא נרשמו טורנירים עדיין.")
else:
    fc1, fc2 = st.columns([3, 1])
    with fc1:
        search = st.text_input("חיפוש", placeholder="שם טורניר...", label_visibility="collapsed")
    with fc2:
        only_p = st.checkbox("⏳ בלבד", value=False)

    disp = df[["date_dt","title","buy_in","bounties","cash_out","net","roi_pct"]].copy()
    disp.columns = ["תאריך","טורניר","כניסה","באונטי","תשלום","רווח/הפסד","ROI%"]
    disp["תאריך"]     = disp["תאריך"].dt.strftime("%d/%m/%y").fillna("—")
    disp["כניסה"]     = disp["כניסה"].map(lambda x: f"${x:,.2f}")
    disp["באונטי"]    = disp["באונטי"].map(lambda x: f"${x:,.2f}")
    disp["תשלום"]     = disp["תשלום"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "⏳")
    disp["רווח/הפסד"] = disp["רווח/הפסד"].map(lambda x: f"+${x:,.2f}" if x > 0 else f"-${abs(x):,.2f}")
    disp["ROI%"]      = disp["ROI%"].map(lambda x: f"{x:+.1f}%")

    if search:
        disp = disp[disp["טורניר"].str.contains(search, case=False, na=False)]
    if only_p:
        disp = disp[disp["תשלום"] == "⏳"]

    st.dataframe(disp, use_container_width=True, hide_index=True,
                 height=min(60 + len(disp) * 38, 480))

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# 7. ניתוח משחק — שיפור לאורך זמן
# ═════════════════════════════════════════════════════════════════════════════

st.subheader("🧠 ניתוח משחק")

gs_rows = list(_ss_game_stats().values())

# נסה לטעון מה-DB אם session_state ריק
if not gs_rows:
    try:
        gs_rows = db.get_all_game_stats()
        for row in gs_rows:
            _ss_game_stats()[row["tournament_id"]] = row
    except Exception:
        pass

# סנן רק טורנירים עם מספיק ידיים
gs_rows = [r for r in gs_rows if (r.get("hands_played") or 0) >= 10]

if not gs_rows:
    st.info("העלה קבצי GG Poker כדי לקבל ניתוח משחק. הנתונים מחושבים אוטומטית בזמן הייבוא.")
else:
    gs_df = pd.DataFrame(gs_rows)
    gs_df["date_dt"] = pd.to_datetime(gs_df.get("date", pd.Series(dtype=str)), errors="coerce")
    gs_df = gs_df.sort_values("date_dt").reset_index(drop=True)
    gs_df["lbl"] = gs_df["date_dt"].dt.strftime("%d/%m").fillna("—")

    # ── סיכום ממוצע ─────────────────────────────────────────────────────────
    st.markdown("**ממוצע כולל**")
    avg_vpip = gs_df["vpip_pct"].mean()
    avg_pfr  = gs_df["pfr_pct"].mean()
    avg_af   = gs_df["af"].mean()
    avg_cbet = gs_df["cbet_pct"].mean()

    ma1, ma2, ma3, ma4 = st.columns(4)
    with ma1: st.metric("VPIP ממוצע", f"{avg_vpip:.1f}%", help="אידיאלי: 16-28%")
    with ma2: st.metric("PFR ממוצע",  f"{avg_pfr:.1f}%",  help="אידיאלי: 12-22%")
    with ma3: st.metric("AF ממוצע",   f"{avg_af:.2f}",    help="אידיאלי: 2-6")
    with ma4: st.metric("C-Bet ממוצע",f"{avg_cbet:.1f}%", help="אידיאלי: 50-80%")

    st.divider()

    # ── גרפי שיפור לאורך זמן ────────────────────────────────────────────────
    st.markdown("**גרפי שיפור לאורך זמן**")

    STAT_CONFIG = [
        ("vpip_pct",      "VPIP %",      "#58a6ff", 16, 28),
        ("pfr_pct",       "PFR %",       "#3fb950", 12, 22),
        ("af",            "Aggression Factor", "#f0883e", 2.0, 6.0),
        ("cbet_pct",      "C-Bet %",     "#bc8cff", 50, 80),
        ("wtsd_pct",      "WTSD %",      "#ff7b72", 22, 32),
        ("fold_to_3b_pct","Fold to 3-Bet %", "#ffa657", 40, 70),
    ]

    tab_labels = [c[1] for c in STAT_CONFIG]
    tabs = st.tabs(tab_labels)

    for tab, (col, label, color, lo, hi) in zip(tabs, STAT_CONFIG):
        with tab:
            col_data = gs_df[col].dropna()
            if len(col_data) < 2:
                st.caption("אין מספיק נתונים לגרף זה.")
                continue

            y_vals = gs_df[col].fillna(method="ffill")
            # Moving average (window=3)
            ma = y_vals.rolling(3, min_periods=1).mean()

            fig = go.Figure()

            # Ideal range band
            fig.add_hrect(y0=lo, y1=hi,
                          fillcolor="rgba(63,185,80,0.08)",
                          line_width=0, annotation_text="טווח אידיאלי",
                          annotation_position="top right",
                          annotation_font=dict(color="#3fb950", size=10))

            # Actual values
            fig.add_trace(go.Scatter(
                x=gs_df["lbl"], y=y_vals,
                mode="lines+markers",
                line=dict(color=color, width=2, dash="dot"),
                marker=dict(size=8, color=color),
                name=label,
                hovertemplate=f"<b>%{{x}}</b><br>{label}: <b>%{{y:.1f}}</b><extra></extra>",
            ))
            # Moving average
            fig.add_trace(go.Scatter(
                x=gs_df["lbl"], y=ma,
                mode="lines",
                line=dict(color=color, width=3),
                name="ממוצע נע",
                hovertemplate=f"<b>%{{x}}</b><br>ממוצע: <b>%{{y:.1f}}</b><extra></extra>",
            ))

            fig.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                height=240, margin=dict(l=0, r=0, t=10, b=0),
                font=dict(color="#8b949e", size=11),
                xaxis=dict(showgrid=False, zeroline=False, tickangle=-45, tickfont=dict(size=11)),
                yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False, tickfont=dict(size=11)),
                hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d", font=dict(color="#e6edf3", size=13)),
                legend=dict(orientation="h", yanchor="bottom", y=1.0,
                            bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    st.divider()

    # ── גילוי דליפות ─────────────────────────────────────────────────────────
    st.markdown("**🔍 זיהוי דליפות**")

    # חשב ממוצע על כל הטורנירים
    avg_stats = {
        "hands_played":   int(gs_df["hands_played"].sum()),
        "vpip_pct":       avg_vpip,
        "pfr_pct":        avg_pfr,
        "af":             avg_af,
        "cbet_pct":       avg_cbet,
        "wtsd_pct":       gs_df["wtsd_pct"].mean(),
        "fold_to_3b_pct": gs_df["fold_to_3b_pct"].mean(),
    }

    leaks = hh_analyzer.detect_leaks(avg_stats)

    if not leaks:
        st.success("✅ לא נמצאו דליפות ברורות — המשחק שלך בטווח הנכון!")
    else:
        for leak in leaks:
            icon = "🔴" if leak["severity"] == "high" else "🟡"
            direction = "⬇️ נמוך מדי" if leak["direction"] == "low" else "⬆️ גבוה מדי"
            with st.expander(f"{icon} {leak['name']} — {direction}  ({leak['value']:.1f})"):
                st.markdown(f"**{leak['message']}**")
                st.caption(f"טווח אידיאלי: {leak['low']} – {leak['high']}")

                # Mini gauge
                lo_g, hi_g = leak["low"], leak["high"]
                val_g = leak["value"]
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=val_g,
                    gauge={
                        "axis": {"range": [max(0, lo_g * 0.5), hi_g * 1.8], "tickfont": {"size": 10}},
                        "bar":  {"color": "#f85149" if leak["severity"] == "high" else "#d29922"},
                        "steps": [
                            {"range": [0, lo_g],   "color": "#21262d"},
                            {"range": [lo_g, hi_g], "color": "rgba(63,185,80,0.2)"},
                            {"range": [hi_g, hi_g * 1.8], "color": "#21262d"},
                        ],
                        "threshold": {"line": {"color": "#3fb950", "width": 3},
                                      "thickness": 0.85,
                                      "value": (lo_g + hi_g) / 2},
                    },
                    number={"suffix": "%" if "pct" in leak["key"] else "", "font": {"size": 20, "color": "#e6edf3"}},
                ))
                fig_g.update_layout(
                    paper_bgcolor="#161b22", height=140,
                    margin=dict(l=10, r=10, t=10, b=10),
                    font=dict(color="#8b949e"),
                )
                st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})

    st.divider()

    # ── טבלת סטטיסטיקות לפי טורניר ──────────────────────────────────────────
    with st.expander("📋 טבלת סטטיסטיקות מלאה"):
        gs_disp = gs_df[["lbl", "hands_played", "vpip_pct", "pfr_pct", "af",
                          "cbet_pct", "wtsd_pct", "fold_to_3b_pct"]].copy()
        gs_disp.columns = ["תאריך", "ידיים", "VPIP%", "PFR%", "AF", "C-Bet%", "WTSD%", "Fold/3B%"]
        for col in ["VPIP%", "PFR%", "C-Bet%", "WTSD%", "Fold/3B%"]:
            gs_disp[col] = gs_disp[col].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
        gs_disp["AF"] = gs_disp["AF"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
        st.dataframe(gs_disp, use_container_width=True, hide_index=True)

st.divider()

# ── 8. ניהול ─────────────────────────────────────────────────────────────────
with st.expander("⚙️ ניהול רשומות"):
    del_id = st.text_input("מזהה טורניר למחיקה", label_visibility="collapsed",
                           placeholder="Tournament ID")
    if st.button("🗑 מחק רשומה"):
        if del_id.strip():
            _ss_delete(del_id.strip())
            _ss_game_stats().pop(del_id.strip(), None)
            st.warning(f"נמחק: {del_id}")
            st.rerun()

st.caption("♠ דשבורד בנקרול פוקר · GG Poker")
