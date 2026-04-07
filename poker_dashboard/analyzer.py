"""
analyzer.py — מנוע ניתוח משחק עבור GG Poker
מחלץ סטטיסטיקות מכל יד ומצבר לרמת טורניר.

מדדים שמחושבים:
    hands_played    — כמות ידיים שנותחו
    vpip_pct        — VPIP: % ידיים שהכנסנו כסף לפוט preflop (מחוץ ל-BB מבלי raise)
    pfr_pct         — PFR: % ידיים שהרמנו preflop
    af              — Aggression Factor: (bets+raises) / calls
    fold_pf_pct     — % קיפולים preflop מחוץ ל-BB
    saw_flop_pct    — % ידיים שראינו את ה-flop
    wtsd_pct        — Went To Showdown %
    wwsf_pct        — Won When Saw Flop %
    cbet_pct        — Continuation Bet % (raised preflop → bet flop)
    fold_to_3b_pct  — % קיפולים כשמ-3-bet על ה-raise שלנו
    three_bet_pct   — % 3-bet כשיש raise לפנינו
"""

import re
from dataclasses import dataclass, field


# ── Patterns ──────────────────────────────────────────────────────────────────

RE_BUTTON_SEAT  = re.compile(r"Seat #(\d+) is the button")
RE_HERO_SEAT    = re.compile(r"Seat (\d+): Hero\s+\(")
RE_TABLE_MAX    = re.compile(r"(\d+)-max")

RE_POSTS_SB     = re.compile(r"Hero: posts (the )?small blind",  re.IGNORECASE)
RE_POSTS_BB     = re.compile(r"Hero: posts (the )?big blind",    re.IGNORECASE)
RE_POSTS_ANTE   = re.compile(r"Hero: posts the ante",            re.IGNORECASE)

RE_HERO_FOLD    = re.compile(r"^Hero: folds",                    re.MULTILINE)
RE_HERO_CALL    = re.compile(r"^Hero: calls",                    re.MULTILINE)
RE_HERO_RAISE   = re.compile(r"^Hero: raises",                   re.MULTILINE)
RE_HERO_BET     = re.compile(r"^Hero: bets",                     re.MULTILINE)
RE_HERO_CHECK   = re.compile(r"^Hero: checks",                   re.MULTILINE)
RE_HERO_ALLIN   = re.compile(r"^Hero:.*and is all-in",           re.MULTILINE | re.IGNORECASE)

RE_SECTION      = re.compile(
    r"\*\*\* (HOLE CARDS|FLOP|TURN|RIVER|SHOWDOWN|SUMMARY) \*\*\*"
)
RE_WIN_POT      = re.compile(r"Hero[:\s]+(?:collected|wins?)\s+[\d,]+", re.IGNORECASE)


# ── Section splitter ──────────────────────────────────────────────────────────

def _split_sections(hand: str) -> dict[str, str]:
    """Splits hand text into named sections: PREFLOP, FLOP, TURN, RIVER, etc."""
    sections: dict[str, str] = {}
    parts = RE_SECTION.split(hand)
    # parts = [before_first, name1, text1, name2, text2, ...]
    if len(parts) > 1:
        sections["PREFLOP_SETUP"] = parts[0]
    for i in range(1, len(parts) - 1, 2):
        sections[parts[i]] = parts[i + 1]
    return sections


# ── Single hand analysis ──────────────────────────────────────────────────────

@dataclass
class HandResult:
    # Preflop
    is_bb:          bool  = False
    is_sb:          bool  = False
    is_btn:         bool  = False
    vpip:           bool  = False   # Voluntarily Put money In Pot
    pfr:            bool  = False   # Pre-Flop Raise
    fold_pf:        bool  = False   # Folded preflop (not counting BB walk)
    three_bet:      bool  = False   # 3-bet preflop
    fold_to_3b:     bool  = False   # Folded to 3-bet after our raise
    # Post-flop
    saw_flop:       bool  = False
    cbet_opp:       bool  = False   # Had c-bet opportunity (raised PF, saw flop OOP/IP)
    cbet_made:      bool  = False   # Made c-bet
    went_to_sd:     bool  = False   # Went to showdown
    won_at_sd:      bool  = False   # Won at showdown
    won_hand:       bool  = False   # Won the pot
    # Aggression counts (postflop)
    bets:           int   = 0
    raises_pf:      int   = 0       # raises preflop
    raises_post:    int   = 0       # raises postflop
    calls:          int   = 0       # calls (all streets)


