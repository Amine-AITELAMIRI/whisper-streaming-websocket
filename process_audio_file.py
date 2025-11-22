#!/usr/bin/env python3
"""
Process an audio file with Whisper in real-time simulation mode.
This is useful when microphone access doesn't work (e.g., in WSL).
"""
import sys
from whisper_online import FasterWhisperASR, OnlineASRProcessor, load_audio
import numpy as np

def process_audio_file(audio_file, model_size="base", language="en", use_vad=True):
    """Process an audio file and display transcriptions"""
    
    print("=" * 60)
    print("🎵 Audio File Transcription")
    print("=" * 60)
    print(f"File: {audio_file}")
    print(f"Model: {model_size}")
    print(f"Language: {language}")
    print("=" * 60)
    
    print("\nLoading model... (this may take a minute on first run)")
    try:
        asr = FasterWhisperASR(language, model_size)
        if use_vad:
            asr.use_vad()
        print("✓ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your internet connection (model needs to download)")
        print("  2. Try a smaller model: --model tiny")
        print("  3. Check if you have enough disk space")
        return
    
    online = OnlineASRProcessor(asr)
    
    print(f"\nLoading audio file: {audio_file}")
    try:
        audio = load_audio(audio_file)
        duration = len(audio) / 16000  # Sample rate is 16kHz
        print(f"✓ Audio loaded: {duration:.2f} seconds")
    except Exception as e:
        print(f"❌ Error loading audio: {e}")
        return
    
    sample_rate = 16000
    chunk_duration = 0.3  # Process in 0.3 second chunks
    chunk_size = int(sample_rate * chunk_duration)
    
    print("\nTranscription:")
    print("-" * 60)
    
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i+chunk_size]
        online.insert_audio_chunk(chunk)
        result = online.process_iter()
        
        if result[2]:  # If there's transcribed text
            start_time, end_time, text = result
            print(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}")
    
    # Get final result
    print("\n" + "-" * 60)
    print("Finishing transcription...")
    final_result = online.finish()
    if final_result[2]:
        print(f"\nFinal transcription: {final_result[2]}")
    
    print("\n✓ Transcription complete!")
    print("=" * 60)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process an audio file with Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a WAV file with default settings
  python3 process_audio_file.py audio.wav
  
  # Use a smaller, faster model
  python3 process_audio_file.py audio.wav --model tiny
  
  # Transcribe in Spanish
  python3 process_audio_file.py audio.wav --language es
  
  # Disable VAD
  python3 process_audio_file.py audio.wav --no-vad
        """
    )
    
    parser.add_argument('audio_file', help='Path to audio file (WAV, MP3, etc.)')
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='base',
        choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
        help='Whisper model size (default: base)'
    )
    parser.add_argument(
        '--language', '-l',
        type=str,
        default='en',
        help='Language code (default: en)'
    )
    parser.add_argument(
        '--no-vad',
        action='store_true',
        help='Disable voice activity detection'
    )
    
    args = parser.parse_args()
    
    process_audio_file(
        args.audio_file,
        model_size=args.model,
        language=args.language,
        use_vad=not args.no_vad
    )

if __name__ == "__main__":
    main()




