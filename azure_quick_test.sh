#!/bin/bash
# One-Click Azure OpenAI Testing Script
# Run this in Azure Cloud Shell for immediate testing
#
# Usage: curl -s https://raw.githubusercontent.com/your-repo/deploy.sh | bash
# Or: ./azure_quick_test.sh
#
# Author: GitHub Copilot
# Date: July 24, 2025

set -e

echo "🚀 James Hardie Azure OpenAI Quick Test Deployment"
echo "=================================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Generate unique names
TIMESTAMP=$(date +%s)
RESOURCE_GROUP="hardie-test-${TIMESTAMP}"
OPENAI_NAME="hardie-openai-${TIMESTAMP}"
LOCATION="eastus"

log "Creating Azure resources..."
log "Resource Group: $RESOURCE_GROUP"
log "Location: $LOCATION"

# Step 1: Create Resource Group
log "Creating resource group..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --tags Project="James Hardie Test" Environment="Testing" || error "Failed to create resource group"

success "Resource group created"

# Step 2: Create Azure OpenAI Service
log "Creating Azure OpenAI service (this may take 2-3 minutes)..."
az cognitiveservices account create \
    --name "$OPENAI_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --kind "OpenAI" \
    --sku "S0" \
    --yes || error "Failed to create Azure OpenAI service"

success "Azure OpenAI service created"

# Step 3: Deploy GPT-4 Model
log "Deploying GPT-4 model..."
az cognitiveservices account deployment create \
    --name "$OPENAI_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --deployment-name "gpt-4" \
    --model-name "gpt-4" \
    --model-version "0613" \
    --model-format "OpenAI" \
    --scale-settings-scale-type "Standard" \
    --scale-settings-capacity 10 || error "Failed to deploy GPT-4 model"

success "GPT-4 model deployed"

# Step 4: Deploy Embedding Model
log "Deploying embedding model..."
az cognitiveservices account deployment create \
    --name "$OPENAI_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --deployment-name "text-embedding-ada-002" \
    --model-name "text-embedding-ada-002" \
    --model-version "2" \
    --model-format "OpenAI" \
    --scale-settings-scale-type "Standard" \
    --scale-settings-capacity 120 || warning "Embedding model deployment failed (optional)"

# Step 5: Get Credentials
log "Retrieving credentials..."
OPENAI_ENDPOINT=$(az cognitiveservices account show \
    --name "$OPENAI_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.endpoint" \
    --output tsv)

OPENAI_KEY=$(az cognitiveservices account keys list \
    --name "$OPENAI_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "key1" \
    --output tsv)

if [ -z "$OPENAI_ENDPOINT" ] || [ -z "$OPENAI_KEY" ]; then
    error "Failed to retrieve credentials"
fi

success "Credentials retrieved"

# Step 6: Test Azure OpenAI API
log "Testing Azure OpenAI API..."

# Test 1: Simple chat completion
echo ""
echo "🧪 Test 1: Basic Chat Completion"
echo "Query: 'What is James Hardie HardiePlank siding?'"

RESPONSE=$(curl -s -X POST \
    "$OPENAI_ENDPOINT/openai/deployments/gpt-4/chat/completions?api-version=2024-02-01" \
    -H "Content-Type: application/json" \
    -H "api-key: $OPENAI_KEY" \
    -d '{
        "messages": [
            {"role": "system", "content": "You are a helpful assistant specializing in James Hardie building products."},
            {"role": "user", "content": "What is James Hardie HardiePlank siding? Give me a brief 2-sentence explanation."}
        ],
        "max_tokens": 150,
        "temperature": 0.1
    }' 2>/dev/null)

if echo "$RESPONSE" | grep -q "choices"; then
    success "✅ Basic API test PASSED"
    echo "Response:"
    echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null || echo "$RESPONSE"
else
    error "Basic API test failed. Response: $RESPONSE"
fi

# Test 2: Technical installation query
echo ""
echo "🧪 Test 2: Technical Installation Query"
echo "Query: 'How do I install HardiePlank siding?'"

RESPONSE2=$(curl -s -X POST \
    "$OPENAI_ENDPOINT/openai/deployments/gpt-4/chat/completions?api-version=2024-02-01" \
    -H "Content-Type: application/json" \
    -H "api-key: $OPENAI_KEY" \
    -d '{
        "messages": [
            {"role": "system", "content": "You are a James Hardie technical expert. Provide accurate installation guidance."},
            {"role": "user", "content": "How do I install HardiePlank siding? List the 3 most important steps."}
        ],
        "max_tokens": 200,
        "temperature": 0.1
    }' 2>/dev/null)

if echo "$RESPONSE2" | grep -q "choices"; then
    success "✅ Technical query test PASSED"
    echo "Response:"
    echo "$RESPONSE2" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null || echo "$RESPONSE2"
else
    warning "Technical query test failed"
fi

# Test 3: Embedding test (if available)
echo ""
echo "🧪 Test 3: Embedding Generation"

EMBED_RESPONSE=$(curl -s -X POST \
    "$OPENAI_ENDPOINT/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-02-01" \
    -H "Content-Type: application/json" \
    -H "api-key: $OPENAI_KEY" \
    -d '{
        "input": "HardiePlank siding installation guide"
    }' 2>/dev/null)

if echo "$EMBED_RESPONSE" | grep -q "data"; then
    success "✅ Embedding test PASSED"
    EMBED_COUNT=$(echo "$EMBED_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['data'][0]['embedding']))" 2>/dev/null || echo "unknown")
    echo "Generated embedding with $EMBED_COUNT dimensions"
else
    warning "Embedding test failed (optional feature)"
fi

# Step 7: Create Simple Test App
echo ""
log "Creating simple test application..."

# Create a simple Flask app for testing
cat > test_app.py << 'EOF'
#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify
from openai import AzureOpenAI

app = Flask(__name__)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01", 
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

@app.route('/')
def home():
    return jsonify({
        "message": "James Hardie Technical Expert - Azure OpenAI Test",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "query": "/query (POST)",
            "test": "/test"
        }
    })

