# JavaScript Integration Guide

Complete guide for integrating the Whisper Transcription WebSocket Server with JavaScript applications.

## Overview

The transcription server is a **WebSocket server** that:
1. Captures audio from your microphone
2. Transcribes it in real-time using Whisper AI
3. Sends transcripts to connected JavaScript clients via WebSocket
4. Supports multiple simultaneous connections

## Architecture

```
┌─────────────────┐         WebSocket         ┌──────────────────┐
│  JavaScript     │ ◄──────────────────────► │  Python          │
│  Client         │    (JSON messages)       │  Server          │
│  (Your App)     │                          │  (transcript_    │
│                 │                          │   server.py)     │
└─────────────────┘                          └──────────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────────┐
                                              │  Microphone      │
                                              │  (Audio Input)   │
                                              └──────────────────┘
```

## Connection

### WebSocket URL Format

```
ws://localhost:8765
```

- **Protocol**: `ws://` (or `wss://` for secure connections)
- **Host**: `localhost` (or server IP address)
- **Port**: `8765` (default, configurable)

### Connection Flow

1. **Client connects** to WebSocket URL
2. **Server sends** connection confirmation
3. **Server starts** transcribing microphone audio
4. **Server sends** transcripts as they're generated
5. **Client receives** and processes transcripts

## Message Format

All messages are **JSON strings** sent over WebSocket.

### 1. Connection Message (from server)

Sent immediately after client connects:

```json
{
  "type": "connected",
  "message": "Connected to transcription server"
}
```

**Fields:**
- `type`: Always `"connected"`
- `message`: Human-readable connection message

### 2. Transcript Message (from server)

Sent whenever a new transcript segment is generated:

```json
{
  "type": "transcript",
  "start_time": 3.86,
  "end_time": 4.98,
  "text": "Hello world",
  "timestamp": 1234567890.123
}
```

**Fields:**
- `type`: Always `"transcript"`
- `start_time`: Start time of the segment in seconds (float)
- `end_time`: End time of the segment in seconds (float)
- `text`: The transcribed text (string)
- `timestamp`: Unix timestamp when transcript was generated (float)

**Example:**
```json
{
  "type": "transcript",
  "start_time": 5.23,
  "end_time": 6.45,
  "text": "This is a test",
  "timestamp": 1703123456.789
}
```

### 3. Ping/Pong (optional)

You can send ping messages to keep the connection alive:

**Client → Server:**
```json
{
  "type": "ping"
}
```

**Server → Client:**
```json
{
  "type": "pong"
}
```

## Integration Examples

### Browser (Vanilla JavaScript)

```javascript
// Create WebSocket connection
const ws = new WebSocket('ws://localhost:8765');

// Handle connection opened
ws.onopen = () => {
    console.log('Connected to transcription server');
};

// Handle incoming messages
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === 'connected') {
        console.log('Server:', message.message);
    } else if (message.type === 'transcript') {
        // Process transcript
        console.log(`[${message.start_time}s - ${message.end_time}s]: ${message.text}`);
        
        // Update your UI
        displayTranscript(message.start_time, message.end_time, message.text);
    }
};

// Handle errors
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

// Handle connection closed
ws.onclose = () => {
    console.log('Disconnected from server');
};

// Function to display transcript in your UI
function displayTranscript(startTime, endTime, text) {
    // Your UI update code here
    const transcriptElement = document.getElementById('transcripts');
    const item = document.createElement('div');
    item.textContent = `[${startTime.toFixed(2)}s]: ${text}`;
    transcriptElement.appendChild(item);
}
```

### Node.js

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
    console.log('Connected to transcription server');
});

ws.on('message', (data) => {
    const message = JSON.parse(data.toString());
    
    if (message.type === 'connected') {
        console.log('Server:', message.message);
    } else if (message.type === 'transcript') {
        console.log(`[${message.start_time}s - ${message.end_time}s]: ${message.text}`);
        
        // Process transcript in your application
        processTranscript(message);
    }
});

ws.on('error', (error) => {
    console.error('WebSocket error:', error);
});

ws.on('close', () => {
    console.log('Disconnected from server');
});

function processTranscript(message) {
    // Your processing logic here
    // e.g., save to database, send to API, etc.
}
```

### React Component

```jsx
import React, { useEffect, useState } from 'react';

function TranscriptionDisplay() {
    const [transcripts, setTranscripts] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const [ws, setWs] = useState(null);

    useEffect(() => {
        // Create WebSocket connection
        const websocket = new WebSocket('ws://localhost:8765');
        
        websocket.onopen = () => {
            setIsConnected(true);
            console.log('Connected to transcription server');
        };
        
        websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            if (message.type === 'connected') {
                console.log('Server:', message.message);
            } else if (message.type === 'transcript') {
                // Add new transcript to state
                setTranscripts(prev => [...prev, {
                    startTime: message.start_time,
                    endTime: message.end_time,
                    text: message.text,
                    timestamp: message.timestamp
                }]);
            }
        };
        
        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            setIsConnected(false);
        };
        
        websocket.onclose = () => {
            setIsConnected(false);
            console.log('Disconnected from server');
        };
        
        setWs(websocket);
        
        // Cleanup on unmount
        return () => {
            websocket.close();
        };
    }, []);

    return (
        <div>
            <div>Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}</div>
            <div>
                {transcripts.map((t, i) => (
                    <div key={i}>
                        [{t.startTime.toFixed(2)}s - {t.endTime.toFixed(2)}s]: {t.text}
                    </div>
                ))}
            </div>
        </div>
    );
}

