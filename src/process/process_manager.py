# main idea behind "Process Manager":
    # We can track all running processes with their status
    # To allow process cancellation
    # Clean up resources after cancellation (efficiency feature)
    # Handle process lifecycle and error states

import os
import signal
import psutil
import threading
import uuid
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
import logging
from flask import session

@dataclass
class ProcessInfo:

    # to store information about running processes

    process_id: int
    start_time: datetime
    status: str  # 'running', 'completed', 'cancelled', 'error'
    session_id: str
    timestamp: str
    annotation_type: str
    input_file: str
    output_folder: str

class ProcessManager:
    # to manage annotation processes and their lifecycle
    
    def __init__(self):
        self._processes: Dict[str, ProcessInfo] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def start_process(self, session_id: str, timestamp: str, annotation_type: str, 
                     input_file: str, output_folder: str) -> str:
        
        # Register a new process
        process_id = os.getpid()  #get current process ID
        
        with self._lock:
            process_key = f"{session_id}_{timestamp}"
            self._processes[process_key] = ProcessInfo(
                process_id=process_id,
                start_time=datetime.now(),
                status='running',
                session_id=session_id,
                timestamp=timestamp,
                annotation_type=annotation_type,
                input_file=input_file,
                output_folder=output_folder
            )
            
        return process_key
    
    def cancel_process(self, process_key: str) -> bool:
        # to cancel a running process

        with self._lock:
            if process_key not in self._processes:
                return False
                
            process_info = self._processes[process_key]
            if process_info.status != 'running':
                return False
            
            try:
                # Kill the process and its children
                parent = psutil.Process(process_info.process_id)
                children = parent.children(recursive=True)
                
                for child in children:
                    child.kill()
                parent.kill()
                
                # clean up temporary files
                if os.path.exists(process_info.output_folder):
                    for root, dirs, files in os.walk(process_info.output_folder):
                        for file in files:
                            try:
                                os.remove(os.path.join(root, file))
                            except Exception as e:
                                self.logger.error(f"Error removing file: {e}")
                    try:
                        os.rmdir(process_info.output_folder)
                    except Exception as e:
                        self.logger.error(f"Error removing directory: {e}")
                
                process_info.status = 'cancelled'
                return True
                
            except Exception as e:
                self.logger.error(f"Error cancelling process: {e}")
                return False
    
    def get_process_status(self, process_key: str) -> Optional[str]:
        # to get current status of a process
        with self._lock:
            if process_key in self._processes:
                return self._processes[process_key].status
            return None
    
    def update_process_status(self, process_key: str, status: str):
        # to update process status
        with self._lock:
            if process_key in self._processes:
                self._processes[process_key].status = status
    
    def cleanup_old_processes(self, max_age_hours: int = 24):
        # to clean up old completed/cancelled processes
        current_time = datetime.now()
        
        with self._lock:
            to_remove = []
            for key, info in self._processes.items():
                age = (current_time - info.start_time).total_seconds() / 3600
                if age > max_age_hours and info.status in ['completed', 'cancelled']:
                    to_remove.append(key)
            
            for key in to_remove:
                del self._processes[key]
    
    def get_session_processes(self, session_id: str) -> Dict[str, ProcessInfo]:
        # to get all processes for a specific session
        with self._lock:
            return {k: v for k, v in self._processes.items() 
                   if v.session_id == session_id}

# Creating global process manager instance
process_manager = ProcessManager()