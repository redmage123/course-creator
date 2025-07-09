"""
Unit tests for user management service.
Tests authentication, registration, and user profile management.
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/user-management'))

# Import the main application
try:
    from main import app, get_password_hash, verify_password, create_access_token, users_collection
    from fastapi.testclient import TestClient
except ImportError:
    pytest.skip("User management service not available", allow_module_level=True)


class TestUserManagement:
    """Test suite for user management service."""
    
    def setup_method(self):
        """Set up test client and mock data."""
        self.client = TestClient(app)
        self.test_user = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "testpass123",
            "role": "student"
        }
        
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Hash should be different from original password
        assert hashed != password
        
        # Verification should work
        assert verify_password(password, hashed)
        
        # Wrong password should fail
        assert not verify_password("wrongpassword", hashed)
        
    def test_access_token_creation(self):
        """Test JWT token creation."""
        test_data = {"sub": "test@example.com", "role": "student"}
        token = create_access_token(test_data)
        
        # Token should be a string
        assert isinstance(token, str)
        
        # Token should have 3 parts (header.payload.signature)
        assert len(token.split('.')) == 3
        
    @patch('main.users_collection')
    def test_register_new_user(self, mock_collection):
        """Test user registration with new user."""
        mock_collection.find_one.return_value = None  # User doesn't exist
        mock_collection.insert_one.return_value = Mock(inserted_id="user_id")
        
        response = self.client.post("/auth/register", json=self.test_user)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["user"]["email"] == self.test_user["email"]
        assert data["user"]["role"] == "instructor"  # Default role
        
    @patch('main.users_collection')
    def test_register_existing_user(self, mock_collection):
        """Test registration with existing user."""
        mock_collection.find_one.return_value = {"email": self.test_user["email"]}
        
        response = self.client.post("/auth/register", json=self.test_user)
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"]
        
    @patch('main.users_collection')
    def test_login_valid_user(self, mock_collection):
        """Test login with valid credentials."""
        hashed_password = get_password_hash(self.test_user["password"])
        mock_user = {
            "email": self.test_user["email"],
            "username": self.test_user["username"],
            "full_name": self.test_user["full_name"],
            "password": hashed_password,
            "role": "student"
        }
        mock_collection.find_one.return_value = mock_user
        
        login_data = {
            "username": self.test_user["email"],
            "password": self.test_user["password"]
        }
        
        response = self.client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
    @patch('main.users_collection')
    def test_login_invalid_credentials(self, mock_collection):
        """Test login with invalid credentials."""
        mock_collection.find_one.return_value = None
        
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = self.client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]
        
    @patch('main.users_collection')
    def test_get_user_profile(self, mock_collection):
        """Test getting user profile with valid token."""
        mock_user = {
            "email": self.test_user["email"],
            "username": self.test_user["username"],
            "full_name": self.test_user["full_name"],
            "role": "student"
        }
        mock_collection.find_one.return_value = mock_user
        
        # Create a valid token
        token = create_access_token({"sub": self.test_user["email"], "role": "student"})
        
        response = self.client.get("/users/profile", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == self.test_user["email"]
        
    def test_get_profile_without_token(self):
        """Test getting profile without authentication."""
        response = self.client.get("/users/profile")
        
        assert response.status_code == 401
        
    @patch('main.users_collection')
    def test_get_all_users_admin(self, mock_collection):
        """Test getting all users as admin."""
        mock_users = [
            {"email": "user1@example.com", "role": "student"},
            {"email": "user2@example.com", "role": "instructor"}
        ]
        mock_collection.find.return_value = mock_users
        
        # Create admin token
        admin_token = create_access_token({"sub": "admin@example.com", "role": "admin"})
        
        response = self.client.get("/users/all", headers={"Authorization": f"Bearer {admin_token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2
        
    @patch('main.users_collection')
    def test_get_all_users_non_admin(self, mock_collection):
        """Test getting all users as non-admin (should fail)."""
        student_token = create_access_token({"sub": "student@example.com", "role": "student"})
        
        response = self.client.get("/users/all", headers={"Authorization": f"Bearer {student_token}"})
        
        assert response.status_code == 403
        
    @patch('main.users_collection')
    def test_delete_user_admin(self, mock_collection):
        """Test deleting user as admin."""
        mock_collection.delete_one.return_value = Mock(deleted_count=1)
        
        admin_token = create_access_token({"sub": "admin@example.com", "role": "admin"})
        
        response = self.client.delete("/users/test@example.com", headers={"Authorization": f"Bearer {admin_token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
    @patch('main.users_collection')
    def test_delete_nonexistent_user(self, mock_collection):
        """Test deleting non-existent user."""
        mock_collection.delete_one.return_value = Mock(deleted_count=0)
        
        admin_token = create_access_token({"sub": "admin@example.com", "role": "admin"})
        
        response = self.client.delete("/users/nonexistent@example.com", headers={"Authorization": f"Bearer {admin_token}"})
        
        assert response.status_code == 404
        
    def test_register_validation_errors(self):
        """Test registration with validation errors."""
        # Missing required fields
        invalid_user = {"email": "invalid-email"}
        
        response = self.client.post("/auth/register", json=invalid_user)
        
        assert response.status_code == 422  # Validation error
        
    def test_login_validation_errors(self):
        """Test login with validation errors."""
        # Missing password
        invalid_login = {"username": "test@example.com"}
        
        response = self.client.post("/auth/login", data=invalid_login)
        
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])