"""
Live Transcription System - Main Application
תמלול שידור חי בזמן אמת
"""
import gradio as gr
from transcription_engine import LiveTranscriptionEngine
from config import Config

# Initialize engine
engine = LiveTranscriptionEngine()

# CSS for RTL Hebrew and modern design
CUSTOM_CSS = """
.hero-title {
    text-align: center;
    font-size: 2.8em;
    font-weight: 700;
    margin: 20px 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    text-align: center;
    font-size: 1.2em;
    color: #666;
    margin-bottom: 30px;
}

.transcription-area {
    background: white;
    padding: 30px;
    border-radius: 15px;
    border: 3px solid #667eea;
    min-height: 500px;
    max-height: 600px;
    overflow-y: auto;
    direction: rtl;
    font-family: 'Assistant', 'Arial', sans-serif;
    font-size: 1.3em;
    line-height: 2.2;
    text-align: right;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.stat-box {
    text-align: center;
    padding: 15px;
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    font-size: 1.05em;
    margin-bottom: 10px;
}

.error-box {
    background: #fee;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid #fcc;
    color: #c00;
    text-align: right;
    direction: rtl;
    font-family: 'Assistant', 'Arial', sans-serif;
}

.success-box {
    background: #efe;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid #cfc;
    color: #060;
    text-align: right;
    direction: rtl;
    font-family: 'Assistant', 'Arial', sans-serif;
}

.button-row {
    gap: 10px;
}
"""


def start_transcription_ui(use_kan11: bool, custom_url: str, chunk_duration: int) -> tuple:
    """
    Start transcription from UI

    Args:
        use_kan11: Whether to use KAN 11 stream
        custom_url: Custom stream URL
        chunk_duration: Audio chunk duration

    Returns:
        Tuple of (status_message, visibility)
    """
    # Determine URL
    if use_kan11:
        url = Config.KAN11_URL
    elif custom_url:
        url = custom_url.strip()
    else:
        return "❌ נא לבחור כאן 11 או להזין לינק", True

    # Validate chunk duration
    if chunk_duration < 5 or chunk_duration > 30:
        return "❌ משך הצ'אנק חייב להיות בין 5 ל-30 שניות", True

    # Start transcription
    result = engine.start_transcription(url, chunk_duration)

    # Show message temporarily
    return result, True


def stop_transcription_ui() -> tuple:
    """
    Stop transcription from UI

    Returns:
        Tuple of (status_message, visibility)
    """
    result = engine.stop_transcription()
    return result, True


def update_transcription_display() -> str:
    """
    Update transcription display

    Returns:
        Current transcription text
    """
    text = engine.get_transcription_text()

    if not text:
        if engine.is_active():
            return "🎙️ מקליט ומתמלל...\n\nהתמלול יופיע כאן בעוד רגע..."
        else:
            return "ממתין לתחילת תמלול...\n\nלחץ על 'התחל תמלול' כדי להתחיל."

    return text


def update_stats_display() -> tuple:
    """
    Update statistics display

    Returns:
        Tuple of (status, chunks, runtime, cost, errors, error_visibility)
    """
    stats = engine.get_stats()
    health_status = engine.get_health_status()

    chunks_text = f"📦 {stats['chunks']} צ'אנקים"
    runtime_text = f"⏱️ {stats['runtime']:.0f}s"
    cost_text = f"💰 ${stats['cost']:.4f}"
    errors_text = f"⚠️ {stats['errors']} שגיאות"

    # Error message
    error_msg = stats.get('last_error', '')
    error_visible = bool(error_msg)

    return health_status, chunks_text, runtime_text, cost_text, errors_text, error_msg, error_visible


def hide_status_message():
    """Hide status message after delay"""
    return "", False


def export_transcription() -> str:
    """
    Export transcription to file

    Returns:
        Path to exported file
    """
    import tempfile
    from datetime import datetime

    text = engine.get_transcription_text()

    if not text:
        return None

    # Create temp file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcription_{timestamp}.txt"
    filepath = f"/tmp/{filename}"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

    return filepath