@app.route('/health')
def health():
    try:
        # Test Azure OpenAI connectivity
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        return jsonify({
            "status": "healthy",
            "azure_openai": "connected",
            "model": "gpt-4",
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "not_set")
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e)
        }), 500

@app.route('/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        user_query = data.get('query', 'How can I help you with James Hardie products?')
        
        messages = [
            {"role": "system", "content": "You are a James Hardie technical expert. Provide helpful, accurate information about James Hardie building products, installation, and troubleshooting."},
            {"role": "user", "content": user_query}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=500,
            temperature=0.1
        )
        
        return jsonify({
            "query": user_query,
            "response": response.choices[0].message.content,
            "model": "gpt-4",
            "provider": "azure_openai",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test')
def test():
    test_queries = [
        "What is HardiePlank siding?",
        "How do I install fiber cement siding?", 
        "What tools do I need for HardiePlank installation?",
        "What are the spacing requirements for HardiePlank?"
    ]
    
    results = []
    for query in test_queries:
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a James Hardie technical expert."},
                    {"role": "user", "content": query}
                ],
                max_tokens=100,
                temperature=0.1
            )
            results.append({
                "query": query,
                "response": response.choices[0].message.content[:200] + "...",
                "status": "success"
            })
        except Exception as e:
            results.append({
                "query": query, 
                "error": str(e),
                "status": "failed"
            })
    
    return jsonify({
        "test_results": results,
        "total_tests": len(test_queries),
        "passed": len([r for r in results if r.get("status") == "success"])
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
EOF

# Set environment variables for the app
export AZURE_OPENAI_ENDPOINT="$OPENAI_ENDPOINT"
export AZURE_OPENAI_KEY="$OPENAI_KEY"

log "Installing Python dependencies..."
pip install flask openai azure-identity --quiet

log "Starting test application on port 5000..."
echo ""
success "🎉 Azure OpenAI setup complete!"

echo ""
echo "=================================================="
echo "📋 DEPLOYMENT SUMMARY"
echo "=================================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Azure OpenAI Service: $OPENAI_NAME"
echo "Endpoint: $OPENAI_ENDPOINT"
echo "Location: $LOCATION"
echo ""
echo "🧪 TEST RESULTS:"
echo "✅ Azure OpenAI Service: Created"
echo "✅ GPT-4 Model: Deployed"
echo "✅ API Connectivity: Working"
echo "✅ Basic Query: Successful"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. Start the test app: python3 test_app.py"
echo "2. Test endpoints:"
echo "   - Health: curl http://localhost:5000/health"
echo "   - Query: curl -X POST http://localhost:5000/query -H 'Content-Type: application/json' -d '{\"query\":\"How do I install HardiePlank?\"}'"
echo "   - Test Suite: curl http://localhost:5000/test"
echo ""
echo "💰 COST INFO:"
echo "- Current setup costs ~$0.50-2.00 per hour when actively used"
echo "- GPT-4 tokens: $0.03 per 1K input tokens, $0.06 per 1K output tokens"
echo ""
echo "🧹 CLEANUP (when done testing):"
echo "   az group delete --name $RESOURCE_GROUP --yes --no-wait"
echo ""
echo "🔑 CREDENTIALS (save these for app deployment):"
echo "AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT"
echo "AZURE_OPENAI_KEY=$OPENAI_KEY"
echo "=================================================="

# Optional: Start the app automatically
read -p "Start the test application now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Starting test application..."
    echo "Access the app at: http://localhost:5000"
    echo "Press Ctrl+C to stop"
    python3 test_app.py
fi
