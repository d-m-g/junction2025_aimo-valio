"""
Voice converter module using ElevenLabs API.

This module provides functions for:
1. Converting text to MP3 audio files (Text-to-Speech)
2. Converting MP3 audio files to text (Speech-to-Text)

Requires ELEVENLABS_API_KEY environment variable to be set.
"""

import os
from pathlib import Path
from typing import Optional

try:
    from elevenlabs.client import ElevenLabs
except ImportError:
    raise ImportError(
        "elevenlabs package is required. Install it with: pip install elevenlabs"
    )


def text_to_mp3(
    text: str,
    output_path: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice: Rachel
    model_id: str = "eleven_multilingual_v2",
    api_key: Optional[str] = None,
) -> str:
    """
    Convert text to MP3 audio file using ElevenLabs Text-to-Speech API.

    Args:
        text: The text to convert to speech
        output_path: Path where the MP3 file will be saved
        voice_id: ElevenLabs voice ID (default: Rachel)
        model_id: Model to use (default: eleven_multilingual_v2)
        api_key: ElevenLabs API key. If not provided, uses ELEVENLABS_API_KEY env var

    Returns:
        Path to the generated MP3 file

    Raises:
        ValueError: If API key is not provided and not found in environment
        Exception: If audio generation fails
    """
    # Get API key
    if api_key is None:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY environment variable not set. "
                "Please set it or pass api_key parameter."
            )

    # Initialize client
    client = ElevenLabs(api_key=api_key)

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Generate audio using text-to-speech API
        # The convert method returns an iterator of bytes
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format="mp3_44100_128",  # MP3 format with good quality
        )

        # Write audio data to file
        with open(output_file, "wb") as f:
            for chunk in audio_generator:
                if isinstance(chunk, bytes):
                    f.write(chunk)
                else:
                    # Try to convert to bytes if needed
                    f.write(bytes(chunk))

        return str(output_file)

    except Exception as e:
        raise Exception(f"Failed to generate audio: {str(e)}")


def mp3_to_text(
    audio_path: str,
    api_key: Optional[str] = None,
    model_id: str = "scribe_v1",
) -> str:
    """
    Convert MP3 audio file to text using ElevenLabs Speech-to-Text API (Scribe).

    Args:
        audio_path: Path to the MP3 audio file
        api_key: ElevenLabs API key. If not provided, uses ELEVENLABS_API_KEY env var
        model_id: Model to use (default: scribe_v1, options: scribe_v1, scribe_v2_realtime)

    Returns:
        Transcribed text from the audio file

    Raises:
        ValueError: If API key is not provided and not found in environment
        FileNotFoundError: If audio file doesn't exist
        Exception: If transcription fails
    """
    # Get API key
    if api_key is None:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY environment variable not set. "
                "Please set it or pass api_key parameter."
            )

    # Check if file exists
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Initialize client
    client = ElevenLabs(api_key=api_key)

    try:
        # Open audio file and transcribe using the speech-to-text API
        with open(audio_path, "rb") as audio_file:
            # The API expects a file-like object
            transcription = client.speech_to_text.convert(
                file=audio_file,
                model_id=model_id,
            )

        # Extract text from transcription response
        # The response is a SpeechToTextConvertResponse object
        if hasattr(transcription, "text"):
            return transcription.text
        elif hasattr(transcription, "transcription"):
            return transcription.transcription
        elif isinstance(transcription, dict):
            # Try common response fields
            if "text" in transcription:
                return transcription["text"]
            elif "transcription" in transcription:
                return transcription["transcription"]
        elif isinstance(transcription, str):
            return transcription
        else:
            # Fallback: convert to string
            return str(transcription)

    except Exception as e:
        raise Exception(f"Failed to transcribe audio: {str(e)}")

