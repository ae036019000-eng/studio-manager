"""
דשבורד בנקרול פוקר — GG Poker
מותאם לאייפון | נתונים ב-session_state (אמין ב-Streamlit Cloud)
3-page routing: dashboard / tournament / improvement
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
    initial_sidebar_state="auto",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# ── CSS — מינימלי, בטוח ל-iOS ─────────────────────────────────────────────────
st.markdown("""
<style>
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

def _ss_tournaments() -> dict:
    """מחזיר את כל הטורנירים מה-session_state."""
    return st.session_state.setdefault("tournaments", {})


def _ss_load_from_db():
    """טוען מה-DB ל-session_state (פעם אחת בלבד)."""
    if st.session_state.get("db_loaded"):
        return
    for row in db.get_all_tournaments():
        _ss_tournaments()[row["tournament_id"]] = row
    try:
        for row in db.get_all_game_stats():
            _ss_game_stats()[row["tournament_id"]] = row
    except Exception:
        pass
    st.session_state["db_loaded"] = True


def _ss_upsert(t: dict):
    """שומר טורניר ב-session_state וגם מנסה ב-DB."""
    tid = t["tournament_id"]
    existing = _ss_tournaments().get(tid)
    if existing:
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


def _ss_game_stats() -> dict:
    return st.session_state.setdefault("game_stats", {})


def _ss_hand_summaries() -> dict:
    return st.session_state.setdefault("hand_summaries", {})


