#!/bin/bash

# Deploy debugging fixes for agent registration
echo "🔧 Deploying Agent Registration Debug Fix"
echo "========================================="

# Check if we're in the right directory
if [ ! -f "controller.py" ]; then
    echo "❌ Error: controller.py not found. Please run this script from the project root."
    exit 1
fi

echo "📋 Changes to be deployed:"
echo "   ✅ Added debugging to agent_register handler"
echo "   ✅ Added debugging to operator_connect handler"
echo "   ✅ Enhanced simple-client.py with registration event handlers"
echo "   ✅ Created test-agent-registration.py for debugging"
echo ""

# Add all changes
echo "📦 Adding changes to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Add debugging for agent registration issue

- Added debug logging to agent_register handler
- Added debug logging to operator_connect handler
- Enhanced simple-client.py with registration event handlers
- Created test script to debug agent registration process
- Will help identify why agents don't appear in UI"

# Push to remote
echo "🚀 Pushing to remote repository..."
git push origin main

echo ""
echo "✅ Debug fixes deployed!"
echo ""
echo "📋 What was added:"
echo "1. Debug logging in controller for agent registration"
echo "2. Debug logging for operator connections"
echo "3. Enhanced simple client with registration handlers"
echo "4. Test script to debug the registration process"
echo ""
echo "🎯 Next steps:"
echo "1. Wait 2-5 minutes for Render to redeploy"
echo "2. Run: python3 simple-client.py"
echo "3. Check Render logs for debug output"
echo "4. Open controller UI and check browser console"
echo ""
echo "🔍 Debug commands:"
echo "   python3 simple-client.py"
echo "   python3 test-agent-registration.py"