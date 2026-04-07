"""
GG Poker Hand History Parser
תומך בפורמט האמיתי:
  Poker Hand #TM...: Tournament #272532852,
  Bounty Hunters Deepstack Turbo $3.20 Hold'em No Limit -
  Level27(10,000/20,000(3,000)) - 2026/03/26 22:30:14
"""

import re
from datetime import datetime
from pathlib import Path


# ── Regex ─────────────────────────────────────────────────────────────────────

# Tournament ID
RE_TOURNAMENT_ID = re.compile(r"Tournament\s+#(\d+)", re.IGNORECASE)

# buy-in — פורמט GG האמיתי: "$3.20 Hold'em" או "$3.20 No Limit" וכו'
RE_BUYIN_TITLE = re.compile(
    r"\$(\d+(?:\.\d+)?)\s+(?:Hold'?em|No\s*Limit|NLH|PLO|Omaha|Stud)",
    re.IGNORECASE,
)
# פורמט ישן עם ראק: $5.00+$0.50
RE_BUYIN_PLUS = re.compile(
    r"\$(\d+(?:\.\d+)?)\s*\+\s*\$(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

# תאריך: 2026/03/26 22:30:14
RE_DATE = re.compile(r"(\d{4})[/-](\d{2})[/-](\d{2})\s+(\d{2}):(\d{2}):(\d{2})")

# שם טורניר: הטקסט שאחרי הפסיק ולפני סכום הכניסה
RE_TITLE = re.compile(
    r"Tournament\s+#\d+,\s*(.+?)\s+\$[\d.]+,?\s+(?:Hold'?em|No\s*Limit|NLH|PLO|Omaha|Stud)",
    re.IGNORECASE,
)

# שם קובץ: GG20260326-1641... או HH20231015...
RE_FNAME_DATE = re.compile(r"(?:GG|HH)(\d{4})(\d{2})(\d{2})")

# Bounty — כל הגרסאות
RE_BOUNTY_PATTERNS = [
    re.compile(r"Hero\s+wins?\s+\$(\d+(?:\.\d+)?)\s+bounty",                     re.IGNORECASE),
    re.compile(r"Hero\s+wins?\s+bounty\s+of\s+\$(\d+(?:\.\d+)?)",                re.IGNORECASE),
    re.compile(r"Hero\s+collected?\s+\$(\d+(?:\.\d+)?)\s+from\s+bounty",         re.IGNORECASE),
    re.compile(r"Hero\s+wins?\s+\$(\d+(?:\.\d+)?)\s+for\s+eliminating",          re.IGNORECASE),
    re.compile(r"Hero\s+wins?\s+\$(\d+(?:\.\d+)?)\s+for\s+knocking\s+out",       re.IGNORECASE),
    re.compile(r"Hero\s+wins?\s+the\s+\$(\d+(?:\.\d+)?)\s+bounty",               re.IGNORECASE),
    re.compile(r"Hero:\s+wins?\s+\$(\d+(?:\.\d+)?)\s+bounty",                    re.IGNORECASE),
]


# ── עזר ──────────────────────────────────────────────────────────────────────

def _parse_date(m: re.Match) -> datetime | None:
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                        int(m.group(4)), int(m.group(5)), int(m.group(6)))
    except Exception:
        return None


def _extract_buyin(header: str) -> tuple[float, float]:
    """
    מחלץ (buy_in, rake) מהשורה הראשונה של היד.
    מנסה קודם $X+$Y, אחר כך $X Hold'em/No Limit.
    """
    # פורמט $X+$Y
    m = RE_BUYIN_PLUS.search(header)
    if m:
        bi, rk = float(m.group(1)), float(m.group(2))
        if bi <= 500:  # sanity check — tournament buy-ins rarely exceed $500
            return bi, rk

    # פורמט GG האמיתי: $3.20 Hold'em
    m = RE_BUYIN_TITLE.search(header)
    if m:
        return float(m.group(1)), 0.0

    return 0.0, 0.0