def handle_uploaded_files(files) -> tuple:
    """
    מנתח שני סוגי קבצים:
      - קבצי היסטוריית ידיים (Poker Hand #...) → ניתוח משחק + bounties
      - קבצי סיכום טורניר (Tournament #..., Buy-in:) → cash_out אוטומטי + buy-in מדויק
    """
    new_c = upd_c = 0
    # tid → {"hh": (result, raw_content), "summary": result}
    by_tid: dict[str, dict] = {}
    log: list = []

    for f in files:
        try:
            content = f.getvalue().decode("utf-8", errors="replace")
        except Exception as e:
            log.append(f"❌ {f.name}: {e}")
            continue

        # זיהוי סוג קובץ
        if hh_parser._is_summary(content):
            result = hh_parser.parse_summary_content(content, f.name)
            if result is None:
                log.append(f"⚠️ {f.name}: סיכום לא זוהה")
                continue
            tid = result["tournament_id"]
            log.append(
                f"📋 {f.name[:40]} → סיכום #{tid} | "
                f"עלות:${result['buy_in']+result['rake']:.2f} | "
                f"תשלום:${result['cash_out']:.2f}" if result.get('cash_out') else
                f"📋 {f.name[:40]} → סיכום #{tid}"
            )
            by_tid.setdefault(tid, {})["summary"] = result
        else:
            result = hh_parser.parse_content(content, f.name)
            if result is None:
                first = content.strip().splitlines()[0][:80] if content.strip() else "(ריק)"
                log.append(f"⚠️ {f.name}: לא זוהה — {first}")
                continue
            tid = result["tournament_id"]
            log.append(
                f"✅ {f.name[:40]} → ידיים #{tid} | "
                f"buy-in:${result['buy_in']:.2f} | bounty:${result['bounties']:.2f}"
            )
            by_tid.setdefault(tid, {})
            if "hh" not in by_tid[tid]:
                by_tid[tid]["hh"] = [result, content]
                by_tid[tid]["hh_count"] = 1
            else:
                by_tid[tid]["hh"][0]["bounties"] += result["bounties"]
                by_tid[tid]["hh"][1] += "\n\n" + content
                by_tid[tid]["hh_count"] = by_tid[tid].get("hh_count", 1) + 1

    # ── מיזוג ושמירה ─────────────────────────────────────────────────────────
    for tid, parts in by_tid.items():
        hh_result, raw_content = parts["hh"] if "hh" in parts else (None, "")
        summary = parts.get("summary")

        # בנה רשומת טורניר — סיכום גובר על ידיים (buy-in ו-cash_out מדויקים יותר)
        if hh_result and summary:
            merged = {**hh_result}
            merged["buy_in"]   = summary["buy_in"]
            merged["rake"]     = summary["rake"]
            merged["cash_out"] = summary["cash_out"]
            merged["title"]    = summary["title"] if summary["title"] != "Unknown" else hh_result["title"]
            if summary.get("date"):
                merged["date"] = summary["date"]
        elif summary:
            merged = {**summary}
        else:
            merged = hh_result

        if merged is None:
            continue

        hh_count = 0
        if "hh" in parts:
            # Count how many HH files contributed (stored separately)
            hh_count = parts.get("hh_count", 1)
        merged["entries"] = hh_count if hh_count > 0 else 1

        if tid in _ss_tournaments():
            upd_c += 1
        else:
            new_c += 1

        # cash_out מהסיכום — לא נדרוס אם כבר הוזן ידנית
        existing = _ss_tournaments().get(tid, {})
        if existing.get("cash_out") is not None and merged.get("cash_out") is None:
            merged["cash_out"] = existing["cash_out"]

        _ss_upsert(merged)

        # ניתוח משחק רק אם יש קובץ ידיים
        if raw_content:
            try:
                game_stats = hh_analyzer.analyze_tournament(raw_content)
                hands = game_stats.get("hands_played", 0)
                log.append(f"🧠 ניתוח #{tid}: {hands} ידיים | VPIP {game_stats.get('vpip_pct',0):.1f}% | PFR {game_stats.get('pfr_pct',0):.1f}%")
                if hands > 0:
                    _ss_game_stats()[tid] = {
                        "tournament_id": tid,
                        "date":  merged.get("date"),
                        "title": merged.get("title"),
                        **game_stats,
                    }
                    try:
                        db.upsert_game_stats(tid, game_stats)
                    except Exception as db_err:
                        log.append(f"⚠️ DB שמירה נכשלה עבור {tid}: {db_err}")
            except Exception as e:
                log.append(f"⚠️ ניתוח משחק נכשל עבור {tid}: {e}")

            try:
                summaries = hh_analyzer.get_hand_summaries(raw_content)
                if summaries:
                    _ss_hand_summaries()[tid] = summaries
            except Exception:
                pass

    n_hh  = sum(1 for p in by_tid.values() if "hh" in p)
    n_sum = sum(1 for p in by_tid.values() if "summary" in p)
    log.insert(0,
        f"📊 {len(files)} קבצים | {len(by_tid)} טורנירים | "
        f"📋 {n_sum} סיכומים | 🃏 {n_hh} היסטוריות | "
        f"✅ {new_c} חדשים | 🔄 {upd_c} עודכנו"
    )
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
    for col in ["buy_in", "rake", "bounties"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    if "cash_out" not in df.columns:
        df["cash_out"] = float("nan")
    df["cash_out"] = pd.to_numeric(df["cash_out"], errors="coerce")

    df["date_dt"]    = pd.to_datetime(df["date"], errors="coerce")
    df["total_cost"] = df["buy_in"] + df["rake"]
    df["total_return"] = df["bounties"] + df["cash_out"]
    df["net"]          = df["total_return"] - df["total_cost"]
    df["roi_pct"]      = df.apply(
        lambda r: r["net"] / r["total_cost"] * 100
        if r["total_cost"] > 0 and pd.notna(r["net"]) else float("nan"),
        axis=1,
    )

total_inv    = df["total_cost"].sum()  if not df.empty else 0.0
df_settled   = df[df["cash_out"].notna()] if not df.empty else pd.DataFrame()
settled_cost = df_settled["total_cost"].sum()    if not df_settled.empty else 0.0
total_ret    = df_settled["total_return"].sum()  if not df_settled.empty else 0.0
net_pl       = total_ret - settled_cost
roi          = (net_pl / settled_cost * 100) if settled_cost > 0 else 0.0
n_total      = len(df)
missing      = sum(1 for t in rows if t.get("cash_out") is None)
# זכיות — טורנירים שקיבלת תשלום כלשהו (cash_out > 0)
n_settled    = len(df_settled)
n_wins       = int((df_settled["cash_out"] > 0).sum()) if not df_settled.empty else 0
itm_pct      = (n_wins / n_settled * 100) if n_settled > 0 else 0.0
total_won    = df_settled.loc[df_settled["cash_out"] > 0, "cash_out"].sum() if not df_settled.empty else 0.0


# ═════════════════════════════════════════════════════════════════════════════
# Page render functions
# ═════════════════════════════════════════════════════════════════════════════

def _render_dashboard():
    # ── 1. כותרת ─────────────────────────────────────────────────────────────
    st.markdown("# ♠ דשבורד בנקרול")
    st.caption("GG Poker · מעקב טורנירים")

    if missing > 0:
        st.warning(f"⚠️ {missing} טורנירים ללא נתוני תשלום")
    elif n_total > 0:
        st.success("✓ כל התשלומים מעודכנים")

    st.divider()

    # ── 2. העלאת קבצים ───────────────────────────────────────────────────────
    st.markdown("### 📂 העלאת קבצים חדשים")
    st.caption("בחר קבצי .txt מ-GG Poker — הנתונים מחושבים אוטומטית")

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
                st.metric("טורנירים שנטענו", len(_ss_tournaments()))
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

    # ── 3. KPI ────────────────────────────────────────────────────────────────
    st.subheader("📊 סיכום")

    if not df.empty and len(df) >= 2:
        df_sorted_kpi = df.sort_values("date_dt", na_position="last")
        last10 = df_sorted_kpi.tail(10)
        inv10 = last10["total_cost"].sum()
        roi10 = (last10["net"].sum() / inv10 * 100) if inv10 > 0 else 0.0
        roi_delta_val = roi10 - roi
        roi_trend_label = f"10 אחרונים: {roi10:+.1f}%"
    else:
        roi_delta_val = 0.0
        roi_trend_label = "—"

    c1, c2 = st.columns(2)
    with c1: st.metric("טורנירים", n_total)
    with c2: st.metric("סה״כ השקעה", fmt(total_inv))

    c3, c4 = st.columns(2)
    with c3: st.metric("סה״כ החזר", fmt(total_ret))
    with c4: st.metric(
        "רווח / הפסד",
        fmt(net_pl, sign=True),
        delta=f"ROI: {roi:+.1f}%",
        delta_color="normal" if net_pl >= 0 else "inverse",
    )

    c5, c6 = st.columns(2)
    with c5: st.metric(
        "ROI",
        f"{roi:+.1f}%",
        delta=roi_trend_label,
        delta_color="normal" if roi_delta_val >= 0 else "inverse",
    )
    with c6: st.metric("ממתינים", missing)

    c7, c8 = st.columns(2)
    with c7: st.metric(
        "זכיות (ITM)",
        f"{n_wins}/{n_settled}",
        delta=f"{itm_pct:.1f}%",
        delta_color="normal",
        help="מספר טורנירים שקיבלת בהם תשלום כלשהו",
    )
    with c8: st.metric(
        "סה״כ זכיות",
        fmt(total_won),
        help="סכום כל התשלומים שקיבלת",
    )

    st.divider()

    # ── 4. גרף ───────────────────────────────────────────────────────────────
    st.subheader("📈 צמיחת הבנקרול")

    if df.empty:
        st.markdown("""
<div style='text-align:center; padding: 40px 20px; color: #8b949e;'>
    <div style='font-size: 3rem;'>♠</div>
    <h3 style='color: #e6edf3;'>ברוך הבא לדשבורד הפוקר שלך</h3>
    <p>העלה קבצי היסטוריית ידיים מ-GG Poker כדי להתחיל לעקוב אחרי הביצועים שלך.</p>
</div>
""", unsafe_allow_html=True)
    else:
        df_c = df.dropna(subset=["date_dt", "cash_out"]).sort_values("date_dt").copy()
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

    # ── 5. עדכון כספים ────────────────────────────────────────────────────────
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

    # ── 6. רשימת טורנירים ────────────────────────────────────────────────────
    st.subheader("🗂 טורנירים")

    if not rows:
        st.info("לא נרשמו טורנירים עדיין.")
    else:
        for t in sorted(rows, key=lambda x: x.get("date") or "", reverse=True):
            tid = t["tournament_id"]
            date_s = str(t.get("date",""))[:10] or "—"
            title  = (t.get("title") or tid)[:40]
            cost   = (t.get("buy_in") or 0) + (t.get("rake") or 0)
            co     = t.get("cash_out")
            net    = ((t.get("bounties") or 0) + (co or 0)) - cost if co is not None else None
            roi_t  = (net / cost * 100) if (net is not None and cost > 0) else None

            with st.container():
                c1, c2 = st.columns([3, 1])
                with c1:
                    entries = t.get("entries", 1)
                    entries_str = f" · {entries}x כניסות" if entries > 1 else ""
                    st.markdown(f"**{title}**  \n{date_s} · Buy-in: ${cost:.2f}{entries_str}")
                    if net is not None:
                        color = "#3fb950" if net >= 0 else "#f85149"
                        sign  = "+" if net >= 0 else ""
                        roi_str = f" &nbsp; ROI: {roi_t:+.1f}%" if roi_t is not None else ""
                        st.markdown(f"<span style='color:{color};font-weight:700'>{sign}${net:.2f}</span>{roi_str}", unsafe_allow_html=True)
                    else:
                        st.caption("⏳ ממתין לתוצאה")
                with c2:
                    gs = _ss_game_stats().get(tid)
                    if gs:
                        if st.button("🔍 ניתוח", key=f"open_{tid}", use_container_width=True):
                            st.session_state["page"] = "tournament"
                            st.session_state["selected_tid"] = tid
                            st.rerun()
                    else:
                        st.caption("אין ניתוח")
                st.divider()

    with st.expander("⚙️ ניהול רשומות"):
        # מחק הכל
        st.markdown("**🗑 נקה את כל הנתונים**")
        st.caption("מוחק את כל הטורנירים מהאפליקציה ומה-DB")
        if st.button("🗑 מחק הכל ואפס", type="secondary", use_container_width=True):
            st.session_state.pop("tournaments", None)
            st.session_state.pop("game_stats", None)
            st.session_state.pop("hand_summaries", None)
            st.session_state.pop("db_loaded", None)
            st.session_state.pop("parse_log", None)
            try:
                import sqlite3
                conn = sqlite3.connect(db.DB_PATH)
                conn.execute("DELETE FROM tournaments")
                conn.execute("DELETE FROM game_stats")
                conn.commit()
                conn.close()
            except Exception:
                pass
            st.success("✅ כל הנתונים נמחקו — העלה מחדש")
            st.rerun()

        st.divider()

        # מחיקת טורניר בודד
        st.markdown("**מחיקת טורניר בודד**")
        with st.form("delete_form"):
            del_id = st.text_input("מזהה טורניר", label_visibility="collapsed",
                                   placeholder="Tournament ID (מספר)")
            if st.form_submit_button("🗑 מחק טורניר זה", use_container_width=True):
                if del_id.strip():
                    _ss_delete(del_id.strip())
                    _ss_game_stats().pop(del_id.strip(), None)
                    _ss_hand_summaries().pop(del_id.strip(), None)
                    st.warning(f"נמחק: {del_id}")
                    st.rerun()

    st.caption("♠ דשבורד בנקרול פוקר · GG Poker")


def _render_tournament(tid: str):
    # Back button
    if st.button("← חזור לדשבורד"):
        st.session_state["page"] = "dashboard"
        st.rerun()

    t   = _ss_tournaments().get(tid, {})
    gs  = _ss_game_stats().get(tid, {})
    hs  = _ss_hand_summaries().get(tid, [])

    # Header
    title    = t.get("title") or tid
    date_s   = str(t.get("date",""))[:10] or "—"
    buy_in   = t.get("buy_in", 0) or 0
    rake     = t.get("rake", 0) or 0
    bounties = t.get("bounties", 0) or 0
    cash_out = t.get("cash_out")
    cost     = buy_in + rake
    ret      = (bounties + (cash_out or 0)) if cash_out is not None else None
    net      = ret - cost if ret is not None else None
    roi_t    = (net / cost * 100) if (net is not None and cost > 0) else None

    st.markdown(f"# {title}")
    st.caption(f"📅 {date_s}  ·  ID: {tid}")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Buy-in", f"${cost:.2f}")
    with c2: st.metric("Bounties", f"${bounties:.2f}")
    with c3: st.metric("תשלום", f"${cash_out:.2f}" if cash_out is not None else "⏳")
    with c4: st.metric("P/L", f"${net:+.2f}" if net is not None else "⏳",
                       delta=f"ROI {roi_t:+.1f}%" if roi_t is not None else None,
                       delta_color="normal" if (roi_t or 0) >= 0 else "inverse")

    st.divider()

    # Stats
    if gs:
        st.subheader("📊 סטטיסטיקות משחק")
        hands = gs.get("hands_played", 0)
        st.caption(f"על בסיס {hands} ידיים")

        sc1, sc2, sc3 = st.columns(3)
        with sc1: st.metric("VPIP", f"{gs.get('vpip_pct',0):.1f}%", help="אידיאלי: 16-28%")
        with sc2: st.metric("PFR",  f"{gs.get('pfr_pct',0):.1f}%",  help="אידיאלי: 12-22%")
        with sc3: st.metric("AF",   f"{gs.get('af',0):.2f}",         help="אידיאלי: 2-6")

        sc4, sc5, sc6 = st.columns(3)
        with sc4: st.metric("C-Bet",   f"{gs.get('cbet_pct',0):.1f}%",      help="אידיאלי: 50-80%")
        with sc5: st.metric("WTSD",    f"{gs.get('wtsd_pct',0):.1f}%",      help="אידיאלי: 22-32%")
        with sc6: st.metric("Fold/3B", f"{gs.get('fold_to_3b_pct',0):.1f}%", help="אידיאלי: 40-70%")

        st.caption("📌 הסטטיסטיקות מבוססות על ניתוח של כל יד בטורניר — VPIP, PFR, AF, C-Bet וכו'. ראה טווחים אידיאליים ב-Tooltip.")

        st.divider()

        # Leaks for THIS tournament
        st.subheader("🔍 דליפות")
        leaks = hh_analyzer.detect_leaks(gs)
        if not leaks:
            st.success("✅ לא נמצאו דליפות ברורות בטורניר זה")
        else:
            for leak in leaks:
                if leak.get("sample_warning"):
                    st.info(f"⚠️ {leak['message']}")
                    continue
                icon = "🔴" if leak["severity"] == "high" else "🟡"
                direction = "⬇️ נמוך מדי" if leak["direction"] == "low" else "⬆️ גבוה מדי"
                st.markdown(f"{icon} **{leak['name']}** — {direction} ({leak['value']:.1f})  \n{leak['message']}")

        st.divider()
    else:
        st.info("אין נתוני ניתוח לטורניר זה. נסה להעלות מחדש את הקובץ.")

    # Hand analysis
    if hs:
        st.subheader(f"📋 ניתוח ידיים ({len(hs)} ידיים)")

        # Section A — Position breakdown table
        pos_stats = {}
        for hand in hs:
            p = hand["עמדה"]
            pos_stats.setdefault(p, {"ידיים": 0, "ניצחונות": 0})
            pos_stats[p]["ידיים"] += 1
            if hand["won"]:
                pos_stats[p]["ניצחונות"] += 1
        pos_df = pd.DataFrame([
            {"עמדה": p, "ידיים": v["ידיים"], "ניצחונות": v["ניצחונות"],
             "Win%": f"{v['ניצחונות']/v['ידיים']*100:.1f}%"}
            for p, v in pos_stats.items()
        ]).sort_values("ידיים", ascending=False)
        st.markdown("**📍 ביצועים לפי עמדה**")
        st.dataframe(pos_df, use_container_width=True, hide_index=True)

        # Section B — Pre-flop action breakdown
        total_h = len(hs)
        folds   = sum(1 for h in hs if "קיפול" in h["פעולה"])
        calls   = sum(1 for h in hs if h["פעולה"].startswith("call"))
        raises  = sum(1 for h in hs if "raise" in h["פעולה"] and "3-bet" not in h["פעולה"])
        three_b = sum(1 for h in hs if "3-bet" in h["פעולה"])
        action_df = pd.DataFrame([
            {"פעולה": "קיפול preflop", "ידיים": folds,   "%": f"{folds/total_h*100:.1f}%"},
            {"פעולה": "Call",          "ידיים": calls,   "%": f"{calls/total_h*100:.1f}%"},
            {"פעולה": "Raise/Open",    "ידיים": raises,  "%": f"{raises/total_h*100:.1f}%"},
            {"פעולה": "3-Bet",         "ידיים": three_b, "%": f"{three_b/total_h*100:.1f}%"},
        ])
        st.markdown("**🃏 פירוט פעולות preflop**")
        st.dataframe(action_df, use_container_width=True, hide_index=True)

        # Section C — Full hand list (collapsed)
        with st.expander(f"📋 כל הידיים ({len(hs)})"):
            hs_df = pd.DataFrame(hs)[["יד", "עמדה", "פעולה", "תוצאה"]]
            st.dataframe(hs_df, use_container_width=True, hide_index=True,
                         height=min(60 + len(hs_df) * 35, 500))
    elif gs:
        st.info("רשימת ידיים לא זמינה — העלה מחדש את קובץ הטורניר")


def _render_improvement():
    # Back button
    if st.button("← חזור"):
        st.session_state["page"] = "dashboard"
        st.rerun()

    st.markdown("# 📈 התפתחות המשחק שלך")
    st.caption("ניתוח קבלת ההחלטות שלך לאורך הטורנירים")

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
        return

    gs_df = pd.DataFrame(gs_rows)
    gs_df["date_dt"] = pd.to_datetime(gs_df.get("date", pd.Series(dtype=str)), errors="coerce")
    gs_df = gs_df.sort_values("date_dt").reset_index(drop=True)
    gs_df["lbl"] = gs_df["date_dt"].dt.strftime("%d/%m").fillna("—")

    # ── סיכום ממוצע ──────────────────────────────────────────────────────────
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

    # ── סיכום מגמה ───────────────────────────────────────────────────────────
    total_hands = int(gs_df["hands_played"].sum())
    n_gs = len(gs_df)
    if n_gs < 3:
        st.info("צריך לפחות 3 טורנירים לניתוח מגמה")
    else:
        st.markdown(f"**סיכום מגמה** — על בסיס {total_hands:,} ידיים")
        half = n_gs // 2
        first_half  = gs_df.iloc[:half]
        second_half = gs_df.iloc[half:]

        TREND_STATS = [
            ("vpip_pct", "VPIP"),
            ("pfr_pct",  "PFR"),
            ("af",       "Aggression Factor"),
            ("cbet_pct", "C-Bet"),
        ]
        trend_lines = []
        for stat_col, stat_name in TREND_STATS:
            if stat_col not in gs_df.columns:
                continue
            avg_first  = first_half[stat_col].mean()
            avg_second = second_half[stat_col].mean()
            diff = avg_second - avg_first
            if abs(diff) < 0.5:
                icon = "➡️ יציב"
            elif diff > 0:
                icon = "📈 משתפר"
            else:
                icon = "📉 מדרדר"
            trend_lines.append(f"**{stat_name}**: {icon}  ({avg_first:.1f} → {avg_second:.1f})")

        for line in trend_lines:
            st.markdown(line)

    st.divider()

    # ── גרפי שיפור לאורך זמן ─────────────────────────────────────────────────
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

            y_vals = gs_df[col].ffill()
            ma = y_vals.rolling(3, min_periods=1).mean()

            fig = go.Figure()

            fig.add_hrect(y0=lo, y1=hi,
                          fillcolor="rgba(63,185,80,0.08)",
                          line_width=0, annotation_text="טווח אידיאלי",
                          annotation_position="top right",
                          annotation_font=dict(color="#3fb950", size=10))

            fig.add_trace(go.Scatter(
                x=gs_df["lbl"], y=y_vals,
                mode="lines+markers",
                line=dict(color=color, width=2, dash="dot"),
                marker=dict(size=8, color=color),
                name=label,
                hovertemplate=f"<b>%{{x}}</b><br>{label}: <b>%{{y:.1f}}</b><extra></extra>",
            ))
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
            if leak.get("sample_warning"):
                st.info(f"⚠️ {leak['message']}")
                continue
            icon = "🔴" if leak["severity"] == "high" else "🟡"
            direction = "⬇️ נמוך מדי" if leak["direction"] == "low" else "⬆️ גבוה מדי"
            with st.expander(f"{icon} {leak['name']} — {direction}  ({leak['value']:.1f})"):
                st.markdown(f"**{leak['message']}**")
                st.caption(f"טווח אידיאלי: {leak['low']} – {leak['high']}")

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

    # ── היסטוריית דליפות (bar chart) ─────────────────────────────────────────
    st.markdown("**📊 היסטוריית דליפות לפי טורניר**")

    leak_labels = []
    leak_counts = []
    for _, row_gs in gs_df.iterrows():
        lbl_val = row_gs.get("lbl", "—")
        row_dict = row_gs.to_dict()
        these_leaks = hh_analyzer.detect_leaks(row_dict)
        real_leaks = [lk for lk in these_leaks if not lk.get("sample_warning")]
        leak_labels.append(lbl_val)
        leak_counts.append(len(real_leaks))

    if any(c > 0 for c in leak_counts):
        fig_lh = go.Figure(go.Bar(
            x=leak_labels,
            y=leak_counts,
            marker_color=["#f85149" if c >= 3 else "#d29922" if c >= 1 else "#3fb950" for c in leak_counts],
            hovertemplate="<b>%{x}</b><br>דליפות: %{y}<extra></extra>",
        ))
        fig_lh.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            height=220, margin=dict(l=0, r=0, t=10, b=0),
            font=dict(color="#8b949e", size=11),
            xaxis=dict(showgrid=False, zeroline=False, tickangle=-45, tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False, tickfont=dict(size=11), dtick=1),
            hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d", font=dict(color="#e6edf3", size=13)),
            showlegend=False,
        )
        st.plotly_chart(fig_lh, use_container_width=True, config={"displayModeBar": False, "responsive": True})
    else:
        st.success("✅ לא נמצאו דליפות בטורנירים האחרונים!")

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

    st.caption("♠ דשבורד בנקרול פוקר · GG Poker")


