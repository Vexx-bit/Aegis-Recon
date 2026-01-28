# Aegis Recon - Redis Queue System Setup Guide

## Overview

The Redis-based job queue system provides asynchronous, scalable job processing for security scans. This system decouples job submission from execution, allowing for better resource management and fault tolerance.

---

## Architecture

```
PHP API (api.php)
    ↓
queue_producer.py → Redis Queue (scans:queue)
                        ↓
                    queue_worker.py → scan_worker.py
                        ↓
                    MySQL (scans table)
```

**Components:**
1. **queue_producer.py** - Enqueues jobs to Redis
2. **queue_worker.py** - Processes jobs from Redis queue
3. **Redis** - Message broker and job queue
4. **MySQL** - Job status and results storage

---

## Installation

### 1. Install Redis

#### Ubuntu/Debian:
```bash
# Update package list
sudo apt update

# Install Redis
sudo apt install redis-server -y

# Start Redis service
sudo systemctl start redis-server

# Enable Redis to start on boot
sudo systemctl enable redis-server

# Verify Redis is running
sudo systemctl status redis-server

# Test Redis connection
redis-cli ping
# Should return: PONG
```

#### CentOS/RHEL:
```bash
# Install EPEL repository
sudo yum install epel-release -y

# Install Redis
sudo yum install redis -y

# Start Redis
sudo systemctl start redis

# Enable on boot
sudo systemctl enable redis

# Verify
redis-cli ping
```

#### Windows (for development):
```bash
# Download Redis for Windows from:
# https://github.com/microsoftarchive/redis/releases

# Or use WSL2 and follow Ubuntu instructions

# Or use Docker:
docker run -d -p 6379:6379 --name redis redis:latest
```

#### macOS:
```bash
# Using Homebrew
brew install redis

# Start Redis
brew services start redis

# Verify
redis-cli ping
```

### 2. Install Python Dependencies

```bash
# Navigate to project directory
cd /path/to/Aegis\ Recon

# Install required packages
pip install redis mysql-connector-python psutil

# Or use requirements file
pip install -r ai_services/requirements.txt
```

Create `ai_services/requirements.txt`:
```
redis>=4.5.0
mysql-connector-python>=8.0.0
psutil>=5.9.0
reportlab>=4.0.0
```

### 3. Configure Environment Variables

Update `.env` file:
```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# MySQL Configuration (already exists)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aegis_recon
DB_USER=root
DB_PASS=

# Queue Worker Settings
WORKER_TIMEOUT=1800  # 30 minutes in seconds
WORKER_LOG_PATH=/tmp/queue_worker.log
```

### 4. Test Redis Connection

```bash
# Test Redis CLI
redis-cli

# Inside Redis CLI:
127.0.0.1:6379> ping
PONG
127.0.0.1:6379> set test "hello"
OK
127.0.0.1:6379> get test
"hello"
127.0.0.1:6379> del test
(integer) 1
127.0.0.1:6379> exit
```

---

## Deployment

### Option 1: Systemd Service (Production - Linux)

#### Step 1: Copy Service File
```bash
# Copy systemd service file
sudo cp deployment/aegis-queue-worker.service /etc/systemd/system/

# Update paths in service file if needed
sudo nano /etc/systemd/system/aegis-queue-worker.service
```

#### Step 2: Set Permissions
```bash
# Make worker script executable
chmod +x ai_services/queue_worker.py

# Create log directory
sudo mkdir -p /var/log/aegis-recon
sudo chown www-data:www-data /var/log/aegis-recon
```

#### Step 3: Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Start the worker
sudo systemctl start aegis-queue-worker

# Enable on boot
sudo systemctl enable aegis-queue-worker

# Check status
sudo systemctl status aegis-queue-worker

# View logs
sudo journalctl -u aegis-queue-worker -f
```

#### Step 4: Manage Service
```bash
# Stop worker
sudo systemctl stop aegis-queue-worker

