#!/bin/bash
# Validate Azure infrastructure before deploying

set -e

echo "🔍 Validating Azure Container Apps deployment..."
echo ""

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi
echo "✅ Azure CLI installed"

# Check login
if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure. Run: az login"
    exit 1
fi
echo "✅ Logged into Azure"

# Validate Bicep template
echo ""
echo "📝 Validating Bicep template..."
az bicep build --file infrastructure/main.bicep

if [ $? -eq 0 ]; then
    echo "✅ Bicep template is valid"
else
    echo "❌ Bicep template validation failed"
    exit 1
fi

# Check if resource group exists
echo ""
RG_NAME="ai-chat-pipeline-rg"
if az group show --name "$RG_NAME" &> /dev/null; then
    echo "⚠️  Resource group '$RG_NAME' already exists"
    echo "   Deployment will update existing resources"
else
    echo "ℹ️  Resource group '$RG_NAME' will be created on deployment"
fi

# Test parameters file (if exists)
if [ -f "infrastructure/parameters.filled.json" ]; then
    echo ""
    echo "📋 Checking parameters.filled.json..."
    
    # Validate JSON syntax
    if jq empty infrastructure/parameters.filled.json 2>/dev/null; then
        echo "✅ parameters.filled.json is valid JSON"
    else
        echo "❌ parameters.filled.json has invalid JSON syntax"
        exit 1
    fi
    
    # Check for placeholder values
    if grep -q "PASTE_YOUR" infrastructure/parameters.filled.json; then
        echo "⚠️  Found placeholder values in parameters.filled.json"
        echo "   Make sure to replace all 'PASTE_YOUR_*' values"
    fi
fi

echo ""
echo "🎯 Validation complete! Ready to deploy."
echo ""
echo "Deploy with:"
echo "  Option 1 (GitHub Actions): Push to main branch"
echo "  Option 2 (Azure CLI):"
echo "    az deployment group create \\"
echo "      --resource-group ai-chat-pipeline-rg \\"
echo "      --template-file infrastructure/main.bicep \\"
echo "      --parameters @infrastructure/parameters.filled.json"
