#!/usr/bin/env bash
# ────────────────────────────────────────────────
# הרצת דשבורד הבנקרול של הפוקר
# ────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# בדוק אם pip זמין
if ! command -v pip &>/dev/null && ! command -v pip3 &>/dev/null; then
    echo "ERROR: pip not found. Please install Python 3.9+ first."
    exit 1
fi

PIP=$(command -v pip3 || command -v pip)

# התקן תלויות אם חסרות
echo "📦  בודק תלויות..."
$PIP install -q -r requirements.txt

# הרץ את האפליקציה
echo ""
echo "♠  מפעיל את דשבורד הבנקרול..."
echo "   פתח את הדפדפן בכתובת: http://localhost:8501"
echo ""
streamlit run app.py --server.headless false --browser.gatherUsageStats false
