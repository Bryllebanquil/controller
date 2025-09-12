#!/bin/bash

# Neural Control Hub - Render Build Script
echo "🏗️  Building Neural Control Hub for Render deployment..."
echo "=================================================="

# Check if we're in the right directory
if [ ! -d "agent-controller ui" ]; then
    echo "❌ Error: 'agent-controller ui' directory not found!"
    echo "Please run this script from the workspace root directory."
    exit 1
fi

# Navigate to frontend directory
cd "agent-controller ui"

echo "📦 Installing production dependencies..."
npm ci --production=false

echo "🔧 Copying Render environment configuration..."
cp .env.render .env.production

echo "🏗️  Building frontend for production..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend build completed successfully!"
    echo "📁 Build output available in: agent-controller ui/dist/"
else
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "=================================================="
echo "🚀 Ready for Render deployment!"
echo ""
echo "Next steps:"
echo "1. Deploy backend service first"
echo "2. Update VITE_API_URL in frontend environment"
echo "3. Deploy frontend service"
echo "=================================================="