def _extract_title(header: str) -> str:
    # פורמט: "Tournament #..., Sunday Hyper $5 Hold'em No Limit - Level..."
    # נרצה לחלץ: "Sunday Hyper $5"
    m = RE_TITLE.search(header)
    if m:
        title = m.group(1).strip()
        # הסר Hold'em/No Limit שנשאר בסוף
        title = re.sub(r"\s+(?:Hold'?em|No\s*Limit|NLH|PLO)\s*$", "", title, flags=re.IGNORECASE).strip()
        return title
    # fallback
    m2 = re.search(r"Tournament\s+#\d+,\s*(.+?)\s*[-–]\s*Level", header, re.IGNORECASE)
    if m2:
        return m2.group(1).strip()
    return "Unknown"


def _extract_bounties(hand: str) -> float:
    total = 0.0
    for pat in RE_BOUNTY_PATTERNS:
        for m in pat.finditer(hand):
            total += float(m.group(1))
    return total


def _date_from_filename(filename: str) -> datetime | None:
    m = RE_FNAME_DATE.search(filename)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass
    return None


# ── Summary file regexes ──────────────────────────────────────────────────────

RE_SUMMARY_BUYIN_3 = re.compile(
    r"Buy-in:\s*\$(\d+(?:\.\d+)?)\+\$(\d+(?:\.\d+)?)\+\$(\d+(?:\.\d+)?)"
)
RE_SUMMARY_BUYIN_2 = re.compile(
    r"Buy-in:\s*\$(\d+(?:\.\d+)?)\+\$(\d+(?:\.\d+)?)"
)
RE_SUMMARY_PLAYERS  = re.compile(r"(\d[\d,]*)\s+Players", re.IGNORECASE)
RE_SUMMARY_DATE     = re.compile(
    r"Tournament started\s+(\d{4})[/-](\d{2})[/-](\d{2})\s+(\d{2}):(\d{2}):(\d{2})"
)
RE_SUMMARY_POSITION = re.compile(
    r"^(\d+(?:st|nd|rd|th))\s*:\s*Hero", re.MULTILINE | re.IGNORECASE
)
RE_SUMMARY_RECEIVED = re.compile(
    r"You received a total of \$(\d+(?:\.\d+)?)", re.IGNORECASE
)
RE_SUMMARY_PAYOUT_LINE = re.compile(
    r"^\d+(?:st|nd|rd|th)\s*:\s*Hero,\s*\$(\d+(?:\.\d+)?)", re.MULTILINE | re.IGNORECASE
)


def _is_summary(content: str) -> bool:
    """בודק אם הקובץ הוא סיכום טורניר (לא היסטוריית ידיים)."""
    first = content.strip().splitlines()[0] if content.strip() else ""
    return (
        bool(re.match(r"Tournament\s+#\d+,", first))
        and "Buy-in:" in content[:400]
        and "Poker Hand" not in content[:200]
    )


