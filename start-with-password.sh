#!/bin/bash

# Agent Controller Startup Script with Password
echo "🚀 Starting Agent Controller with Security"
echo "=========================================="

# Check if ADMIN_PASSWORD is set
if [ -z "$ADMIN_PASSWORD" ]; then
    echo "❌ ADMIN_PASSWORD environment variable is not set!"
    echo ""
    echo "🔐 For security, you must set a password before starting the server."
    echo ""
    echo "Set it with:"
    echo "   export ADMIN_PASSWORD='your_secure_password_here'"
    echo ""
    echo "Or start with:"
    echo "   ADMIN_PASSWORD='your_password' python3 start-backend.py"
    echo ""
    echo "⚠️  This is a security feature - no default password is allowed."
    exit 1
fi

echo "✅ ADMIN_PASSWORD is set (length: ${#ADMIN_PASSWORD} characters)"
echo "🌐 Starting server on http://localhost:8080"
echo ""
echo "📋 Access Information:"
echo "   • Login URL: http://localhost:8080/login"
echo "   • Dashboard URL: http://localhost:8080/dashboard"
echo "   • Password: [HIDDEN FOR SECURITY]"
echo ""
echo "🔒 Security Features Enabled:"
echo "   • SSL verification enabled"
echo "   • Input validation active"
echo "   • Security headers enabled"
echo "   • Dangerous command blocking"
echo ""

# Start the backend server
python3 start-backend.py