# Restart worker
sudo systemctl restart aegis-queue-worker

# View recent logs
sudo journalctl -u aegis-queue-worker -n 100

# Follow logs in real-time
sudo journalctl -u aegis-queue-worker -f
```

### Option 2: Manual Start (Development)

```bash
# Navigate to ai_services directory
cd ai_services

# Run worker in foreground
python3 queue_worker.py

# Or run in background
nohup python3 queue_worker.py > /tmp/queue_worker.log 2>&1 &

# Check if running
ps aux | grep queue_worker

# Kill worker
pkill -f queue_worker.py
```

### Option 3: Supervisor (Alternative to Systemd)

Install Supervisor:
```bash
sudo apt install supervisor -y
```

Create `/etc/supervisor/conf.d/aegis-queue-worker.conf`:
```ini
[program:aegis-queue-worker]
command=/usr/bin/python3 /var/www/html/Aegis Recon/ai_services/queue_worker.py
directory=/var/www/html/Aegis Recon/ai_services
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/aegis-recon/queue_worker.log
environment=PATH="/usr/bin:/usr/local/bin"
```

Start with Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start aegis-queue-worker
sudo supervisorctl status
```

---

## Usage

### Enqueue a Job (Python)

```bash
python3 ai_services/queue_producer.py \
  --job-id scan_123 \
  --target example.com \
  --user-id abc123
```

### Enqueue a Job (PHP)

```php
<?php
$jobId = 'scan_' . uniqid();
$target = 'example.com';
$userId = 'user_hash';

$command = sprintf(
    'python3 %s --job-id=%s --target=%s --user-id=%s',
    escapeshellarg(__DIR__ . '/../ai_services/queue_producer.py'),
    escapeshellarg($jobId),
    escapeshellarg($target),
    escapeshellarg($userId)
);

$output = shell_exec($command);
$result = json_decode($output, true);

if ($result['success']) {
    echo "Job enqueued: {$result['job_id']}\n";
    echo "Queue position: {$result['queue_position']}\n";
}
?>
```

### Monitor Queue

```bash
# Check queue length
redis-cli llen scans:queue

# View jobs in queue (first 10)
redis-cli lrange scans:queue 0 9

# View specific job status
redis-cli hgetall job:scan_123

# Clear entire queue (DANGER!)
redis-cli del scans:queue
```

---

## Monitoring & Troubleshooting

### Check Worker Status

```bash
# Systemd
sudo systemctl status aegis-queue-worker

# Process
ps aux | grep queue_worker

# Logs
tail -f /tmp/queue_worker.log
sudo journalctl -u aegis-queue-worker -f
```

### Check Redis Status

```bash
# Service status
sudo systemctl status redis-server

# Connection test
redis-cli ping

# Memory usage
redis-cli info memory

# Connected clients
redis-cli client list

# Queue statistics
redis-cli llen scans:queue
```

### Common Issues

#### Issue: Worker not processing jobs
**Solution:**
```bash
# Check if worker is running
sudo systemctl status aegis-queue-worker

# Check Redis connection
redis-cli ping

# Check MySQL connection
mysql -u root -p -e "USE aegis_recon; SELECT COUNT(*) FROM scans;"

# Restart worker
sudo systemctl restart aegis-queue-worker
```

#### Issue: Jobs stuck in queue
**Solution:**
```bash
# Check queue length
redis-cli llen scans:queue

# View stuck jobs
redis-cli lrange scans:queue 0 -1

# Clear queue if needed
redis-cli del scans:queue

# Check worker logs
sudo journalctl -u aegis-queue-worker -n 100
```

#### Issue: Redis connection refused
**Solution:**
```bash
# Start Redis
sudo systemctl start redis-server

# Check Redis config
sudo nano /etc/redis/redis.conf

# Ensure bind address allows connections
# bind 127.0.0.1

# Restart Redis
sudo systemctl restart redis-server
```

