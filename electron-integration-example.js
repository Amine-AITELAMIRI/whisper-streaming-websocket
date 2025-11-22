/**
 * Example Electron integration for real-time transcription
 * 
 * This shows how to connect to the Python transcription server
 * from your Electron application.
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const WebSocket = require('ws'); // npm install ws

class TranscriptionClient {
    constructor(wsUrl = 'ws://localhost:8765') {
        this.wsUrl = wsUrl;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.onTranscriptCallback = null;
        this.onErrorCallback = null;
        this.onConnectCallback = null;
        this.onDisconnectCallback = null;
    }

    /**
     * Set callback for when transcripts are received
     * @param {Function} callback - Function(startTime, endTime, text)
     */
    onTranscript(callback) {
        this.onTranscriptCallback = callback;
    }

    /**
     * Set callback for errors
     * @param {Function} callback - Function(error)
     */
    onError(callback) {
        this.onErrorCallback = callback;
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
     * Connect to the transcription server
     */
    connect() {
        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.on('open', () => {
                console.log('Connected to transcription server');
                this.reconnectAttempts = 0;
                if (this.onConnectCallback) {
                    this.onConnectCallback();
                }
            });

            this.ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    
                    if (message.type === 'transcript' && this.onTranscriptCallback) {
                        this.onTranscriptCallback(
                            message.start_time,
                            message.end_time,
                            message.text
                        );
                    } else if (message.type === 'connected') {
                        console.log('Server message:', message.message);
                    }
                } catch (error) {
                    console.error('Error parsing message:', error);
                }
            });

            this.ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                if (this.onErrorCallback) {
                    this.onErrorCallback(error);
                }
            });

            this.ws.on('close', () => {
                console.log('Disconnected from transcription server');
                if (this.onDisconnectCallback) {
                    this.onDisconnectCallback();
                }
                
                // Attempt to reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
                    setTimeout(() => this.connect(), 2000);
                }
            });

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
     * Send ping to keep connection alive
     */
    ping() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }));
        }
    }
}

// Example usage in your Electron app
function setupTranscription() {
    const transcriptionClient = new TranscriptionClient('ws://localhost:8765');

    // Handle transcripts
    transcriptionClient.onTranscript((startTime, endTime, text) => {
        console.log(`[${startTime.toFixed(2)}s - ${endTime.toFixed(2)}s]: ${text}`);
        
        // Update your UI here
        // e.g., send to renderer process via IPC
        // mainWindow.webContents.send('transcript', { startTime, endTime, text });
        
        // Or store in a variable
        // currentTranscripts.push({ startTime, endTime, text });
    });

    // Handle connection events
    transcriptionClient.onConnect(() => {
        console.log('Transcription started');
        // Update UI to show "listening" status
    });

    transcriptionClient.onDisconnect(() => {
        console.log('Transcription stopped');
        // Update UI to show "disconnected" status
    });

    transcriptionClient.onError((error) => {
        console.error('Transcription error:', error);
        // Show error message to user
    });

    // Connect
    transcriptionClient.connect();

    // Keep connection alive with periodic pings
    setInterval(() => transcriptionClient.ping(), 30000); // Every 30 seconds

    return transcriptionClient;
}

// Example with IPC (Inter-Process Communication)
function setupTranscriptionWithIPC(mainWindow) {
    const transcriptionClient = new TranscriptionClient('ws://localhost:8765');

    transcriptionClient.onTranscript((startTime, endTime, text) => {
        // Send transcript to renderer process
        mainWindow.webContents.send('transcript', {
            startTime,
            endTime,
            text,
            timestamp: Date.now()
        });
    });

    // Handle IPC messages from renderer
    ipcMain.on('start-transcription', () => {
        transcriptionClient.connect();
    });

    ipcMain.on('stop-transcription', () => {
        transcriptionClient.disconnect();
    });

    transcriptionClient.connect();
    return transcriptionClient;
}

// Example React component (for renderer process)
/*
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
            <div>Status: {isConnected ? '🟢 Listening' : '🔴 Disconnected'}</div>
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
*/

module.exports = { TranscriptionClient, setupTranscription, setupTranscriptionWithIPC };



