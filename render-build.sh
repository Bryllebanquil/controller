#!/bin/bash

# Render.com Build Script
# This script runs during Render deployment to build the React frontend

set -e  # Exit on any error

echo "🚀 Render build process starting..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Build React frontend
echo "🔨 Building React frontend..."
cd "agent-controller ui v2.1"

# Install Node.js dependencies
echo "📥 Installing npm dependencies..."
npm install

# Build production bundle
echo "🏗️ Building production bundle..."
npm run build

# Verify build
if [ ! -f "build/index.html" ] || [ ! -d "build/assets" ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "✅ Frontend build completed!"

# Return to project root
cd ..

echo "🎉 Render build process completed successfully!"