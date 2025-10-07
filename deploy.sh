#!/bin/bash

# Agent Controller Deployment Script
echo "🚀 Agent Controller Deployment Script"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "controller.py" ]; then
    echo "❌ Error: controller.py not found. Please run this script from the project root."
    exit 1
fi

# Check if UI v2.1 build exists
if [ ! -d "agent-controller ui v2.1/build" ]; then
    echo "❌ Error: UI v2.1 build directory not found."
    echo "Please ensure 'agent-controller ui v2.1/build/' exists with the built UI files."
    exit 1
fi

echo "✅ Project structure verified"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed or not in PATH"
    exit 1
fi

# Check git status
echo "📋 Checking git status..."
git status --porcelain

# Ask for confirmation
echo ""
echo "🔍 The following changes will be deployed:"
echo "   - Updated controller.py with UI v2.1 integration"
echo "   - Updated requirements-controller.txt"
echo "   - Updated render.yaml configuration"
echo "   - UI v2.1 build files"
echo ""
read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Add specific files only (safer than git add .)
echo "📦 Adding changes to git..."
git add controller.py
git add start-backend.py
git add requirements-controller.txt
git add render.yaml
git add "agent-controller ui v2.1/build/"
git add docker-compose.yml
git add simple-client.py
git add main.py
git add client.py
git add test-agent-registration.py
git add test_security.py
git add "agent-controller ui/src/components/Login.tsx"
git add "agent-controller ui/src/services/api.ts"
git add "agent-controller ui/src/services/websocket.ts"

# Commit changes
echo "💾 Committing changes..."
git commit -m "Security fixes and agent-controller UI v2.1 integration

- Fixed hardcoded password vulnerability (require ADMIN_PASSWORD env var)
- Enabled SSL verification in all Socket.IO clients
- Removed password exposure from frontend UI
- Added input validation and dangerous command blocking
- Added security headers (XSS, CSRF, CSP protection)
- Fixed threading race conditions with proper synchronization
- Improved error handling with specific exception types
- Fixed Docker configuration to use environment variables
- Added subprocess path validation to prevent injection
- Updated deployment script to be safer (selective file addition)"

# Push to remote
echo "🚀 Pushing to remote repository..."
git push origin main

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📋 Next steps:"
echo "1. Go to your Render dashboard"
echo "2. Find your 'agent-controller-backend' service"
echo "3. Click 'Manual Deploy' → 'Deploy latest commit'"
echo "4. Wait for deployment to complete"
echo "5. Test at: https://agent-controller-backend.onrender.com"
echo ""
echo "🔧 REQUIRED environment variables:"
echo "   - ADMIN_PASSWORD: Set a secure password (REQUIRED - no default)"
echo "   - SECRET_KEY: Generate a secure secret key"
echo "   - VITE_SOCKET_URL: WebSocket URL for frontend"
echo "   - VITE_API_URL: API URL for frontend"
echo ""
echo "🎯 Expected result:"
echo "   - Root URL serves UI v2.1 login"
echo "   - /dashboard URL serves UI v2.1 interface"
echo "   - Client connects automatically"