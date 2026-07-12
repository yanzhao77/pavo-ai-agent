"""Tests for Auth module (S9 - Phase 3)."""
import time
from app.services.auth import create_token, verify_token, revoke_token, clean_expired


class TestAuthModule:
    def test_create_and_verify(self):
        token = create_token("testuser")
        assert isinstance(token, str)
        assert len(token) > 10
        user_id = verify_token(token)
        assert user_id == "testuser"

    def test_invalid_token_returns_none(self):
        assert verify_token("invalid-token") is None

    def test_empty_token(self):
        assert verify_token("") is None

    def test_revoke_token(self):
        token = create_token("user1")
        assert verify_token(token) == "user1"
        assert revoke_token(token) is True
        assert verify_token(token) is None

    def test_revoke_invalid_token(self):
        assert revoke_token("invalid") is False

    def test_clean_expired(self):
        # Create a token and verify it works
        token = create_token("user2")
        assert verify_token(token) == "user2"
        # clean shouldn't remove active tokens
        assert clean_expired() >= 0
        assert verify_token(token) == "user2"

    def test_multiple_users(self):
        t1 = create_token("alice")
        t2 = create_token("bob")
        assert verify_token(t1) == "alice"
        assert verify_token(t2) == "bob"
        assert verify_token(t1) == "alice"  # Still valid
