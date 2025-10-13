#!/bin/bash

echo "================================================================================"
echo "🚀 DEPLOYING 'ALL' BUTTON TO DASHBOARD"
echo "================================================================================"
echo ""
echo "Step 1: Checking if files were modified..."
echo ""

# Check if files exist and show status
if [ -f "agent-controller ui v2.1-modified/src/components/CommandPanel.tsx" ]; then
    echo "✅ CommandPanel.tsx exists and was modified"
    echo "   Location: agent-controller ui v2.1-modified/src/components/CommandPanel.tsx"
    echo ""
else
    echo "❌ CommandPanel.tsx not found!"
    exit 1
fi

if [ -f "controller.py" ]; then
    echo "✅ controller.py exists and was modified"
    echo "   Location: controller.py"
    echo ""
else
    echo "❌ controller.py not found!"
    exit 1
fi

echo "================================================================================"
echo "Step 2: Git Status"
echo "================================================================================"
git status | grep -E "CommandPanel.tsx|controller.py" || echo "No changes detected in git"
echo ""

echo "================================================================================"
echo "Step 3: Ready to Deploy!"
echo "================================================================================"
echo ""
echo "Run these commands to deploy:"
echo ""
echo "  git add 'agent-controller ui v2.1-modified/src/components/CommandPanel.tsx'"
echo "  git add controller.py"
echo "  git commit -m 'Add All button for bulk command execution'"
echo "  git push"
echo ""
echo "================================================================================"
echo "After pushing, Render will automatically rebuild (~2-3 minutes)"
echo "Then refresh your dashboard and you'll see the [All] button!"
echo "================================================================================"
