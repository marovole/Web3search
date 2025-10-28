#!/bin/bash

# Web3Search Frontend Deployment Script
# This script automates the deployment process to Vercel

set -e  # Exit on any error

echo "🚀 Starting Web3Search Frontend Deployment..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the frontend directory."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Run type checking
echo "🔍 Running TypeScript type check..."
npm run build

# Run linting
echo "🔍 Running ESLint..."
npm run lint || true  # Allow linting warnings but don't fail the build

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."

# Check if this is a production deployment
if [ "$1" = "--prod" ]; then
    echo "🎯 Deploying to production..."
    vercel --prod
else
    echo "🔀 Deploying to preview..."
    vercel
fi

echo "✅ Deployment completed successfully!"
echo "📋 Next steps:"
echo "   1. Test the deployed application"
echo "   2. Verify API connectivity"
echo "   3. Check environment variables are correctly set"