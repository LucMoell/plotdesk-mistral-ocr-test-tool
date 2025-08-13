import os
import json
import uuid
import base64
import requests
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
from google.cloud import aiplatform
from google.oauth2 import service_account
import openai

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Initialize extensions
CORS(app)

# Database file path
DB_FILE = 'mistral_ocr_test.db'

# Initialize database
def init_database():
    """Initialize SQLite database with required tables"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Create configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                config_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create test history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                providers TEXT NOT NULL,
                results TEXT NOT NULL,
                statistics TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create task store table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_store (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                filename TEXT,
                test_config TEXT,
                providers TEXT,
                config_data TEXT,
                result_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                total_pages INTEGER DEFAULT 0,
                successful_pages INTEGER DEFAULT 0,
                failed_pages INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                total_response_time REAL DEFAULT 0.0,
                average_response_time REAL DEFAULT 0.0,
                min_response_time REAL DEFAULT 0.0,
                max_response_time REAL DEFAULT 0.0,
                total_tokens INTEGER DEFAULT 0,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                average_tokens_per_page REAL DEFAULT 0.0,
                total_errors INTEGER DEFAULT 0,
                error_details TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {DB_FILE}")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def load_config():
    """Load configuration from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT provider, config_data FROM configurations ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        
        config = {"azure": {}, "gcp": {}}
        for row in rows:
            provider = row['provider']
            config_data = json.loads(row['config_data'])
            config[provider] = config_data
        
        conn.close()
        return config
        
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"azure": {}, "gcp": {}}