# ═════════════════════════════════════════════════════════════════════════════
# Sidebar navigation
# ═════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ♠ פוקר")
    st.divider()
    nav = st.radio(
        "ניווט",
        ["📊 דשבורד", "📈 שיפור משחק"],
        index=0 if st.session_state.get("page", "dashboard") != "improvement" else 1,
        label_visibility="collapsed",
    )
    if nav == "📊 דשבורד" and st.session_state.get("page") not in ("dashboard", "tournament"):
        st.session_state["page"] = "dashboard"
        st.rerun()
    elif nav == "📈 שיפור משחק" and st.session_state.get("page") != "improvement":
        st.session_state["page"] = "improvement"
        st.rerun()

    st.divider()
    st.caption(f"🃏 {n_total} טורנירים")
    st.caption(f"💰 ROI: {roi:+.1f}%")
    st.caption(f"🏆 ITM: {itm_pct:.1f}%")


# ═════════════════════════════════════════════════════════════════════════════
# Routing
# ═════════════════════════════════════════════════════════════════════════════

page = st.session_state.get("page", "dashboard")
selected_tid = st.session_state.get("selected_tid")

if page == "tournament" and selected_tid:
    _render_tournament(selected_tid)
elif page == "improvement":
    _render_improvement()
else:
    _render_dashboard()
