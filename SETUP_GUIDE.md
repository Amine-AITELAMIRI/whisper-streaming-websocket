# Real-Time Transcription Setup Guide

This guide will walk you through setting up and using the real-time audio transcription script.

## Step 1: Check Your Environment

You're currently in WSL (Windows Subsystem for Linux). For audio transcription, you have two main options:

### Option A: Use Windows Directly (Easiest)
### Option B: Set Up WSL Audio (More Complex)

---

## Step 2: Install Required Dependencies

### 2.1 Install pyaudio (for audio capture)

```bash
pip install pyaudio
```

If you get an error about PortAudio, install it first:
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev
pip install pyaudio
```

### 2.2 Verify Installation

```bash
python3 -c "import pyaudio; print('✓ pyaudio installed successfully')"
```

---

## Step 3: Test Audio Device Access

### 3.1 List Available Audio Devices

```bash
python3 realtime_transcribe.py --list-devices
```

**Expected Output (if working):**
```
Available audio input devices:

Index | Name
------------------------------------------------------------
    0 | Microsoft Sound Mapper - Input
    1 | Microphone (Realtek Audio)
    2 | ...
```

**If you see errors:**
- WSL doesn't have direct audio access
- You'll need to either:
  - Run from Windows PowerShell/CMD instead
  - Set up PulseAudio in WSL
  - Process audio files instead of real-time

---

## Step 4: Download the Whisper Model

The first time you run the script, it will download the model. This can take a few minutes.

### 4.1 Test Model Download

```bash
python3 realtime_transcribe.py --model base --list-devices
```

This will:
1. Try to download the "base" model (if not already cached)
2. List audio devices

**If you get a model download error:**
- Check your internet connection
- The model will be cached in `~/.cache/huggingface/` or similar
- You can manually download models if needed

---

## Step 5: Run Real-Time Transcription

### 5.1 Basic Usage

```bash
python3 realtime_transcribe.py --model base
```

**What happens:**
1. Script loads the Whisper model (first time: downloads it)
2. Opens your microphone
3. Starts listening and transcribing
4. Displays transcriptions in real-time
5. Press `Ctrl+C` to stop

### 5.2 Example Output

```
============================================================
🎤 Real-time Audio Transcription
============================================================
Model: base
Language: en
Sample Rate: 16000 Hz
Chunk Duration: 0.3s
VAD: Enabled
============================================================

Loading Whisper model... (this may take a minute)
✓ Model loaded successfully!

🎙️  Listening... (Press Ctrl+C to stop)

------------------------------------------------------------
[0.00s - 2.50s]: Hello, this is a test
[2.50s - 5.00s]: How are you doing today?
```

---

## Step 6: Alternative - Process Audio Files

If real-time microphone input doesn't work in WSL, you can process audio files instead.

### 6.1 Create a File Processing Script

Create `process_audio_file.py`:

```python
#!/usr/bin/env python3
"""Process an audio file with Whisper"""
import sys
from whisper_online import FasterWhisperASR, OnlineASRProcessor, load_audio
import numpy as np

if len(sys.argv) < 2:
    print("Usage: python3 process_audio_file.py <audio_file.wav>")
    sys.exit(1)

audio_file = sys.argv[1]

print("Loading model...")
asr = FasterWhisperASR("en", "base")
asr.use_vad()
online = OnlineASRProcessor(asr)

print(f"Processing {audio_file}...")
audio = load_audio(audio_file)
sample_rate = 16000
chunk_duration = 0.3
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
final_result = online.finish()
if final_result[2]:
    print(f"\nFinal: {final_result[2]}")
```

### 6.2 Use It

```bash
python3 process_audio_file.py demo.wav
```

---

## Step 7: Troubleshooting

### Problem: "PortAudio library not found"
**Solution:**
```bash
sudo apt-get install portaudio19-dev
pip install --force-reinstall pyaudio
```

### Problem: "No audio devices found" in WSL
**Solutions:**
1. **Run from Windows** (easiest):
   ```powershell
   # In Windows PowerShell
   cd D:\CODING\whisper-streaming-websocket
   python realtime_transcribe.py --model base
   ```

2. **Set up PulseAudio in WSL**:
   ```bash
   sudo apt-get install pulseaudio
   # Then configure PulseAudio (requires additional setup)
   ```

3. **Process audio files instead** (see Step 6)

### Problem: "Error loading model" / "Cannot find files on Hub"
**Solutions:**
1. Check internet connection
2. Try a different model size: `--model tiny` (smaller, downloads faster)
3. Manually download model (advanced)

### Problem: Model download is slow
**Solution:**
- Use smaller models: `tiny`, `base`, or `small`
- Models are cached after first download
- Large models (large-v3) can be 1-3 GB

---

## Step 8: Common Usage Examples

### Use a smaller, faster model:
```bash
python3 realtime_transcribe.py --model tiny
```

### Transcribe in Spanish:
```bash
python3 realtime_transcribe.py --model base --language es
```

### Use a specific microphone:
```bash
# First list devices
python3 realtime_transcribe.py --list-devices

# Then use device index
python3 realtime_transcribe.py --model base --device 1
```

### Disable VAD (Voice Activity Detection):
```bash
python3 realtime_transcribe.py --model base --no-vad
```

---

## Quick Start Checklist

- [ ] Install pyaudio: `pip install pyaudio`
- [ ] Test audio devices: `python3 realtime_transcribe.py --list-devices`
- [ ] If devices found: Run transcription: `python3 realtime_transcribe.py --model base`
- [ ] If no devices: Try running from Windows PowerShell instead
- [ ] If still issues: Use file processing script (Step 6)

---

## Next Steps

Once you have it working:
1. Experiment with different model sizes
2. Try different languages
3. Adjust chunk duration for your needs
4. Process audio files for batch transcription

Good luck! 🎤




