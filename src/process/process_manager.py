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
import multiprocessing
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging
import shutil

@dataclass
class ProcessInfo:

    # to store information about running processes

    process_id: int
    child_pids: List[int]  # Track child process IDs
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
        process_id = os.getpid()  # Get current process ID
        
        # Create output directory if it doesn't exist
        # os.makedirs(output_folder, exist_ok=True)
        
        with self._lock:
            process_key = f"{session_id}_{timestamp}"
            self._processes[process_key] = ProcessInfo(
                process_id=process_id,
                child_pids=[],  # Initially empty, will be populated when child process starts
                start_time=datetime.now(),
                status='running',
                session_id=session_id,
                timestamp=timestamp,
                annotation_type=annotation_type,
                input_file=input_file,
                output_folder=output_folder
            )
            
        return process_key
    
    def register_child_process(self, process_key: str, child_pid: int) -> bool:
        # Register a child process ID with a parent process
        with self._lock:
            if process_key not in self._processes:
                return False
            
            self._processes[process_key].child_pids.append(child_pid)
            return True
    
    def cancel_process(self, process_key: str) -> bool:
        # to cancel a running process and clean up resources
        with self._lock:
            if process_key not in self._processes:
                self.logger.error(f"Process key {process_key} not found")
                return False
                
            process_info = self._processes[process_key]
            if process_info.status != 'running':
                self.logger.info(f"Process {process_key} already in state {process_info.status}")
                return False
            
            try:
                # Create a cancellation file as a signal
                cancel_file = os.path.join(process_info.output_folder, "cancel.txt")
                with open(cancel_file, 'w') as f:
                    f.write(f"Cancelled at {datetime.now().isoformat()}")
                
                # First try to terminate child processes
                for pid in process_info.child_pids:
                    try:
                        self.logger.info(f"Attempting to terminate child process {pid}")
                        child_process = psutil.Process(pid)
                        child_process.terminate()  # Try graceful termination first
                        
                        # Give it a moment to terminate gracefully
                        try:
                            child_process.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            self.logger.warning(f"Child process {pid} did not terminate gracefully, forcing kill")
                            child_process.kill()
                    except psutil.NoSuchProcess:
                        self.logger.info(f"Child process {pid} already terminated")
                    except Exception as e:
                        self.logger.error(f"Error terminating child process {pid}: {e}")
                
                # Update process status
                process_info.status = 'cancelled'
                self.logger.info(f"Process {process_key} cancelled successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error cancelling process: {e}")
                return False
            
    def get_process_info(self, process_key: str) -> Optional[ProcessInfo]:
    # to get complete process info
        with self._lock:
            if process_key in self._processes:
                return self._processes[process_key]
            return None

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
                self.logger.info(f"Updated process {process_key} status to {status}")
    
    def cleanup_old_processes(self, max_age_hours: int = 24):
        # to clean up old completed/cancelled processes
        current_time = datetime.now()
        
        with self._lock:
            to_remove = []
            for key, info in self._processes.items():
                age = (current_time - info.start_time).total_seconds() / 3600
                if age > max_age_hours and info.status in ['completed', 'cancelled', 'error']:
                    to_remove.append(key)
            
            for key in to_remove:
                # Clean up output folder if it still exists
                try:
                    info = self._processes[key]
                    if os.path.exists(info.output_folder):
                        shutil.rmtree(info.output_folder)
                except Exception as e:
                    self.logger.error(f"Error cleaning up process {key}: {e}")
                
                del self._processes[key]
                self.logger.info(f"Cleaned up old process: {key}")
    
    def get_session_processes(self, session_id: str) -> Dict[str, ProcessInfo]:
        # to get all processes for a specific session
        with self._lock:
            return {k: v for k, v in self._processes.items() 
                   if v.session_id == session_id}

# Creating global process manager instance
process_manager = ProcessManager()