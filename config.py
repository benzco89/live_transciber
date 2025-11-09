"""
Configuration file for Live Transcription System
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings"""

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Stream URLs
    KAN11_URL = "https://r.il.cdn-redge.media/livehls/oil/kancdn-live/live/tmp/kan11/live.livx/playlist.m3u8?renditions"

    # Audio settings
    CHUNK_DURATION = int(os.getenv("CHUNK_DURATION", "10"))  # seconds
    AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    AUDIO_CHANNELS = int(os.getenv("AUDIO_CHANNELS", "1"))
    AUDIO_BITRATE = os.getenv("AUDIO_BITRATE", "32k")

    # Error handling
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    STREAM_TIMEOUT = 30  # seconds

    # Transcription settings
    WHISPER_MODEL = "whisper-1"
    WHISPER_LANGUAGE = "he"
    SENTENCES_PER_PARAGRAPH = 3

    # UI settings
    TRANSCRIPTION_UPDATE_INTERVAL = 1  # seconds
    STATS_UPDATE_INTERVAL = 5  # seconds

    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        errors = []

        if not cls.OPENAI_API_KEY or not cls.OPENAI_API_KEY.startswith('sk-'):
            errors.append("OPENAI_API_KEY is missing or invalid")

        return errors
