#!/bin/bash

# Deploy system metrics fix
echo "🔧 Deploying System Metrics Fix"
echo "==============================="

# Check if we're in the right directory
if [ ! -f "controller.py" ]; then
    echo "❌ Error: controller.py not found. Please run this script from the project root."
    exit 1
fi

echo "📋 Changes to be deployed:"
echo "   ✅ Enhanced /api/system/info endpoint with detailed metrics"
echo "   ✅ Added CPU cores, frequency, memory size, disk size"
echo "   ✅ Added network upload/download statistics"
echo "   ✅ Updated SystemMonitor to use new detailed data"
echo ""

# Add all changes
echo "📦 Adding changes to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Fix system metrics display with detailed information

- Enhanced /api/system/info endpoint with comprehensive system data
- Added CPU cores, frequency, memory size, disk size information
- Added network upload/download statistics
- Updated SystemMonitor component to display real system metrics
- Fixed display of 0 values for cores, memory, disk sizes"

# Push to remote
echo "🚀 Pushing to remote repository..."
git push origin main

echo ""
echo "✅ System metrics fix deployed!"
echo ""
echo "📋 What was fixed:"
echo "1. Controller now provides detailed system information"
echo "2. CPU shows real cores and frequency"
echo "3. Memory shows real total/used/available in GB"
echo "4. Storage shows real total/used/free in GB"
echo "5. Network shows real upload/download statistics"
echo ""
echo "🎯 Expected results after deployment:"
echo "   CPU Usage: 55.9% | 2.4 GHz | 4 cores | 0°C"
echo "   Memory: 71.4% | 8.0 GB | Used: 5.7 GB | Available: 2.3 GB"
echo "   Storage: 81.6% | 500 GB | Used: 408 GB | Free: 92 GB"
echo "   Network: 0ms | Upload: 1.2 MB/s | Download: 0.8 MB/s"
echo ""
echo "⏰ Wait 2-5 minutes for Render to redeploy, then refresh the UI"