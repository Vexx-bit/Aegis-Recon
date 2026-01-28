#!/usr/bin/env python3
"""
Update scan status in database after completion
"""

import sys
import os
import json
import mysql.connector
from pathlib import Path

def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent / '.env'
    env_vars = {}
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def update_scan_status(job_id, status, results_path=None, error_message=None):
    """
    Update scan status in database
    
    Args:
        job_id: Job identifier
        status: New status ('done' or 'error')
        results_path: Path to results JSON file
        error_message: Error message if status is 'error'
    """
    env = load_env()
    
    try:
        # Connect to database
        db = mysql.connector.connect(
            host=env.get('DB_HOST', 'localhost'),
            port=int(env.get('DB_PORT', 3306)),
            user=env.get('DB_USER', 'root'),
            password=env.get('DB_PASS', ''),
            database=env.get('DB_NAME', 'aegis_recon')
        )
        
        cursor = db.cursor()
        
        # Load results if available
        results_json = None
        if results_path and os.path.exists(results_path):
            with open(results_path, 'r') as f:
                results_json = json.dumps(json.load(f))
        
        # Update scan record
        if status == 'done':
            cursor.execute("""
                UPDATE scans 
                SET status = 'done',
                    results = %s,
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE job_id = %s
            """, (results_json, job_id))
        else:
            cursor.execute("""
                UPDATE scans 
                SET status = 'error',
                    error_message = %s,
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE job_id = %s
            """, (error_message, job_id))
        
        db.commit()
        print(f"✓ Updated scan {job_id} status to {status}")
        
        cursor.close()
        db.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Error updating scan status: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python update_scan_status.py <job_id> <status> [results_path] [error_message]")
        sys.exit(1)
    
    job_id = sys.argv[1]
    status = sys.argv[2]
    results_path = sys.argv[3] if len(sys.argv) > 3 else None
    error_message = sys.argv[4] if len(sys.argv) > 4 else None
    
    success = update_scan_status(job_id, status, results_path, error_message)
    sys.exit(0 if success else 1)
