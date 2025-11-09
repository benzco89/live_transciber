"""
Live Transcription Engine with robust error handling
"""
import subprocess
import tempfile
import os
import threading
import time
import logging
from typing import Optional, Dict, List
from datetime import datetime
from queue import Queue

import openai
from openai import OpenAI

from config import Config


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Custom exception for transcription errors"""
    pass


class StreamError(Exception):
    """Custom exception for stream errors"""
    pass


class LiveTranscriptionEngine:
    """
    Live transcription engine with robust error handling and recovery
    """

    def __init__(self):
        self.is_running = False
        self.stream_process: Optional[subprocess.Popen] = None
        self.transcription_text = ""
        self.sentence_buffer: List[str] = []
        self.stats = {
            'chunks': 0,
            'runtime': 0,
            'cost': 0,
            'errors': 0,
            'last_error': None
        }
        self.start_time: Optional[float] = None
        self.worker_thread: Optional[threading.Thread] = None
        self.error_count = 0
        self.last_successful_chunk = None
        self.client: Optional[OpenAI] = None

    def start_transcription(self, url: str, chunk_duration: Optional[int] = None) -> str:
        """
        Start live transcription

        Args:
            url: Stream URL
            chunk_duration: Duration of each audio chunk in seconds

        Returns:
            Status message
        """
        if self.is_running:
            logger.warning("Transcription already running")
            return "⚠️ תמלול כבר רץ!"

        # Validate configuration
        config_errors = Config.validate()
        if config_errors:
            error_msg = "\n".join(config_errors)
            logger.error(f"Configuration errors: {error_msg}")
            return f"❌ שגיאות הגדרה:\n{error_msg}"

        if not url:
            return "❌ חסר לינק לשידור"

        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return f"❌ שגיאה באתחול OpenAI: {str(e)}"

        # Reset state
        self.is_running = True
        self.transcription_text = ""
        self.sentence_buffer = []
        self.stats = {
            'chunks': 0,
            'runtime': 0,
            'cost': 0,
            'errors': 0,
            'last_error': None
        }
        self.start_time = time.time()
        self.error_count = 0
        self.last_successful_chunk = time.time()

        # Start worker thread
        chunk_dur = chunk_duration or Config.CHUNK_DURATION
        self.worker_thread = threading.Thread(
            target=self._transcription_worker,
            args=(url, chunk_dur),
            daemon=True
        )
        self.worker_thread.start()

        logger.info(f"Transcription started for URL: {url}")
        return "✅ תמלול התחיל!"

    def stop_transcription(self) -> str:
        """Stop live transcription"""
        if not self.is_running:
            return "⚠️ תמלול לא פעיל"

        logger.info("Stopping transcription")
        self.is_running = False

        # Terminate stream process
        if self.stream_process:
            try:
                self.stream_process.terminate()
                self.stream_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.stream_process.kill()
            except Exception as e:
                logger.error(f"Error terminating stream process: {e}")

        return "⏹️ תמלול הופסק"

    def _add_text_to_buffer(self, text: str):
        """Add text to buffer and create paragraphs"""
        if not text or not text.strip():
            return

        self.sentence_buffer.append(text.strip())

        # Create paragraph every N sentences
        if len(self.sentence_buffer) >= Config.SENTENCES_PER_PARAGRAPH:
            paragraph = " ".join(self.sentence_buffer)
            self.transcription_text += paragraph + "\n\n"
            self.sentence_buffer = []

    def _retry_with_backoff(self, func, max_retries=None, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic

        Args:
            func: Function to execute
            max_retries: Maximum number of retries (default from config)
            *args, **kwargs: Arguments for the function

        Returns:
            Function result

        Raises:
            Exception: If all retries fail
        """
        max_retries = max_retries or Config.MAX_RETRIES
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    delay = Config.RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")

        raise last_exception

    def _start_stream(self, url: str) -> subprocess.Popen:
        """
        Start ffmpeg stream process with error handling

        Args:
            url: Stream URL

        Returns:
            subprocess.Popen object

        Raises:
            StreamError: If stream fails to start
        """
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', url,
            '-f', 'mp3',
            '-acodec', 'libmp3lame',
            '-ar', str(Config.AUDIO_SAMPLE_RATE),
            '-ac', str(Config.AUDIO_CHANNELS),
            '-b:a', Config.AUDIO_BITRATE,
            '-loglevel', 'error',  # Only show errors
            'pipe:1'
        ]

        try:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8
            )

            # Wait a bit and check if process started successfully
            time.sleep(3)

            if process.poll() is not None:
                stderr = process.stderr.read().decode('utf-8', errors='ignore')
                raise StreamError(f"Stream process died immediately: {stderr}")

            logger.info("Stream started successfully")
            return process

        except FileNotFoundError:
            raise StreamError("ffmpeg not found. Please install ffmpeg.")
        except Exception as e:
            raise StreamError(f"Failed to start stream: {str(e)}")

    def _transcribe_audio_file(self, file_path: str) -> str:
        """
        Transcribe audio file using OpenAI Whisper

        Args:
            file_path: Path to audio file

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        if not os.path.exists(file_path):
            raise TranscriptionError(f"Audio file not found: {file_path}")

        if os.path.getsize(file_path) == 0:
            raise TranscriptionError("Audio file is empty")

        try:
            with open(file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=Config.WHISPER_MODEL,
                    file=audio_file,
                    language=Config.WHISPER_LANGUAGE
                )

            return transcript.text.strip()

        except openai.APIError as e:
            raise TranscriptionError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {str(e)}")

    def _capture_audio_chunk(self, chunk_duration: int) -> Optional[str]:
        """
        Capture audio chunk from stream

        Args:
            chunk_duration: Duration in seconds

        Returns:
            Path to temporary audio file, or None if failed
        """
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_filename = temp_file.name
        temp_file.close()

        try:
            # Calculate approximate size
            # Sample rate * duration * channels * bytes per sample * compression ratio
            approx_size = Config.AUDIO_SAMPLE_RATE * chunk_duration * Config.AUDIO_CHANNELS * 2 * 0.125

            # Read audio data with timeout
            audio_data = self.stream_process.stdout.read(int(approx_size * 1.5))

            if not audio_data:
                logger.warning("No audio data received from stream")
                return None

            # Write to file
            with open(temp_filename, 'wb') as f:
                f.write(audio_data)

            # Verify file
            if os.path.getsize(temp_filename) < 1000:  # Less than 1KB
                logger.warning("Audio chunk too small, skipping")
                return None

            return temp_filename

        except Exception as e:
            logger.error(f"Failed to capture audio chunk: {e}")
            return None

    def _transcription_worker(self, url: str, chunk_duration: int):
        """
        Main worker thread for transcription

        Args:
            url: Stream URL
            chunk_duration: Duration of each chunk in seconds
        """
        logger.info(f"Worker started for {url}")

        try:
            # Start stream with retry
            self.stream_process = self._retry_with_backoff(
                self._start_stream,
                max_retries=Config.MAX_RETRIES,
                url=url
            )

        except Exception as e:
            logger.error(f"Failed to start stream after retries: {e}")
            self.stats['last_error'] = f"שגיאת חיבור לשידור: {str(e)}"
            self.is_running = False
            return

        chunk_num = 0

        while self.is_running:
            chunk_num += 1
            temp_filename = None

            try:
                # Check stream health
                if self.stream_process.poll() is not None:
                    raise StreamError("Stream process died")

                # Check if we're stuck (no successful chunk for too long)
                if self.last_successful_chunk:
                    time_since_success = time.time() - self.last_successful_chunk
                    if time_since_success > Config.STREAM_TIMEOUT:
                        raise StreamError(f"No successful chunk for {time_since_success:.0f}s")

                # Capture audio chunk
                temp_filename = self._capture_audio_chunk(chunk_duration)

                if not temp_filename:
                    continue

                # Transcribe with retry
                text = self._retry_with_backoff(
                    self._transcribe_audio_file,
                    max_retries=2,
                    file_path=temp_filename
                )

                # Add to buffer
                if text:
                    self._add_text_to_buffer(text)
                    self.last_successful_chunk = time.time()
                    self.error_count = 0  # Reset error count on success

                # Update stats
                runtime = time.time() - self.start_time
                self.stats.update({
                    'chunks': chunk_num,
                    'runtime': runtime,
                    'cost': (chunk_duration * chunk_num / 60) * 0.006
                })

            except StreamError as e:
                logger.error(f"Stream error: {e}")
                self.stats['errors'] += 1
                self.stats['last_error'] = f"שגיאת שידור: {str(e)}"
                self.error_count += 1

                # Try to restart stream if too many errors
                if self.error_count >= 3:
                    logger.info("Attempting to restart stream...")
                    try:
                        if self.stream_process:
                            self.stream_process.terminate()

                        time.sleep(5)
                        self.stream_process = self._retry_with_backoff(
                            self._start_stream,
                            max_retries=2,
                            url=url
                        )
                        self.error_count = 0
                        logger.info("Stream restarted successfully")
                    except Exception as restart_error:
                        logger.error(f"Failed to restart stream: {restart_error}")
                        self.stats['last_error'] = "כשל בהתחברות מחדש לשידור"
                        break

            except TranscriptionError as e:
                logger.error(f"Transcription error: {e}")
                self.stats['errors'] += 1
                self.stats['last_error'] = f"שגיאת תמלול: {str(e)}"
                # Continue to next chunk

            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                self.stats['errors'] += 1
                self.stats['last_error'] = f"שגיאה: {str(e)}"

            finally:
                # Cleanup temp file
                if temp_filename and os.path.exists(temp_filename):
                    try:
                        os.unlink(temp_filename)
                    except Exception as e:
                        logger.error(f"Failed to delete temp file: {e}")

        # Cleanup
        if self.stream_process:
            try:
                self.stream_process.terminate()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

        logger.info("Worker stopped")
        self.is_running = False

    def get_transcription_text(self) -> str:
        """Get current transcription text"""
        result = self.transcription_text

        # Add buffered sentences
        if self.sentence_buffer:
            result += " ".join(self.sentence_buffer)

        return result if result else ""

    def get_stats(self) -> Dict:
        """Get current statistics"""
        return self.stats.copy()

    def is_active(self) -> bool:
        """Check if transcription is active"""
        return self.is_running

    def get_health_status(self) -> str:
        """Get health status message"""
        if not self.is_running:
            return "🔴 מופסק"

        if self.stats.get('last_error'):
            return f"⚠️ פעיל עם שגיאות ({self.stats['errors']})"

        time_since_start = time.time() - self.start_time if self.start_time else 0
        if time_since_start > 10 and self.stats['chunks'] == 0:
            return "⚠️ ממתין לתמלול..."

        return "🟢 פעיל"
