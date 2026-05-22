#!/bin/bash
# GitHub Repository Setup Commands for Amazon Connect MCP Server
# Run these commands to create the repository and push the code

# Configuration
REPO_NAME="amazon-connect-mcp"
REPO_OWNER="timmy-t-bot"
VISIBILITY="public"

# ============================================
# OPTION 1: Using GitHub CLI (gh)
# ============================================

# Check if gh CLI is installed
if command -v gh &> /dev/null; then
    echo "Using GitHub CLI (gh) for repository creation..."
    
    # Create the repository
    gh repo create "${REPO_OWNER}/${REPO_NAME}" \
        --${VISIBILITY} \
        --description="MCP Server for Amazon Connect outbound communication and infrastructure management" \
        --homepage="https://github.com/${REPO_OWNER}/${REPO_NAME}" \
        --enable-wiki=false \
        --enable-issues=true \
        --enable-discussions=true \
        --source=. \
        --remote=origin \
        --push
    
    echo "Repository created and code pushed successfully!"
    
    # Enable branch protection (requires admin access)
    echo "To enable branch protection, run:"
    echo "  gh api repos/${REPO_OWNER}/${REPO_NAME}/branches/main/protection \"
    echo "    --method PUT \"
    echo "    --input branch-protection.json"
    
else
    echo "GitHub CLI (gh) not found. See manual instructions below."
fi

# ============================================
# OPTION 2: Manual GitHub Setup
# ============================================

echo ""
echo "========================================"
echo "Manual Repository Setup Instructions"
echo "========================================"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to: https://github.com/new"
echo "   - Repository name: ${REPO_NAME}"
echo "   - Description: MCP Server for Amazon Connect outbound communication and infrastructure management"
echo "   - Visibility: Public"
echo "   - Do NOT initialize with README (we already have one)"
echo ""
echo "2. Add the remote repository:"
echo "   git remote add origin https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
echo "   # OR for SSH:"
echo "   git remote add origin git@github.com:${REPO_OWNER}/${REPO_NAME}.git"
echo ""
echo "3. Push the code:"
echo "   git push -u origin main"
echo ""
echo "4. Set repository topics (via web interface or API):"
echo "   - mcp"
echo "   - amazon-connect"
echo "   - contact-center"
echo "   - outbound-calling"
echo "   - aws"
echo "   - ai-agents"
echo "   - model-context-protocol"
echo "   - python"
echo "   - telephony"
echo ""

# ============================================
# Post-Setup Configuration
# ============================================

echo ""
echo "========================================"
echo "Post-Setup Configuration Required"
echo "========================================"
echo ""
echo "1. Enable GitHub Actions:"
echo "   - Go to: Settings > Actions > General"
echo "   - Select 'Allow all actions and reusable workflows'"
echo ""
echo "2. Configure PyPI OIDC (for automated publishing):"
echo "   - Go to: https://pypi.org/manage/account/publishing/"
echo "   - Add a new 'pending publisher':"
echo "     * PyPI Project Name: amazon-connect-mcp"
echo "     * Owner: ${REPO_OWNER}"
echo "     * Repository Name: ${REPO_NAME}"
echo "     * Workflow Name: publish.yml"
echo "     * Environment Name: pypi"
echo ""
echo "3. (Optional) Configure Test PyPI OIDC:"
echo "   - Go to: https://test.pypi.org/manage/account/publishing/"
echo "   - Add a new 'pending publisher' with same details"
echo ""
echo "4. Configure branch protection rules:"
echo "   - Go to: Settings > Branches"
echo "   - Add rule for 'main' branch:"
echo "     * Require pull request reviews before merging (1 reviewer)"
echo "     * Require status checks to pass (test, lint)"
echo "     * Restrict pushes to matching branches"
echo ""
echo "5. Enable Dependabot alerts:"
echo "   - Go to: Settings > Security > Code security and analysis"
echo "   - Enable 'Dependabot alerts'"
echo "   - Enable 'Dependabot security updates'"
echo ""

# ============================================
# Verification Commands
# ============================================

echo ""
echo "========================================"
echo "Verification"
echo "========================================"
echo ""
echo "After pushing, verify with:"
echo "  git remote -v"
echo "  git log --oneline -5"
echo "  git status"
echo ""
echo "GitHub repository will be available at:"
echo "  https://github.com/${REPO_OWNER}/${REPO_NAME}"
echo ""
