# Electron Integration Guide

This guide shows how to integrate the Python transcription server with your Electron application.

## Setup

### 1. Install WebSocket Library in Electron

```bash
cd /path/to/your/electron/app
npm install ws
```

### 2. Start the Transcription Server

From the whisper-streaming-websocket directory:

```bash
# Default settings (port 8765)
python transcript_server.py

# Custom port and model
python transcript_server.py --port 8765 --model base

# With VAC for better latency
python transcript_server.py --port 8765 --model base --vac
```

### 3. Integrate in Your Electron App

#### Option A: Simple Integration (Copy the client class)

Copy the `TranscriptionClient` class from `electron-integration-example.js` into your Electron app:

```javascript
// main.js or wherever your main process code is
const { TranscriptionClient } = require('./transcription-client');

const client = new TranscriptionClient('ws://localhost:8765');

client.onTranscript((startTime, endTime, text) => {
    console.log(`Got transcript: ${text}`);
    // Send to renderer process
    mainWindow.webContents.send('transcript', { startTime, endTime, text });
});

client.connect();
```

#### Option B: Use IPC (Inter-Process Communication)

```javascript
// main.js
const { ipcMain, BrowserWindow } = require('electron');
const { TranscriptionClient } = require('./transcription-client');

let transcriptionClient = null;

ipcMain.on('start-transcription', () => {
    if (!transcriptionClient) {
        transcriptionClient = new TranscriptionClient('ws://localhost:8765');
        transcriptionClient.onTranscript((startTime, endTime, text) => {
            BrowserWindow.getAllWindows().forEach(win => {
                win.webContents.send('transcript', { startTime, endTime, text });
            });
        });
        transcriptionClient.connect();
    }
});

ipcMain.on('stop-transcription', () => {
    if (transcriptionClient) {
        transcriptionClient.disconnect();
        transcriptionClient = null;
    }
});
```

```javascript
// renderer.js (in your UI)
const { ipcRenderer } = require('electron');

// Listen for transcripts
ipcRenderer.on('transcript', (event, data) => {
    console.log(`[${data.startTime.toFixed(2)}s]: ${data.text}`);
    // Update your UI here
    updateTranscriptUI(data);
});

// Start transcription
document.getElementById('start-btn').addEventListener('click', () => {
    ipcRenderer.send('start-transcription');
});

// Stop transcription
document.getElementById('stop-btn').addEventListener('click', () => {
    ipcRenderer.send('stop-transcription');
});
```

## Starting the Server Automatically

### Option 1: Spawn from Electron

```javascript
// main.js
const { spawn } = require('child_process');
const path = require('path');

// Path to the transcription server
const serverPath = path.join(__dirname, '../../whisper-streaming-websocket/transcript_server.py');

function startTranscriptionServer() {
    const server = spawn('python', [serverPath, '--port', '8765', '--model', 'base'], {
        cwd: path.dirname(serverPath)
    });
    
    server.stdout.on('data', (data) => {
        console.log(`Server: ${data}`);
    });
    
    server.stderr.on('data', (data) => {
        console.error(`Server error: ${data}`);
    });
    
    server.on('close', (code) => {
        console.log(`Server exited with code ${code}`);
    });
    
    return server;
}

// Start server when app starts
let transcriptionServer = startTranscriptionServer();

// Stop server when app closes
app.on('will-quit', () => {
    if (transcriptionServer) {
        transcriptionServer.kill();
    }
});
```

### Option 2: Check if Server is Running

```javascript
const WebSocket = require('ws');

function checkServerRunning(port = 8765) {
    return new Promise((resolve) => {
        const ws = new WebSocket(`ws://localhost:${port}`);
        
        ws.on('open', () => {
            ws.close();
            resolve(true);
        });
        
        ws.on('error', () => {
            resolve(false);
        });
    });
}

async function ensureServerRunning() {
    const isRunning = await checkServerRunning();
    if (!isRunning) {
        console.log('Starting transcription server...');
        // Start server (see Option 1)
        startTranscriptionServer();
        // Wait a bit for server to start
        await new Promise(resolve => setTimeout(resolve, 3000));
    }
}
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

## Complete Example

See `electron-integration-example.js` for a complete working example.

## Troubleshooting

1. **Connection refused**: Make sure the Python server is running
2. **Module not found**: Install `ws` package: `npm install ws`
3. **Port already in use**: Change the port with `--port` argument
4. **No audio devices**: Check audio device access (especially in WSL)

## Running on Different Machines

If your Electron app and transcription server are on different machines:

1. Use `--host 0.0.0.0` to bind to all interfaces
2. Update WebSocket URL: `ws://your-server-ip:8765`
3. Make sure firewall allows connections on port 8765

```bash
python transcript_server.py --host 0.0.0.0 --port 8765
```



