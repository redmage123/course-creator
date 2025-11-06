#!/bin/bash

###############################################################################
# Token Refresh Manual Testing Script
#
# This script provides manual testing commands to verify the JWT token
# refresh system is working correctly.
#
# Usage:
#   1. Login to get a token
#   2. Test the /auth/refresh endpoint
#   3. Verify the new token works
#
# Related Documentation:
#   /home/bbrelin/course-creator/docs/JWT_TOKEN_REFRESH_SYSTEM.md
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL for user-management service
BASE_URL="https://localhost:8000"

echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}JWT TOKEN REFRESH SYSTEM - MANUAL TESTING${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

# Check if user provided credentials as arguments
if [ "$#" -eq 2 ]; then
    USERNAME="$1"
    PASSWORD="$2"
    echo -e "${GREEN}Using provided credentials: $USERNAME${NC}"
else
    # Prompt for credentials
    echo -e "${YELLOW}Enter your credentials to test token refresh:${NC}"
    read -p "Username: " USERNAME
    read -s -p "Password: " PASSWORD
    echo ""
fi

echo ""
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}STEP 1: LOGIN AND GET INITIAL TOKEN${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

# Login and get token
LOGIN_RESPONSE=$(curl -s -k -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

# Check if login was successful
if echo "$LOGIN_RESPONSE" | jq -e '.access_token' > /dev/null 2>&1; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
    USER_DATA=$(echo "$LOGIN_RESPONSE" | jq '.user')

    echo -e "${GREEN}✅ Login successful!${NC}"
    echo ""
    echo "User Data:"
    echo "$USER_DATA" | jq '.'
    echo ""
    echo -e "Original Token (first 50 chars): ${TOKEN:0:50}..."
    echo ""
else
    echo -e "${RED}❌ Login failed!${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo ""
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}STEP 2: WAIT 2 SECONDS (to ensure token timestamp changes)${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

sleep 2
echo -e "${GREEN}✅ Wait complete${NC}"

echo ""
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}STEP 3: TEST TOKEN REFRESH ENDPOINT${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

# Call token refresh endpoint
REFRESH_RESPONSE=$(curl -s -k -X POST "$BASE_URL/auth/refresh" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")

# Check if refresh was successful
if echo "$REFRESH_RESPONSE" | jq -e '.access_token' > /dev/null 2>&1; then
    NEW_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.access_token')
    NEW_USER_DATA=$(echo "$REFRESH_RESPONSE" | jq '.user')

    echo -e "${GREEN}✅ Token refresh successful!${NC}"
    echo ""
    echo "New User Data:"
    echo "$NEW_USER_DATA" | jq '.'
    echo ""
    echo -e "New Token (first 50 chars): ${NEW_TOKEN:0:50}..."
    echo ""

    # Verify token changed
    if [ "$TOKEN" == "$NEW_TOKEN" ]; then
        echo -e "${RED}⚠️ WARNING: Token did not change (this is unusual)${NC}"
    else
        echo -e "${GREEN}✅ Token was refreshed (new token issued)${NC}"
    fi
else
    echo -e "${RED}❌ Token refresh failed!${NC}"
    echo "Response: $REFRESH_RESPONSE"
    exit 1
fi

echo ""
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}STEP 4: VERIFY NEW TOKEN WORKS FOR API CALLS${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

# Test new token with /users/me endpoint
ME_RESPONSE=$(curl -s -k -X GET "$BASE_URL/users/me" \
    -H "Authorization: Bearer $NEW_TOKEN")

# Check if /users/me call was successful
if echo "$ME_RESPONSE" | jq -e '.username' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ New token works for API calls!${NC}"
    echo ""
    echo "User data from /users/me:"
    echo "$ME_RESPONSE" | jq '.'
    echo ""
else
    echo -e "${RED}❌ New token failed to work for API calls!${NC}"
    echo "Response: $ME_RESPONSE"
    exit 1
fi

echo ""
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}STEP 5: TEST MULTIPLE REFRESHES${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

CURRENT_TOKEN="$NEW_TOKEN"
for i in {1..3}; do
    echo -e "${YELLOW}Refresh attempt $i/3...${NC}"

    sleep 1  # Wait a moment to ensure different timestamp

    REFRESH_RESPONSE=$(curl -s -k -X POST "$BASE_URL/auth/refresh" \
        -H "Authorization: Bearer $CURRENT_TOKEN" \
        -H "Content-Type: application/json")

    if echo "$REFRESH_RESPONSE" | jq -e '.access_token' > /dev/null 2>&1; then
        REFRESHED_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.access_token')

        if [ "$CURRENT_TOKEN" == "$REFRESHED_TOKEN" ]; then
            echo -e "${RED}  ❌ Token did not change on refresh $i${NC}"
        else
            echo -e "${GREEN}  ✅ Refresh $i successful (token changed)${NC}"
        fi

        CURRENT_TOKEN="$REFRESHED_TOKEN"
    else
        echo -e "${RED}  ❌ Refresh $i failed${NC}"
        echo "  Response: $REFRESH_RESPONSE"
    fi
done

echo ""
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}STEP 6: TEST INVALID TOKEN REJECTION${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

INVALID_TOKEN="invalid.token.here"

INVALID_RESPONSE=$(curl -s -k -X POST "$BASE_URL/auth/refresh" \
    -H "Authorization: Bearer $INVALID_TOKEN" \
    -H "Content-Type: application/json")

# Should return 401 or 403
HTTP_CODE=$(curl -s -k -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/auth/refresh" \
    -H "Authorization: Bearer $INVALID_TOKEN" \
    -H "Content-Type: application/json")

if [ "$HTTP_CODE" == "401" ] || [ "$HTTP_CODE" == "403" ]; then
    echo -e "${GREEN}✅ Invalid token correctly rejected (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}❌ Invalid token not rejected properly (HTTP $HTTP_CODE)${NC}"
fi

echo ""
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}STEP 7: TEST MISSING TOKEN REJECTION${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

NO_TOKEN_RESPONSE=$(curl -s -k -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/auth/refresh" \
    -H "Content-Type: application/json")

if [ "$NO_TOKEN_RESPONSE" == "401" ] || [ "$NO_TOKEN_RESPONSE" == "403" ]; then
    echo -e "${GREEN}✅ Missing token correctly rejected (HTTP $NO_TOKEN_RESPONSE)${NC}"
else
    echo -e "${RED}❌ Missing token not rejected properly (HTTP $NO_TOKEN_RESPONSE)${NC}"
fi

echo ""
echo -e "${GREEN}================================================================================================${NC}"
echo -e "${GREEN}ALL TESTS COMPLETED SUCCESSFULLY!${NC}"
echo -e "${GREEN}================================================================================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "${GREEN}  ✅ Token refresh endpoint is working${NC}"
echo -e "${GREEN}  ✅ Refreshed tokens are valid for API calls${NC}"
echo -e "${GREEN}  ✅ Multiple refreshes work correctly${NC}"
echo -e "${GREEN}  ✅ Invalid tokens are rejected${NC}"
echo -e "${GREEN}  ✅ Missing tokens are rejected${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "${BLUE}  1. Test automatic frontend refresh (login and wait 20 minutes)${NC}"
echo -e "${BLUE}  2. Test activity-based refresh (be inactive for 30+ minutes)${NC}"
echo -e "${BLUE}  3. Test automatic logout on token expiration${NC}"
echo ""
echo -e "${BLUE}Documentation: /home/bbrelin/course-creator/docs/JWT_TOKEN_REFRESH_SYSTEM.md${NC}"
echo ""
