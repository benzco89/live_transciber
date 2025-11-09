#!/bin/bash

# Live Transcription System - Launch Script
# סקריפט הפעלה למערכת תמלול חי

set -e

echo "🎙️ מערכת תמלול שידור חי"
echo "=========================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 לא מותקן"
    echo "התקן Python 3.8 או גרסה חדשה יותר"
    exit 1
fi

echo "✅ Python נמצא: $(python3 --version)"

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg לא מותקן"
    echo ""
    echo "התקן ffmpeg:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: choco install ffmpeg"
    exit 1
fi

echo "✅ ffmpeg נמצא: $(ffmpeg -version | head -n1)"

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️  קובץ .env לא נמצא"
    echo "יוצר .env מתוך .env.example..."
    cp .env.example .env
    echo ""
    echo "❌ נא לערוך את קובץ .env ולהוסיף את OPENAI_API_KEY שלך"
    echo "לאחר מכן הרץ שוב את הסקריפט"
    exit 1
fi

echo "✅ קובץ .env נמצא"

# Check if packages are installed
if ! python3 -c "import gradio" 2>/dev/null; then
    echo "📦 מתקין תלויות..."
    pip install -q -r requirements.txt
    echo "✅ התקנה הושלמה"
else
    echo "✅ כל התלויות מותקנות"
fi

echo ""
echo "🚀 מפעיל את מערכת התמלול..."
echo ""
echo "הממשק יהיה זמין בכתובת: http://localhost:7860"
echo "לעצירה: Ctrl+C"
echo ""
echo "=========================="
echo ""

# Run the app
python3 app.py
