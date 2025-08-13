import os
import json
import uuid
import asyncio
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from celery import Celery
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Initialize extensions
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# Initialize Celery
celery = Celery('mistral_ocr_test', broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Initialize Redis for session storage
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

# Import tasks after Celery initialization
from tasks import process_ocr_task, generate_test_files

@app.route('/')
def index():
    """Main page with configuration and test interface"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Handle configuration for Azure and GCP providers"""
    if request.method == 'POST':
        config_data = request.json
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        
        # Store configuration in Redis
        redis_client.setex(f"config:{session_id}", 3600, json.dumps(config_data))
        
        return jsonify({"status": "success", "session_id": session_id})
    
    # GET request - return current config
    session_id = session.get('session_id')
    if session_id:
        config_data = redis_client.get(f"config:{session_id}")
        if config_data:
            return jsonify(json.loads(config_data))
    
    return jsonify({"azure": {}, "gcp": {}})

@app.route('/api/generate-test-files', methods=['POST'])
def generate_files():
    """Generate test PDF files for testing"""
    try:
        data = request.json
        test_scenarios = data.get('scenarios', [])
        
        # Generate test files asynchronously
        task = generate_test_files.delay(test_scenarios)
        
        return jsonify({
            "status": "success",
            "task_id": task.id,
            "message": "Test files generation started"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start OCR processing"""
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
        
        # Get configuration
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({"status": "error", "message": "No configuration found"}), 400
        
        config_data = redis_client.get(f"config:{session_id}")
        if not config_data:
            return jsonify({"status": "error", "message": "Configuration not found"}), 400
        
        config = json.loads(config_data)
        
        # Save uploaded file
        filename = f"uploads/{uuid.uuid4()}_{file.filename}"
        os.makedirs('uploads', exist_ok=True)
        file.save(filename)
        
        # Start OCR processing task
        task = process_ocr_task.delay(filename, config)
        
        return jsonify({
            "status": "success",
            "task_id": task.id,
            "filename": file.filename
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/batch-test', methods=['POST'])
def batch_test():
    """Start batch testing with multiple files"""
    try:
        data = request.json
        test_config = data.get('test_config', {})
        
        # Get configuration
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({"status": "error", "message": "No configuration found"}), 400
        
        config_data = redis_client.get(f"config:{session_id}")
        if not config_data:
            return jsonify({"status": "error", "message": "Configuration not found"}), 400
        
        config = json.loads(config_data)
        
        # Start batch processing
        task = process_ocr_task.delay(None, config, test_config)
        
        return jsonify({
            "status": "success",
            "task_id": task.id,
            "message": "Batch test started"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/task-status/<task_id>')
def task_status(task_id):
    """Get task status and results"""
    try:
        task = celery.AsyncResult(task_id)
        
        if task.ready():
            if task.successful():
                result = task.result
                return jsonify({
                    "status": "completed",
                    "result": result
                })
            else:
                return jsonify({
                    "status": "failed",
                    "error": str(task.info)
                })
        else:
            return jsonify({
                "status": "running",
                "progress": task.info.get('progress', 0) if task.info else 0
            })
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """Get comprehensive statistics from Redis"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({"status": "error", "message": "No session found"}), 400
        
        # Get all statistics for this session
        stats_keys = redis_client.keys(f"stats:{session_id}:*")
        statistics = {}
        
        for key in stats_keys:
            stat_type = key.decode('utf-8').split(':')[-1]
            data = redis_client.get(key)
            if data:
                statistics[stat_type] = json.loads(data)
        
        return jsonify({
            "status": "success",
            "statistics": statistics
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    emit('status', {'message': 'Connected to Mistral OCR Test Server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('test_files', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