export default TranscriptionDisplay;
```

### Electron (Main Process)

```javascript
const { app, BrowserWindow, ipcMain } = require('electron');
const WebSocket = require('ws');

let transcriptionClient = null;

function connectToTranscriptionServer() {
    transcriptionClient = new WebSocket('ws://localhost:8765');
    
    transcriptionClient.on('open', () => {
        console.log('Connected to transcription server');
        // Notify renderer process
        BrowserWindow.getAllWindows().forEach(win => {
            win.webContents.send('transcription-status', { connected: true });
        });
    });
    
    transcriptionClient.on('message', (data) => {
        const message = JSON.parse(data.toString());
        
        if (message.type === 'transcript') {
            // Send transcript to all renderer processes
            BrowserWindow.getAllWindows().forEach(win => {
                win.webContents.send('transcript', {
                    startTime: message.start_time,
                    endTime: message.end_time,
                    text: message.text,
                    timestamp: message.timestamp
                });
            });
        }
    });
    
    transcriptionClient.on('error', (error) => {
        console.error('Transcription error:', error);
    });
    
    transcriptionClient.on('close', () => {
        console.log('Disconnected from transcription server');
        BrowserWindow.getAllWindows().forEach(win => {
            win.webContents.send('transcription-status', { connected: false });
        });
    });
}

// IPC handlers
ipcMain.on('start-transcription', () => {
    if (!transcriptionClient || transcriptionClient.readyState !== WebSocket.OPEN) {
        connectToTranscriptionServer();
    }
});

ipcMain.on('stop-transcription', () => {
    if (transcriptionClient) {
        transcriptionClient.close();
        transcriptionClient = null;
    }
});
```

### Electron (Renderer Process)

```javascript
const { ipcRenderer } = require('electron');

// Listen for transcripts
ipcRenderer.on('transcript', (event, data) => {
    console.log(`[${data.startTime.toFixed(2)}s]: ${data.text}`);
    // Update UI
    updateTranscriptDisplay(data);
});

// Listen for connection status
ipcRenderer.on('transcription-status', (event, data) => {
    if (data.connected) {
        console.log('Transcription started');
    } else {
        console.log('Transcription stopped');
    }
});

// Start/stop transcription
document.getElementById('start-btn').addEventListener('click', () => {
    ipcRenderer.send('start-transcription');
});

document.getElementById('stop-btn').addEventListener('click', () => {
    ipcRenderer.send('stop-transcription');
});
```

## Complete Integration Pattern

Here's a reusable class you can use in any JavaScript application:

```javascript
class TranscriptionClient {
    constructor(wsUrl = 'ws://localhost:8765') {
        this.wsUrl = wsUrl;
        this.ws = null;
        this.onTranscriptCallback = null;
        this.onConnectCallback = null;
        this.onDisconnectCallback = null;
        this.onErrorCallback = null;
    }

    /**
     * Set callback for when transcripts are received
     * @param {Function} callback - Function(startTime, endTime, text, timestamp)
     */
    onTranscript(callback) {
        this.onTranscriptCallback = callback;
    }

    /**
     * Set callback for when connection is established
     * @param {Function} callback - Function()
     */
    onConnect(callback) {
        this.onConnectCallback = callback;
    }

    /**
     * Set callback for when connection is lost
     * @param {Function} callback - Function()
     */
    onDisconnect(callback) {
        this.onDisconnectCallback = callback;
    }

    /**
     * Set callback for errors
     * @param {Function} callback - Function(error)
     */
    onError(callback) {
        this.onErrorCallback = callback;
    }

