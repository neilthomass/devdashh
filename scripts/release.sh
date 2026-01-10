#!/bin/bash
# Release script for devdash
# Usage: ./scripts/release.sh 1.0.1

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/release.sh <version>"
    echo "Example: ./scripts/release.sh 1.0.1"
    exit 1
fi

# Validate version format
if [[ ! $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format X.Y.Z (e.g., 1.0.1)"
    exit 1
fi

echo "Releasing version $VERSION..."

# Update version in pyproject.toml
sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# Update version in __init__.py
sed -i '' "s/^__version__ = \".*\"/__version__ = \"$VERSION\"/" devdash/__init__.py

# Commit version bump
git add pyproject.toml devdash/__init__.py
git commit -m "Bump version to $VERSION"
git push

# Create and push tag
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin "v$VERSION"

# Create GitHub release (triggers PyPI publish)
gh release create "v$VERSION" \
    --title "v$VERSION" \
    --generate-notes

echo "Released v$VERSION!"
echo "  GitHub: https://github.com/neilthomass/devdashh/releases/tag/v$VERSION"
echo "  PyPI will update automatically via GitHub Actions"
