#!/bin/bash

# Deploy Modified UI v2.1 to Render (Test Environment)
echo "🧪 Agent Controller Modified UI v2.1 - Test Deployment Script"
echo "=============================================================="

# Check if we're in the right directory
if [ ! -f "controller.py" ]; then
    echo "❌ Error: controller.py not found. Please run this script from the project root."
    exit 1
fi

# Check if modified UI directory exists
if [ ! -d "agent-controller ui v2.1-modified" ]; then
    echo "❌ Error: 'agent-controller ui v2.1-modified' directory not found."
    exit 1
fi

echo "✅ Project structure verified"

# Build the modified UI locally to verify it works
echo ""
echo "🔨 Building modified UI locally to verify..."
cd "agent-controller ui v2.1-modified"

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "🏗️  Building UI..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed! Please fix errors before deploying."
    cd ..
    exit 1
fi

echo "✅ Build successful!"
cd ..

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed or not in PATH"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo ""
echo "📋 Current branch: $CURRENT_BRANCH"
echo ""
echo "⚠️  DEPLOYMENT OPTIONS:"
echo ""
echo "   Option 1 (RECOMMENDED): Create a new Render service for testing"
echo "   - Keeps your production v2.1 running"
echo "   - Test the modified version safely"
echo "   - No downtime on production"
echo ""
echo "   Option 2: Update existing service temporarily"
echo "   - Replaces production with modified version"
echo "   - Can rollback if needed"
echo "   - Brief downtime during deployment"
echo ""
read -p "Which option do you prefer? (1 or 2): " OPTION

if [ "$OPTION" = "1" ]; then
    echo ""
    echo "✅ You chose Option 1: Create separate test service"
    echo ""
    echo "📋 Steps to deploy:"
    echo ""
    echo "1. Commit and push the modified UI:"
    git add "agent-controller ui v2.1-modified/"
    git add render-test-modified.yaml
    
    read -p "   Do you want to commit these changes? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git commit -m "Add agent-controller UI v2.1-modified (Hybrid version) for testing

- Added Login screen with authentication
- Added loading screen for connection states
- Added ErrorBoundary for error handling
- Added Process Manager nested tabs
- Enhanced Monitoring with Network Performance
- Maintained clean architecture and mobile responsiveness
- Ready for Render deployment testing"
        
        echo "🚀 Pushing to remote..."
        git push origin $CURRENT_BRANCH
        
        echo ""
        echo "✅ Code pushed successfully!"
        echo ""
        echo "📋 NEXT STEPS:"
        echo ""
        echo "2. Go to Render Dashboard: https://dashboard.render.com"
        echo ""
        echo "3. Click 'New +' → 'Blueprint'"
        echo ""
        echo "4. Select your repository"
        echo ""
        echo "5. In 'Blueprint Name', enter: render-test-modified.yaml"
        echo ""
        echo "6. Render will create a new service: 'agent-controller-backend-test'"
        echo ""
        echo "7. Set environment variables in Render dashboard:"
        echo "   - ADMIN_PASSWORD: your_secure_password"
        echo "   - SECRET_KEY: your_secret_secret_key"
        echo ""
        echo "8. Click 'Apply' to deploy"
        echo ""
        echo "9. Your test URL will be: https://agent-controller-backend-test.onrender.com"
        echo ""
        echo "🎯 RESULT:"
        echo "   - Production (v2.1): Still running at your current URL"
        echo "   - Test (v2.1-modified): Running at new test URL"
        echo "   - Both can run simultaneously!"
    else
        echo "❌ Deployment cancelled"
        exit 1
    fi
    
elif [ "$OPTION" = "2" ]; then
    echo ""
    echo "⚠️  You chose Option 2: Update existing service"
    echo ""
    echo "⚠️  WARNING: This will replace your production deployment!"
    echo ""
    read -p "Are you absolutely sure? (type 'YES' to confirm): " CONFIRM
    
    if [ "$CONFIRM" != "YES" ]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
    
    # Backup current render.yaml
    cp render.yaml render.yaml.backup
    echo "✅ Backed up render.yaml to render.yaml.backup"
    
    # Update render.yaml to use modified UI
    sed -i.tmp 's|agent-controller ui v2.1|agent-controller ui v2.1-modified|g' render.yaml
    rm render.yaml.tmp 2>/dev/null || true
    
    echo "✅ Updated render.yaml to use modified UI"
    
    # Commit and push
    git add render.yaml
    git add "agent-controller ui v2.1-modified/"
    
    git commit -m "TESTING: Deploy agent-controller UI v2.1-modified

⚠️  TESTING DEPLOYMENT - Can be reverted
- Temporarily replacing v2.1 with v2.1-modified
- Testing hybrid features (Login, Process Manager, Network Monitoring)
- Can rollback by reverting this commit"
    
    echo "🚀 Pushing to remote..."
    git push origin $CURRENT_BRANCH
    
    echo ""
    echo "✅ Code pushed successfully!"
    echo ""
    echo "📋 NEXT STEPS:"
    echo ""
    echo "1. Go to Render Dashboard: https://dashboard.render.com"
    echo "2. Find your 'agent-controller-backend' service"
    echo "3. It should auto-deploy (autoDeploy: true)"
    echo "4. Or click 'Manual Deploy' → 'Deploy latest commit'"
    echo "5. Wait for deployment to complete"
    echo ""
    echo "🔄 TO ROLLBACK:"
    echo "   git revert HEAD"
    echo "   git push origin $CURRENT_BRANCH"
    echo "   (Then redeploy on Render)"
    
else
    echo "❌ Invalid option. Deployment cancelled."
    exit 1
fi

echo ""
echo "✅ Deployment preparation complete!"
echo ""
echo "📝 TESTING CHECKLIST:"
echo "   [ ] Login screen appears"
echo "   [ ] Can authenticate with password"
echo "   [ ] 'Connecting...' screen shows briefly"
echo "   [ ] Dashboard loads correctly"
echo "   [ ] Mobile navigation works"
echo "   [ ] Process Manager tab appears in Commands"
echo "   [ ] Network Performance shows in Monitoring"
echo "   [ ] ErrorBoundary handles errors gracefully"
echo ""
