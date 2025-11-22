# Testing the WebSocket Setup

Follow these steps to test the transcript server before integrating with Electron.

## Prerequisites

1. Install websockets (if not already installed):
```bash
pip install websockets
```

2. Make sure your microphone is working

## Step 1: Start the Server

Open a terminal in the `whisper-streaming-websocket` directory and run:

```bash
python transcript_server.py --port 8765 --model base
```

**Expected output:**
```
============================================================
🌐 Transcription WebSocket Server
============================================================
Host: localhost
Port: 8765
Model: base
Language: en
VAD: Enabled
VAC: Disabled
============================================================

Starting transcription server...
WebSocket URL: ws://localhost:8765

Waiting for clients to connect...
Press Ctrl+C to stop
------------------------------------------------------------

✅ Server running on ws://localhost:8765
Waiting for clients to connect...
```

**Keep this terminal open!**

## Step 2: Run the Test Client

Open a **new terminal** in the same directory and run:

```bash
python test_transcript_client.py --port 8765
```

**Expected output:**
```
============================================================
🧪 Testing Transcript WebSocket Server
============================================================
Connecting to: ws://localhost:8765
Press Ctrl+C to disconnect
------------------------------------------------------------
✅ Connected to server!

📨 Server: Connected to transcription server

🎙️  Listening for transcripts...

------------------------------------------------------------
```

**Keep this terminal open too!**

## Step 3: Test Transcription

1. **Speak into your microphone**
2. **Watch Terminal 2** - you should see transcripts appearing in real-time:
   ```
   [3.86s - 4.98s]: Hello world
   [5.02s - 5.72s]: This is a test
   [5.74s - 6.28s]: The transcription is working
   ```

## Step 4: Verify Everything Works

✅ **Server Terminal 1**: Should show "Client connected" messages
✅ **Client Terminal 2**: Should show real-time transcripts as you speak
✅ **No errors**: Both terminals should run without errors

## Troubleshooting

### Connection Refused Error

**Problem:**
```
❌ Connection refused!
Make sure the server is running
```

**Solution:**
- Make sure the server is running in Terminal 1
- Check that the port matches (default: 8765)
- Try a different port: `--port 8766`

### No Transcripts Appearing

**Problem:** Client connects but no transcripts appear

**Solution:**
- Check your microphone is working
- Make sure microphone permissions are granted
- Try speaking louder or closer to the microphone
- Check server terminal for any error messages

### Module Not Found

**Problem:**
```
ModuleNotFoundError: No module named 'websockets'
```

**Solution:**
```bash
pip install websockets
```

### Port Already in Use

**Problem:**
```
Address already in use
```

**Solution:**
```bash
# Use a different port
python transcript_server.py --port 8766
python test_transcript_client.py --port 8766
```

## Successful Test Checklist

- [ ] Server starts without errors
- [ ] Client connects successfully  
- [ ] Server shows "Client connected" message
- [ ] Transcripts appear when speaking
- [ ] Timestamps are correct
- [ ] Both can be stopped with Ctrl+C

## Next Steps

Once the test is successful:

1. ✅ Server is working correctly
2. ✅ WebSocket communication is working
3. ✅ You're ready to integrate with Electron!

Copy the `TranscriptionClient` class from `electron-integration-example.js` to your Electron app and connect to `ws://localhost:8765`.

## Advanced Testing

### Test with Different Models

```bash
# Server with tiny model (faster)
python transcript_server.py --port 8765 --model tiny

# Server with VAC (better latency)
python transcript_server.py --port 8765 --model base --vac
```

### Test Connection from Remote Machine

If testing from a different machine on the network:

```bash
# Server (use 0.0.0.0 to accept connections from any IP)
python transcript_server.py --host 0.0.0.0 --port 8765

# Client (use server's IP address)
python test_transcript_client.py --host 192.168.1.100 --port 8765
```



