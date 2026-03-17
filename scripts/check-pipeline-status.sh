#!/bin/bash

# Course Creator Pipeline Status Checker
# Check CI/CD pipeline status using GitHub CLI

echo "🔍 Checking Course Creator CI/CD Pipeline Status..."
echo "=================================================="

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not installed. Install it to check pipeline status."
    echo "📖 Visit: https://cli.github.com/"
    echo ""
    echo "🌐 Alternatively, check directly in browser:"
    echo "   https://github.com/redmage123/course-creator/actions"
    exit 1
fi

# Get latest workflow run
echo "📊 Latest Pipeline Runs:"
gh run list --limit 5 --workflow="test.yml" || {
    echo "❌ Failed to fetch pipeline status"
    echo "🌐 Check manually: https://github.com/redmage123/course-creator/actions"
    exit 1
}

echo ""
echo "🔍 Detailed Status for Latest Run:"
LATEST_RUN_ID=$(gh run list --limit 1 --workflow="test.yml" --json databaseId --jq '.[0].databaseId')

if [ -n "$LATEST_RUN_ID" ]; then
    gh run view $LATEST_RUN_ID || {
        echo "❌ Failed to get detailed status"
    }
else
    echo "❌ No recent pipeline runs found"
fi

echo ""
echo "🌐 View in browser: https://github.com/redmage123/course-creator/actions"
echo "⚡ To watch live: gh run watch (if a run is in progress)"