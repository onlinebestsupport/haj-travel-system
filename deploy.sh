#!/bin/bash
# deploy.sh - One-click deployment script

echo "🚀 Deploying Alhudha Haj Travel System to Railway..."
echo "================================================"

# Step 1: Check git status
echo "📊 Checking git status..."
git status

# Step 2: Add all files
echo "\n📦 Adding files to git..."
git add .

# Step 3: Commit
echo "\n💾 Committing changes..."
git commit -m "Ready for Railway deployment"

# Step 4: Push to Railway
echo "\n🚀 Pushing to Railway..."
git push railway main

echo "\n✅ Deployment initiated!"
echo "📊 Check status: railway logs"
echo "🌐 Open app: railway open"
