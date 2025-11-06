#!/bin/bash

################################################################################
# Integration Test Runner with Real Infrastructure
#
# BUSINESS CONTEXT:
# Starts test infrastructure (PostgreSQL + Redis), waits for health checks,
# runs integration tests, and tears down infrastructure.
#
# USAGE:
#   ./tests/integration/run_integration_tests.sh
#
# REQUIREMENTS:
#   - Docker and docker-compose installed
#   - Ports 5434 and 6380 available
#   - Python 3.10+ with pytest, asyncpg, redis, openpyxl, pandas, odfpy
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Integration Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}[1/7] Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"
echo ""

# Step 2: Stop any existing test infrastructure
echo -e "${YELLOW}[2/7] Cleaning up existing test infrastructure...${NC}"
cd "$PROJECT_ROOT"
docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# Step 3: Start test infrastructure
echo -e "${YELLOW}[3/7] Starting test infrastructure (PostgreSQL + Redis)...${NC}"
docker-compose -f docker-compose.test.yml up -d

# Wait for services to start
sleep 3
echo -e "${GREEN}✅ Infrastructure starting${NC}"
echo ""

# Step 4: Wait for health checks
echo -e "${YELLOW}[4/7] Waiting for services to be healthy...${NC}"

MAX_WAIT=60
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    POSTGRES_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' course-creator-postgres-test 2>/dev/null || echo "starting")
    REDIS_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' course-creator-redis-test 2>/dev/null || echo "starting")

    if [ "$POSTGRES_HEALTH" = "healthy" ] && [ "$REDIS_HEALTH" = "healthy" ]; then
        echo -e "${GREEN}✅ PostgreSQL: healthy${NC}"
        echo -e "${GREEN}✅ Redis: healthy${NC}"
        break
    fi

    echo "   Waiting... PostgreSQL: $POSTGRES_HEALTH, Redis: $REDIS_HEALTH ($ELAPSED/$MAX_WAIT seconds)"
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}❌ Services failed to become healthy within ${MAX_WAIT} seconds${NC}"
    echo ""
    echo "Container logs:"
    docker logs course-creator-postgres-test --tail 50
    docker logs course-creator-redis-test --tail 50
    docker-compose -f docker-compose.test.yml down -v
    exit 1
fi

echo -e "${GREEN}✅ All services healthy${NC}"
echo ""

# Step 5: Install Python dependencies
echo -e "${YELLOW}[5/7] Installing Python test dependencies...${NC}"
pip install -q pytest pytest-asyncio asyncpg redis openpyxl pandas odfpy fastapi pyjwt 2>&1 | grep -v "already satisfied" || true
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 6: Run integration tests
echo -e "${YELLOW}[6/7] Running integration tests...${NC}"
echo ""

# Set environment variables for tests
export TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5434/course_creator_test"
export TEST_REDIS_URL="redis://localhost:6380"
export TEST_JWT_SECRET="test-secret-key-for-integration-tests-only"
export PYTHONPATH="$PROJECT_ROOT/services/course-management:$PROJECT_ROOT/services/user-management:$PROJECT_ROOT/services/organization-management:$PYTHONPATH"

# Run tests with pytest
cd "$PROJECT_ROOT"
python -m pytest tests/integration/test_project_import_api.py \
    -v \
    --tb=short \
    --color=yes \
    -m integration \
    || TEST_EXIT_CODE=$?

echo ""

# Step 7: Cleanup
echo -e "${YELLOW}[7/7] Cleaning up test infrastructure...${NC}"
docker-compose -f docker-compose.test.yml down -v
echo -e "${GREEN}✅ Infrastructure stopped${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
if [ "${TEST_EXIT_CODE:-0}" -eq 0 ]; then
    echo -e "${GREEN}✅ All integration tests passed!${NC}"
    echo -e "${BLUE}========================================${NC}"
    exit 0
else
    echo -e "${RED}❌ Some integration tests failed${NC}"
    echo -e "${BLUE}========================================${NC}"
    exit ${TEST_EXIT_CODE}
fi
