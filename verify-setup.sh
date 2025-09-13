#!/bin/bash

# Verification script for Neural Control Hub setup
# This script verifies that the frontend and backend are properly connected

echo "🔍 Verifying Neural Control Hub Setup"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $2 -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if required files exist
echo "📁 Checking required files..."

files_to_check=(
    "controller.py"
    "client.py"
    "agent-controller ui/package.json"
    "agent-controller ui/src/services/api.ts"
    "agent-controller ui/src/services/websocket.ts"
    "agent-controller ui/.env"
    "agent-controller ui/vite.config.ts"
    "client.env"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        print_status "File exists: $file" 0
    else
        print_status "File missing: $file" 1
    fi
done

# Check if Python dependencies are available
echo ""
echo "🐍 Checking Python environment..."
if command -v python3 &> /dev/null; then
    print_status "Python3 is available" 0
    python3 --version
else
    print_status "Python3 not found" 1
fi

# Check if Node.js dependencies are available
echo ""
echo "📦 Checking Node.js environment..."
if command -v node &> /dev/null; then
    print_status "Node.js is available" 0
    node --version
    if command -v npm &> /dev/null; then
        print_status "npm is available" 0
        npm --version
    else
        print_status "npm not found" 1
    fi
else
    print_status "Node.js not found" 1
fi

# Check if frontend dependencies are installed
echo ""
echo "📦 Checking frontend dependencies..."
if [ -d "agent-controller ui/node_modules" ]; then
    print_status "Frontend dependencies installed" 0
else
    print_status "Frontend dependencies not installed" 1
    print_warning "Run: cd 'agent-controller ui' && npm install"
fi

# Check client configuration
echo ""
echo "🤖 Checking client configuration..."
if [ -f "client.env" ]; then
    if grep -q "FIXED_SERVER_URL=http://localhost:8080" "client.env"; then
        print_status "Client configured for local controller" 0
    else
        print_status "Client not configured for local controller" 1
    fi
else
    print_status "Client environment file missing" 1
fi

# Check if Python dependencies are installed
echo ""
echo "🐍 Checking Python dependencies..."
if [ -f "requirements.txt" ]; then
    if python3 -c "import flask, flask_cors, flask_socketio" 2>/dev/null; then
        print_status "Python dependencies installed" 0
    else
        print_status "Python dependencies not installed" 1
        print_warning "Run: pip3 install -r requirements.txt"
    fi
else
    print_warning "requirements.txt not found"
fi

# Check environment configuration
echo ""
echo "⚙️  Checking environment configuration..."

if [ -f "agent-controller ui/.env" ]; then
    if grep -q "VITE_API_URL" "agent-controller ui/.env"; then
        print_status "Frontend environment configured" 0
    else
        print_status "Frontend environment not configured" 1
    fi
else
    print_status "Frontend .env file missing" 1
fi

# Check CORS configuration
echo ""
echo "🌐 Checking CORS configuration..."
if grep -q "localhost:3000" "controller.py"; then
    print_status "CORS configured for frontend" 0
else
    print_status "CORS not configured for frontend" 1
fi

# Check if ports are available
echo ""
echo "🔌 Checking port availability..."

# Check port 8080 (backend)
if netstat -tuln 2>/dev/null | grep -q ":8080 "; then
    print_warning "Port 8080 is in use (backend might already be running)"
else
    print_status "Port 8080 is available" 0
fi

# Check port 3000 (frontend)
if netstat -tuln 2>/dev/null | grep -q ":3000 "; then
    print_warning "Port 3000 is in use (frontend might already be running)"
else
    print_status "Port 3000 is available" 0
fi

# Final summary
echo ""
echo "📊 Setup Verification Summary"
echo "============================="
echo ""
echo "To start the development environment:"
echo "  ./start-dev.sh"
echo ""
echo "To test the connection:"
echo "  python3 test-connection.py"
echo ""
echo "Frontend will be available at: http://localhost:3000"
echo "Backend API will be available at: http://localhost:8080"
echo ""
echo "For production deployment, see CONNECTION_SETUP.md"