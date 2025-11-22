#!/usr/bin/env python3
"""
Examples of how to integrate realtime_transcribe.py with other applications
"""

from realtime_transcribe import realtime_transcribe
import queue
import threading
import json

# Example 1: Using a callback function to process transcripts
def example_callback():
    """Example showing how to use a callback function"""
    
    def my_transcript_handler(start_time, end_time, text):
        """This function is called every time a transcript is generated"""
        print(f"📝 Received: {text}")
        # Do something with the transcript here
        # - Send to an API
        # - Update a UI
        # - Process the text
        # - etc.
    
    # Run transcription with callback
    realtime_transcribe(
        model_size="base",
        transcript_callback=my_transcript_handler
    )


# Example 2: Using a queue to collect transcripts
def example_queue():
    """Example showing how to use a queue to collect transcripts"""
    
    transcript_queue = queue.Queue()
    
    def queue_handler(start_time, end_time, text):
        """Add transcripts to queue"""
        transcript_queue.put({
            'start_time': start_time,
            'end_time': end_time,
            'text': text
        })
    
    # Start transcription in a separate thread
    def run_transcription():
        realtime_transcribe(
            model_size="base",
            transcript_callback=queue_handler
        )
    
    transcribe_thread = threading.Thread(target=run_transcription, daemon=True)
    transcribe_thread.start()
    
    # Process transcripts from queue in your main application
    print("Waiting for transcripts...")
    while True:
        try:
            transcript = transcript_queue.get(timeout=1.0)
            print(f"Got transcript: {transcript['text']}")
            # Process transcript here
            transcript_queue.task_done()
        except queue.Empty:
            continue


# Example 3: Save to file and read from another process
def example_file_output():
    """Example showing file-based integration"""
    
    output_file = "transcripts.jsonl"
    
    # Start transcription with JSON output to file
    def run_transcription():
        realtime_transcribe(
            model_size="base",
            output_file=output_file,
            json_output=True
        )
    
    transcribe_thread = threading.Thread(target=run_transcription, daemon=True)
    transcribe_thread.start()
    
    # Read transcripts from file in another process/thread
    def read_transcripts():
        import time
        with open(output_file, 'r') as f:
            # Read new lines as they're written
            while True:
                line = f.readline()
                if line:
                    transcript = json.loads(line)
                    print(f"Read from file: {transcript['text']}")
                else:
                    time.sleep(0.1)  # Wait for more data
    
    read_thread = threading.Thread(target=read_transcripts, daemon=True)
    read_thread.start()
    
    transcribe_thread.join()


# Example 4: Class-based integration
class TranscriptCollector:
    """Example class to collect and process transcripts"""
    
    def __init__(self):
        self.transcripts = []
        self.lock = threading.Lock()
    
    def handle_transcript(self, start_time, end_time, text):
        """Callback method to handle transcripts"""
        with self.lock:
            self.transcripts.append({
                'start_time': start_time,
                'end_time': end_time,
                'text': text
            })
            print(f"Collected {len(self.transcripts)} transcripts")
    
    def get_all_transcripts(self):
        """Get all collected transcripts"""
        with self.lock:
            return self.transcripts.copy()
    
    def get_full_text(self):
        """Get all transcripts as a single string"""
        with self.lock:
            return ' '.join(t['text'] for t in self.transcripts)


def example_class_integration():
    """Example using a class to collect transcripts"""
    
    collector = TranscriptCollector()
    
    def run_transcription():
        realtime_transcribe(
            model_size="base",
            transcript_callback=collector.handle_transcript
        )
    
    transcribe_thread = threading.Thread(target=run_transcription, daemon=True)
    transcribe_thread.start()
    
    # Your application can access transcripts via collector methods
    import time
    time.sleep(10)  # Run for 10 seconds
    
    print("\nAll transcripts:")
    for t in collector.get_all_transcripts():
        print(f"  [{t['start_time']:.2f}s]: {t['text']}")
    
    print(f"\nFull text: {collector.get_full_text()}")


# Example 5: Integration with web application (Flask/FastAPI)
def example_web_integration():
    """Example showing how to integrate with a web app"""
    
    from flask import Flask, jsonify, Response
    import queue as q
    
    app = Flask(__name__)
    transcript_queue = q.Queue()
    
    def transcript_callback(start_time, end_time, text):
        transcript_queue.put({
            'start_time': start_time,
            'end_time': end_time,
            'text': text,
            'timestamp': time.time()
        })
    
    @app.route('/transcripts')
    def get_transcripts():
        """Stream transcripts as Server-Sent Events"""
        def generate():
            while True:
                try:
                    transcript = transcript_queue.get(timeout=1.0)
                    yield f"data: {json.dumps(transcript)}\n\n"
                except q.Empty:
                    yield ": keep-alive\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    # Start transcription in background
    def start_transcription():
        realtime_transcribe(
            model_size="base",
            transcript_callback=transcript_callback
        )
    
    threading.Thread(target=start_transcription, daemon=True).start()
    
    # Run Flask app
    # app.run(port=5000)


if __name__ == "__main__":
    print("This file contains integration examples.")
    print("Import the functions you need or use them as reference.")
    print("\nQuick example:")
    
    # Simple callback example
    def simple_handler(start_time, end_time, text):
        print(f"→ {text}")
    
    print("\nStarting transcription with callback (Ctrl+C to stop)...")
    realtime_transcribe(
        model_size="base",
        transcript_callback=simple_handler
    )



