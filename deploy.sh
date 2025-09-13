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

# Add all changes
echo "📦 Adding changes to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Deploy agent-controller UI v2.1 integration

- Modified controller.py to serve UI v2.1 at root and /dashboard routes
- Added static asset serving for UI v2.1
- Updated requirements-controller.txt with flask-cors
- Updated render.yaml for single-service deployment
- Integrated UI v2.1 build files"

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
echo "🔧 If you need to set environment variables:"
echo "   - ADMIN_PASSWORD: Set a secure password"
echo "   - SECRET_KEY: Generate a secure secret key"
echo ""
echo "🎯 Expected result:"
echo "   - Root URL serves UI v2.1 login"
echo "   - /dashboard URL serves UI v2.1 interface"
echo "   - Client connects automatically"