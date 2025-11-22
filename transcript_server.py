#!/usr/bin/env python3
"""
HTTP/WebSocket server for real-time transcription
Designed for integration with Electron and other remote applications
"""
import json
import asyncio
import websockets
import threading
import argparse
from realtime_transcribe import realtime_transcribe, running, signal_handler
import signal

# Store active WebSocket connections
connections = set()

# Stable transcript state - accumulates all committed text segments
full_transcript = ""
_update_count = 0  # Track updates for periodic logging

async def register(websocket):
    """Register a new WebSocket connection"""
    connections.add(websocket)
    print(f"Client connected. Total connections: {len(connections)}")

async def unregister(websocket):
    """Unregister a WebSocket connection"""
    connections.discard(websocket)
    print(f"Client disconnected. Total connections: {len(connections)}")

async def broadcast_transcript(start_time, end_time, text):
    """Broadcast transcript to all connected clients - non-blocking
    (Kept for backwards compatibility; new code uses broadcast_full_transcript)"""
    if not connections:
        return
    
    message = json.dumps({
        'type': 'transcript',
        'start_time': start_time,
        'end_time': end_time,
        'text': text,
        'timestamp': asyncio.get_event_loop().time()
    }, ensure_ascii=False)
    
    # Send to all connected clients (fire-and-forget to prevent blocking)
    disconnected = set()
    send_tasks = []
    for connection in connections:
        try:
            # Use create_task to send asynchronously without blocking
            task = asyncio.create_task(connection.send(message))
            send_tasks.append((connection, task))
        except Exception:
            disconnected.add(connection)
    
    # Wait for sends to complete, but with timeout to prevent blocking
    for connection, task in send_tasks:
        try:
            await asyncio.wait_for(task, timeout=0.1)  # 100ms timeout
        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
            disconnected.add(connection)
        except Exception:
            disconnected.add(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        connections.discard(conn)

async def broadcast_full_transcript(full_text):
    """Broadcast the full accumulated transcript to all connected clients - non-blocking
    
    This function sends a stable, monotonic transcript that clients can safely
    use without worrying about duplicates or partial segments.
    """
    if not connections:
        return
    
    message = json.dumps({
        'type': 'transcript',
        'mode': 'full',
        'text': full_text,
        'timestamp': asyncio.get_event_loop().time()
    }, ensure_ascii=False)
    
    # Send to all connected clients (fire-and-forget to prevent blocking)
    disconnected = set()
    send_tasks = []
    for connection in connections:
        try:
            # Use create_task to send asynchronously without blocking
            task = asyncio.create_task(connection.send(message))
            send_tasks.append((connection, task))
        except Exception:
            disconnected.add(connection)
    
    # Wait for sends to complete, but with timeout to prevent blocking
    for connection, task in send_tasks:
        try:
            await asyncio.wait_for(task, timeout=0.1)  # 100ms timeout
        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
            disconnected.add(connection)
        except Exception:
            disconnected.add(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        connections.discard(conn)

def transcript_callback(start_time, end_time, text):
    """Callback function that accumulates committed text segments and broadcasts
    the full transcript via WebSocket.
    
    This function maintains a stable, monotonic transcript by accumulating
    new committed segments from the ASR processor. Empty or whitespace-only
    segments are ignored to prevent duplicate broadcasts.
    """
    global full_transcript, _update_count
    
    # Ignore empty or whitespace-only text
    new_text = text.strip() if text else ""
    if not new_text:
        return
    
    # Accumulate the new committed segment into the full transcript
    if full_transcript:
        # Append with a space separator
        full_transcript = (full_transcript + " " + new_text).strip()
    else:
        # First segment - initialize the full transcript
        full_transcript = new_text
        print(f"[Transcript] Initialized full transcript (length: {len(full_transcript)} chars)")
    
    _update_count += 1
    
    # Periodic logging (every 10 updates) to track progress without spam
    if _update_count % 10 == 0:
        print(f"[Transcript] Update #{_update_count}: full transcript length = {len(full_transcript)} chars")
    
    # Schedule broadcast in the event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                broadcast_full_transcript(full_transcript),
                loop
            )
    except RuntimeError:
        # No event loop running yet, create a temporary one
        asyncio.run(broadcast_full_transcript(full_transcript))

async def handle_client(websocket, path=None):
    """Handle WebSocket client connections
    
    Args:
        websocket: WebSocket connection
        path: Optional path (for compatibility with different websockets versions)
    """
    await register(websocket)
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'connected',
            'message': 'Connected to transcription server'
        }))
        
        # Keep connection alive and handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"Error in connection handler: {e}")
    finally:
        await unregister(websocket)

