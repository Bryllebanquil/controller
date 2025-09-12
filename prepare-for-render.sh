#!/bin/bash

# Neural Control Hub - Render Preparation Script
echo "🚀 Preparing Neural Control Hub for Render deployment..."
echo "=================================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📝 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
fi

# Check if we have a remote
if ! git remote get-url origin >/dev/null 2>&1; then
    echo ""
    echo "⚠️  No Git remote configured!"
    echo "Please add your GitHub repository as origin:"
    echo ""
    echo "git remote add origin https://github.com/yourusername/your-repo-name.git"
    echo ""
    read -p "Press Enter after adding the remote, or Ctrl+C to exit..."
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Build outputs
dist/
build/

# Environment files
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Runtime
*.pid
*.seed
*.pid.lock
EOF
    echo "✅ .gitignore created"
fi

# Check if all required files exist
echo ""
echo "🔍 Checking required files for Render deployment..."

required_files=(
    "controller.py"
    "start-render-backend.py"
    "backend-requirements.txt"
    "render-backend.yaml"
    "render-frontend.yaml"
    "agent-controller ui/package.json"
    "agent-controller ui/.env.render"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Please ensure all files are present before deployment."
    exit 1
fi

echo ""
echo "📦 Building frontend for testing..."
cd "agent-controller ui"
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Building frontend..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend build successful"
    cd ..
else
    echo "❌ Frontend build failed"
    cd ..
    exit 1
fi

# Add all files to git
echo ""
echo "📝 Adding files to Git..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Prepare Neural Control Hub for Render deployment

- Add Render configuration files
- Update CORS for production
- Add production startup scripts
- Configure environment variables
- Ready for deployment"
    
    if [ $? -eq 0 ]; then
        echo "✅ Changes committed successfully"
    else
        echo "❌ Failed to commit changes"
        exit 1
    fi
fi

echo ""
echo "🚀 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub"
else
    echo "❌ Failed to push to GitHub"
    echo "Please check your Git configuration and try again"
    exit 1
fi

echo ""
echo "=================================================="
echo "🎉 Neural Control Hub is ready for Render deployment!"
echo ""
echo "Next steps:"
echo "1. Go to https://render.com and sign in"
echo "2. Follow the RENDER-DEPLOYMENT-GUIDE.md"
echo "3. Deploy backend service first"
echo "4. Deploy frontend service second"
echo ""
echo "📚 Documentation available:"
echo "   - RENDER-DEPLOYMENT-GUIDE.md (complete guide)"
echo "   - DEPLOYMENT-CHECKLIST.md (quick checklist)"
echo ""
echo "🔗 Your repository is ready at:"
git remote get-url origin
echo "=================================================="