"""
Example usage of whisper_online as a module
"""
import numpy as np
from whisper_online import FasterWhisperASR, OnlineASRProcessor, load_audio, load_audio_chunk

# Initialize faster-whisper ASR
asr = FasterWhisperASR("en", "large-v3")
asr.use_vad()  # Enable voice activity detection

# Create online processor
online = OnlineASRProcessor(asr)

# Example 1: Process audio from a file in chunks
def process_audio_file(audio_file_path, chunk_duration=0.3):
    """
    Process an audio file by loading it in chunks
    chunk_duration: duration of each chunk in seconds (default 0.3s)
    """
    # Load entire audio file
    audio = load_audio(audio_file_path)
    sample_rate = 16000
    chunk_size = int(sample_rate * chunk_duration)
    
    for i in range(0, len(audio), chunk_size):
        audio_chunk = audio[i:i+chunk_size]
        online.insert_audio_chunk(audio_chunk)
        result = online.process_iter()
        
        if result[2]:  # If there's transcribed text
            start_time, end_time, text = result
            print(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}")
    
    # Get final result when done
    final_result = online.finish()
    if final_result[2]:
        print(f"Final: {final_result[2]}")


# Example 2: Process audio chunks from a real-time source
def process_realtime_audio():
    """
    Process audio chunks from a real-time source (microphone, stream, etc.)
    Replace get_audio_chunk() with your actual audio source
    """
    audio_available = True  # Your condition for audio availability
    
    while audio_available:
        # Your audio source should provide 16kHz mono float32 numpy array
        audio_chunk = get_audio_chunk()  # Replace with your audio source
        
        # Ensure audio is the correct format
        if not isinstance(audio_chunk, np.ndarray):
            audio_chunk = np.array(audio_chunk, dtype=np.float32)
        
        online.insert_audio_chunk(audio_chunk)
        result = online.process_iter()
        
        if result[2]:  # If there's transcribed text
            start_time, end_time, text = result
            print(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}")
    
    # Get final result when done
    final_result = online.finish()
    if final_result[2]:
        print(f"Final: {final_result[2]}")


# Example 3: Simple usage pattern (as shown in your original request)
def simple_usage():
    """
    Simple usage pattern matching your original example
    """
    audio_available = True  # Your condition for audio availability
    
    while audio_available:
        audio_chunk = get_audio_chunk()  # Your audio source (16kHz, float32)
        online.insert_audio_chunk(audio_chunk)
        result = online.process_iter()
        
        if result[2]:  # If there's transcribed text
            start_time, end_time, text = result
            print(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}")
    
    # Get final result when done
    final_result = online.finish()
    if final_result[2]:
        print(f"Final: {final_result[2]}")


if __name__ == "__main__":
    # Uncomment one of the examples below:
    
    # Example: Process an audio file
    # process_audio_file("path/to/your/audio.wav")
    
    # Example: Process real-time audio
    # process_realtime_audio()
    
    pass

