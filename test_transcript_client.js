/**
 * Simple Node.js/JavaScript example for testing the transcript WebSocket server
 * 
 * Usage:
 *   node test_transcript_client.js
 *   node test_transcript_client.js --host localhost --port 8765
 */

const WebSocket = require('ws');

// Parse command line arguments
const args = process.argv.slice(2);
let host = 'localhost';
let port = 8765;

for (let i = 0; i < args.length; i++) {
    if (args[i] === '--host' && args[i + 1]) {
        host = args[i + 1];
        i++;
    } else if (args[i] === '--port' && args[i + 1]) {
        port = parseInt(args[i + 1]);
        i++;
    }
}

const wsUrl = `ws://${host}:${port}`;

console.log('='.repeat(60));
console.log('🧪 Testing Transcript WebSocket Server');
console.log('='.repeat(60));
console.log(`Connecting to: ${wsUrl}`);
console.log('Press Ctrl+C to disconnect');
console.log('-'.repeat(60));

let transcriptCount = 0;
let startTime = null;

const ws = new WebSocket(wsUrl);

ws.on('open', () => {
    console.log('\n✅ Connected to server!\n');
    console.log('🎙️  Listening for transcripts...\n');
    console.log('-'.repeat(60));
    startTime = Date.now();
});

ws.on('message', (data) => {
    try {
        const message = JSON.parse(data.toString());
        
        if (message.type === 'connected') {
            console.log(`📨 Server: ${message.message}\n`);
        } else if (message.type === 'transcript') {
            transcriptCount++;
            const startTime = message.start_time || 0;
            const endTime = message.end_time || 0;
            const text = message.text || '';
            
            console.log(`[${startTime.toFixed(2)}s - ${endTime.toFixed(2)}s]: ${text}`);
        } else if (message.type === 'pong') {
            // Server responded to ping
            console.log('✓ Ping received');
        }
    } catch (error) {
        console.error('Error parsing message:', error);
    }
});

ws.on('error', (error) => {
    console.error('\n❌ WebSocket error:', error.message);
    console.log('\nMake sure the server is running:');
    console.log(`  python transcript_server.py --port ${port}`);
    process.exit(1);
});

ws.on('close', () => {
    const elapsed = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;
    console.log('\n' + '-'.repeat(60));
    console.log(`\n✅ Test complete!`);
    console.log(`   Transcripts received: ${transcriptCount}`);
    console.log(`   Connected time: ${elapsed}s`);
    console.log('='.repeat(60));
    process.exit(0);
});

// Send periodic ping to keep connection alive
const pingInterval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000); // Every 30 seconds

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
    console.log('\n\nDisconnecting...');
    clearInterval(pingInterval);
    if (ws) {
        ws.close();
    }
});



