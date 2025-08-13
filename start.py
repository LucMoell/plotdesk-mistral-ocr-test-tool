#!/usr/bin/env python3
"""
Startup script for Mistral OCR Test Suite
This script initializes all necessary services and starts the application
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

def check_redis():
    """Check if Redis is running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis is running")
        return True
    except Exception as e:
        print(f"✗ Redis is not running: {e}")
        return False

def start_redis():
    """Start Redis server"""
    try:
        # Try to start Redis (this might not work on all systems)
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        if check_redis():
            print("✓ Redis started successfully")
            return True
        else:
            print("✗ Failed to start Redis automatically")
            print("Please start Redis manually: redis-server")
            return False
    except FileNotFoundError:
        print("✗ Redis not found in PATH")
        print("Please install Redis and ensure it's in your PATH")
        return False

def start_celery_worker():
    """Start Celery worker"""
    try:
        # Start Celery worker
        worker_process = subprocess.Popen([
            'celery', '-A', 'tasks', 'worker', 
            '--loglevel=info', '--concurrency=2'
        ])
        print("✓ Celery worker started")
        return worker_process
    except Exception as e:
        print(f"✗ Failed to start Celery worker: {e}")
        return None

def start_celery_beat():
    """Start Celery beat scheduler (if needed)"""
    try:
        beat_process = subprocess.Popen([
            'celery', '-A', 'tasks', 'beat', 
            '--loglevel=info'
        ])
        print("✓ Celery beat started")
        return beat_process
    except Exception as e:
        print(f"✗ Failed to start Celery beat: {e}")
        return None

def create_directories():
    """Create necessary directories"""
    directories = ['uploads', 'test_files', 'results', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")

def setup_environment():
    """Setup environment variables"""
    if not os.path.exists('.env'):
        print("⚠ No .env file found")
        print("Please copy env_example.txt to .env and configure your settings")
        return False
    
    print("✓ Environment file found")
    return True

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down...")
    sys.exit(0)

def main():
    """Main startup function"""
    print("🚀 Starting Mistral OCR Test Suite...")
    print("=" * 50)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create directories
    create_directories()
    
    # Check environment
    if not setup_environment():
        print("Please configure your environment before starting")
        return
    
    # Check/start Redis
    if not check_redis():
        if not start_redis():
            print("Cannot continue without Redis")
            return
    
    # Start Celery worker
    worker_process = start_celery_worker()
    if not worker_process:
        print("Cannot continue without Celery worker")
        return
    
    # Start Celery beat (optional)
    beat_process = start_celery_beat()
    
    # Start Flask application
    print("\n🌐 Starting Flask application...")
    try:
        from app import app, socketio
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"✗ Error starting Flask app: {e}")
    finally:
        # Cleanup
        if worker_process:
            worker_process.terminate()
        if beat_process:
            beat_process.terminate()
        print("✓ Cleanup completed")

if __name__ == "__main__":
    main()
