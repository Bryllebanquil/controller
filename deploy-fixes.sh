#!/bin/bash

# Deploy fixes for heartbeat and demo data removal
echo "🔧 Deploying Connection and UI Fixes"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "controller.py" ]; then
    echo "❌ Error: controller.py not found. Please run this script from the project root."
    exit 1
fi

echo "📋 Changes to be deployed:"
echo "   ✅ Added ping/pong handlers to controller.py"
echo "   ✅ Added agent_register handler to controller.py"
echo "   ✅ Removed demo data from UI v2.1"
echo "   ✅ Fixed hardcoded values in SystemMonitor"
echo "   ✅ Disabled mock data in WebRTC component"
echo ""

# Add all changes
echo "📦 Adding changes to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Fix agent connection and remove demo data

- Add ping/pong Socket.IO handlers for heartbeat
- Add agent_register handler for proper agent registration
- Remove hardcoded demo data from UI v2.1
- Fix SystemMonitor to show real-time data
- Disable mock data in WebRTC component
- Set network activity to 0.0 instead of simulated values"

# Push to remote
echo "🚀 Pushing to remote repository..."
git push origin main

echo ""
echo "✅ Fixes deployed!"
echo ""
echo "📋 What was fixed:"
echo "1. Controller now responds to ping messages with pong"
echo "2. Controller properly registers agents"
echo "3. UI no longer shows fake demo data"
echo "4. System metrics show real values (0 when no data)"
echo ""
echo "🎯 Next steps:"
echo "1. Wait for Render to redeploy (2-5 minutes)"
echo "2. Test simple client connection again"
echo "3. Check if agents appear in the UI"
echo ""
echo "🧪 Test command:"
echo "python3 simple-client.py"