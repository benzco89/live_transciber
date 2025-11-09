#!/usr/bin/env python3
"""
בדיקת המערכת - Test Setup
"""
import sys
import subprocess

def check_requirement(name, check_func):
    """בדיקת דרישה"""
    try:
        result = check_func()
        print(f"✅ {name}: {result}")
        return True
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

def check_python():
    """בדיקת Python"""
    version = sys.version.split()[0]
    major, minor = map(int, version.split('.')[:2])
    if major >= 3 and minor >= 8:
        return f"v{version}"
    raise Exception(f"Python {major}.{minor} נמוך מדי, נדרש 3.8+")

def check_ffmpeg():
    """בדיקת ffmpeg"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return version_line.split()[2]
        raise Exception("ffmpeg לא מותקן")
    except FileNotFoundError:
        raise Exception("ffmpeg לא נמצא במערכת")

def check_openai():
    """בדיקת ספריית OpenAI"""
    import openai
    return f"v{openai.__version__}"

def check_gradio():
    """בדיקת Gradio"""
    import gradio as gr
    return f"v{gr.__version__}"

def check_env_file():
    """בדיקת קובץ .env"""
    import os
    from dotenv import load_dotenv
    
    if not os.path.exists('.env'):
        raise Exception("קובץ .env לא קיים")
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY', '')
    
    if not api_key or api_key == 'sk-your-key-here':
        raise Exception("OPENAI_API_KEY לא הוגדר בקובץ .env")
    
    if not api_key.startswith('sk-'):
        raise Exception("OPENAI_API_KEY נראה לא תקין")
    
    return "מוגדר ותקין"

def main():
    print("🔍 בודק את המערכת...\n")
    
    checks = [
        ("Python", check_python),
        ("OpenAI Library", check_openai),
        ("Gradio", check_gradio),
        ("FFmpeg", check_ffmpeg),
        ("API Key", check_env_file),
    ]
    
    results = []
    for name, check_func in checks:
        results.append(check_requirement(name, check_func))
    
    print("\n" + "="*50)
    
    if all(results):
        print("✅ כל הבדיקות עברו בהצלחה!")
        print("\nהמערכת מוכנה להרצה. הפעל עם:")
        print("  python app.py")
        return 0
    else:
        print("❌ יש בעיות שצריך לתקן")
        print("\nראה את ההוראות למעלה לתיקון הבעיות")
        return 1

if __name__ == "__main__":
    sys.exit(main())
