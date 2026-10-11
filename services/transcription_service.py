import os
import time
import threading
from pathlib import Path
from datetime import datetime
import streamlit as st
from typing import List, Dict, Optional

# Import whisper model - we'll use the cache_resource decorator for this
try:
    import torch
    import whisper
except ImportError:
    # If imports fail, we'll handle gracefully
    pass

class TranscriptionService:
    def __init__(self):
        self.inbox_dir = "./inbox"
        self.raw_markdown_dir = "./raw-markdown"
        self.processing_queue = []
        self.processed_files = set()
        self.current_status = "Idle"
        self.total_processed = 0
        self.last_processed_timestamp = None
        self.is_running = False
        self.thread = None
        
    def get_pending_files(self) -> List[str]:
        """Get all pending .m4a files sorted by creation time (FIFO)"""
        try:
            files = []
            for filename in os.listdir(self.inbox_dir):
                if filename.endswith('.m4a'):
                    filepath = os.path.join(self.inbox_dir, filename)
                    # Get file creation time (or modification time as fallback)
                    stat = os.stat(filepath)
                    creation_time = stat.st_ctime  # Creation time on Unix systems
                    files.append((filename, creation_time))
            
            # Sort by creation time (oldest first)
            files.sort(key=lambda x: x[1])
            return [filename for filename, _ in files]
        except Exception as e:
            print(f"Error getting pending files: {e}")
            return []
    
    def load_whisper_model(self):
        """Load the whisper model with caching"""
        # This will be cached using @st.cache_resource
        try:
            model = whisper.load_model("base")
            return model
        except Exception as e:
            print(f"Error loading whisper model: {e}")
            return None
    
    def transcribe_file(self, filename: str, model) -> Optional[str]:
        """Transcribe a single .m4a file and save as markdown"""
        try:
            input_path = os.path.join(self.inbox_dir, filename)
            output_path = os.path.join(self.raw_markdown_dir, f"{os.path.splitext(filename)[0]}.md")
            
            # Transcribe the audio file
            result = model.transcribe(input_path)
            
            # Save as markdown
            with open(output_path, 'w') as f:
                f.write(f"# Transcription of {filename}\n\n")
                f.write(result["text"])
            
            return output_path
        except Exception as e:
            print(f"Error transcribing {filename}: {e}")
            return None
    
    def process_queue(self):
        """Process files in the queue sequentially"""
        # Load model once for this thread
        model = self.load_whisper_model()
        if not model:
            print("Failed to load whisper model")
            return
            
        while self.is_running:
            pending_files = self.get_pending_files()
            
            if pending_files:
                # Process oldest file first
                filename = pending_files[0]
                
                if filename not in self.processed_files:
                    try:
                        self.current_status = f"Processing {filename}"
                        
                        # Transcribe the file
                        output_path = self.transcribe_file(filename, model)
                        
                        if output_path:
                            self.processed_files.add(filename)
                            self.total_processed += 1
                            self.last_processed_timestamp = datetime.now()
                            print(f"Successfully processed: {filename}")
                    except Exception as e:
                        print(f"Error processing {filename}: {e}")
                
                # Remove the processed file from inbox (optional - could keep for reference)
                try:
                    os.remove(os.path.join(self.inbox_dir, filename))
                except Exception as e:
                    print(f"Warning: Could not remove processed file {filename}: {e}")
            
            # Sleep briefly to avoid high CPU usage
            time.sleep(1)
    
    def start_service(self):
        """Start the transcription service in a background thread"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self.process_queue, daemon=True)
            self.thread.start()
            print("Transcription service started")
    
    def stop_service(self):
        """Stop the transcription service"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join()
        print("Transcription service stopped")
    
    def get_status(self) -> Dict:
        """Get current status of the service"""
        return {
            "current_status": self.current_status,
            "total_processed": self.total_processed,
            "last_processed_timestamp": self.last_processed_timestamp,
            "is_running": self.is_running,
            "pending_files_count": len(self.get_pending_files())
        }

# Global instance
transcription_service = TranscriptionService()

@st.cache_resource
def init_transcription_service():
    """Initialize and start the transcription service"""
    transcription_service.start_service()
    return transcription_service

# Export the service for use in app.py
__all__ = ['init_transcription_service', 'transcription_service']