#### Issue: Stuck jobs not being reconciled
**Solution:**
```bash
# Check MySQL for stuck jobs
mysql -u root -p aegis_recon -e "
SELECT job_id, status, updated_at 
FROM scans 
WHERE status = 'running' 
AND updated_at < DATE_SUB(NOW(), INTERVAL 30 MINUTE);
"

# Worker reconciles every 5 minutes automatically
# Or restart worker to force reconciliation
sudo systemctl restart aegis-queue-worker
```

---

## Performance Tuning

### Redis Configuration

Edit `/etc/redis/redis.conf`:

```conf
# Maximum memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence (optional for queue)
save ""  # Disable RDB snapshots for better performance
appendonly no  # Disable AOF for queue use case

# Network
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Limits
maxclients 10000
```

Restart Redis after changes:
```bash
sudo systemctl restart redis-server
```

### Worker Scaling

Run multiple workers for parallel processing:

```bash
# Copy service file for worker 2
sudo cp /etc/systemd/system/aegis-queue-worker.service \
        /etc/systemd/system/aegis-queue-worker@2.service

# Start multiple workers
sudo systemctl start aegis-queue-worker
sudo systemctl start aegis-queue-worker@2

# Enable both
sudo systemctl enable aegis-queue-worker
sudo systemctl enable aegis-queue-worker@2
```

---

## Security

### Redis Security

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Set password
requirepass your_strong_password_here

# Bind to localhost only
bind 127.0.0.1

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""

# Restart Redis
sudo systemctl restart redis-server
```

Update `.env`:
```bash
REDIS_PASSWORD=your_strong_password_here
```

### Firewall Rules

```bash
# Allow Redis only from localhost (default)
sudo ufw deny 6379

# Or allow from specific IPs
sudo ufw allow from 192.168.1.0/24 to any port 6379
```

---

## Backup & Recovery

### Backup Redis Data

```bash
# Manual backup
redis-cli BGSAVE

# Copy RDB file
sudo cp /var/lib/redis/dump.rdb /backup/redis-$(date +%Y%m%d).rdb
```

### Restore Redis Data

```bash
# Stop Redis
sudo systemctl stop redis-server

# Restore RDB file
sudo cp /backup/redis-20231029.rdb /var/lib/redis/dump.rdb
sudo chown redis:redis /var/lib/redis/dump.rdb

# Start Redis
sudo systemctl start redis-server
```

---

## Testing

### Test Queue System

```bash
# 1. Start worker
python3 ai_services/queue_worker.py

# 2. In another terminal, enqueue test job
python3 ai_services/queue_producer.py \
  --job-id test_001 \
  --target 127.0.0.1 \
  --user-id test_user

# 3. Monitor worker logs
tail -f /tmp/queue_worker.log

# 4. Check job status in MySQL
mysql -u root -p aegis_recon -e "
SELECT job_id, status, created_at, updated_at 
FROM scans 
WHERE job_id = 'test_001';
"
```

---

## Maintenance

### Daily Tasks

```bash
# Check worker status
sudo systemctl status aegis-queue-worker

# Check queue length
redis-cli llen scans:queue

# Check for stuck jobs
mysql -u root -p aegis_recon -e "
SELECT COUNT(*) as stuck_jobs
FROM scans 
WHERE status = 'running' 
AND updated_at < DATE_SUB(NOW(), INTERVAL 30 MINUTE);
"
```

### Weekly Tasks

```bash
# Review logs
sudo journalctl -u aegis-queue-worker --since "7 days ago" | less

# Clean up old jobs
mysql -u root -p aegis_recon -e "
DELETE FROM scans 
WHERE completed_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
"

# Check Redis memory
redis-cli info memory
```

---

## Support

For issues with the queue system:
1. Check worker logs: `sudo journalctl -u aegis-queue-worker -f`
2. Check Redis: `redis-cli ping`
3. Check MySQL: `mysql -u root -p aegis_recon`
4. Review this documentation
5. Contact: support@aegisrecon.example.com
