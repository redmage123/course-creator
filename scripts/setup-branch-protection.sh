#!/bin/bash
# Setup branch protection rules for the course-creator repository (TU-BUG-015)
#
# This script enforces:
#   - No direct pushes to main/master
#   - PR required with at least 1 approval before merge
#   - Required status checks: qa-gate, CI jobs
#
# Usage:
#   export GITHUB_TOKEN=<your-personal-access-token>
#   bash scripts/setup-branch-protection.sh
#
# Requires: GitHub token with 'repo' scope for redmage123/course-creator

set -euo pipefail

REPO_OWNER="redmage123"
REPO_NAME="course-creator"
BRANCHES=("main" "master")

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "ERROR: GITHUB_TOKEN environment variable is required."
  echo "  export GITHUB_TOKEN=<your-personal-access-token>"
  echo "  Token needs 'repo' scope for ${REPO_OWNER}/${REPO_NAME}"
  exit 1
fi

API_BASE="https://api.github.com"
AUTH_HEADER="Authorization: Bearer ${GITHUB_TOKEN}"
ACCEPT_HEADER="Accept: application/vnd.github+json"

apply_branch_protection() {
  local branch=$1
  echo "Applying branch protection to: ${branch}"

  # Check if branch exists
  local status
  status=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "${AUTH_HEADER}" \
    -H "${ACCEPT_HEADER}" \
    "${API_BASE}/repos/${REPO_OWNER}/${REPO_NAME}/branches/${branch}")

  if [[ "$status" == "404" ]]; then
    echo "  Branch '${branch}' does not exist — skipping."
    return 0
  fi

  # Apply branch protection
  local response
  response=$(curl -s -w "\n%{http_code}" \
    -X PUT \
    -H "${AUTH_HEADER}" \
    -H "${ACCEPT_HEADER}" \
    -H "Content-Type: application/json" \
    "${API_BASE}/repos/${REPO_OWNER}/${REPO_NAME}/branches/${branch}/protection" \
    -d '{
      "required_status_checks": {
        "strict": true,
        "contexts": [
          "QA Sign-Off Required",
          "code-quality",
          "unit-tests"
        ]
      },
      "enforce_admins": true,
      "required_pull_request_reviews": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false
      },
      "restrictions": null,
      "allow_force_pushes": false,
      "allow_deletions": false,
      "block_creations": false,
      "required_conversation_resolution": true
    }')

  local http_code
  http_code=$(echo "$response" | tail -1)
  local body
  body=$(echo "$response" | head -n -1)

  if [[ "$http_code" == "200" ]]; then
    echo "  ✅ Branch protection applied to '${branch}'"
    echo "     - Direct pushes: BLOCKED"
    echo "     - PR reviews required: 1 approval minimum"
    echo "     - Required checks: QA Sign-Off Required, code-quality, unit-tests"
    echo "     - Dismiss stale reviews on new commits: YES"
    echo "     - Enforce for admins: YES"
  else
    echo "  ❌ Failed to apply protection to '${branch}' (HTTP ${http_code})"
    echo "  Response: $body"
    return 1
  fi
}

echo "========================================"
echo "TU-BUG-015: Branch Protection Setup"
echo "Repo: ${REPO_OWNER}/${REPO_NAME}"
echo "========================================"
echo ""

for branch in "${BRANCHES[@]}"; do
  apply_branch_protection "$branch"
  echo ""
done

echo "========================================"
echo "Also installing local pre-push hook..."
echo "========================================"

# Install a local pre-push hook to catch direct pushes before they hit GitHub
HOOK_DIR="$(git rev-parse --git-dir 2>/dev/null)/hooks"
if [[ -d "$HOOK_DIR" ]]; then
  cat > "${HOOK_DIR}/pre-push" << 'HOOK_EOF'
#!/bin/bash
# Pre-push hook: prevent direct pushes to main or master (TU-BUG-015)
# Enforces the "PR only" workflow locally.

protected_branches=("main" "master")
current_branch=$(git symbolic-ref HEAD 2>/dev/null | sed 's|refs/heads/||')

for branch in "${protected_branches[@]}"; do
  if [[ "$current_branch" == "$branch" ]]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  BLOCKED: Direct push to '${branch}' is not allowed.             ║"
    echo "║                                                               ║"
    echo "║  All changes must go through a Pull Request with:            ║"
    echo "║    ✓ At least 1 approval                                     ║"
    echo "║    ✓ QA sign-off (qa-pass or qa-warn label)                  ║"
    echo "║    ✓ All required CI checks passing                          ║"
    echo "║                                                               ║"
    echo "║  Create a feature branch and open a PR instead.              ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    exit 1
  fi
done

exit 0
HOOK_EOF
  chmod +x "${HOOK_DIR}/pre-push"
  echo "✅ Pre-push hook installed at ${HOOK_DIR}/pre-push"
else
  echo "⚠️  Not in a git repo — skipping local hook install."
fi

echo ""
echo "Branch protection setup complete."
echo ""
echo "NOTE: Re-run this script whenever the repo is freshly cloned to reinstall"
echo "      the local pre-push hook. The GitHub-side protection persists permanently."
