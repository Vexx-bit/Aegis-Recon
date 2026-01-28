#!/usr/bin/env python3
"""
Aegis Recon - Job Queue Worker
Processes scan jobs from Redis queue and manages job lifecycle.
"""

import sys
import json
import time
import signal
import subprocess
import logging
import redis
import mysql.connector
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/queue_worker.log')
    ]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


class QueueWorker:
    """Worker for processing scan jobs from Redis queue."""
    
    def __init__(self, redis_config: Dict[str, Any], mysql_config: Dict[str, Any]):
        """
        Initialize queue worker.
        
        Args:
            redis_config: Redis connection configuration
            mysql_config: MySQL connection configuration
        """
        self.redis_config = redis_config
        self.mysql_config = mysql_config
        self.redis_client = None
        self.mysql_conn = None
        self.current_job = None
        self.current_process = None
        
        self._connect_redis()
        self._connect_mysql()
    
    def _connect_redis(self):
        """Connect to Redis."""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                db=self.redis_config.get('db', 0),
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    def _connect_mysql(self):
        """Connect to MySQL."""
        try:
            self.mysql_conn = mysql.connector.connect(
                host=self.mysql_config.get('host', 'localhost'),
                port=self.mysql_config.get('port', 3306),
                user=self.mysql_config.get('user', 'root'),
                password=self.mysql_config.get('password', ''),
                database=self.mysql_config.get('database', 'aegis_recon')
            )
            logger.info("Connected to MySQL successfully")
        except mysql.connector.Error as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            raise
    
    def _reconnect_mysql(self):
        """Reconnect to MySQL if connection is lost."""
        try:
            if self.mysql_conn:
                self.mysql_conn.close()
            self._connect_mysql()
        except Exception as e:
            logger.error(f"Failed to reconnect to MySQL: {str(e)}")
    
    def update_job_status(self, job_id: str, status: str, error_message: str = None):
        """
        Update job status in MySQL.
        
        Args:
            job_id: Job identifier
            status: New status
            error_message: Optional error message
        """
        try:
            cursor = self.mysql_conn.cursor()
            
            if status in ['done', 'completed']:
                sql = """
                    UPDATE scans 
                    SET status = %s, updated_at = NOW(), completed_at = NOW()
                    WHERE job_id = %s
                """
                cursor.execute(sql, (status, job_id))
            elif status == 'error' or status == 'failed':
                sql = """
                    UPDATE scans 
                    SET status = %s, error_message = %s, updated_at = NOW(), completed_at = NOW()
                    WHERE job_id = %s
                """
                cursor.execute(sql, (status, error_message, job_id))
            else:
                sql = """
                    UPDATE scans 
                    SET status = %s, updated_at = NOW()
                    WHERE job_id = %s
                """
                cursor.execute(sql, (status, job_id))
            
            self.mysql_conn.commit()
            cursor.close()
            
            logger.info(f"Updated job {job_id} status to: {status}")
            
        except mysql.connector.Error as e:
            logger.error(f"Failed to update job status: {str(e)}")
            self._reconnect_mysql()
    
    def update_redis_job_status(self, job_id: str, status: str):
        """Update job status in Redis."""
        try:
            job_key = f"job:{job_id}"
            self.redis_client.hset(job_key, 'status', status)
            self.redis_client.hset(job_key, 'updated_at', datetime.utcnow().isoformat() + 'Z')
        except Exception as e:
            logger.error(f"Failed to update Redis job status: {str(e)}")
    
    def process_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Process a single scan job.
        
        Args:
            job_data: Job information
            
        Returns:
            True if job completed successfully
        """
        job_id = job_data.get('job_id')
        target = job_data.get('target')
        
        logger.info(f"Processing job {job_id} for target: {target}")
        
        # Update status to running
        self.update_job_status(job_id, 'running')
        self.update_redis_job_status(job_id, 'running')
        
        # Build command to run scan_worker.py
        scan_worker_path = os.path.join(
            os.path.dirname(__file__),
            'scan_worker.py'
        )
        
        command = [
            'python',
            scan_worker_path,
            target,
            f'--job-id={job_id}'
        ]
        
        try:
            # Run scan worker
            logger.info(f"Executing: {' '.join(command)}")
            
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for completion with timeout
            timeout = 30 * 60  # 30 minutes
            stdout, stderr = self.current_process.communicate(timeout=timeout)
            
            return_code = self.current_process.returncode
            self.current_process = None
            
            if return_code == 0:
                logger.info(f"Job {job_id} completed successfully")
                self.update_job_status(job_id, 'done')
                self.update_redis_job_status(job_id, 'done')
                return True
            else:
                error_msg = f"Scan worker exited with code {return_code}: {stderr}"
                logger.error(f"Job {job_id} failed: {error_msg}")
                self.update_job_status(job_id, 'error', error_msg)
                self.update_redis_job_status(job_id, 'error')
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Job {job_id} timed out after {timeout} seconds")
            
            # Kill the process
            if self.current_process:
                self._kill_process_tree(self.current_process.pid)
                self.current_process = None
            
            self.update_job_status(job_id, 'error', 'Job timed out after 30 minutes')
            self.update_redis_job_status(job_id, 'error')
            return False
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")
            self.update_job_status(job_id, 'error', str(e))
            self.update_redis_job_status(job_id, 'error')
            return False
    
    def _kill_process_tree(self, pid: int):
        """Kill a process and all its children."""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Kill children first
            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Kill parent
            try:
                parent.kill()
            except psutil.NoSuchProcess:
                pass
            
            logger.info(f"Killed process tree for PID {pid}")
            
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} not found")
        except Exception as e:
            logger.error(f"Error killing process tree: {str(e)}")
    
    def reconcile_stuck_jobs(self):
        """Find and mark stuck jobs as errors."""
        try:
            cursor = self.mysql_conn.cursor(dictionary=True)
            
            # Find jobs running for more than 30 minutes
            sql = """
                SELECT job_id, target_domain, updated_at
                FROM scans
                WHERE status = 'running'
                  AND updated_at < DATE_SUB(NOW(), INTERVAL 30 MINUTE)
            """
            
            cursor.execute(sql)
            stuck_jobs = cursor.fetchall()
            
            for job in stuck_jobs:
                job_id = job['job_id']
                logger.warning(f"Found stuck job: {job_id} (last update: {job['updated_at']})")
                
                # Mark as error
                self.update_job_status(
                    job_id,
                    'error',
                    'Job stuck for more than 30 minutes - marked as failed'
                )
                self.update_redis_job_status(job_id, 'error')
            
            cursor.close()
            
            if stuck_jobs:
                logger.info(f"Reconciled {len(stuck_jobs)} stuck jobs")
            
        except mysql.connector.Error as e:
            logger.error(f"Error reconciling stuck jobs: {str(e)}")
            self._reconnect_mysql()
    
    def run(self):
        """Main worker loop."""
        logger.info("Queue worker started. Waiting for jobs...")
        
        last_reconcile = datetime.now()
        reconcile_interval = timedelta(minutes=5)
        
        while not shutdown_requested:
            try:
                # Reconcile stuck jobs every 5 minutes
                if datetime.now() - last_reconcile > reconcile_interval:
                    self.reconcile_stuck_jobs()
                    last_reconcile = datetime.now()
                
                # Block and wait for job (BLPOP with 5 second timeout)
                result = self.redis_client.blpop('scans:queue', timeout=5)
                
                if result is None:
                    # No job available, continue loop
                    continue
                
                # Extract job data
                queue_name, job_json = result
                job_data = json.loads(job_json)
                
                self.current_job = job_data
                
                # Process the job
                self.process_job(job_data)
                
                self.current_job = None
                
            except redis.ConnectionError as e:
                logger.error(f"Redis connection error: {str(e)}")
                time.sleep(5)
                self._connect_redis()
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid job JSON: {str(e)}")
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {str(e)}")
                time.sleep(1)
        
        logger.info("Queue worker shutting down...")
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        # Kill current process if running
        if self.current_process:
            logger.info("Killing current scan process...")
            self._kill_process_tree(self.current_process.pid)
        
        # Close connections
        if self.mysql_conn:
            self.mysql_conn.close()
            logger.info("Closed MySQL connection")
        
        if self.redis_client:
            self.redis_client.close()
            logger.info("Closed Redis connection")


def main():
    """Main entry point."""
    # Load configuration from environment
    redis_config = {
        'host': os.environ.get('REDIS_HOST', 'localhost'),
        'port': int(os.environ.get('REDIS_PORT', 6379)),
        'db': int(os.environ.get('REDIS_DB', 0))
    }
    
    mysql_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', 3306)),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASS', ''),
        'database': os.environ.get('DB_NAME', 'aegis_recon')
    }
    
    try:
        # Create and run worker
        worker = QueueWorker(redis_config, mysql_config)
        worker.run()
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
