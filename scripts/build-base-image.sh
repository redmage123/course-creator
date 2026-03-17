#!/bin/bash

# Build Course Creator Base Image for System Package Caching
# This eliminates repeated apt downloads across all service builds

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🏗️  Building Course Creator Base Image..."
echo "This caches system packages to eliminate repeated downloads"
echo

# Build the base image
docker build -f Dockerfile.base -t course-creator-base:latest .

echo
echo "✅ Base image built successfully!"
echo "📦 System packages cached in: course-creator-base:latest"
echo
echo "Benefits:"
echo "  - No more apt downloads during service builds"
echo "  - Faster build times for all services"
echo "  - Shared base layer across all containers"
echo
echo "Usage:"
echo "  1. Run this script once: ./build-base-image.sh"
echo "  2. Service builds will automatically use cached base image"
echo "  3. Rebuild base image when system dependencies change"