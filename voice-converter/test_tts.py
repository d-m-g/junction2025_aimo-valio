#!/usr/bin/env python3
"""
Simple script to test text-to-speech and speech-to-text conversion using ElevenLabs API.

Usage:
    python test_tts.py "Your text here"
    python test_tts.py  # Will use default text and also convert test_voice.mp3 to text
"""

import sys
import os
from voice_converter import text_to_mp3, mp3_to_text


def main():
    # Get text from command line argument or use default
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "Hello! This is a test of the ElevenLabs text-to-speech API. How are you today?"
    
    # Output file path
    output_file = "output.mp3"
    
    print(f"Converting text to speech...")
    print(f"Text: {text}")
    print(f"Output file: {output_file}")
    
    try:
        # Convert text to MP3
        result_path = text_to_mp3(
            text=text,
            output_path=output_file,
        )
        
        print(f"\n✅ Success! Audio saved to: {result_path}")
        print(f"You can now play the file: {result_path}")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("Please set your ELEVENLABS_API_KEY environment variable:")
        print("  export ELEVENLABS_API_KEY=your_api_key_here")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    
    # Convert test_voice.mp3 to text if it exists
    test_voice_file = "test_voice.mp3"
    if os.path.exists(test_voice_file):
        print(f"\n{'='*60}")
        print(f"Converting {test_voice_file} to text...")
        print(f"{'='*60}")
        
        try:
            transcribed_text = mp3_to_text(
                audio_path=test_voice_file,
            )
            
            print(f"\n✅ Transcription successful!")
            print(f"\nTranscribed text:")
            print(f"{'-'*60}")
            print(transcribed_text)
            print(f"{'-'*60}")
            
        except FileNotFoundError:
            print(f"\n⚠️  File {test_voice_file} not found. Skipping transcription.")
        except ValueError as e:
            print(f"\n❌ Error: {e}")
        except Exception as e:
            print(f"\n❌ Error during transcription: {e}")
    else:
        print(f"\n⚠️  {test_voice_file} not found. Skipping speech-to-text conversion.")


if __name__ == "__main__":
    main()