def parse_summary_content(content: str, filename: str) -> dict | None:
    """
    מנתח קובץ סיכום טורניר של GG Poker.
    מחזיר dict עם tournament_id, buy_in, rake, cash_out, date, position, players.
    """
    content = content.strip().replace('\r\n', '\n').replace('\r', '\n')
    if not content:
        return None

    first_line = content.splitlines()[0]

    # Tournament ID
    m = RE_TOURNAMENT_ID.search(first_line)
    if not m:
        return None
    tournament_id = m.group(1)

    # Title
    title = _extract_title(first_line)

    # Buy-in
    buy_in = rake = 0.0
    m3 = RE_SUMMARY_BUYIN_3.search(content)
    if m3:
        # $prize+$rake+$bounty_contribution → cost = all three
        prize_part  = float(m3.group(1))
        rake_part   = float(m3.group(2))
        bounty_part = float(m3.group(3))
        buy_in = prize_part + bounty_part  # without rake
        rake   = rake_part
    else:
        m2 = RE_SUMMARY_BUYIN_2.search(content)
        if m2:
            buy_in = float(m2.group(1))
            rake   = float(m2.group(2))

    # Date
    date = None
    dm = RE_SUMMARY_DATE.search(content)
    if dm:
        date = _parse_date(dm)
    if date is None:
        date = _date_from_filename(filename)

    # Cash out — prefer "received a total of" line
    cash_out = None
    mr = RE_SUMMARY_RECEIVED.search(content)
    if mr:
        cash_out = float(mr.group(1))
    else:
        mp = RE_SUMMARY_PAYOUT_LINE.search(content)
        if mp:
            cash_out = float(mp.group(1))

    # Position and players
    position = None
    mpos = RE_SUMMARY_POSITION.search(content)
    if mpos:
        position = mpos.group(1)

    players = None
    mpl = RE_SUMMARY_PLAYERS.search(content)
    if mpl:
        players = int(mpl.group(1).replace(",", ""))

    return {
        "tournament_id": tournament_id,
        "filename":      filename,
        "title":         title,
        "date":          date,
        "buy_in":        buy_in,
        "rake":          rake,
        "bounties":      0.0,        # bounties collected tracked from hand history
        "cash_out":      cash_out,   # set automatically from summary
        "position":      position,
        "players":       players,
        "source_file":   filename,
        "is_summary":    True,
    }


# ── API ───────────────────────────────────────────────────────────────────────

def parse_content(content: str, filename: str) -> dict | None:
    """
    מנתח תוכן קובץ היסטוריית ידיים של GG Poker מהזיכרון.
    מחזיר dict או None אם הקובץ לא מזוהה כטורניר.
    """
    content = content.strip()
    if not content:
        return None

    # Normalise Windows line endings before splitting
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    hands = [h.strip() for h in re.split(r"\n{2,}", content) if h.strip()]
    if not hands:
        return None

    first = hands[0]

    # חובה — Tournament ID
    m = RE_TOURNAMENT_ID.search(first)
    if not m:
        return None
    tournament_id = m.group(1)

    # תאריך — מהיד הראשונה, אחרת משם הקובץ
    date = None
    dm = RE_DATE.search(first)
    if dm:
        date = _parse_date(dm)
    if date is None:
        date = _date_from_filename(filename)

    buy_in, rake = _extract_buyin(first)
    title = _extract_title(first)

    # bounties — סרוק כל הידיים
    bounties = sum(_extract_bounties(h) for h in hands)

    return {
        "tournament_id": tournament_id,
        "filename":      filename,
        "title":         title,
        "date":          date,
        "buy_in":        buy_in,
        "rake":          rake,
        "bounties":      bounties,
        "source_file":   filename,
    }


def parse_file(filepath: str | Path) -> dict | None:
    filepath = Path(filepath)
    try:
        raw = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return parse_content(raw, filepath.name)


def parse_folder(folder: str | Path) -> list[dict]:
    folder = Path(folder)
    tournaments: dict[str, dict] = {}

    for filepath in sorted(folder.glob("*.txt")):
        result = parse_file(filepath)
        if result is None:
            continue
        tid = result["tournament_id"]
        if tid not in tournaments:
            tournaments[tid] = result
        else:
            tournaments[tid]["bounties"] += result["bounties"]
            if result["date"] and (
                tournaments[tid]["date"] is None
                or result["date"] < tournaments[tid]["date"]
            ):
                tournaments[tid]["date"] = result["date"]
            if tournaments[tid]["buy_in"] == 0.0 and result["buy_in"] > 0:
                tournaments[tid]["buy_in"] = result["buy_in"]
                tournaments[tid]["rake"]   = result["rake"]

    results = list(tournaments.values())
    results.sort(key=lambda r: r["date"] or datetime.min)
    return results
