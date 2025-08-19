#!/bin/bash

# Version Bump Script for Private Fund Management System
# Usage: ./scripts/version-bump.sh [patch|minor|major]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to patch if no argument provided
VERSION_TYPE=${1:-patch}

# Validate version type
if [[ ! "$VERSION_TYPE" =~ ^(patch|minor|major)$ ]]; then
    echo -e "${RED}Error: Invalid version type. Use 'patch', 'minor', or 'major'${NC}"
    exit 1
fi

echo -e "${YELLOW}🔄 Starting version bump process...${NC}"

# Get current version
CURRENT_VERSION=$(cat VERSION)
echo -e "Current version: ${GREEN}v$CURRENT_VERSION${NC}"

# Calculate new version
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

case $VERSION_TYPE in
    "major")
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    "minor")
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    "patch")
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo -e "New version: ${GREEN}v$NEW_VERSION${NC}"

# Confirm with user
read -p "Proceed with version bump to v$NEW_VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Version bump cancelled.${NC}"
    exit 0
fi

# Update VERSION file
echo "$NEW_VERSION" > VERSION
echo -e "${GREEN}✓${NC} Updated VERSION file"

# Update backend version
sed -i.bak "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" backend/app/__init__.py
rm backend/app/__init__.py.bak
echo -e "${GREEN}✓${NC} Updated backend version"

# Update frontend package.json
sed -i.bak "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" frontend/package.json
rm frontend/package.json.bak
echo -e "${GREEN}✓${NC} Updated frontend version"

# Prompt for changelog entry
echo -e "${YELLOW}📝 Please update CHANGELOG.md with the new version details.${NC}"
echo "Add a new section for v$NEW_VERSION at the top of the file."
read -p "Press enter when you have updated the changelog..."

# Git operations
echo -e "${YELLOW}📦 Committing version bump...${NC}"
git add VERSION backend/app/__init__.py frontend/package.json CHANGELOG.md
git commit -m "chore: bump version to v$NEW_VERSION"

# Create tag
echo -e "${YELLOW}🏷️  Creating git tag...${NC}"
git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"

echo -e "${GREEN}🎉 Version bump complete!${NC}"
echo -e "Created tag: ${GREEN}v$NEW_VERSION${NC}"
echo -e "To publish: ${YELLOW}git push origin main --tags${NC}"