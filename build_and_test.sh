#!/bin/bash
# Build and Test Script for Popup Notification Fix

echo "=================================================="
echo "🔧 Building Frontend with Popup Notification Fix"
echo "=================================================="
echo ""

# Navigate to frontend directory
cd "agent-controller ui v2.1-modified"

# Install dependencies (if needed)
echo "📦 Installing dependencies..."
npm install

# Build the frontend
echo ""
echo "🏗️  Building frontend..."
npm run build

# Check if build succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📁 Build output:"
    ls -lh build/
    echo ""
    echo "=================================================="
    echo "🎉 Frontend built successfully!"
    echo "=================================================="
    echo ""
    echo "Next steps:"
    echo "1. Test locally: python controller.py"
    echo "2. Open: http://localhost:8080"
    echo "3. Run: python test_notifications.py"
    echo "4. Deploy: git add . && git commit -m 'Fix popup notifications' && git push"
    echo ""
else
    echo ""
    echo "❌ Build failed! Check errors above."
    exit 1
fi

cd ..
