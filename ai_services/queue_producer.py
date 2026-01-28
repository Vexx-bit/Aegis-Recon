#!/usr/bin/env python3
"""
Aegis Recon - Job Queue Producer
Pushes scan jobs to Redis queue for asynchronous processing.
"""

import sys
import json
import argparse
import redis
import os
from datetime import datetime
from typing import Dict, Any


class QueueProducer:
    """Producer for Redis-based job queue."""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        """
        Initialize queue producer.
        
        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            redis_db: Redis database number
        """
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis at {redis_host}:{redis_port}: {str(e)}")
    
    def enqueue_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Enqueue a scan job to Redis.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            True if job was enqueued successfully
        """
        # Validate job data
        required_fields = ['job_id', 'target', 'user_id']
        for field in required_fields:
            if field not in job_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Add metadata
        job_data['enqueued_at'] = datetime.utcnow().isoformat() + 'Z'
        job_data['status'] = 'queued'
        
        # Convert to JSON
        job_json = json.dumps(job_data)
        
        # Push to Redis list (RPUSH adds to end of list)
        queue_name = 'scans:queue'
        self.redis_client.rpush(queue_name, job_json)
        
        # Also store job metadata in hash for quick lookup
        job_key = f"job:{job_data['job_id']}"
        self.redis_client.hset(job_key, mapping={
            'job_id': job_data['job_id'],
            'target': job_data['target'],
            'user_id': job_data['user_id'],
            'status': 'queued',
            'enqueued_at': job_data['enqueued_at']
        })
        
        # Set expiration on job metadata (7 days)
        self.redis_client.expire(job_key, 7 * 24 * 60 * 60)
        
        return True
    
    def get_queue_length(self) -> int:
        """Get current queue length."""
        return self.redis_client.llen('scans:queue')
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status from Redis."""
        job_key = f"job:{job_id}"
        job_data = self.redis_client.hgetall(job_key)
        
        if not job_data:
            return None
        
        return job_data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Aegis Recon - Job Queue Producer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python queue_producer.py --job-id scan123 --target example.com --user-id abc123
  python queue_producer.py -j scan456 -t 192.168.1.1 -u user456
        """
    )
    
    parser.add_argument(
        '--job-id', '-j',
        required=True,
        help='Unique job identifier'
    )
    
    parser.add_argument(
        '--target', '-t',
        required=True,
        help='Target domain or IP address'
    )
    
    parser.add_argument(
        '--user-id', '-u',
        required=True,
        help='User ID (for consent tracking)'
    )
    
    parser.add_argument(
        '--redis-host',
        default=os.environ.get('REDIS_HOST', 'localhost'),
        help='Redis server hostname (default: localhost)'
    )
    
    parser.add_argument(
        '--redis-port',
        type=int,
        default=int(os.environ.get('REDIS_PORT', 6379)),
        help='Redis server port (default: 6379)'
    )
    
    parser.add_argument(
        '--redis-db',
        type=int,
        default=int(os.environ.get('REDIS_DB', 0)),
        help='Redis database number (default: 0)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create producer
        producer = QueueProducer(
            redis_host=args.redis_host,
            redis_port=args.redis_port,
            redis_db=args.redis_db
        )
        
        # Prepare job data
        job_data = {
            'job_id': args.job_id,
            'target': args.target,
            'user_id': args.user_id
        }
        
        # Enqueue job
        producer.enqueue_job(job_data)
        
        # Get queue length
        queue_length = producer.get_queue_length()
        
        # Output success message
        print(json.dumps({
            'success': True,
            'job_id': args.job_id,
            'queue_position': queue_length,
            'message': f'Job enqueued successfully. Position in queue: {queue_length}'
        }))
        
        return 0
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