# Build Gradio Interface
with gr.Blocks(css=CUSTOM_CSS, theme=gr.themes.Soft(), title="תמלול לייב - כאן 11") as app:

    # Header
    gr.HTML("<h1 class='hero-title'>🎙️ תמלול שידור חי בזמן אמת</h1>")
    gr.HTML("<p class='subtitle'>תמלול אוטומטי של שידורים חיים בעברית</p>")

    with gr.Row():
        # Main column - Transcription
        with gr.Column(scale=3):

            # Source selection
            gr.Markdown("### 📺 בחירת מקור שידור")

            with gr.Row():
                use_kan11 = gr.Checkbox(
                    label="📺 כאן 11 (שידור ישיר)",
                    value=True,
                    scale=2,
                    info="סמן לתמלול שידור כאן 11"
                )

                custom_url = gr.Textbox(
                    placeholder="או הדבק כאן URL אחר (HLS/m3u8)...",
                    show_label=False,
                    lines=1,
                    scale=5
                )

            # Settings
            with gr.Accordion("⚙️ הגדרות מתקדמות", open=False):
                chunk_duration = gr.Slider(
                    minimum=5,
                    maximum=30,
                    value=Config.CHUNK_DURATION,
                    step=1,
                    label="משך צ'אנק (שניות)",
                    info="משך כל קטע אודיו לתמלול. ערך נמוך = עדכונים מהירים יותר אבל עלות גבוהה יותר"
                )

                gr.Markdown(f"""
                **מידע על ההגדרות:**
                - **משך צ'אנק**: {Config.CHUNK_DURATION}s (ברירת מחדל)
                - **מודל**: OpenAI Whisper
                - **שפה**: עברית
                - **עלות משוערת**: $0.006 לדקה
                """)

            # Control buttons
            with gr.Row(elem_classes="button-row"):
                start_btn = gr.Button(
                    "▶️ התחל תמלול",
                    variant="primary",
                    size="lg",
                    scale=3
                )
                stop_btn = gr.Button(
                    "⏹️ עצור",
                    variant="stop",
                    size="lg",
                    scale=1
                )
                export_btn = gr.Button(
                    "💾 ייצא",
                    variant="secondary",
                    size="lg",
                    scale=1
                )

            # Status message
            status_msg = gr.Textbox(
                show_label=False,
                interactive=False,
                visible=False,
                container=False
            )

            gr.Markdown("---")

            # Transcription display
            gr.Markdown("### 📝 תמלול רציף")

            transcription_display = gr.Textbox(
                value="ממתין לתחילת תמלול...\n\nלחץ על 'התחל תמלול' כדי להתחיל.",
                lines=20,
                max_lines=25,
                show_label=False,
                interactive=False,
                elem_classes="transcription-area",
                show_copy_button=True,
                rtl=True
            )

            # Export download
            export_file = gr.File(
                label="קובץ מיוצא",
                visible=False,
                interactive=False
            )

        # Sidebar - Statistics and info
        with gr.Column(scale=1):

            gr.Markdown("### 📊 סטטוס ומידע")

            with gr.Column(elem_classes="stat-box"):
                status_indicator = gr.Markdown("🔴 מופסק")

            with gr.Column(elem_classes="stat-box"):
                chunks_display = gr.Markdown("📦 0 צ'אנקים")

            with gr.Column(elem_classes="stat-box"):
                runtime_display = gr.Markdown("⏱️ 0s")

            with gr.Column(elem_classes="stat-box"):
                cost_display = gr.Markdown("💰 $0.00")

            with gr.Column(elem_classes="stat-box"):
                errors_display = gr.Markdown("⚠️ 0 שגיאות")

            # Error display
            error_display = gr.Markdown(
                "",
                visible=False,
                elem_classes="error-box"
            )

            gr.Markdown("---")

            # Instructions
            gr.Markdown("""
            ### 💡 הוראות שימוש

            **התחלה מהירה:**
            1. ✅ וודא שכאן 11 מסומן
            2. ▶️ לחץ 'התחל תמלול'
            3. 📝 צפה בתמלול בזמן אמת!

            **שידורים אחרים:**
            - הדבק URL של HLS/m3u8
            - עובד עם רוב השידורים החיים

            **פיצ'רים:**
            - ✨ תמלול בזמן אמת
            - 🔄 התאוששות אוטומטית משגיאות
            - 💾 ייצוא לקובץ טקסט
            - 📊 מעקב אחר עלויות

            **דרישות:**
            - מפתח API של OpenAI
            - חיבור אינטרנט יציב
            - ffmpeg מותקן במערכת
            """)

            gr.Markdown("---")

            gr.Markdown("""
            ### ℹ️ אודות

            מערכת תמלול חיה מתקדמת
            המשתמשת ב-OpenAI Whisper
            לתמלול אוטומטי בעברית.

            **טכנולוגיות:**
            - OpenAI Whisper API
            - FFmpeg
            - Gradio
            - Python

            [GitHub](https://github.com) | [תיעוד](https://docs.openai.com)
            """)

    # Event handlers
    start_btn.click(
        fn=start_transcription_ui,
        inputs=[use_kan11, custom_url, chunk_duration],
        outputs=[status_msg, status_msg]  # message, visibility
    ).then(
        fn=hide_status_message,
        inputs=None,
        outputs=[status_msg, status_msg],
        every=3  # Hide after 3 seconds
    )

    stop_btn.click(
        fn=stop_transcription_ui,
        outputs=[status_msg, status_msg]
    ).then(
        fn=hide_status_message,
        inputs=None,
        outputs=[status_msg, status_msg],
        every=3
    )

    export_btn.click(
        fn=export_transcription,
        outputs=export_file
    )

    # Auto-update timers
    # Fast timer for transcription (every 1 second)
    transcription_timer = gr.Timer(Config.TRANSCRIPTION_UPDATE_INTERVAL)
    transcription_timer.tick(
        fn=update_transcription_display,
        outputs=transcription_display
    )

    # Slower timer for stats (every 5 seconds)
    stats_timer = gr.Timer(Config.STATS_UPDATE_INTERVAL)
    stats_timer.tick(
        fn=update_stats_display,
        outputs=[
            status_indicator,
            chunks_display,
            runtime_display,
            cost_display,
            errors_display,
            error_display,
            error_display  # visibility
        ]
    )


def main():
    """Main entry point"""
    import sys
    import logging

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check ffmpeg
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ שגיאה: ffmpeg לא מותקן במערכת")
        print("התקן ffmpeg באמצעות:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: choco install ffmpeg")
        sys.exit(1)

    # Validate config
    errors = Config.validate()
    if errors:
        print("❌ שגיאות הגדרה:")
        for error in errors:
            print(f"  - {error}")
        print("\nצור קובץ .env עם OPENAI_API_KEY או הגדר משתנה סביבה")
        sys.exit(1)

    # Launch app
    print("🚀 מפעיל את מערכת התמלול...")
    print(f"📺 URL של כאן 11: {Config.KAN11_URL}")

    app.queue()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        show_api=False
    )


if __name__ == "__main__":
    main()
