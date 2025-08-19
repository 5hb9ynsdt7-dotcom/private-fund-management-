#!/bin/bash

# Version Check Script for Private Fund Management System
# Usage: ./scripts/check-version.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📋 Version Status Report${NC}"
echo "=========================="

# Get current version from VERSION file
if [ -f "VERSION" ]; then
    VERSION_FILE=$(cat VERSION)
    echo -e "VERSION file: ${GREEN}v$VERSION_FILE${NC}"
else
    echo -e "VERSION file: ${RED}Not found${NC}"
    VERSION_FILE="unknown"
fi

# Check backend version
if [ -f "backend/app/__init__.py" ]; then
    BACKEND_VERSION=$(grep '__version__' backend/app/__init__.py | sed 's/.*"\(.*\)".*/\1/')
    if [ "$BACKEND_VERSION" = "$VERSION_FILE" ]; then
        echo -e "Backend version: ${GREEN}v$BACKEND_VERSION ✓${NC}"
    else
        echo -e "Backend version: ${RED}v$BACKEND_VERSION ✗${NC} (mismatch)"
    fi
else
    echo -e "Backend version: ${RED}Not found${NC}"
fi

# Check frontend version
if [ -f "frontend/package.json" ]; then
    FRONTEND_VERSION=$(grep '"version":' frontend/package.json | sed 's/.*"\(.*\)".*/\1/')
    if [ "$FRONTEND_VERSION" = "$VERSION_FILE" ]; then
        echo -e "Frontend version: ${GREEN}v$FRONTEND_VERSION ✓${NC}"
    else
        echo -e "Frontend version: ${RED}v$FRONTEND_VERSION ✗${NC} (mismatch)"
    fi
else
    echo -e "Frontend version: ${RED}Not found${NC}"
fi

# Check git tags
if command -v git &> /dev/null && [ -d ".git" ]; then
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
    if [ "$LATEST_TAG" = "v$VERSION_FILE" ]; then
        echo -e "Latest git tag: ${GREEN}$LATEST_TAG ✓${NC}"
    else
        echo -e "Latest git tag: ${YELLOW}$LATEST_TAG${NC} (tag not created yet)"
    fi
    
    # Check if there are uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "Working directory: ${YELLOW}Has uncommitted changes${NC}"
    else
        echo -e "Working directory: ${GREEN}Clean ✓${NC}"
    fi
else
    echo -e "Git repository: ${RED}Not found${NC}"
fi

# Check changelog
if [ -f "CHANGELOG.md" ]; then
    if grep -q "\[${VERSION_FILE}\]" CHANGELOG.md; then
        echo -e "Changelog entry: ${GREEN}Found for v$VERSION_FILE ✓${NC}"
    else
        echo -e "Changelog entry: ${YELLOW}Missing for v$VERSION_FILE${NC}"
    fi
else
    echo -e "Changelog: ${RED}Not found${NC}"
fi

echo ""
echo -e "${YELLOW}📊 Summary${NC}"
echo "=========="

# Check for version consistency
ALL_VERSIONS_MATCH=true
if [ "$BACKEND_VERSION" != "$VERSION_FILE" ] || [ "$FRONTEND_VERSION" != "$VERSION_FILE" ]; then
    ALL_VERSIONS_MATCH=false
fi

if [ "$ALL_VERSIONS_MATCH" = true ]; then
    echo -e "Version consistency: ${GREEN}All versions match ✓${NC}"
else
    echo -e "Version consistency: ${RED}Version mismatch detected ✗${NC}"
    echo "Run './scripts/version-bump.sh' to synchronize versions"
fi

# Release readiness check
if [ "$ALL_VERSIONS_MATCH" = true ] && [ "$LATEST_TAG" = "v$VERSION_FILE" ] && [ -z "$(git status --porcelain)" ]; then
    echo -e "Release readiness: ${GREEN}Ready for deployment ✓${NC}"
elif [ "$ALL_VERSIONS_MATCH" = true ] && [ "$LATEST_TAG" != "v$VERSION_FILE" ]; then
    echo -e "Release readiness: ${YELLOW}Ready to tag (run git tag)${NC}"
else
    echo -e "Release readiness: ${RED}Not ready${NC}"
fi