    /**
     * Connect to the transcription server
     */
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.warn('Already connected');
            return;
        }

        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                console.log('Connected to transcription server');
                if (this.onConnectCallback) {
                    this.onConnectCallback();
                }
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    
                    if (message.type === 'connected') {
                        console.log('Server:', message.message);
                    } else if (message.type === 'transcript' && this.onTranscriptCallback) {
                        this.onTranscriptCallback(
                            message.start_time,
                            message.end_time,
                            message.text,
                            message.timestamp
                        );
                    }
                } catch (error) {
                    console.error('Error parsing message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                if (this.onErrorCallback) {
                    this.onErrorCallback(error);
                }
            };

            this.ws.onclose = () => {
                console.log('Disconnected from transcription server');
                if (this.onDisconnectCallback) {
                    this.onDisconnectCallback();
                }
            };

        } catch (error) {
            console.error('Error connecting:', error);
            if (this.onErrorCallback) {
                this.onErrorCallback(error);
            }
        }
    }

    /**
     * Disconnect from the transcription server
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    /**
     * Check if currently connected
     * @returns {boolean}
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Usage example:
const client = new TranscriptionClient('ws://localhost:8765');

client.onTranscript((startTime, endTime, text, timestamp) => {
    console.log(`[${startTime.toFixed(2)}s]: ${text}`);
    // Update your UI or process the transcript
});

client.onConnect(() => {
    console.log('Transcription started');
});

client.onDisconnect(() => {
    console.log('Transcription stopped');
});

client.connect();
```

## Message Flow Diagram

```
Client                          Server
  │                               │
  │─── WebSocket Connect ────────►│
  │                               │
  │◄── {type: "connected"} ──────│
  │                               │
  │                               │ [Listening to microphone]
  │                               │ [Processing audio...]
  │                               │
  │◄── {type: "transcript",      │
  │     start_time: 3.86,        │
  │     end_time: 4.98,          │
  │     text: "Hello"} ──────────│
  │                               │
  │                               │ [More audio processing...]
  │                               │
  │◄── {type: "transcript",      │
  │     start_time: 5.02,        │
  │     end_time: 5.72,          │
  │     text: "world"} ──────────│
  │                               │
  │                               │ [... continues ...]
  │                               │
  │─── Close Connection ─────────►│
  │                               │
```

## Data Types

### Transcript Object

When you receive a transcript message, you get:

```typescript
interface Transcript {
    type: "transcript";
    start_time: number;    // Float: seconds (e.g., 3.86)
    end_time: number;      // Float: seconds (e.g., 4.98)
    text: string;          // String: transcribed text (e.g., "Hello world")
    timestamp: number;     // Float: Unix timestamp (e.g., 1703123456.789)
}
```

### Connection Status

```typescript
interface ConnectionStatus {
    type: "connected";
    message: string;       // String: "Connected to transcription server"
}
```

## Error Handling

### Connection Errors

```javascript
ws.onerror = (error) => {
    // Common errors:
    // - Connection refused: Server not running
    // - Network error: Can't reach server
    // - Invalid URL: Wrong WebSocket URL
    console.error('Connection error:', error);
    
    // Retry logic
    setTimeout(() => {
        client.connect();
    }, 3000); // Retry after 3 seconds
};
```

### Message Parsing Errors

```javascript
ws.onmessage = (event) => {
    try {
        const message = JSON.parse(event.data);
        // Process message
    } catch (error) {
        console.error('Error parsing message:', error);
        // Message is not valid JSON, skip it
    }
};
```

### Reconnection Pattern

```javascript
class TranscriptionClient {
    constructor(wsUrl) {
        this.wsUrl = wsUrl;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // 2 seconds
    }

    connect() {
        // ... connection code ...
        
        this.ws.onclose = () => {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
                setTimeout(() => this.connect(), this.reconnectDelay);
            } else {
                console.error('Max reconnection attempts reached');
            }
        };
    }
}
```

## Server Configuration

The server can be configured with these options:

```bash
python transcript_server.py \
    --host localhost \          # Host to bind to
    --port 8765 \               # WebSocket port
    --model tiny \              # Model size (tiny, base, small, medium, large, large-v2, large-v3)
    --language en \             # Language code
    --chunk-duration 0.7 \      # Audio chunk duration (seconds)
    --vac \                     # Enable VAC (Voice Activity Controller) - recommended
    --no-vad                    # Disable VAD (Voice Activity Detection)
```

## Best Practices

1. **Always check connection state** before sending messages
2. **Handle reconnection** for production applications
3. **Parse JSON safely** with try-catch
4. **Clean up connections** when component unmounts
5. **Use ping/pong** to keep connection alive if needed
6. **Handle errors gracefully** with user-friendly messages

## Testing

1. **Start the server:**
   ```bash
   python transcript_server.py --port 8765 --model tiny
   ```

2. **Test connection:**
   ```javascript
   const ws = new WebSocket('ws://localhost:8765');
   ws.onopen = () => console.log('✅ Connected!');
   ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
   ```

3. **Verify transcripts:**
   - Speak into microphone
   - Check console for transcript messages
   - Verify `type: "transcript"` messages are received

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Make sure server is running on correct port |
| No transcripts | Check microphone permissions and audio input |
| Messages not parsing | Verify JSON format, add try-catch |
| Connection drops | Implement reconnection logic |
| Slow transcripts | Use smaller model (tiny/base) or enable VAC |

## Summary

- **Protocol**: WebSocket (ws:// or wss://)
- **Message Format**: JSON strings
- **Transcript Type**: `{type: "transcript", start_time, end_time, text, timestamp}`
- **Connection Type**: `{type: "connected", message}`
- **Real-time**: Transcripts sent as they're generated
- **Multiple Clients**: Server supports multiple simultaneous connections

The server handles all audio capture and transcription - your JavaScript client just needs to connect and receive the transcripts!



