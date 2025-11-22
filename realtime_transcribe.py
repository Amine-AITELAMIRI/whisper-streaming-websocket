#!/usr/bin/env python3
"""
Real-time audio transcription using whisper_online module.
Captures audio from microphone and transcribes it in real-time.
"""
import numpy as np
import sys
import signal
import argparse
import threading
import queue
import time
import json
from typing import Callable, Optional, TextIO
from whisper_online import FasterWhisperASR, OnlineASRProcessor, VACOnlineASRProcessor

# Try to import audio library (prefer sounddevice, fallback to pyaudio)
AUDIO_LIB = None
sd = None
pyaudio = None

# Try sounddevice first
try:
    import sounddevice as sd
    # Test if it actually works by trying to query devices
    try:
        sd.query_devices()
        AUDIO_LIB = 'sounddevice'
    except Exception:
        # sounddevice is installed but can't access devices (e.g., WSL)
        print("⚠️  sounddevice installed but cannot access audio devices.", file=sys.stderr)
        print("   This is common in WSL. Trying pyaudio...", file=sys.stderr)
        sd = None
        raise ImportError("sounddevice cannot access devices")
except (ImportError, OSError) as e:
    # Try pyaudio as fallback
    try:
        import pyaudio
        AUDIO_LIB = 'pyaudio'
    except ImportError:
        if 'PortAudio' in str(e) or 'portaudio' in str(e).lower():
            print("Error: PortAudio library not found!")
            print("\nPlease install PortAudio:")
            print("  Ubuntu/Debian: sudo apt-get install portaudio19-dev")
            print("  Fedora: sudo dnf install portaudio-devel")
            print("  Arch: sudo pacman -S portaudio")
            print("  macOS: brew install portaudio")
            print("\nThen install one of:")
            print("  pip install sounddevice")
            print("  pip install pyaudio")
        else:
            print("Error: No audio library found!")
            print("\nPlease install one of the following:")
            print("  1. sounddevice: pip install sounddevice")
            print("     (On Linux, you may also need: sudo apt-get install portaudio19-dev)")
            print("  2. pyaudio: pip install pyaudio")
            print("     (On Linux, you may also need: sudo apt-get install portaudio19-dev python3-pyaudio)")
        sys.exit(1)

# Global flag for graceful shutdown
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\nStopping transcription...")
    running = False

def list_audio_devices():
    """List available audio input devices"""
    print("\nAvailable audio input devices:")
    try:
        if AUDIO_LIB == 'sounddevice':
            try:
                devices = sd.query_devices(kind='input')
                print(devices)
            except Exception as e:
                print(f"Error with sounddevice: {e}")
                print("\nTrying pyaudio instead...")
                # Try to import pyaudio if not already imported
                try:
                    import pyaudio
                    list_audio_devices_pyaudio()
                except ImportError:
                    print("\n⚠️  pyaudio is not installed.")
                    print("\nTo fix audio device access in WSL, try one of these options:")
                    print("\nOption 1: Install pyaudio")
                    print("  pip install pyaudio")
                    print("\nOption 2: Set up PulseAudio for WSL")
                    print("  sudo apt-get install pulseaudio")
                    print("  # Then configure PulseAudio to use Windows audio")
                    print("\nOption 3: Use Windows PowerShell/CMD instead of WSL")
                    print("  # Run the script from Windows directly")
                    print("\nOption 4: Use WSL audio forwarding")
                    print("  # Install and configure WSL audio support")
        elif AUDIO_LIB == 'pyaudio':
            list_audio_devices_pyaudio()
    except Exception as e:
        print(f"Error listing devices: {e}")
        print("\n⚠️  Could not access audio devices.")
        print("If you're using WSL, audio device access may be limited.")
        print("\nTry installing pyaudio: pip install pyaudio")
    print()

def list_audio_devices_pyaudio():
    """List devices using pyaudio"""
    try:
        p = pyaudio.PyAudio()
        print("\nIndex | Name")
        print("-" * 60)
        found_devices = False
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    print(f"{i:5d} | {info['name']}")
                    found_devices = True
            except Exception as e:
                continue
        if not found_devices:
            print("No input devices found.")
        p.terminate()
    except Exception as e:
        print(f"Error with pyaudio: {e}")

