# JavaScript Testing Guide

Simple JavaScript examples to test the transcript WebSocket server.

## Option 1: Browser Test (HTML/JavaScript)

### Setup

1. **Start the Python server:**
```bash
python transcript_server.py --port 8765 --model tiny
```

2. **Open `test_transcript_client.html` in your browser:**
   - Double-click the file, or
   - Open it from your browser: `File > Open > test_transcript_client.html`

3. **Connect and test:**
   - Enter the host (default: `localhost`) and port (default: `8765`)
   - Click "Connect"
   - Start speaking into your microphone
   - Transcripts will appear in real-time!

### Features

- ✅ Real-time transcript display
- ✅ Connection status indicator
- ✅ Statistics (transcript count, connected time)
- ✅ Beautiful, modern UI
- ✅ Auto-scrolling transcripts
- ✅ Works in any modern browser

## Option 2: Node.js Test (Command Line)

### Setup

1. **Install WebSocket library (if not already installed):**
```bash
npm install ws
```

2. **Start the Python server:**
```bash
python transcript_server.py --port 8765 --model tiny
```

3. **Run the Node.js client:**
```bash
# Default (localhost:8765)
node test_transcript_client.js

# Custom host and port
node test_transcript_client.js --host localhost --port 8765
```

### Expected Output

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
[3.86s - 4.98s]: Hello world
[5.02s - 5.72s]: This is a test
[5.74s - 6.28s]: The transcription is working
```

## Option 3: Use in Your Own JavaScript/TypeScript Code

### Browser (Vanilla JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    console.log('Connected!');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'transcript') {
        console.log(`[${message.start_time}s]: ${message.text}`);
        // Do something with the transcript
    }
};

ws.onerror = (error) => {
    console.error('Error:', error);
};

ws.onclose = () => {
    console.log('Disconnected');
};
```

### Node.js

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
    console.log('Connected!');
});

ws.on('message', (data) => {
    const message = JSON.parse(data.toString());
    if (message.type === 'transcript') {
        console.log(`[${message.start_time}s]: ${message.text}`);
        // Do something with the transcript
    }
});

ws.on('error', (error) => {
    console.error('Error:', error);
});

ws.on('close', () => {
    console.log('Disconnected');
});
```

### React Component Example

```jsx
import React, { useEffect, useState } from 'react';

function TranscriptionDisplay() {
    const [transcripts, setTranscripts] = useState([]);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8765');
        
        ws.onopen = () => {
            setIsConnected(true);
        };
        
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'transcript') {
                setTranscripts(prev => [...prev, {
                    startTime: message.start_time,
                    endTime: message.end_time,
                    text: message.text,
                    timestamp: message.timestamp
                }]);
            }
        };
        
        ws.onclose = () => {
            setIsConnected(false);
        };
        
        return () => ws.close();
    }, []);

    return (
        <div>
            <div>Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}</div>
            <div>
                {transcripts.map((t, i) => (
                    <div key={i}>
                        [{t.startTime.toFixed(2)}s]: {t.text}
                    </div>
                ))}
            </div>
        </div>
    );
}

export default TranscriptionDisplay;
```

### Vue.js Example

```vue
<template>
  <div>
    <div>Status: {{ isConnected ? '🟢 Connected' : '🔴 Disconnected' }}</div>
    <div v-for="(transcript, index) in transcripts" :key="index">
      [{{ transcript.startTime.toFixed(2) }}s]: {{ transcript.text }}
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      transcripts: [],
      isConnected: false,
      ws: null
    };
  },
  mounted() {
    this.ws = new WebSocket('ws://localhost:8765');
    
    this.ws.onopen = () => {
      this.isConnected = true;
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'transcript') {
        this.transcripts.push({
          startTime: message.start_time,
          endTime: message.end_time,
          text: message.text
        });
      }
    };
    
    this.ws.onclose = () => {
      this.isConnected = false;
    };
  },
  beforeUnmount() {
    if (this.ws) {
      this.ws.close();
    }
  }
};
</script>
```

## Message Format

The server sends JSON messages in this format:

```json
{
  "type": "transcript",
  "start_time": 3.86,
  "end_time": 4.98,
  "text": "Hello world",
  "timestamp": 1234567890.123
}
```

Connection message:
```json
{
  "type": "connected",
  "message": "Connected to transcription server"
}
```

## Testing Checklist

- [ ] Server is running (`python transcript_server.py`)
- [ ] Can connect to WebSocket URL
- [ ] Receives connection confirmation message
- [ ] Transcripts appear when speaking
- [ ] Timestamps are correct
- [ ] Connection stays stable
- [ ] Can disconnect cleanly

## Troubleshooting

### Connection Refused
- Make sure the server is running
- Check the host and port are correct
- Firewall might be blocking the connection

### No Transcripts Appearing
- Check your microphone is working
- Make sure the Python server is processing audio
- Check browser/OS microphone permissions
- Speak clearly and loudly enough

### Browser CORS Issues
- This shouldn't happen with WebSockets
- If using HTTPS, make sure server supports WSS (secure WebSocket)

## Next Steps

Once testing works, integrate the WebSocket client into your Electron app using the patterns shown above!