def analyze_hand(hand_text: str) -> HandResult | None:
    """Analyse a single hand block. Returns None if Hero not dealt in."""

    sec = _split_sections(hand_text)
    setup = sec.get("PREFLOP_SETUP", "")
    hole  = sec.get("HOLE CARDS", "")
    flop  = sec.get("FLOP", "")
    turn  = sec.get("TURN", "")
    river = sec.get("RIVER", "")
    sd    = sec.get("SHOWDOWN", "")

    # Hero must have been dealt cards
    if "Dealt to Hero" not in hole:
        return None

    r = HandResult()

    # ── Position ────────────────────────────────────────────────────────────
    r.is_bb  = bool(RE_POSTS_BB.search(setup))
    r.is_sb  = bool(RE_POSTS_SB.search(setup))

    m_btn  = RE_BUTTON_SEAT.search(setup)
    m_hero = RE_HERO_SEAT.search(setup)
    if m_btn and m_hero:
        r.is_btn = (m_btn.group(1) == m_hero.group(1))

    # ── Preflop actions (inside HOLE CARDS section) ──────────────────────────
    hero_raised_pf = False
    hero_called_pf = False
    hero_folded_pf = False

    # Count raises before Hero's action (to detect 3-bet opportunity)
    raises_before_hero = 0
    for line in hole.splitlines():
        stripped = line.strip()
        if re.match(r"^(?!Hero)\w.*: raises", stripped):
            raises_before_hero += 1
        elif stripped.startswith("Hero:"):
            if "raises" in stripped:
                hero_raised_pf = True
                r.pfr = True
                r.raises_pf += 1
                if raises_before_hero >= 1:
                    r.three_bet = True
            elif "calls" in stripped:
                hero_called_pf = True
                r.calls += 1
            elif "folds" in stripped:
                hero_folded_pf = True
            break  # Hero acted — stop scanning preflop

    # VPIP: put money in voluntarily (raise or call, excluding BB without action)
    r.vpip = hero_raised_pf or hero_called_pf

    # Fold preflop (only counts when NOT in BB and got a walk)
    if hero_folded_pf:
        r.fold_pf = not r.is_bb  # BB fold to raise counts; pure walk doesn't

    # Fold to 3-bet: Hero raised, then someone re-raised, then Hero folded
    if hero_raised_pf:
        re_raise_after = False
        hero_acted_after = False
        for line in hole.splitlines():
            stripped = line.strip()
            if hero_acted_after:
                break
            if not re_raise_after:
                if re.match(r"^(?!Hero)\w.*: raises", stripped):
                    # Count re-raises AFTER Hero's raise
                    # Simple: once we've seen Hero raise, any raise from others = 3-bet
                    re_raise_after = True
            else:
                if stripped.startswith("Hero:") and "folds" in stripped:
                    r.fold_to_3b = True
                    hero_acted_after = True
                elif stripped.startswith("Hero:"):
                    hero_acted_after = True

    # ── Flop ────────────────────────────────────────────────────────────────
    if flop and not hero_folded_pf:
        r.saw_flop = True

        # C-bet opportunity: Hero raised preflop and there's a flop
        if hero_raised_pf:
            r.cbet_opp = True
            # C-bet made: Hero's first postflop action on flop is a bet
            for line in flop.splitlines():
                stripped = line.strip()
                if stripped.startswith("Hero:"):
                    if "bets" in stripped:
                        r.cbet_made = True
                    break   # only first action counts

        # Count Hero's postflop aggression on flop
        for line in flop.splitlines():
            stripped = line.strip()
            if stripped.startswith("Hero:"):
                if "bets" in stripped:   r.bets += 1
                elif "raises" in stripped: r.raises_post += 1
                elif "calls" in stripped:  r.calls += 1

    # ── Turn & River ─────────────────────────────────────────────────────────
    for street_text in (turn, river):
        for line in street_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("Hero:"):
                if "bets" in stripped:    r.bets += 1
                elif "raises" in stripped: r.raises_post += 1
                elif "calls" in stripped:  r.calls += 1

    # ── Showdown ──────────────────────────────────────────────────────────────
    # GG Poker: לפעמים "Hero: shows" מופיע בסקשן HOLE CARDS (all-in preflop)
    hero_showed = (
        "Hero: shows" in sd
        or "Hero showed" in sd
        or "Hero: shows" in hole   # all-in preflop run-out
    )
    r.went_to_sd = hero_showed

    # Win detection
    r.won_hand = bool(RE_WIN_POT.search(hand_text))
    if r.went_to_sd:
        r.won_at_sd = r.won_hand

    return r


# ── Tournament aggregator ─────────────────────────────────────────────────────

