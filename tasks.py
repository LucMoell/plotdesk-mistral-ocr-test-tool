import os
import json
import time
import asyncio
import aiohttp
from datetime import datetime
from celery import Celery
import redis
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import PyPDF2
from PIL import Image
import io
import base64
from openai import AzureOpenAI
from google.cloud import aiplatform
from google.auth import credentials
import numpy as np
import pandas as pd

# Initialize Celery
celery = Celery('mistral_ocr_test')
celery.conf.update({
    'broker_url': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    'result_backend': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
})

# Initialize Redis
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

class OCRProvider:
    """Base class for OCR providers"""
    
    def __init__(self, config):
        self.config = config
        self.metrics = {
            'total_tokens': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'requests_made': 0,
            'errors': [],
            'response_times': [],
            'start_time': time.time()
        }
    
    async def process_page(self, page_image, page_number):
        """Process a single page - to be implemented by subclasses"""
        raise NotImplementedError
    
    def get_metrics(self):
        """Get current metrics"""
        self.metrics['total_time'] = time.time() - self.metrics['start_time']
        return self.metrics

class AzureMistralProvider(OCRProvider):
    """Azure OpenAI Mistral provider"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = AzureOpenAI(
            api_key=config['api_key'],
            api_version=config.get('api_version', '2024-02-15-preview'),
            azure_endpoint=config['endpoint']
        )
        self.deployment_name = config['deployment_name']
    
    async def process_page(self, page_image, page_number):
        """Process a single page with Azure Mistral"""
        start_time = time.time()
        
        try:
            # Convert image to base64
            img_buffer = io.BytesIO()
            page_image.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Prepare the request
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please extract all text from this image. Return only the extracted text without any additional formatting or explanations."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_str}"
                            }
                        }
                    ]
                }
            ]
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=4000,
                temperature=0.1
            )
            
            # Update metrics
            response_time = time.time() - start_time
            self.metrics['response_times'].append(response_time)
            self.metrics['requests_made'] += 1
            
            if hasattr(response.usage, 'prompt_tokens'):
                self.metrics['input_tokens'] += response.usage.prompt_tokens
            if hasattr(response.usage, 'completion_tokens'):
                self.metrics['output_tokens'] += response.usage.completion_tokens
            if hasattr(response.usage, 'total_tokens'):
                self.metrics['total_tokens'] += response.usage.total_tokens
            
            return {
                'page_number': page_number,
                'text': response.choices[0].message.content,
                'response_time': response_time,
                'tokens_used': getattr(response.usage, 'total_tokens', 0),
                'status': 'success'
            }
            
        except Exception as e:
            error_info = {
                'page_number': page_number,
                'error': str(e),
                'response_time': time.time() - start_time,
                'status': 'error'
            }
            self.metrics['errors'].append(error_info)
            return error_info

class GCPMistralProvider(OCRProvider):
    """GCP Mistral provider"""
    
    def __init__(self, config):
        super().__init__(self, config)
        
        # Initialize GCP client
        if 'service_account_path' in config:
            credentials_obj = credentials.Credentials.from_service_account_file(
                config['service_account_path']
            )
            aiplatform.init(credentials=credentials_obj)
        else:
            aiplatform.init()
        
        self.project_id = config['project_id']
        self.location = config.get('location', 'us-central1')
        self.endpoint_id = config['endpoint_id']
        
        # Get the endpoint
        self.endpoint = aiplatform.Endpoint(
            endpoint_name=f"projects/{self.project_id}/locations/{self.location}/endpoints/{self.endpoint_id}"
        )
    
    async def process_page(self, page_image, page_number):
        """Process a single page with GCP Mistral"""
        start_time = time.time()
        
        try:
            # Convert image to base64
            img_buffer = io.BytesIO()
            page_image.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Prepare the request
            request_data = {
                "instances": [
                    {
                        "prompt": "Please extract all text from this image. Return only the extracted text without any additional formatting or explanations.",
                        "image": img_str
                    }
                ]
            }
            
            # Make API call
            response = self.endpoint.predict(request_data)
            
            # Update metrics
            response_time = time.time() - start_time
            self.metrics['response_times'].append(response_time)
            self.metrics['requests_made'] += 1
            
            # Extract text from response (adjust based on actual GCP response format)
            text = response.predictions[0] if response.predictions else ""
            
            return {
                'page_number': page_number,
                'text': text,
                'response_time': response_time,
                'tokens_used': 0,  # GCP might not provide token info
                'status': 'success'
            }
            
        except Exception as e:
            error_info = {
                'page_number': page_number,
                'error': str(e),
                'response_time': time.time() - start_time,
                'status': 'error'
            }
            self.metrics['errors'].append(error_info)
            return error_info

def create_test_pdf(pages, filename, content_type="mixed"):
    """Create a test PDF with specified number of pages"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    for i in range(pages):
        # Add page number
        story.append(Paragraph(f"Page {i+1}", styles['Heading1']))
        story.append(Spacer(1, 12))
        
        if content_type == "text_heavy":
            # Add lots of text
            for j in range(20):
                story.append(Paragraph(
                    f"This is paragraph {j+1} on page {i+1}. " * 5,
                    styles['Normal']
                ))
        elif content_type == "image_heavy":
            # Add text with image descriptions
            story.append(Paragraph(
                f"Page {i+1} contains an image with detailed text content. " * 10,
                styles['Normal']
            ))
        else:  # mixed
            # Add mixed content
            story.append(Paragraph(
                f"Page {i+1} contains mixed content with text and images. " * 8,
                styles['Normal']
            ))
        
        story.append(Spacer(1, 12))
    
    doc.build(story)

