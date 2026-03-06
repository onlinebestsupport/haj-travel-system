# 🚀 RAILWAY DEPLOYMENT INSTRUCTIONS

## Step 1: Install Railway CLI (if not already installed)
npm install -g @railway/cli

## Step 2: Login to Railway
railway login

## Step 3: Link your project
railway link

## Step 4: Add PostgreSQL database
railway add

## Step 5: Set environment variables
railway variables set SECRET_KEY="your-secret-key-here"

## Step 6: Deploy
git push railway main

## Step 7: View logs
railway logs

## Step 8: Open your app
railway open

## Environment Variables needed in Railway:
- DATABASE_URL (auto-provided by PostgreSQL)
- SECRET_KEY (generate a random string)
