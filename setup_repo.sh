#!/bin/bash

echo "🚀 Setting up Compliance Copilot repository..."

# Initialize git
git init
echo "✅ Git initialized"

# Add all files
git add .
echo "✅ Files added"

# Commit
git commit -m "Initial commit - Compliance Copilot v0.1.0-alpha"
echo "✅ Commit created"

# Set main branch
git branch -M main
echo "✅ Branch set to main"

# Add remote (replace with your username if different)
git remote add origin https://github.com/cyberai/compliance-copilot.git
echo "✅ Remote added"

# Push to GitHub
echo "📤 Pushing to GitHub (you may be asked for credentials)..."
git push -u origin main
echo "✅ Push complete!"

echo ""
echo "🎉 Repository setup complete!"
echo "Next steps:"
echo "1. Go to: https://github.com/cyberai/compliance-copilot/settings/secrets/actions"
echo "2. Add PYPI_API_TOKEN with your PyPI token"
echo "3. Create and push tag: git tag v0.1.0-alpha && git push origin v0.1.0-alpha"
echo "4. Create GitHub Release"
