#!/bin/bash

# Build and Deploy Script for Agent Controller
# This script builds the React frontend and prepares the app for deployment

set -e  # Exit on any error

echo "🚀 Starting build and deployment process..."

# Check if we're in the correct directory
if [ ! -f "controller.py" ]; then
    echo "❌ Error: controller.py not found. Please run this script from the project root."
    exit 1
fi

# Build the React frontend
echo "📦 Building React frontend..."
cd "agent-controller ui v2.1"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📥 Installing npm dependencies..."
    npm install
fi

# Build the production bundle
echo "🔨 Building production bundle..."
npm run build

# Verify build was successful
if [ ! -f "build/index.html" ]; then
    echo "❌ Error: Build failed - index.html not found"
    exit 1
fi

if [ ! -d "build/assets" ]; then
    echo "❌ Error: Build failed - assets directory not found"
    exit 1
fi

echo "✅ Frontend build completed successfully!"

# Go back to project root
cd ..

# List the built assets for verification
echo "📋 Built assets:"
ls -la "agent-controller ui v2.1/build/assets/"

echo "🎉 Build process completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Commit and push your changes to GitHub"
echo "2. Render will automatically detect and deploy the changes"
echo "3. The dashboard should now work correctly"
echo ""
echo "🔗 Your app will be available at: https://agent-controller-backend.onrender.com/dashboard"