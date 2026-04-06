"""
GG Poker Hand History Parser
Reads .txt hand history files and extracts tournament data.
"""

import re
import os
from datetime import datetime
from pathlib import Path


# ── Regex patterns for GG Poker hand history format ──────────────────────────

# Tournament ID — כמה פורמטים: #T123, #123456, Tournament #HD...
RE_TOURNAMENT_ID = re.compile(r"Tournament\s+#(\w+)", re.IGNORECASE)

# Buy-in — $5+$0.50 / $5.00+$0.50 / 5+0.5 / ($5+$0.50)
RE_BUYIN = re.compile(
    r"\$?(\d+(?:\.\d+)?)\s*\+\s*\$?(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
# Buy-in without rake, e.g. "Buy-in: $10.00" or "Total Buy-In: $10.50"
RE_BUYIN_SINGLE = re.compile(
    r"(?:buy.?in|total buy.?in)[:\s]+\$?(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

# Date formats: 2024/03/15 18:00:12 or 2024-03-15 18:00:12
RE_DATE = re.compile(r"(\d{4})[/-](\d{2})[/-](\d{2})\s+(\d{2}):(\d{2}):(\d{2})")

RE_TITLE = re.compile(
    r"Tournament\s+#\w+,\s*(?:\$?[\d.]+\+\$?[\d.]+\s+)?(.+?)(?:,|\s+-\s+|\s+Level\s+)",
    re.IGNORECASE,
)

# Bounty — כל הגרסאות הידועות של GG Poker
RE_BOUNTY = re.compile(
    r"Hero\s+(?:wins?|collected?)\s+(?:the\s+)?\$(\d+(?:\.\d+)?)"
    r"(?:\s+(?:bounty|from bounty|for (?:eliminating|knocking out)))?",
    re.IGNORECASE,
)
RE_BOUNTY_ALT = re.compile(
    r"Hero\s+wins?\s+bounty\s+of\s+\$(\d+(?:\.\d+)?)", re.IGNORECASE
)
# "Hero: wins bounty $X"
RE_BOUNTY_ALT2 = re.compile(
    r"Hero[:\s]+wins?\s+\$?(\d+(?:\.\d+)?)\s+bounty", re.IGNORECASE
)

# Filename patterns: "HH20231015 T123456789 No Limit Hold'em $5+$0.50.txt"
RE_FNAME_DATE = re.compile(r"HH(\d{4})(\d{2})(\d{2})")
RE_FNAME_TID = re.compile(r"\bT(\d+)\b")
RE_FNAME_BUYIN = re.compile(r"\$(\d+(?:\.\d+)?)\+\$(\d+(?:\.\d+)?)")

# ─────────────────────────────────────────────────────────────────────────────


def _parse_date(match: re.Match) -> datetime | None:
    try:
        y, mo, d, h, mi, s = [int(x) for x in match.groups()]
        return datetime(y, mo, d, h, mi, s)
    except Exception:
        return None


def _extract_buyin_from_text(text: str) -> tuple[float, float]:
    """Return (buy_in, rake). Tries $X+$Y first, then single buy-in line."""
    # נסה $X+$Y (buy-in + rake)
    for m in RE_BUYIN.finditer(text):
        bi, rk = float(m.group(1)), float(m.group(2))
        # סנן התאמות לא סבירות (כגון chip counts כמו 1000+200)
        if bi <= 10000:
            return bi, rk
    # נסה "Buy-in: $X" בלבד
    m = RE_BUYIN_SINGLE.search(text)
    if m:
        return float(m.group(1)), 0.0
    return 0.0, 0.0


def _extract_bounties_from_hand(hand: str) -> float:
    """Sum all bounty amounts won by Hero in a single hand block."""
    total = 0.0
    for pattern in (RE_BOUNTY, RE_BOUNTY_ALT, RE_BOUNTY_ALT2):
        for m in pattern.finditer(hand):
            total += float(m.group(1))
    return total


def _parse_title(first_hand: str) -> str:
    """Extract a human-readable tournament name from the hand header."""
    m = RE_TITLE.search(first_hand)
    if m:
        return m.group(1).strip()
    return "Unknown"


def _info_from_filename(filename: str) -> dict:
    """Best-effort extraction from the file name alone."""
    info: dict = {}

    m = RE_FNAME_DATE.search(filename)
    if m:
        try:
            info["date"] = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass

    m = RE_FNAME_TID.search(filename)
    if m:
        info["tournament_id"] = m.group(1)

    m = RE_FNAME_BUYIN.search(filename)
    if m:
        info["buy_in"] = float(m.group(1))
        info["rake"] = float(m.group(2))

    return info


def parse_content(content: str, filename: str) -> dict | None:
    """
    Parse GG Poker hand history from a string (in-memory, no disk access).

    Returns a dict with keys:
        tournament_id, filename, date, buy_in, rake, bounties, title, source_file
    or None if not a recognisable tournament history.
    """
    info = _info_from_filename(filename)
    info.setdefault("tournament_id", None)
    info.setdefault("date", None)
    info.setdefault("buy_in", 0.0)
    info.setdefault("rake", 0.0)
    info["bounties"]    = 0.0
    info["title"]       = "Unknown"
    info["filename"]    = filename
    info["source_file"] = filename

    if not content.strip():
        return None

    hands = [h.strip() for h in re.split(r"\n{2,}", content) if h.strip()]
    if not hands:
        return None

    first_hand = hands[0]

    m = RE_TOURNAMENT_ID.search(first_hand)
    if m:
        info["tournament_id"] = m.group(1)
    if not info["tournament_id"]:
        return None

    m = RE_DATE.search(first_hand)
    if m:
        info["date"] = _parse_date(m)

    bi, rk = _extract_buyin_from_text(first_hand)
    if bi > 0:
        info["buy_in"] = bi
        info["rake"]   = rk

    info["title"] = _parse_title(first_hand)

    for hand in hands:
        info["bounties"] += _extract_bounties_from_hand(hand)

    return info


def parse_file(filepath: str | Path) -> dict | None:
    """
    Parse a single GG Poker hand history .txt file from disk.
    """
    filepath = Path(filepath)
    try:
        raw = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return parse_content(raw, filepath.name)


def parse_folder(folder: str | Path) -> list[dict]:
    """
    Parse all .txt files in *folder*.

    Multiple files for the same tournament are merged (bounties summed,
    earliest date kept).  Returns a list of tournament dicts sorted by date.
    """
    folder = Path(folder)
    tournaments: dict[str, dict] = {}

    txt_files = sorted(folder.glob("*.txt"))
    if not txt_files:
        return []

    for filepath in txt_files:
        result = parse_file(filepath)
        if result is None:
            continue

        tid = result["tournament_id"]
        if tid not in tournaments:
            tournaments[tid] = result
        else:
            # Merge: accumulate bounties, keep the earliest date
            existing = tournaments[tid]
            existing["bounties"] += result["bounties"]
            if result["date"] and (
                existing["date"] is None or result["date"] < existing["date"]
            ):
                existing["date"] = result["date"]
            # If buy-in was unknown, take first non-zero value
            if existing["buy_in"] == 0.0 and result["buy_in"] > 0.0:
                existing["buy_in"] = result["buy_in"]
                existing["rake"] = result["rake"]

    results = list(tournaments.values())
    results.sort(key=lambda r: r["date"] or datetime.min)
    return results