def realtime_transcribe_sounddevice(model_size="large-v3", language="en", device=None, 
                                    sample_rate=16000, chunk_duration=0.5, use_vad=True, use_vac=False,
                                    transcript_callback=None, output_file=None, json_output=False,
                                    setup_signal_handler=True):
    """Real-time transcription using sounddevice with async processing to reduce latency
    
    Args:
        transcript_callback: Optional callback function(start_time, end_time, text) called for each transcript
        output_file: Optional file path or file handle to write transcripts
        json_output: If True, output transcripts as JSON lines (one JSON object per line)
        setup_signal_handler: If True, set up SIGINT signal handler (default: True, set False when running in thread)
    """
    global running
    
    print("=" * 60)
    print("🎤 Real-time Audio Transcription (using sounddevice)")
    print("=" * 60)
    print(f"Model: {model_size}")
    print(f"Language: {language}")
    print(f"Sample Rate: {sample_rate} Hz")
    print(f"Chunk Duration: {chunk_duration}s")
    print(f"VAD: {'Enabled' if use_vad else 'Disabled'}")
    print(f"VAC: {'Enabled' if use_vac else 'Disabled'}")
    print("=" * 60)
    print("\nLoading Whisper model... (this may take a minute)")
    
    # Initialize ASR
    try:
        asr = FasterWhisperASR(language, model_size)
        if use_vad:
            asr.use_vad()
        print("✓ Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    # Create online processor - use VAC if requested for better latency
    if use_vac:
        try:
            online = VACOnlineASRProcessor(chunk_duration, asr)
            print("✓ Using VAC (Voice Activity Controller) for better latency")
        except Exception as e:
            print(f"⚠️  VAC not available: {e}, using standard processor")
            online = OnlineASRProcessor(asr, buffer_trimming=("segment", 10))  # Shorter buffer
    else:
        # Use shorter buffer trimming to reduce latency (5 seconds instead of 10)
        online = OnlineASRProcessor(asr, buffer_trimming=("segment", 5))
    
    # Calculate chunk size in samples - use larger chunks to reduce processing frequency
    # This reduces the number of processing calls and helps prevent latency buildup
    chunk_size = int(sample_rate * chunk_duration)
    
    # Queue for async audio processing
    audio_queue = queue.Queue(maxsize=5)  # Reduced from 10 to 5 to prevent latency buildup
    
    # Open output file if specified
    output_fh = None
    if output_file:
        if isinstance(output_file, str):
            output_fh = open(output_file, 'w', encoding='utf-8')
        else:
            output_fh = output_file  # Assume it's already a file handle
    
    print("\n🎙️  Listening... (Press Ctrl+C to stop)\n")
    print("-" * 60)
    
    def audio_callback(indata, frames, time_info, status):
        """Callback function for audio input - non-blocking"""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        
        if not running:
            raise sd.CallbackStop
        
        # Convert to float32 if needed (sounddevice already provides float32)
        audio_chunk = indata[:, 0].astype(np.float32).copy()  # Take first channel (mono)
        
        # Add to queue (non-blocking, drop if queue is full to prevent latency)
        try:
            audio_queue.put_nowait(audio_chunk)
        except queue.Full:
            # Queue is full, skip this chunk to prevent latency buildup
            pass
    
    def process_audio_worker():
        """Worker thread that processes audio from queue"""
        while running or not audio_queue.empty():
            try:
                # Get audio chunk with timeout
                audio_chunk = audio_queue.get(timeout=0.1)
                
                # Process audio chunk
                try:
                    online.insert_audio_chunk(audio_chunk)
                    result = online.process_iter()
                    
                    if result[2]:  # If there's transcribed text
                        start_time, end_time, text = result
                        
                        # Call custom callback if provided
                        if transcript_callback:
                            try:
                                transcript_callback(start_time, end_time, text)
                            except Exception as e:
                                print(f"Error in transcript callback: {e}", file=sys.stderr)
                        
                        # Write to file if specified
                        if output_fh:
                            if json_output:
                                json_line = json.dumps({
                                    'start_time': start_time,
                                    'end_time': end_time,
                                    'text': text,
                                    'timestamp': time.time()
                                }, ensure_ascii=False)
                                output_fh.write(json_line + '\n')
                                output_fh.flush()
                            else:
                                output_fh.write(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}\n")
                                output_fh.flush()
                        
                        # Print to stdout if no file output or always print
                        if not output_file or not json_output:
                            print(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}", flush=True)
                            
                except Exception as e:
                    print(f"Error processing audio: {e}", file=sys.stderr)
                
                audio_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                if running:
                    print(f"Error in audio worker: {e}", file=sys.stderr)
    
    # Set up signal handler for graceful shutdown (only in main thread)
    if setup_signal_handler:
        signal.signal(signal.SIGINT, signal_handler)
    
    # Start processing thread
    processing_thread = threading.Thread(target=process_audio_worker, daemon=True)
    processing_thread.start()
    
    try:
        # Start audio stream
        with sd.InputStream(
            device=device,
            channels=1,  # Mono
            samplerate=sample_rate,
            blocksize=chunk_size,
            dtype=np.float32,
            callback=audio_callback
        ):
            # Keep running until interrupted
            while running:
                sd.sleep(100)  # Sleep in 100ms chunks
                
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Wait for queue to empty
        audio_queue.join()
        print("\n" + "-" * 60)
        print("Finishing transcription...")
        
        # Get final result
        try:
            final_result = online.finish()
            if final_result[2]:
                final_text = final_result[2]
                if transcript_callback:
                    try:
                        transcript_callback(final_result[0] or 0, final_result[1] or 0, final_text)
                    except Exception as e:
                        print(f"Error in final transcript callback: {e}", file=sys.stderr)
                
                if output_fh:
                    if json_output:
                        json_line = json.dumps({
                            'start_time': final_result[0] or 0,
                            'end_time': final_result[1] or 0,
                            'text': final_text,
                            'timestamp': time.time(),
                            'final': True
                        }, ensure_ascii=False)
                        output_fh.write(json_line + '\n')
                        output_fh.flush()
                    else:
                        output_fh.write(f"\nFinal transcription: {final_text}\n")
                        output_fh.flush()
                
                if not output_file or not json_output:
                    print(f"\nFinal transcription: {final_text}")
        except Exception as e:
            print(f"Error finishing: {e}")
        
        # Close output file if we opened it
        if output_fh and output_file and isinstance(output_file, str):
            output_fh.close()
        
        print("\n✓ Transcription stopped.")
        print("=" * 60)

def realtime_transcribe_pyaudio(model_size="large-v3", language="en", device=None,
                                sample_rate=16000, chunk_duration=0.5, use_vad=True, use_vac=False,
                                transcript_callback=None, output_file=None, json_output=False,
                                setup_signal_handler=True):
    """Real-time transcription using pyaudio
    
    Args:
        transcript_callback: Optional callback function(start_time, end_time, text) called for each transcript
        output_file: Optional file path or file handle to write transcripts
        json_output: If True, output transcripts as JSON lines (one JSON object per line)
        setup_signal_handler: If True, set up SIGINT signal handler (default: True, set False when running in thread)
    """
    global running
    
    print("=" * 60)
    print("🎤 Real-time Audio Transcription (using pyaudio)")
    print("=" * 60)
    print(f"Model: {model_size}")
    print(f"Language: {language}")
    print(f"Sample Rate: {sample_rate} Hz")
    print(f"Chunk Duration: {chunk_duration}s")
    print(f"VAD: {'Enabled' if use_vad else 'Disabled'}")
    print(f"VAC: {'Enabled' if use_vac else 'Disabled'}")
    print("=" * 60)
    print("\nLoading Whisper model... (this may take a minute)")
    
    # Initialize ASR
    try:
        asr = FasterWhisperASR(language, model_size)
        if use_vad:
            asr.use_vad()
        print("✓ Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    # Create online processor - use VAC if requested for better latency
    if use_vac:
        try:
            online = VACOnlineASRProcessor(chunk_duration, asr)
            print("✓ Using VAC (Voice Activity Controller) for better latency")
        except Exception as e:
            print(f"⚠️  VAC not available: {e}, using standard processor")
            online = OnlineASRProcessor(asr, buffer_trimming=("segment", 10))  # Shorter buffer
    else:
        # Use shorter buffer trimming to reduce latency (5 seconds instead of 10)
        online = OnlineASRProcessor(asr, buffer_trimming=("segment", 5))
    
    # Calculate chunk size in samples
    chunk_size = int(sample_rate * chunk_duration)
    
    # Queue for async audio processing
    audio_queue = queue.Queue(maxsize=5)  # Reduced from 10 to 5 to prevent latency buildup
    
    # Open output file if specified
    output_fh = None
    if output_file:
        if isinstance(output_file, str):
            output_fh = open(output_file, 'w', encoding='utf-8')
        else:
            output_fh = output_file  # Assume it's already a file handle
    
    print("\n🎙️  Listening... (Press Ctrl+C to stop)\n")
    print("-" * 60)
    
    # Set up signal handler for graceful shutdown (only in main thread)
    if setup_signal_handler:
        signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    def audio_callback(in_data, frame_count, time_info, status):
        """Callback function for audio input - non-blocking"""
        if not running:
            return (None, pyaudio.paComplete)
        
        # Convert bytes to float32 numpy array
        # PyAudio provides int16, we need to convert to float32
        audio_int16 = np.frombuffer(in_data, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        
        # Add to queue (non-blocking, drop if queue is full to prevent latency)
        try:
            audio_queue.put_nowait(audio_float32)
        except queue.Full:
            # Queue is full, skip this chunk to prevent latency buildup
            pass
        
        return (None, pyaudio.paContinue)
    
    def process_audio_worker():
        """Worker thread that processes audio from queue"""
        while running or not audio_queue.empty():
            try:
                # Get audio chunk with timeout
                audio_chunk = audio_queue.get(timeout=0.1)
                
                # Process audio chunk
                try:
                    online.insert_audio_chunk(audio_chunk)
                    result = online.process_iter()
                    
                    if result[2]:  # If there's transcribed text
                        start_time, end_time, text = result
                        
                        # Call custom callback if provided
                        if transcript_callback:
                            try:
                                transcript_callback(start_time, end_time, text)
                            except Exception as e:
                                print(f"Error in transcript callback: {e}", file=sys.stderr)
                        
                        # Write to file if specified
                        if output_fh:
                            if json_output:
                                json_line = json.dumps({
                                    'start_time': start_time,
                                    'end_time': end_time,
                                    'text': text,
                                    'timestamp': time.time()
                                }, ensure_ascii=False)
                                output_fh.write(json_line + '\n')
                                output_fh.flush()
                            else:
                                output_fh.write(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}\n")
                                output_fh.flush()
                        
                        # Print to stdout if no file output or always print
                        if not output_file or not json_output:
                            print(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}", flush=True)
                            
                except Exception as e:
                    print(f"Error processing audio: {e}", file=sys.stderr)
                
                audio_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                if running:
                    print(f"Error in audio worker: {e}", file=sys.stderr)
    
    # Start processing thread
    processing_thread = threading.Thread(target=process_audio_worker, daemon=True)
    processing_thread.start()
    
    try:
        # Open audio stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,  # Mono
            rate=sample_rate,
            input=True,
            input_device_index=device,
            frames_per_buffer=chunk_size,
            stream_callback=audio_callback
        )
        
        stream.start_stream()
        
        # Keep running until interrupted
        while running and stream.is_active():
            import time
            time.sleep(0.1)
        
        stream.stop_stream()
        stream.close()
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        p.terminate()
        # Wait for queue to empty
        audio_queue.join()
        print("\n" + "-" * 60)
        print("Finishing transcription...")
        
        # Get final result
        try:
            final_result = online.finish()
            if final_result[2]:
                final_text = final_result[2]
                if transcript_callback:
                    try:
                        transcript_callback(final_result[0] or 0, final_result[1] or 0, final_text)
                    except Exception as e:
                        print(f"Error in final transcript callback: {e}", file=sys.stderr)
                
                if output_fh:
                    if json_output:
                        json_line = json.dumps({
                            'start_time': final_result[0] or 0,
                            'end_time': final_result[1] or 0,
                            'text': final_text,
                            'timestamp': time.time(),
                            'final': True
                        }, ensure_ascii=False)
                        output_fh.write(json_line + '\n')
                        output_fh.flush()
                    else:
                        output_fh.write(f"\nFinal transcription: {final_text}\n")
                        output_fh.flush()
                
                if not output_file or not json_output:
                    print(f"\nFinal transcription: {final_text}")
        except Exception as e:
            print(f"Error finishing: {e}")
        
        # Close output file if we opened it
        if output_fh and output_file and isinstance(output_file, str):
            output_fh.close()
        
        print("\n✓ Transcription stopped.")
        print("=" * 60)

def realtime_transcribe(model_size="large-v3", language="en", device=None, sample_rate=16000, 
                       chunk_duration=0.5, use_vad=True, use_vac=False,
                       transcript_callback=None, output_file=None, json_output=False,
                       setup_signal_handler=True):
    """Main function that routes to the appropriate audio library
    
    Args:
        transcript_callback: Optional callback function(start_time, end_time, text) called for each transcript
        output_file: Optional file path or file handle to write transcripts
        json_output: If True, output transcripts as JSON lines (one JSON object per line)
        setup_signal_handler: If True, set up SIGINT signal handler (default: True, set False when running in thread)
    """
    if AUDIO_LIB == 'sounddevice':
        realtime_transcribe_sounddevice(model_size, language, device, sample_rate, 
                                       chunk_duration, use_vad, use_vac,
                                       transcript_callback, output_file, json_output,
                                       setup_signal_handler)
    elif AUDIO_LIB == 'pyaudio':
        realtime_transcribe_pyaudio(model_size, language, device, sample_rate, 
                                   chunk_duration, use_vad, use_vac,
                                   transcript_callback, output_file, json_output,
                                   setup_signal_handler)

def main():
    parser = argparse.ArgumentParser(
        description="Real-time audio transcription using Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default settings (English, large-v3 model)
  python realtime_transcribe.py
  
  # Use a smaller, faster model
  python realtime_transcribe.py --model base
  
  # Transcribe in Spanish
  python realtime_transcribe.py --language es
  
  # List available audio devices
  python realtime_transcribe.py --list-devices
  
  # Use specific audio device
  python realtime_transcribe.py --device 1
        """
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="large-v3",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help="Whisper model size (default: large-v3)"
    )
    
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="en",
        help="Language code (default: en)"
    )
    
    parser.add_argument(
        "--device", "-d",
        type=int,
        default=None,
        help="Audio device index (use --list-devices to see available devices)"
    )
    
    parser.add_argument(
        "--chunk-duration", "-c",
        type=float,
        default=0.5,
        help="Audio chunk duration in seconds (default: 0.5, larger = less processing = lower latency)"
    )
    
    parser.add_argument(
        "--no-vad",
        action="store_true",
        help="Disable voice activity detection"
    )
    
    parser.add_argument(
        "--vac",
        action="store_true",
        help="Use VAC (Voice Activity Controller) for better latency - only processes when speech is detected"
    )
    
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path to save transcripts (default: stdout)"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output transcripts as JSON lines (one JSON object per line)"
    )
    
    args = parser.parse_args()
    
    if args.list_devices:
        list_audio_devices()
        return
    
    realtime_transcribe(
        model_size=args.model,
        language=args.language,
        device=args.device,
        chunk_duration=args.chunk_duration,
        use_vad=not args.no_vad,
        use_vac=args.vac,
        output_file=args.output,
        json_output=args.json
    )

if __name__ == "__main__":
    main()
