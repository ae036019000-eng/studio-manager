# Poker Bankroll Dashboard — Context

## Stack
- **Python / Streamlit** — `app.py` is the entry point
- **SQLite** — `/tmp/bankroll.db` (writable on Streamlit Cloud)
- **session_state** — primary data store (reliable on Cloud; DB is best-effort backup)
- **Plotly** — interactive charts

## Files
| File | Purpose |
|------|---------|
| `app.py` | Main UI — KPI, upload, chart, analysis, table |
| `parser.py` | Parse GG Poker `.txt` hand history files |
| `analyzer.py` | Per-hand stats: VPIP, PFR, AF, C-Bet, leaks |
| `database.py` | SQLite schema + CRUD helpers |
| `requirements.txt` | `streamlit>=1.32`, `pandas>=2.0`, `plotly>=5.18` |
| `tests.py` | 31-test suite (parser, analyzer, DB) |

## Key design decisions
- **No sidebar** — hidden via CSS (`display:none`) for iPhone UX
- **`st.form` upload** — always shows the submit button (iOS Safari fix)
- **`session_state` is truth** — DB may be empty on cold start; state persists within a session
- **cash_out stays NaN** — until user enters payout; P/L/ROI only calculated on settled tournaments
- **Analysis loaded on upload** — `handle_uploaded_files()` calls `hh_analyzer.analyze_tournament()` and stores result in `_ss_game_stats()`

## GG Poker hand format
```
Poker Hand #TM...: Tournament #272532852,
Bounty Hunters Deepstack Turbo $3.20 Hold'em No Limit -
Level27(10,000/20,000(3,000)) - 2026/03/26 22:30:14
```
- Tournament ID: `Tournament #(\d+)`
- Buy-in: `\$(\d+(?:\.\d+)?)\s+(?:Hold'?em|No\s*Limit|...)` — NOT `$X+$Y` format
- Title: text between `Tournament #NNN,` and `$X Hold'em`

## Session_state keys
- `tournaments` — `dict[tournament_id → dict]`
- `game_stats`  — `dict[tournament_id → dict]`
- `db_loaded`   — bool flag (load from DB once per session)
- `parse_log`   — list of strings from last upload

## Known bugs fixed
1. `fillna(method="ffill")` → `.ffill()` (pandas 2.x deprecation)
2. `sample_warning` leak item lacks `direction`/`value` → handled with `st.info()`
3. `cash_out=None` was coerced to 0 → KPI showed wrong P/L
4. `KeyError: 'cash_out'` → all numeric cols ensured before DataFrame ops
5. iOS vertical text → replaced custom HTML KPI cards with `st.metric()`
6. Upload confirm button not appearing on iOS → `st.form` + `st.form_submit_button`

## Running locally
```bash
cd studio-manager
git pull origin main
python3 -m streamlit run poker_dashboard/app.py
```

## Streamlit Cloud settings
- **Branch**: `main`
- **Main file**: `poker_dashboard/app.py`
- **Repo**: `ae036019000-eng/studio-manager`

## Analysis stats (analyzer.py)
| Stat | Ideal range | Notes |
|------|-------------|-------|
| VPIP% | 16–28% | voluntary preflop investment |
| PFR%  | 12–22% | preflop raise % |
| AF    | 2.0–6.0 | aggression factor |
| C-Bet%| 50–80% | continuation bet |
| WTSD% | 22–32% | went to showdown |
| Fold/3B% | 40–70% | fold to 3-bet |
