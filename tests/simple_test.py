#!/usr/bin/env python3
"""
Simple test to verify pytest functionality
"""

def test_simple():
    """Simple test that should always pass"""
    assert 1 + 1 == 2

def test_another_simple():
    """Another simple test"""
    assert "hello" == "hello"

if __name__ == "__main__":
    print("Simple test file created")