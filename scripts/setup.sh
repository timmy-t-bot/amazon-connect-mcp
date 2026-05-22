#!/bin/bash
# Setup script for Amazon Connect MCP Server development

set -e

echo "Setting up Amazon Connect MCP Server development environment..."

# Check for Python 3.10+
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1-2)
if [ -z "$python_version" ]; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

# Check Python version (3.10+)
required_version="3.10"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "Error: Python 3.10+ required, found $python_version"
    exit 1
fi

echo "✓ Python $python_version detected"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "✓ Virtual environment ready"

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip

# Try to use uv if available
if command -v uv &> /dev/null; then
    echo "Using uv for fast package installation..."
    uv pip install -e ".[dev]"
else
    pip install -e ".[dev]"
fi

echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# AWS Configuration
AWS_REGION=us-east-1
# AWS_PROFILE=default
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=

# Connect Configuration
# CONNECT_INSTANCE_ID=your-instance-id
# CONNECT_INSTANCE_ALIAS=your-instance-alias

# API Bridge Configuration (optional)
# CONNECT_API_BRIDGE_ENABLED=false
# CONNECT_API_BRIDGE_URL=https://your-api.execute-api.region.amazonaws.com/prod
# CONNECT_API_BRIDGE_API_KEY=

# MCP Configuration
MCP_SERVER_NAME=amazon-connect-mcp
MCP_TRANSPORT=stdio
MCP_PORT=8000
EOF
    echo "✓ .env file created - please edit with your AWS credentials"
fi

# Run initial checks
echo ""
echo "Running initial checks..."
python -c "import amazon_connect_mcp; print('✓ Package imports successfully')"

echo ""
echo "================================================"
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your AWS credentials"
echo "2. Run tests: pytest"
echo "3. Run the server: python -m amazon_connect_mcp"
echo ""
echo "For MCP client configuration, see README.md"
echo "================================================"
