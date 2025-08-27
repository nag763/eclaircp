#!/bin/bash

# EclairCP Installation Test Script
# This script tests the installation and basic functionality of EclairCP

set -e  # Exit on any error

echo "🧪 Testing EclairCP Installation from GitHub"
echo "============================================="

# Create a temporary directory for testing
TEST_DIR=$(mktemp -d)
echo "📁 Created test directory: $TEST_DIR"

# Change to test directory
cd "$TEST_DIR"

echo ""
echo "📦 Testing installation with UV..."
echo "uv tool install git+https://github.com/nag763/eclaircp.git"

# Test UV installation (if UV is available)
if command -v uv &> /dev/null; then
    echo "✅ UV is available"
    
    # Install EclairCP
    uv tool install git+https://github.com/nag763/eclaircp.git
    
    echo ""
    echo "🔍 Testing installed command..."
    
    # Test version command
    eclaircp --version
    
    # Test help command
    echo ""
    echo "📖 Testing help command..."
    eclaircp --help | head -10
    
    echo ""
    echo "✅ UV installation test completed successfully!"
    
else
    echo "⚠️  UV not available, skipping UV installation test"
fi

echo ""
echo "📦 Testing installation with pip..."

# Create a virtual environment for pip testing
python3 -m venv pip_test_env
source pip_test_env/bin/activate

# Install with pip
pip install git+https://github.com/nag763/eclaircp.git

echo ""
echo "🔍 Testing pip-installed command..."

# Test version command
eclaircp --version

# Test help command
echo ""
echo "📖 Testing help command..."
eclaircp --help | head -10

echo ""
echo "✅ Pip installation test completed successfully!"

# Deactivate virtual environment
deactivate

echo ""
echo "🧹 Cleaning up test directory..."
cd /
rm -rf "$TEST_DIR"

echo ""
echo "🎉 All installation tests passed!"
echo "EclairCP is ready for distribution and use."