def start_transcription(model_size, language, use_vad, use_vac, chunk_duration):
    """Start transcription in a separate thread with optimizations for low latency"""
    def run():
        # Don't set up signal handler in thread - signals are handled in main thread
        # Enable VAC by default for better latency (only processes when speech detected)
        realtime_transcribe(
            model_size=model_size,
            language=language,
            use_vad=use_vad,
            use_vac=use_vac,  # VAC helps prevent latency by only processing during speech
            chunk_duration=chunk_duration,
            transcript_callback=transcript_callback,
            setup_signal_handler=False  # Signals handled in main thread
        )
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

async def main_server_with_stop(host, port, stop_event):
    """Run the WebSocket server with stop event"""
    async with websockets.serve(handle_client, host, port):
        print(f"\n✅ Server running on ws://{host}:{port}")
        print("Waiting for clients to connect...")
        await stop_event.wait()  # Wait until stop event is set

def main():
    parser = argparse.ArgumentParser(
        description="WebSocket server for real-time transcription",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with default settings
  python transcript_server.py
  
  # Start on custom port
  python transcript_server.py --port 8765
  
  # Use smaller model
  python transcript_server.py --model base --port 8765
        """
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind to (default: localhost, use 0.0.0.0 for all interfaces)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="WebSocket port (default: 8765)"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help="Whisper model size (default: base)"
    )
    
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="en",
        help="Language code (default: en)"
    )
    
    parser.add_argument(
        "--chunk-duration", "-c",
        type=float,
        default=0.7,
        help="Audio chunk duration in seconds (default: 0.7, larger = less processing = lower latency)"
    )
    
    parser.add_argument(
        "--no-vad",
        action="store_true",
        help="Disable voice activity detection"
    )
    
    parser.add_argument(
        "--vac",
        action="store_true",
        default=True,
        help="Use VAC (Voice Activity Controller) for better latency - enabled by default"
    )
    
    parser.add_argument(
        "--no-vac",
        dest="vac",
        action="store_false",
        help="Disable VAC (Voice Activity Controller)"
    )
    
    args = parser.parse_args()
    
    # Set up signal handler in main thread for graceful shutdown
    transcription_thread_ref = None
    stop_event_ref = {'stop_event': None}  # Use dict to allow modification
    
    def shutdown_handler(sig, frame):
        """Handle shutdown gracefully"""
        global running
        print("\n\nShutting down server...")
        running = False
        # Stop transcription by setting the global running flag
        import realtime_transcribe
        realtime_transcribe.running = False
        # Stop the asyncio event loop
        if stop_event_ref['stop_event']:
            stop_event_ref['stop_event'].set()
    
    signal.signal(signal.SIGINT, shutdown_handler)
    
    print("=" * 60)
    print("🌐 Transcription WebSocket Server")
    print("=" * 60)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Model: {args.model}")
    print(f"Language: {args.language}")
    print(f"VAD: {'Disabled' if args.no_vad else 'Enabled'}")
    print(f"VAC: {'Enabled' if args.vac else 'Disabled'} (recommended for low latency)")
    print("=" * 60)
    print("\nStarting transcription server...")
    print(f"WebSocket URL: ws://{args.host}:{args.port}")
    print("\nWaiting for clients to connect...")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    # Start transcription in background
    transcription_thread_ref = start_transcription(
        model_size=args.model,
        language=args.language,
        use_vad=not args.no_vad,
        use_vac=args.vac,
        chunk_duration=args.chunk_duration
    )
    
    # Create stop event for asyncio loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stop_event = asyncio.Event()
    
    # Make stop_event accessible to signal handler
    stop_event_ref['stop_event'] = stop_event
    
    # Start WebSocket server
    try:
        loop.run_until_complete(main_server_with_stop(args.host, args.port, stop_event))
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        stop_event.set()
    finally:
        # Clean up
        try:
            # Cancel any pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception as e:
            pass
        finally:
            loop.close()
        print("Server stopped.")

if __name__ == "__main__":
    main()

