# 🚀 הוראות הפעלה על המחשב שלך

## התקנה מהירה

### 1. שכפל את הקוד
```bash
git clone <repository-url>
cd live_transciber
```

### 2. התקן ffmpeg

**Windows:**
```bash
# דרך Chocolatey
choco install ffmpeg

# או הורד ידנית מ-https://ffmpeg.org/download.html
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### 3. התקן ספריות Python
```bash
pip install -r requirements.txt
```

### 4. הגדר API Key

ערוך את קובץ `.env` והחלף את:
```
OPENAI_API_KEY=sk-your-key-here
```

במפתח שלך מ-https://platform.openai.com/api-keys

### 5. בדוק שהכל עובד
```bash
python test_setup.py
```

אם הכל ירוק ✅ - אתה מוכן!

### 6. הפעל את המערכת
```bash
python app.py
```

או:
```bash
./run.sh
```

### 7. פתח בדפדפן
```
http://localhost:7860
```

---

## פתרון בעיות נפוצות

### "ffmpeg not found"
וודא שffmpeg מותקן ונמצא ב-PATH:
```bash
ffmpeg -version
```

### "OPENAI_API_KEY is missing"
וודא שערכת את קובץ `.env` עם המפתח שלך

### "Permission denied"
במערכות Unix:
```bash
chmod +x run.sh
chmod +x test_setup.py
```

---

## עלות משוערת

- **Whisper API**: $0.006 לדקה
- **שעה של תמלול**: ~$0.36
- **יום עבודה (8 שעות)**: ~$2.88

המערכת מציגה עלות בזמן אמת!