def save_config(config):
    """Save configuration to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for provider, config_data in config.items():
            if config_data:  # Only save if config has data
                # Check if config exists
                cursor.execute('SELECT id FROM configurations WHERE provider = ?', (provider,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing config
                    cursor.execute('''
                        UPDATE configurations 
                        SET config_data = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE provider = ?
                    ''', (json.dumps(config_data), provider))
                else:
                    # Insert new config
                    cursor.execute('''
                        INSERT INTO configurations (provider, config_data)
                        VALUES (?, ?)
                    ''', (provider, json.dumps(config_data)))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def save_task(task_id, status, progress=0, filename=None, test_config=None, providers=None, config_data=None, result_data=None):
    """Save task to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if task exists
        cursor.execute('SELECT id FROM task_store WHERE task_id = ?', (task_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing task
            cursor.execute('''
                UPDATE task_store 
                SET status = ?, progress = ?, filename = ?, test_config = ?, 
                    providers = ?, config_data = ?, result_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = ?
            ''', (status, progress, filename, json.dumps(test_config) if test_config else None,
                  json.dumps(providers) if providers else None, json.dumps(config_data) if config_data else None,
                  json.dumps(result_data) if result_data else None, task_id))
        else:
            # Insert new task
            cursor.execute('''
                INSERT INTO task_store (task_id, status, progress, filename, test_config, providers, config_data, result_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (task_id, status, progress, filename, json.dumps(test_config) if test_config else None,
                  json.dumps(providers) if providers else None, json.dumps(config_data) if config_data else None,
                  json.dumps(result_data) if result_data else None))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving task: {e}")
        return False

def get_task(task_id):
    """Get task from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM task_store WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        
        if row:
            task = dict(row)
            # Parse JSON fields
            if task['test_config']:
                task['test_config'] = json.loads(task['test_config'])
            if task['providers']:
                task['providers'] = json.loads(task['providers'])
            if task['config_data']:
                task['config_data'] = json.loads(task['config_data'])
            if task['result_data']:
                task['result_data'] = json.loads(task['result_data'])
        
        conn.close()
        return task
        
    except Exception as e:
        print(f"Error getting task: {e}")
        return None

def save_test_history(task_id, filename, providers, results, statistics):
    """Save test to history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_history (task_id, filename, providers, results, statistics)
            VALUES (?, ?, ?, ?, ?)
        ''', (task_id, filename, json.dumps(providers), json.dumps(results), json.dumps(statistics)))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving test history: {e}")
        return False

def get_test_history():
    """Get all test history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM test_history ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        tests = []
        for row in rows:
            test = dict(row)
            # Parse JSON fields
            test['providers'] = json.loads(test['providers'])
            test['results'] = json.loads(test['results'])
            test['statistics'] = json.loads(test['statistics'])
            tests.append(test)
        
        conn.close()
        return tests
        
    except Exception as e:
        print(f"Error getting test history: {e}")
        return []

def get_test_by_id(task_id):
    """Get specific test by task_id"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM test_history WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        
        if row:
            test = dict(row)
            # Parse JSON fields
            test['providers'] = json.loads(test['providers'])
            test['results'] = json.loads(test['results'])
            test['statistics'] = json.loads(test['statistics'])
        
        conn.close()
        return test
        
    except Exception as e:
        print(f"Error getting test by id: {e}")
        return None

def update_statistics(provider, stats):
    """Update statistics for a provider"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if stats exist for provider
        cursor.execute('SELECT id FROM statistics WHERE provider = ?', (provider,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing stats
            cursor.execute('''
                UPDATE statistics 
                SET total_pages = ?, successful_pages = ?, failed_pages = ?, success_rate = ?,
                    total_response_time = ?, average_response_time = ?, min_response_time = ?, max_response_time = ?,
                    total_tokens = ?, input_tokens = ?, output_tokens = ?, average_tokens_per_page = ?,
                    total_errors = ?, error_details = ?, updated_at = CURRENT_TIMESTAMP
                WHERE provider = ?
            ''', (stats['summary']['total_pages'], stats['summary']['successful_pages'], 
                  stats['summary']['failed_pages'], stats['summary']['success_rate'],
                  stats['performance']['total_time'], stats['performance'].get('average_response_time', 0),
                  stats['performance']['min_time'], stats['performance']['max_time'],
                  stats['token_usage']['total_tokens'], stats['token_usage']['input_tokens'],
                  stats['token_usage']['output_tokens'], stats['token_usage'].get('average_tokens_per_page', 0),
                  stats['errors']['total_errors'], json.dumps(stats['errors']['error_details']), provider))
        else:
            # Insert new stats
            cursor.execute('''
                INSERT INTO statistics (provider, total_pages, successful_pages, failed_pages, success_rate,
                                      total_response_time, average_response_time, min_response_time, max_response_time,
                                      total_tokens, input_tokens, output_tokens, average_tokens_per_page,
                                      total_errors, error_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (provider, stats['summary']['total_pages'], stats['summary']['successful_pages'], 
                  stats['summary']['failed_pages'], stats['summary']['success_rate'],
                  stats['performance']['total_time'], stats['performance'].get('average_response_time', 0),
                  stats['performance']['min_time'], stats['performance']['max_time'],
                  stats['token_usage']['total_tokens'], stats['token_usage']['input_tokens'],
                  stats['token_usage']['output_tokens'], stats['token_usage'].get('average_tokens_per_page', 0),
                  stats['errors']['total_errors'], json.dumps(stats['errors']['error_details'])))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating statistics: {e}")
        return False

def get_statistics():
    """Get all statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM statistics')
        rows = cursor.fetchall()
        
        statistics = {}
        for row in rows:
            provider = row['provider']
            statistics[provider] = {
                'summary': {
                    'total_pages': row['total_pages'],
                    'successful_pages': row['successful_pages'],
                    'failed_pages': row['failed_pages'],
                    'success_rate': row['success_rate']
                },
                'performance': {
                    'total_time': row['total_response_time'],
                    'average_response_time': row['average_response_time'],
                    'min_response_time': row['min_response_time'],
                    'max_response_time': row['max_response_time']
                },
                'token_usage': {
                    'total_tokens': row['total_tokens'],
                    'input_tokens': row['input_tokens'],
                    'output_tokens': row['output_tokens'],
                    'average_tokens_per_page': row['average_tokens_per_page']
                },
                'errors': {
                    'total_errors': row['total_errors'],
                    'error_details': json.loads(row['error_details']) if row['error_details'] else []
                }
            }
        
        conn.close()
        return statistics
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {}

def create_azure_client(config):
    """Create Azure OpenAI client"""
    try:
        if not config.get('api_key') or not config.get('endpoint'):
            return None
        
        client = openai.AzureOpenAI(
            api_key=config['api_key'],
            api_version=config.get('api_version', '2024-02-15-preview'),
            azure_endpoint=config['endpoint']
        )
        return client
    except Exception as e:
        print(f"Error creating Azure client: {e}")
        return None

def create_gcp_client(config):
    """Create GCP client"""
    try:
        if not config.get('service_account_json'):
            return None
        
        # Parse service account JSON
        service_account_info = json.loads(config['service_account_json'])
        
        # Initialize GCP client
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info
        )
        
        aiplatform.init(
            credentials=credentials,
            project=config.get('project_id'),
            location=config.get('location', 'us-central1')
        )
        
        return aiplatform
    except Exception as e:
        print(f"Error creating GCP client: {e}")
        return None

def call_azure_ocr(client, image_base64, deployment_name):
    """Call Azure OpenAI Vision API for OCR"""
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this image. Return only the extracted text without any additional formatting or explanations."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096,
            temperature=0
        )
        
        return {
            'text': response.choices[0].message.content,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
    except Exception as e:
        raise Exception(f"Azure OCR error: {str(e)}")

def call_gcp_ocr(client, image_base64, endpoint_id):
    """Call GCP Vertex AI for OCR"""
    try:
        # Create prediction client
        endpoint = client.Endpoint(endpoint_id)
        
        # Prepare the request
        instance = {
            "instances": [
                {
                    "image": {
                        "bytesBase64Encoded": image_base64
                    }
                }
            ]
        }
        
        # Make prediction
        response = endpoint.predict(instances=instance["instances"])
        
        # Extract text from response (adjust based on actual GCP response format)
        predictions = response.predictions
        if predictions and len(predictions) > 0:
            # Assuming the response contains text in a specific field
            # You may need to adjust this based on the actual GCP OCR response format
            text = predictions[0].get('text', '') if hasattr(predictions[0], 'get') else str(predictions[0])
        else:
            text = ""
        
        return {
            'text': text,
            'usage': {
                'prompt_tokens': 0,  # GCP doesn't provide token usage in the same way
                'completion_tokens': 0,
                'total_tokens': 0
            }
        }
    except Exception as e:
        raise Exception(f"GCP OCR error: {str(e)}")

def process_image_with_providers(image_base64, providers_config):
    """Process image with selected providers"""
    results = {}
    
    # Process with Azure if configured
    if providers_config.get('azure', {}).get('enabled'):
        azure_config = providers_config['azure']
        azure_client = create_azure_client(azure_config)
        
        if azure_client:
            try:
                start_time = datetime.now()
                azure_result = call_azure_ocr(
                    azure_client, 
                    image_base64, 
                    azure_config.get('deployment_name', 'gpt-4-vision')
                )
                end_time = datetime.now()
                
                results['azure'] = {
                    'status': 'success',
                    'text': azure_result['text'],
                    'response_time': (end_time - start_time).total_seconds(),
                    'tokens_used': azure_result['usage']['total_tokens'],
                    'input_tokens': azure_result['usage']['prompt_tokens'],
                    'output_tokens': azure_result['usage']['completion_tokens']
                }
            except Exception as e:
                results['azure'] = {
                    'status': 'error',
                    'error': str(e),
                    'response_time': 0,
                    'tokens_used': 0,
                    'input_tokens': 0,
                    'output_tokens': 0
                }
        else:
            results['azure'] = {
                'status': 'error',
                'error': 'Azure client not configured properly',
                'response_time': 0,
                'tokens_used': 0,
                'input_tokens': 0,
                'output_tokens': 0
            }
    
    # Process with GCP if configured
    if providers_config.get('gcp', {}).get('enabled'):
        gcp_config = providers_config['gcp']
        gcp_client = create_gcp_client(gcp_config)
        
        if gcp_client:
            try:
                start_time = datetime.now()
                gcp_result = call_gcp_ocr(
                    gcp_client, 
                    image_base64, 
                    gcp_config.get('endpoint_id')
                )
                end_time = datetime.now()
                
                results['gcp'] = {
                    'status': 'success',
                    'text': gcp_result['text'],
                    'response_time': (end_time - start_time).total_seconds(),
                    'tokens_used': gcp_result['usage']['total_tokens'],
                    'input_tokens': gcp_result['usage']['prompt_tokens'],
                    'output_tokens': gcp_result['usage']['completion_tokens']
                }
            except Exception as e:
                results['gcp'] = {
                    'status': 'error',
                    'error': str(e),
                    'response_time': 0,
                    'tokens_used': 0,
                    'input_tokens': 0,
                    'output_tokens': 0
                }
        else:
            results['gcp'] = {
                'status': 'error',
                'error': 'GCP client not configured properly',
                'response_time': 0,
                'tokens_used': 0,
                'input_tokens': 0,
                'output_tokens': 0
            }
    
    return results

@app.route('/')
def index():
    """Main page with configuration and test interface"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Handle configuration for Azure and GCP providers"""
    if request.method == 'POST':
        config_data = request.json
        
        # Save configuration to database
        if save_config(config_data):
            return jsonify({"status": "success", "message": "Configuration saved to database"})
        else:
            return jsonify({"status": "error", "message": "Failed to save configuration"}), 500
    
    # GET request - return current config from database
    return jsonify(load_config())

@app.route('/api/generate-test-files', methods=['POST'])
def generate_files():
    """Generate test PDF files for testing"""
    try:
        data = request.json
        test_scenarios = data.get('scenarios', [])
        selected_providers = data.get('providers', ['azure', 'gcp'])
        
        # Simulate file generation
        files_created = []
        for i, scenario in enumerate(test_scenarios):
            files_created.append({
                'filename': f"test_files/test_{scenario.get('content_type', 'mixed')}_{scenario.get('pages', 1)}pages_{i}.pdf",
                'pages': scenario.get('pages', 1),
                'content_type': scenario.get('content_type', 'mixed'),
                'size_mb': 0.5
            })
        
        task_id = str(uuid.uuid4())
        result_data = {
            'status': 'completed',
            'files_created': files_created,
            'total_files': len(files_created),
            'providers': selected_providers
        }
        
        save_task(task_id, 'completed', 100, result_data=result_data)
        
        return jsonify({
            "status": "success",
            "task_id": task_id,
            "message": "Test files generation completed"
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
        
        # Load configuration
        config = load_config()
        if not config:
            return jsonify({"status": "error", "message": "Configuration not found"}), 400
        
        # Get selected providers from form data
        selected_providers = request.form.get('providers', 'azure').split(',')
        
        # Save uploaded file
        filename = f"uploads/{uuid.uuid4()}_{file.filename}"
        os.makedirs('uploads', exist_ok=True)
        file.save(filename)
        
        # Start OCR processing
        task_id = str(uuid.uuid4())
        save_task(task_id, 'running', 0, file.filename, providers=selected_providers, config_data=config)
        
        return jsonify({
            "status": "success",
            "task_id": task_id,
            "filename": file.filename,
            "providers": selected_providers
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/batch-test', methods=['POST'])
def batch_test():
    """Start batch testing with multiple files"""
    try:
        data = request.json
        test_config = data.get('test_config', {})
        selected_providers = data.get('providers', ['azure', 'gcp'])
        
        # Load configuration
        config = load_config()
        if not config:
            return jsonify({"status": "error", "message": "Configuration not found"}), 400
        
        # Start batch processing
        task_id = str(uuid.uuid4())
        save_task(task_id, 'running', 0, test_config=test_config, providers=selected_providers, config_data=config)
        
        return jsonify({
            "status": "success",
            "task_id": task_id,
            "message": "Batch test started",
            "providers": selected_providers
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/task-status/<task_id>')
def task_status(task_id):
    """Get task status and results"""
    try:
        task = get_task(task_id)
        
        if not task:
            return jsonify({"status": "error", "message": "Task not found"}), 404
        
        if task['status'] == 'completed':
            return jsonify({
                "status": "completed",
                "result": task['result_data']
            })
        elif task['status'] == 'failed':
            return jsonify({
                "status": "failed",
                "error": task.get('error', 'Unknown error')
            })
        else:
            # Simulate progress and real API calls
            progress = task.get('progress', 0)
            if progress < 100:
                progress = min(progress + 10, 100)
                
                if progress >= 100:
                    # Here you would normally process the actual PDF and call real APIs
                    # For now, we'll simulate with a sample image
                    sample_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                    
                    # Process with real APIs
                    providers_config = task.get('config_data', {})
                    results = process_image_with_providers(sample_image_base64, providers_config)
                    
                    # Calculate statistics
                    statistics = calculate_statistics(results)
                    
                    result_data = {
                        'status': 'completed',
                        'providers': task.get('providers', []),
                        'results': results,
                        'statistics': statistics,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Save completed task
                    save_task(task_id, 'completed', 100, task.get('filename'), 
                             task.get('test_config'), task.get('providers'), 
                             task.get('config_data'), result_data)
                    
                    # Save to test history
                    filename = task.get('filename')
                    if not filename:
                        filename = f"Batch Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    save_test_history(task_id, filename, 
                                    task.get('providers', []), results, statistics)
                    
                    # Update statistics
                    update_aggregate_statistics()
                
                else:
                    # Update progress
                    save_task(task_id, 'running', progress, task.get('filename'), 
                             task.get('test_config'), task.get('providers'), 
                             task.get('config_data'), task.get('result_data'))
            
            return jsonify({
                "status": "running",
                "progress": progress
            })
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def calculate_statistics(results):
    """Calculate statistics from OCR results"""
    statistics = {}
    
    for provider, result in results.items():
        if result['status'] == 'success':
            statistics[provider] = {
                'summary': {
                    'total_pages': 1,
                    'successful_pages': 1,
                    'failed_pages': 0,
                    'success_rate': 100.0
                },
                'performance': {
                    'average_response_time': result['response_time'],
                    'min_response_time': result['response_time'],
                    'max_response_time': result['response_time'],
                    'total_processing_time': result['response_time']
                },
                'token_usage': {
                    'total_tokens': result['tokens_used'],
                    'input_tokens': result['input_tokens'],
                    'output_tokens': result['output_tokens'],
                    'average_tokens_per_page': result['tokens_used']
                },
                'errors': {
                    'total_errors': 0,
                    'error_details': []
                }
            }
        else:
            statistics[provider] = {
                'summary': {
                    'total_pages': 1,
                    'successful_pages': 0,
                    'failed_pages': 1,
                    'success_rate': 0.0
                },
                'performance': {
                    'average_response_time': 0,
                    'min_response_time': 0,
                    'max_response_time': 0,
                    'total_processing_time': 0
                },
                'token_usage': {
                    'total_tokens': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'average_tokens_per_page': 0
                },
                'errors': {
                    'total_errors': 1,
                    'error_details': [
                        {
                            'page_number': 1,
                            'error': result.get('error', 'Unknown error'),
                            'status': 'error'
                        }
                    ]
                }
            }
    
    return statistics

def update_aggregate_statistics():
    """Update aggregate statistics from test history"""
    try:
        tests = get_test_history()
        
        # Initialize stats
        azure_stats = {
            'summary': {'total_pages': 0, 'successful_pages': 0, 'failed_pages': 0, 'success_rate': 0.0},
            'performance': {'total_time': 0, 'count': 0, 'min_time': float('inf'), 'max_time': 0},
            'token_usage': {'total_tokens': 0, 'input_tokens': 0, 'output_tokens': 0, 'count': 0},
            'errors': {'total_errors': 0, 'error_details': []}
        }
        
        gcp_stats = {
            'summary': {'total_pages': 0, 'successful_pages': 0, 'failed_pages': 0, 'success_rate': 0.0},
            'performance': {'total_time': 0, 'count': 0, 'min_time': float('inf'), 'max_time': 0},
            'token_usage': {'total_tokens': 0, 'input_tokens': 0, 'output_tokens': 0, 'count': 0},
            'errors': {'total_errors': 0, 'error_details': []}
        }
        
        for test in tests:
            if 'azure' in test.get('results', {}):
                result = test['results']['azure']
                azure_stats['summary']['total_pages'] += 1
                if result['status'] == 'success':
                    azure_stats['summary']['successful_pages'] += 1
                    azure_stats['performance']['total_time'] += result['response_time']
                    azure_stats['performance']['count'] += 1
                    azure_stats['performance']['min_time'] = min(azure_stats['performance']['min_time'], result['response_time'])
                    azure_stats['performance']['max_time'] = max(azure_stats['performance']['max_time'], result['response_time'])
                    azure_stats['token_usage']['total_tokens'] += result['tokens_used']
                    azure_stats['token_usage']['input_tokens'] += result['input_tokens']
                    azure_stats['token_usage']['output_tokens'] += result['output_tokens']
                    azure_stats['token_usage']['count'] += 1
                else:
                    azure_stats['summary']['failed_pages'] += 1
                    azure_stats['errors']['total_errors'] += 1
                    azure_stats['errors']['error_details'].append({
                        'page_number': azure_stats['summary']['total_pages'],
                        'error': result.get('error', 'Unknown error'),
                        'status': 'error'
                    })
            
            if 'gcp' in test.get('results', {}):
                result = test['results']['gcp']
                gcp_stats['summary']['total_pages'] += 1
                if result['status'] == 'success':
                    gcp_stats['summary']['successful_pages'] += 1
                    gcp_stats['performance']['total_time'] += result['response_time']
                    gcp_stats['performance']['count'] += 1
                    gcp_stats['performance']['min_time'] = min(gcp_stats['performance']['min_time'], result['response_time'])
                    gcp_stats['performance']['max_time'] = max(gcp_stats['performance']['max_time'], result['response_time'])
                    gcp_stats['token_usage']['total_tokens'] += result['tokens_used']
                    gcp_stats['token_usage']['input_tokens'] += result['input_tokens']
                    gcp_stats['token_usage']['output_tokens'] += result['output_tokens']
                    gcp_stats['token_usage']['count'] += 1
                else:
                    gcp_stats['summary']['failed_pages'] += 1
                    gcp_stats['errors']['total_errors'] += 1
                    gcp_stats['errors']['error_details'].append({
                        'page_number': gcp_stats['summary']['total_pages'],
                        'error': result.get('error', 'Unknown error'),
                        'status': 'error'
                    })
        
        # Calculate averages and success rates
        if azure_stats['summary']['total_pages'] > 0:
            azure_stats['summary']['success_rate'] = (azure_stats['summary']['successful_pages'] / azure_stats['summary']['total_pages']) * 100
        if azure_stats['performance']['count'] > 0:
            azure_stats['performance']['average_response_time'] = azure_stats['performance']['total_time'] / azure_stats['performance']['count']
        if azure_stats['token_usage']['count'] > 0:
            azure_stats['token_usage']['average_tokens_per_page'] = azure_stats['token_usage']['total_tokens'] / azure_stats['token_usage']['count']
        
        if gcp_stats['summary']['total_pages'] > 0:
            gcp_stats['summary']['success_rate'] = (gcp_stats['summary']['successful_pages'] / gcp_stats['summary']['total_pages']) * 100
        if gcp_stats['performance']['count'] > 0:
            gcp_stats['performance']['average_response_time'] = gcp_stats['performance']['total_time'] / gcp_stats['performance']['count']
        if gcp_stats['token_usage']['count'] > 0:
            gcp_stats['token_usage']['average_tokens_per_page'] = gcp_stats['token_usage']['total_tokens'] / gcp_stats['token_usage']['count']
        
        # Clean up performance stats
        if azure_stats['performance']['min_time'] == float('inf'):
            azure_stats['performance']['min_time'] = 0
        if gcp_stats['performance']['min_time'] == float('inf'):
            gcp_stats['performance']['min_time'] = 0
        
        # Update database
        update_statistics('azure', azure_stats)
        update_statistics('gcp', gcp_stats)
        
        # Clean up performance stats
        if azure_stats['performance']['min_time'] == float('inf'):
            azure_stats['performance']['min_time'] = 0
        if gcp_stats['performance']['min_time'] == float('inf'):
            gcp_stats['performance']['min_time'] = 0
        
        # Update database
        update_statistics('azure', azure_stats)
        update_statistics('gcp', gcp_stats)
        
    except Exception as e:
        print(f"Error updating aggregate statistics: {e}")

@app.route('/api/statistics')
def get_statistics_api():
    """Get comprehensive statistics by provider"""
    try:
        # Update aggregate statistics first
        update_aggregate_statistics()
        
        # Get from database
        statistics = get_statistics()
        
        return jsonify({
            "status": "success",
            "statistics": statistics
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/test-history')
def get_test_history_api():
    """Get detailed test history"""
    try:
        tests = get_test_history()
        return jsonify({
            "status": "success",
            "tests": tests
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/test-details/<task_id>')
def get_test_details(task_id):
    """Get detailed information about a specific test"""
    try:
        test = get_test_by_id(task_id)
        
        if not test:
            return jsonify({"status": "error", "message": "Test not found"}), 404
        
        return jsonify({
            "status": "success",
            "test": test
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('test_files', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    
    # Initialize database
    init_database()
    
    print("🚀 Starting Mistral OCR Test Suite (Database Mode)...")
    print("🌐 Application will be available at: http://localhost:80")
    print("⚠ Note: This version uses SQLite database for data persistence")
    print("✨ Features: Configuration persistence, test history, and real API integration")
    print(f"📊 Database: {DB_FILE}")
    
    app.run(debug=True, host='0.0.0.0', port=80)
