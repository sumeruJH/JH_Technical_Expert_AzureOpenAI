#!/usr/bin/env python3
"""
Cloud-Optimized James Hardie Technical Expert System
Azure-native deployment with minimal dependencies and maximum performance.

Author: GitHub Copilot
Date: July 24, 2025
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Minimal imports for cloud deployment
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Azure OpenAI (primary)
try:
    from openai import AzureOpenAI
    from azure.identity import DefaultAzureCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# Standard OpenAI (fallback)
try:
    import openai
    STANDARD_OPENAI_AVAILABLE = True
except ImportError:
    STANDARD_OPENAI_AVAILABLE = False

# Configure logging for cloud
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
CORS(app)

# Global variables for AI clients
azure_client = None
openai_client = None
request_count = 0
error_count = 0

def initialize_ai_clients():
    """Initialize AI clients with cloud-optimized configuration"""
    global azure_client, openai_client
    
    # Azure OpenAI (preferred for cloud)
    if AZURE_AVAILABLE:
        try:
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            api_key = os.getenv('AZURE_OPENAI_KEY')
            
            if endpoint:
                if api_key:
                    # Use API key authentication
                    azure_client = AzureOpenAI(
                        api_key=api_key,
                        api_version="2024-02-01",
                        azure_endpoint=endpoint
                    )
                    logger.info("✅ Azure OpenAI initialized with API key")
                else:
                    # Use managed identity (preferred for cloud)
                    try:
                        credential = DefaultAzureCredential()
                        azure_client = AzureOpenAI(
                            azure_ad_token_provider=credential,
                            api_version="2024-02-01",
                            azure_endpoint=endpoint
                        )
                        logger.info("✅ Azure OpenAI initialized with managed identity")
                    except Exception as e:
                        logger.warning(f"Managed identity failed: {e}")
        except Exception as e:
            logger.error(f"Azure OpenAI initialization failed: {e}")
    
    # Standard OpenAI (fallback)
    if STANDARD_OPENAI_AVAILABLE:
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                openai_client = openai.OpenAI(api_key=openai_key)
                logger.info("✅ Standard OpenAI initialized as fallback")
        except Exception as e:
            logger.error(f"Standard OpenAI initialization failed: {e}")
    
    if not azure_client and not openai_client:
        logger.error("❌ No AI clients available")

def generate_response(messages: List[Dict], max_tokens: int = 1500) -> Dict[str, Any]:
    """Generate response using available AI client"""
    global request_count, error_count
    
    request_count += 1
    start_time = time.time()
    
    # Try Azure OpenAI first
    if azure_client:
        try:
            response = azure_client.chat.completions.create(
                model=os.getenv('AZURE_OPENAI_CHAT_MODEL', 'gpt-4'),
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return {
                'content': response.choices[0].message.content,
                'provider': 'azure_openai',
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'response_time': time.time() - start_time
            }
        except Exception as e:
            logger.error(f"Azure OpenAI error: {e}")
            error_count += 1
    
    # Fallback to standard OpenAI
    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective model
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return {
                'content': response.choices[0].message.content,
                'provider': 'openai',
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'response_time': time.time() - start_time
            }
        except Exception as e:
            logger.error(f"Standard OpenAI error: {e}")
            error_count += 1
    
    # No AI available
    error_count += 1
    return {
        'content': "I'm temporarily unable to process your request. Please try again later.",
        'provider': 'none',
        'error': 'No AI service available',
        'response_time': time.time() - start_time
    }

# Simple in-memory knowledge base for quick responses
JAMES_HARDIE_KNOWLEDGE = {
    'hardieplank': {
        'description': 'HardiePlank® lap siding is a fiber cement siding that combines the look of wood with superior durability and performance.',
        'installation': [
            'Start with proper wall preparation and moisture barrier',
            'Install starter strip at bottom of wall',
            'Cut siding with appropriate tools (circular saw with carbide blade)',
            'Maintain 1/4" gap at all joints and penetrations',
            'Use corrosion-resistant fasteners (stainless steel or galvanized)',
            'Pre-drill holes for nails to prevent cracking'
        ],
        'tools': ['Circular saw with carbide blade', 'Drill', 'Level', 'Chalk line', 'Safety equipment'],
        'fasteners': 'Use 6d or 8d galvanized or stainless steel siding nails'
    },
    'hardietrim': {
        'description': 'HardieTrim® boards provide clean lines and architectural detail with the durability of fiber cement.',
        'installation': [
            'Cut with carbide-tipped blade',
            'Pre-drill nail holes',
            'Maintain proper clearances from grade and rooflines',
            'Seal all cut edges with approved primer/paint'
        ]
    },
    'installation_general': [
        'Always follow local building codes',
        'Maintain proper clearances (6" from grade, 2" from rooflines)',
        'Use proper flashing and weather barriers',
        'Prime and paint all cut edges within 60 days',
        'Store materials flat and off the ground'
    ]
}

def get_quick_answer(query: str) -> Optional[str]:
    """Get quick answer from knowledge base"""
    query_lower = query.lower()
    
    if 'hardieplank' in query_lower:
        if 'install' in query_lower:
            steps = JAMES_HARDIE_KNOWLEDGE['hardieplank']['installation']
            return f"HardiePlank installation key steps:\n" + "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
        elif 'tool' in query_lower:
            tools = JAMES_HARDIE_KNOWLEDGE['hardieplank']['tools']
            return f"Tools needed for HardiePlank installation: {', '.join(tools)}"
        else:
            return JAMES_HARDIE_KNOWLEDGE['hardieplank']['description']
    
    elif 'hardietrim' in query_lower:
        return JAMES_HARDIE_KNOWLEDGE['hardietrim']['description']
    
    elif any(word in query_lower for word in ['install', 'installation']):
        steps = JAMES_HARDIE_KNOWLEDGE['installation_general']
        return "General James Hardie installation guidelines:\n" + "\n".join(f"• {step}" for step in steps)
    
    return None

# Routes
@app.route('/')
def home():
    """Home page with simple interface"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>James Hardie Technical Expert</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            input[type="text"] { width: 70%; padding: 10px; font-size: 16px; }
            button { padding: 10px 20px; font-size: 16px; background: #007acc; color: white; border: none; cursor: pointer; }
            .response { margin-top: 20px; padding: 20px; background: #f5f5f5; border-radius: 5px; }
            .status { margin: 10px 0; padding: 10px; background: #e7f3ff; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 James Hardie Technical Expert</h1>
            <p>Ask questions about James Hardie products, installation, and troubleshooting.</p>
            
            <div>
                <input type="text" id="query" placeholder="How do I install HardiePlank siding?" />
                <button onclick="askQuestion()">Ask</button>
            </div>
            
            <div class="status" id="status">Ready</div>
            <div class="response" id="response" style="display:none;"></div>
            
            <hr style="margin: 40px 0;">
            
            <h3>API Endpoints:</h3>
            <ul>
                <li><strong>POST /api/query</strong> - Ask technical questions</li>
                <li><strong>GET /api/health</strong> - Health check</li>
                <li><strong>GET /api/metrics</strong> - Performance metrics</li>
            </ul>
            
            <h3>Quick Test:</h3>
            <button onclick="testAPI()">Test API</button>
        </div>
        
        <script>
            async function askQuestion() {
                const query = document.getElementById('query').value;
                if (!query) return;
                
                document.getElementById('status').innerText = 'Processing...';
                document.getElementById('response').style.display = 'none';
                
                try {
                    const response = await fetch('/api/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query })
                    });
                    
                    const data = await response.json();
                    
                    document.getElementById('status').innerText = 
                        `Response from ${data.provider || 'unknown'} in ${(data.response_time || 0).toFixed(2)}s`;
                    
                    document.getElementById('response').innerHTML = 
                        `<strong>Q:</strong> ${query}<br><br><strong>A:</strong> ${data.content || data.error}`;
                    document.getElementById('response').style.display = 'block';
                    
                } catch (error) {
                    document.getElementById('status').innerText = 'Error: ' + error.message;
                }
            }
            
            async function testAPI() {
                document.getElementById('status').innerText = 'Testing API...';
                
                try {
                    const response = await fetch('/api/health');
                    const data = await response.json();
                    
                    document.getElementById('status').innerText = 
                        `API Status: ${data.status} | Azure: ${data.azure_available} | OpenAI: ${data.openai_available}`;
                    
                } catch (error) {
                    document.getElementById('status').innerText = 'API Test Failed: ' + error.message;
                }
            }
            
            // Allow Enter key to submit
            document.getElementById('query').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') askQuestion();
            });
        </script>
    </body>
    </html>
    """
    return html

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'azure_available': azure_client is not None,
        'openai_available': openai_client is not None,
        'requests_processed': request_count,
        'error_count': error_count,
        'environment': os.getenv('ENVIRONMENT', 'unknown')
    })

@app.route('/api/metrics')
def metrics():
    """Performance metrics endpoint"""
    return jsonify({
        'requests_processed': request_count,
        'error_count': error_count,
        'error_rate': error_count / max(request_count, 1),
        'uptime': time.time(),
        'azure_configured': azure_client is not None,
        'openai_configured': openai_client is not None
    })

@app.route('/api/query', methods=['POST'])
def api_query():
    """Main query endpoint"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        user_query = data['query'].strip()
        if not user_query:
            return jsonify({'error': 'Empty query'}), 400
        
        # Try quick answer first
        quick_answer = get_quick_answer(user_query)
        if quick_answer:
            return jsonify({
                'content': quick_answer,
                'provider': 'knowledge_base',
                'response_time': 0.01,
                'cached': True
            })
        
        # Use AI for complex queries
        messages = [
            {
                "role": "system",
                "content": """You are a James Hardie technical expert assistant. Provide accurate, helpful information about James Hardie products including:

- HardiePlank® lap siding
- HardieTrim® boards  
- HardiePanel® vertical siding
- HardieSoffit® panels

Focus on:
- Installation procedures and best practices
- Product specifications and compatibility
- Tools and fasteners required
- Troubleshooting common issues
- Building code compliance
- Safety considerations

Keep responses concise but comprehensive. Always recommend following local building codes and manufacturer instructions."""
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
        
        response = generate_response(messages)
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test_endpoints():
    """Test multiple queries for validation"""
    test_queries = [
        "What is HardiePlank siding?",
        "How do I install HardiePlank?",
        "What tools do I need for installation?",
        "What are the fastener requirements?"
    ]
    
    results = []
    for query in test_queries:
        try:
            quick_answer = get_quick_answer(query)
            if quick_answer:
                results.append({
                    'query': query,
                    'response': quick_answer[:100] + '...',
                    'provider': 'knowledge_base',
                    'status': 'success'
                })
            else:
                messages = [
                    {"role": "system", "content": "You are a James Hardie technical expert."},
                    {"role": "user", "content": query}
                ]
                response = generate_response(messages, max_tokens=100)
                results.append({
                    'query': query,
                    'response': response['content'][:100] + '...',
                    'provider': response['provider'],
                    'status': 'success' if 'error' not in response else 'failed'
                })
        except Exception as e:
            results.append({
                'query': query,
                'error': str(e),
                'status': 'failed'
            })
    
    return jsonify({
        'test_results': results,
        'total_tests': len(test_queries),
        'passed': len([r for r in results if r['status'] == 'success'])
    })

# Initialize AI clients on startup
initialize_ai_clients()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"🚀 Starting James Hardie Technical Expert")
    logger.info(f"Port: {port}")
    logger.info(f"Debug: {debug}")
    logger.info(f"Azure OpenAI: {'✅' if azure_client else '❌'}")
    logger.info(f"Standard OpenAI: {'✅' if openai_client else '❌'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