def analyze_tournament(content: str) -> dict:
    """
    מנתח את כל הידיים בקובץ טורניר.
    מחזיר dict עם כל הסטטיסטיקות המצוברות.
    """
    hands = [h.strip() for h in re.split(r"\n{2,}", content) if h.strip()]

    results: list[HandResult] = []
    for hand in hands:
        r = analyze_hand(hand)
        if r is not None:
            results.append(r)

    n = len(results)
    if n == 0:
        return {"hands_played": 0}

    def pct(num, den=None):
        d = den if den is not None else n
        return round(num / d * 100, 1) if d > 0 else 0.0

    vpip_count       = sum(1 for r in results if r.vpip)
    pfr_count        = sum(1 for r in results if r.pfr)
    fold_pf_count    = sum(1 for r in results if r.fold_pf)
    saw_flop_count   = sum(1 for r in results if r.saw_flop)
    wtsd_count       = sum(1 for r in results if r.went_to_sd)
    wsd_won          = sum(1 for r in results if r.won_at_sd)
    wwsf_count       = sum(1 for r in results if r.saw_flop and r.won_hand)
    cbet_opps        = sum(1 for r in results if r.cbet_opp)
    cbet_made        = sum(1 for r in results if r.cbet_made)
    three_bet_opps   = sum(1 for r in results if any(
        # opportunity = faced a raise while not being the raiser
        not r.pfr and r.vpip or not r.pfr
    ))
    three_bet_count  = sum(1 for r in results if r.three_bet)
    fold_to_3b_opps  = sum(1 for r in results if r.pfr)  # raised PF = potential 3-bet target
    fold_to_3b_count = sum(1 for r in results if r.fold_to_3b)

    total_agg = sum(r.bets + r.raises_pf + r.raises_post for r in results)
    total_calls = sum(r.calls for r in results)
    af = round(total_agg / total_calls, 2) if total_calls > 0 else float(total_agg)

    return {
        "hands_played":     n,
        "vpip_pct":         pct(vpip_count),
        "pfr_pct":          pct(pfr_count),
        "af":               af,
        "fold_pf_pct":      pct(fold_pf_count),
        "saw_flop_pct":     pct(saw_flop_count),
        "wtsd_pct":         pct(wtsd_count, saw_flop_count),
        "wwsf_pct":         pct(wwsf_count, saw_flop_count),
        "cbet_pct":         pct(cbet_made, cbet_opps),
        "fold_to_3b_pct":   pct(fold_to_3b_count, fold_to_3b_opps),
        "three_bet_pct":    pct(three_bet_count),
    }


# ── Leak detector ─────────────────────────────────────────────────────────────

# טווחים אידיאליים לטורנירים (ערכים ממוצעים של שחקנים רווחיים)
IDEAL_RANGES = {
    "vpip_pct":       (16, 28,  "VPIP",          "% ידיים שנכנסים לפוט"),
    "pfr_pct":        (12, 22,  "PFR",           "% העלאות preflop"),
    "af":             (2.0, 6.0,"AF",            "מדד אגרסיביות"),
    "cbet_pct":       (50, 80,  "C-Bet",         "% continuation bet"),
    "wtsd_pct":       (22, 32,  "WTSD",          "% הגעה ל-showdown"),
    "fold_to_3b_pct": (40, 70,  "Fold to 3-Bet", "% קיפול ל-3-bet"),
}


def detect_leaks(stats: dict) -> list[dict]:
    """
    מחזיר רשימת דליפות שנמצאו.
    כל פריט: {stat, name, desc, value, low, high, severity, message}
    """
    if stats.get("hands_played", 0) < 20:
        return []   # אין מספיק ידיים לניתוח

    leaks = []
    for key, (lo, hi, name, desc) in IDEAL_RANGES.items():
        val = stats.get(key)
        if val is None:
            continue
        if val < lo:
            severity = "high" if val < lo * 0.7 else "medium"
            if key == "vpip_pct":
                msg = f"VPIP {val}% — משחק מעט מדי ידיים (יכול להחמיץ הזדמנויות)"
            elif key == "pfr_pct":
                msg = f"PFR {val}% — לא מספיק אגרסיבי preflop"
            elif key == "af":
                msg = f"AF {val} — משחק פסיבי מדי (קורא במקום להמר/להעלות)"
            elif key == "cbet_pct":
                msg = f"C-Bet {val}% — מדלג על continuation bets — דליפת ערך"
            elif key == "wtsd_pct":
                msg = f"WTSD {val}% — מקפל יותר מדי לפני showdown"
            elif key == "fold_to_3b_pct":
                msg = f"Fold to 3-Bet {val}% — קורא יותר מדי ל-3-bet"
            else:
                msg = f"{name} {val}% — מתחת לטווח האידיאלי ({lo}-{hi})"
            leaks.append({"key": key, "name": name, "value": val, "low": lo, "high": hi, "severity": severity, "message": msg, "direction": "low"})
        elif val > hi:
            severity = "high" if val > hi * 1.4 else "medium"
            if key == "vpip_pct":
                msg = f"VPIP {val}% — משחק יותר מדי ידיים (loose preflop)"
            elif key == "pfr_pct":
                msg = f"PFR {val}% — מעלה יותר מדי preflop"
            elif key == "af":
                msg = f"AF {val} — אגרסיבי מדי (bluffing יותר מדי?)"
            elif key == "cbet_pct":
                msg = f"C-Bet {val}% — c-bet אוטומטי מדי, קל לקרוא"
            elif key == "wtsd_pct":
                msg = f"WTSD {val}% — מגיע ל-showdown עם ידיים חלשות מדי (calling station)"
            elif key == "fold_to_3b_pct":
                msg = f"Fold to 3-Bet {val}% — מקפל יותר מדי ל-3-bet (ניתן לנצל)"
            else:
                msg = f"{name} {val}% — מעל הטווח האידיאלי ({lo}-{hi})"
            leaks.append({"key": key, "name": name, "value": val, "low": lo, "high": hi, "severity": severity, "message": msg, "direction": "high"})

    return leaks
