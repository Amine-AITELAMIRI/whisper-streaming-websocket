#!/usr/bin/env python3
"""
Simple test client for the transcript WebSocket server
This allows you to test the server before integrating with Electron
"""
import asyncio
import websockets
import json
import sys
import signal

running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\nDisconnecting...")
    running = False

async def test_client(uri):
    """Test client that connects to the transcript server"""
    global running
    
    print("=" * 60)
    print("🧪 Testing Transcript WebSocket Server")
    print("=" * 60)
    print(f"Connecting to: {uri}")
    print("Press Ctrl+C to disconnect")
    print("-" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to server!\n")
            
            # Wait for initial connection message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(message)
                if data.get('type') == 'connected':
                    print(f"📨 Server: {data.get('message', '')}\n")
            except asyncio.TimeoutError:
                pass
            
            print("🎙️  Listening for transcripts...\n")
            print("-" * 60)
            
            # Listen for transcripts
            while running:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'transcript':
                        start_time = data.get('start_time', 0)
                        end_time = data.get('end_time', 0)
                        text = data.get('text', '')
                        
                        print(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}")
                    
                    elif data.get('type') == 'pong':
                        # Server responded to ping
                        pass
                        
                except asyncio.TimeoutError:
                    # Send periodic ping to keep connection alive
                    try:
                        await websocket.send(json.dumps({'type': 'ping'}))
                    except:
                        break
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("\n❌ Connection closed by server")
                    break
                    
    except ConnectionRefusedError:
        print("❌ Connection refused!")
        print("\nMake sure the server is running:")
        print("  python transcript_server.py --port 8765")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    print("\n✅ Test complete!")
    print("=" * 60)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test client for transcript WebSocket server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Connect to default server
  python test_transcript_client.py
  
  # Connect to custom port
  python test_transcript_client.py --port 8765
  
  # Connect to remote server
  python test_transcript_client.py --host 192.168.1.100 --port 8765
        """
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Server host (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Server port (default: 8765)"
    )
    
    args = parser.parse_args()
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    uri = f"ws://{args.host}:{args.port}"
    
    try:
        asyncio.run(test_client(uri))
    except KeyboardInterrupt:
        print("\n\nDisconnected.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()



