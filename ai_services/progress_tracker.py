#!/usr/bin/env python3
"""
Progress Tracker - Real-time scan progress updates
Writes progress to database for dashboard to display
"""

import json
import os
import mysql.connector
from pathlib import Path
from typing import Optional
from datetime import datetime


class ProgressTracker:
    """Track and report scan progress in real-time."""
    
    PHASES = {
        1: 'Subdomain Enumeration',
        2: 'OSINT Intelligence Gathering',
        3: 'Port Scanning',
        4: 'Technology Detection',
        5: 'Vulnerability Scanning'
    }
    
    # Estimated duration for each phase (in seconds)
    PHASE_ESTIMATES = {
        1: 30,   # Subdomain Enumeration: ~30 seconds
        2: 20,   # OSINT: ~20 seconds
        3: 120,  # Port Scanning: ~2 minutes
        4: 30,   # Technology Detection: ~30 seconds
        5: 60    # Vulnerability Scanning: ~1 minute
    }
    
    def __init__(self, job_id: str):
        """
        Initialize progress tracker.
        
        Args:
            job_id: Job identifier
        """
        self.job_id = job_id
        self.db = None
        self.start_time = datetime.now()
        self.current_phase = 0
        self.total_phases = 5
        self.phase_start_time = None
        
        # Connect to database
        self._connect_db()
    
    def _connect_db(self):
        """Connect to database."""
        try:
            # Load environment variables
            env_path = Path(__file__).parent.parent / '.env'
            env_vars = {}
            
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            
            self.db = mysql.connector.connect(
                host=env_vars.get('DB_HOST', 'localhost'),
                port=int(env_vars.get('DB_PORT', 3306)),
                user=env_vars.get('DB_USER', 'root'),
                password=env_vars.get('DB_PASS', ''),
                database=env_vars.get('DB_NAME', 'aegis_recon')
            )
        except Exception as e:
            print(f"Warning: Could not connect to database for progress tracking: {e}")
            self.db = None
    
    def start_phase(self, phase_num: int, details: Optional[str] = None):
        """
        Start a new phase.
        
        Args:
            phase_num: Phase number (1-5)
            details: Optional details about the phase
        """
        self.current_phase = phase_num
        self.phase_start_time = datetime.now()
        
        phase_name = self.PHASES.get(phase_num, f'Phase {phase_num}')
        activity = details or f'Starting {phase_name}...'
        
        progress_pct = int((phase_num - 1) / self.total_phases * 100)
        
        self._update_progress(
            phase=phase_name,
            activity=activity,
            progress=progress_pct,
            status='running'
        )
    
    def update_activity(self, activity: str, sub_progress: Optional[int] = None):
        """
        Update current activity within a phase.
        
        Args:
            activity: Description of current activity
            sub_progress: Optional sub-progress within phase (0-100)
        """
        phase_name = self.PHASES.get(self.current_phase, f'Phase {self.current_phase}')
        
        # Calculate overall progress
        base_progress = int((self.current_phase - 1) / self.total_phases * 100)
        phase_weight = int(100 / self.total_phases)
        
        if sub_progress is not None:
            progress_pct = base_progress + int(phase_weight * sub_progress / 100)
        else:
            progress_pct = base_progress
        
        self._update_progress(
            phase=phase_name,
            activity=activity,
            progress=progress_pct,
            status='running'
        )
    
    def complete_phase(self, phase_num: int, summary: Optional[str] = None):
        """
        Mark a phase as complete.
        
        Args:
            phase_num: Phase number that completed
            summary: Optional summary of phase results
        """
        phase_name = self.PHASES.get(phase_num, f'Phase {phase_num}')
        activity = summary or f'Completed {phase_name}'
        
        progress_pct = int(phase_num / self.total_phases * 100)
        
        self._update_progress(
            phase=phase_name,
            activity=activity,
            progress=progress_pct,
            status='running'
        )
    
    def complete_scan(self, summary: str = 'Scan completed successfully'):
        """
        Mark entire scan as complete.
        
        Args:
            summary: Completion summary
        """
        self._update_progress(
            phase='Complete',
            activity=summary,
            progress=100,
            status='done'
        )
    
    def error(self, error_msg: str):
        """
        Report an error.
        
        Args:
            error_msg: Error message
        """
        self._update_progress(
            phase='Error',
            activity=error_msg,
            progress=0,
            status='error'
        )
    
    def _update_progress(self, phase: str, activity: str, progress: int, status: str):
        """
        Update progress in database.
        
        Args:
            phase: Current phase name
            activity: Current activity description
            progress: Progress percentage (0-100)
            status: Status (running, done, error)
        """
        if not self.db:
            return
        
        try:
            # Calculate elapsed time (total scan time)
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            # Calculate phase elapsed time
            if self.phase_start_time:
                phase_elapsed = (datetime.now() - self.phase_start_time).total_seconds()
            else:
                phase_elapsed = 0
            
            # Estimate remaining time using realistic phase estimates
            if progress > 0 and progress < 100:
                # Use overall progress for total remaining
                estimated_total = elapsed / (progress / 100)
                total_remaining = int(max(0, estimated_total - elapsed))
            else:
                total_remaining = 0
            
            # Use phase-specific estimate for current phase remaining
            phase_estimate = self.PHASE_ESTIMATES.get(self.current_phase, 60)
            phase_remaining = int(max(0, phase_estimate - phase_elapsed))
            
            # If phase just started (< 5 seconds), use full phase estimate
            if phase_elapsed < 5:
                phase_remaining = phase_estimate
            
            # Create progress JSON with both total and phase-specific times
            progress_data = {
                'phase': phase,
                'activity': activity,
                'progress': progress,
                'elapsed_seconds': int(elapsed),
                'estimated_remaining_seconds': total_remaining,
                'phase_elapsed_seconds': int(phase_elapsed),
                'phase_remaining_seconds': phase_remaining,
                'timestamp': datetime.now().isoformat()
            }
            
            cursor = self.db.cursor()
            
            # Update scan record with progress
            cursor.execute("""
                UPDATE scans 
                SET progress_data = %s,
                    updated_at = NOW()
                WHERE job_id = %s
            """, (json.dumps(progress_data), self.job_id))
            
            self.db.commit()
            cursor.close()
            
        except Exception as e:
            print(f"Warning: Could not update progress: {e}")
    
    def close(self):
        """Close database connection."""
        if self.db:
            try:
                self.db.close()
            except:
                pass


# Convenience functions for use in scan worker
_tracker = None

def init_tracker(job_id: str):
    """Initialize global progress tracker."""
    global _tracker
    _tracker = ProgressTracker(job_id)
    return _tracker

def start_phase(phase_num: int, details: Optional[str] = None):
    """Start a phase."""
    if _tracker:
        _tracker.start_phase(phase_num, details)

def update_activity(activity: str, sub_progress: Optional[int] = None):
    """Update activity."""
    if _tracker:
        _tracker.update_activity(activity, sub_progress)

def complete_phase(phase_num: int, summary: Optional[str] = None):
    """Complete a phase."""
    if _tracker:
        _tracker.complete_phase(phase_num, summary)

def complete_scan(summary: str = 'Scan completed successfully'):
    """Complete scan."""
    if _tracker:
        _tracker.complete_scan(summary)

def report_error(error_msg: str):
    """Report error."""
    if _tracker:
        _tracker.error(error_msg)

def close_tracker():
    """Close tracker."""
    global _tracker
    if _tracker:
        _tracker.close()
        _tracker = None
