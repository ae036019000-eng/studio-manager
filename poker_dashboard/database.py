"""
SQLite database layer for the Poker Bankroll Dashboard.

Schema
------
tournaments
    id              INTEGER  PK autoincrement
    tournament_id   TEXT     unique GG tournament number
    filename        TEXT
    title           TEXT
    date            TEXT     ISO-8601
    buy_in          REAL     total buy-in paid (excluding rake)
    rake            REAL     fee paid to the house
    bounties        REAL     bounty money collected during play
    cash_out        REAL     final payout (NULL = unknown)
    notes           TEXT
    created_at      TEXT     ISO-8601 insert timestamp
    updated_at      TEXT     ISO-8601 last update timestamp
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


# /tmp תמיד ניתן לכתיבה — גם ב-Streamlit Cloud
DB_PATH = Path("/tmp/bankroll.db")


# ── Connection helper ─────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Schema ────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create tables if they don't exist yet."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tournaments (
                id            INTEGER  PRIMARY KEY AUTOINCREMENT,
                tournament_id TEXT     NOT NULL UNIQUE,
                filename      TEXT,
                title         TEXT,
                date          TEXT,
                buy_in        REAL     NOT NULL DEFAULT 0,
                rake          REAL     NOT NULL DEFAULT 0,
                bounties      REAL     NOT NULL DEFAULT 0,
                cash_out      REAL,
                notes         TEXT,
                created_at    TEXT     NOT NULL,
                updated_at    TEXT     NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS game_stats (
                tournament_id   TEXT     PRIMARY KEY,
                hands_played    INTEGER  DEFAULT 0,
                vpip_pct        REAL,
                pfr_pct         REAL,
                af              REAL,
                fold_pf_pct     REAL,
                saw_flop_pct    REAL,
                wtsd_pct        REAL,
                wwsf_pct        REAL,
                cbet_pct        REAL,
                fold_to_3b_pct  REAL,
                three_bet_pct   REAL,
                updated_at      TEXT
            )
            """
        )


# ── Write operations ──────────────────────────────────────────────────────────

def upsert_tournament(parsed: dict) -> str:
    """
    Insert a newly-parsed tournament or update its parser-controlled fields.

    Fields that the user can edit manually (cash_out, notes) are never
    overwritten by a re-parse — only the header data and bounties are updated.

    Returns 'inserted' | 'updated' | 'skipped'.
    """
    tid = parsed.get("tournament_id")
    if not tid:
        return "skipped"

    date_str = (
        parsed["date"].isoformat()
        if isinstance(parsed.get("date"), datetime)
        else parsed.get("date")
    )
    now = _now()

    with _connect() as conn:
        existing = conn.execute(
            "SELECT id, bounties FROM tournaments WHERE tournament_id = ?", (tid,)
        ).fetchone()

        if existing is None:
            conn.execute(
                """
                INSERT INTO tournaments
                    (tournament_id, filename, title, date, buy_in, rake, bounties,
                     cash_out, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
                """,
                (
                    tid,
                    parsed.get("filename"),
                    parsed.get("title", "Unknown"),
                    date_str,
                    parsed.get("buy_in", 0.0),
                    parsed.get("rake", 0.0),
                    parsed.get("bounties", 0.0),
                    now,
                    now,
                ),
            )
            return "inserted"
        else:
            # Refresh parser fields; preserve cash_out / notes
            conn.execute(
                """
                UPDATE tournaments
                SET filename   = ?,
                    title      = ?,
                    date       = ?,
                    buy_in     = ?,
                    rake       = ?,
                    bounties   = ?,
                    updated_at = ?
                WHERE tournament_id = ?
                """,
                (
                    parsed.get("filename"),
                    parsed.get("title", "Unknown"),
                    date_str,
                    parsed.get("buy_in", 0.0),
                    parsed.get("rake", 0.0),
                    parsed.get("bounties", 0.0),
                    now,
                    tid,
                ),
            )
            return "updated"


def set_cash_out(tournament_id: str, amount: float | None, notes: str = "") -> None:
    """Set the final payout (and optional notes) for a tournament."""
    with _connect() as conn:
        conn.execute(
            """
            UPDATE tournaments
            SET cash_out   = ?,
                notes      = ?,
                updated_at = ?
            WHERE tournament_id = ?
            """,
            (amount, notes or None, _now(), tournament_id),
        )


def delete_tournament(tournament_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM tournaments WHERE tournament_id = ?", (tournament_id,)
        )


# ── Read operations ───────────────────────────────────────────────────────────

def get_all_tournaments() -> list[dict]:
    """Return every tournament row as a list of plain dicts, ordered by date."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM   tournaments
            ORDER  BY COALESCE(date, created_at) ASC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def get_missing_payouts() -> list[dict]:
    """Tournaments where cash_out has never been recorded (NULL)."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM   tournaments
            WHERE  cash_out IS NULL
            ORDER  BY COALESCE(date, created_at) ASC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    """Aggregate KPI figures."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*)                              AS total_tournaments,
                COALESCE(SUM(buy_in + rake), 0)       AS total_invested,
                COALESCE(SUM(bounties), 0)            AS total_bounties,
                COALESCE(SUM(COALESCE(cash_out, 0)), 0) AS total_cash,
                COUNT(*) FILTER (WHERE cash_out IS NULL) AS missing_payouts
            FROM tournaments
            """
        ).fetchone()
    return dict(row)


# ── Game stats ────────────────────────────────────────────────────────────────

def upsert_game_stats(tournament_id: str, stats: dict) -> None:
    """שמור או עדכן סטטיסטיקות משחק לטורניר."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO game_stats
                (tournament_id, hands_played, vpip_pct, pfr_pct, af,
                 fold_pf_pct, saw_flop_pct, wtsd_pct, wwsf_pct,
                 cbet_pct, fold_to_3b_pct, three_bet_pct, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(tournament_id) DO UPDATE SET
                hands_played   = excluded.hands_played,
                vpip_pct       = excluded.vpip_pct,
                pfr_pct        = excluded.pfr_pct,
                af             = excluded.af,
                fold_pf_pct    = excluded.fold_pf_pct,
                saw_flop_pct   = excluded.saw_flop_pct,
                wtsd_pct       = excluded.wtsd_pct,
                wwsf_pct       = excluded.wwsf_pct,
                cbet_pct       = excluded.cbet_pct,
                fold_to_3b_pct = excluded.fold_to_3b_pct,
                three_bet_pct  = excluded.three_bet_pct,
                updated_at     = excluded.updated_at
            """,
            (
                tournament_id,
                stats.get("hands_played", 0),
                stats.get("vpip_pct"),
                stats.get("pfr_pct"),
                stats.get("af"),
                stats.get("fold_pf_pct"),
                stats.get("saw_flop_pct"),
                stats.get("wtsd_pct"),
                stats.get("wwsf_pct"),
                stats.get("cbet_pct"),
                stats.get("fold_to_3b_pct"),
                stats.get("three_bet_pct"),
                _now(),
            ),
        )


def get_all_game_stats() -> list[dict]:
    """החזר את כל סטטיסטיקות המשחק מחוברות לתאריך הטורניר."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT  gs.*,
                    t.date,
                    t.title
            FROM    game_stats gs
            JOIN    tournaments t USING (tournament_id)
            ORDER   BY COALESCE(t.date, gs.updated_at) ASC
            """
        ).fetchall()
    return [dict(r) for r in rows]