@celery.task(bind=True)
def generate_test_files(self, scenarios):
    """Generate test PDF files for different scenarios"""
    try:
        files_created = []
        
        for scenario in scenarios:
            pages = scenario.get('pages', 1)
            content_type = scenario.get('content_type', 'mixed')
            filename = f"test_files/test_{content_type}_{pages}pages_{int(time.time())}.pdf"
            
            create_test_pdf(pages, filename, content_type)
            files_created.append({
                'filename': filename,
                'pages': pages,
                'content_type': content_type,
                'size_mb': os.path.getsize(filename) / (1024 * 1024)
            })
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'progress': len(files_created) / len(scenarios) * 100}
            )
        
        return {
            'status': 'completed',
            'files_created': files_created,
            'total_files': len(files_created)
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

@celery.task(bind=True)
def process_ocr_task(self, file_path=None, config=None, test_config=None):
    """Process OCR task with comprehensive metrics tracking"""
    try:
        # Initialize provider based on config
        if config.get('azure', {}).get('enabled'):
            provider = AzureMistralProvider(config['azure'])
        elif config.get('gcp', {}).get('enabled'):
            provider = GCPMistralProvider(config['gcp'])
        else:
            raise ValueError("No provider configured")
        
        results = []
        total_pages = 0
        
        if test_config:
            # Batch testing mode
            test_files = test_config.get('files', [])
            total_files = len(test_files)
            
            for i, test_file in enumerate(test_files):
                file_results = await process_single_file(test_file, provider, self)
                results.extend(file_results)
                
                # Update progress
                progress = (i + 1) / total_files * 100
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': progress,
                        'current_file': test_file,
                        'files_processed': i + 1,
                        'total_files': total_files
                    }
                )
        else:
            # Single file mode
            results = await process_single_file(file_path, provider, self)
        
        # Calculate comprehensive statistics
        stats = calculate_statistics(results, provider.get_metrics())
        
        # Store statistics in Redis
        session_id = config.get('session_id', 'default')
        redis_client.setex(
            f"stats:{session_id}:latest",
            3600,
            json.dumps(stats)
        )
        
        return {
            'status': 'completed',
            'results': results,
            'statistics': stats,
            'total_pages': len(results)
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

async def process_single_file(file_path, provider, task):
    """Process a single PDF file"""
    results = []
    
    try:
        # Open PDF and extract pages
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                # Convert PDF page to image
                page = pdf_reader.pages[page_num]
                
                # For simplicity, we'll create a text representation
                # In a real implementation, you'd convert PDF pages to images
                page_text = page.extract_text()
                
                # Process with OCR provider
                result = await provider.process_page(page_text, page_num + 1)
                results.append(result)
                
                # Update task progress
                progress = (page_num + 1) / total_pages * 100
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': progress,
                        'current_page': page_num + 1,
                        'total_pages': total_pages
                    }
                )
                
                # Add small delay to avoid rate limits
                await asyncio.sleep(0.1)
    
    except Exception as e:
        results.append({
            'page_number': 0,
            'error': str(e),
            'status': 'error'
        })
    
    return results

def calculate_statistics(results, provider_metrics):
    """Calculate comprehensive statistics from results and metrics"""
    successful_results = [r for r in results if r.get('status') == 'success']
    error_results = [r for r in results if r.get('status') == 'error']
    
    stats = {
        'summary': {
            'total_pages': len(results),
            'successful_pages': len(successful_results),
            'failed_pages': len(error_results),
            'success_rate': len(successful_results) / len(results) * 100 if results else 0
        },
        'performance': {
            'average_response_time': np.mean([r.get('response_time', 0) for r in successful_results]) if successful_results else 0,
            'min_response_time': min([r.get('response_time', 0) for r in successful_results]) if successful_results else 0,
            'max_response_time': max([r.get('response_time', 0) for r in successful_results]) if successful_results else 0,
            'total_processing_time': provider_metrics.get('total_time', 0)
        },
        'token_usage': {
            'total_tokens': provider_metrics.get('total_tokens', 0),
            'input_tokens': provider_metrics.get('input_tokens', 0),
            'output_tokens': provider_metrics.get('output_tokens', 0),
            'average_tokens_per_page': provider_metrics.get('total_tokens', 0) / len(successful_results) if successful_results else 0
        },
        'errors': {
            'total_errors': len(error_results),
            'error_details': error_results
        },
        'provider_metrics': provider_metrics
    }
    
    return stats
