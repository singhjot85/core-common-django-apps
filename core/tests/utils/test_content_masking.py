"""
Unit tests for ContentMaskingUtils and PatternMatcher.

Validates sensitive keyword matching, deep recursive masking
in dictionaries and lists, and preservation of safe non-string primitives.
"""

from core.utils.error_handling.content_masking import (
    ContentMaskingUtils,
    PatternMatcher,
    get_sensitive_matcher,
)


class TestPatternMatcher:
    """
    Test suite for PatternMatcher sensitive keyword detection.
    """

    def test_detects_common_sensitive_phrases(self):
        """
        Matcher correctly flags sensitive keys like password, token, and secret.
        """
        matcher = PatternMatcher()

        assert matcher.is_sensitive("password") is True
        assert matcher.is_sensitive("user_password") is True
        assert matcher.is_sensitive("access_token") is True
        assert matcher.is_sensitive("client_secret") is True
        assert matcher.is_sensitive("auth_key") is True

    def test_ignores_non_sensitive_phrases(self):
        """
        Matcher does not flag normal attributes like username, status, or email.
        """
        matcher = PatternMatcher()

        assert matcher.is_sensitive("username") is False
        assert matcher.is_sensitive("status") is False
        assert matcher.is_sensitive("created_at") is False
        assert matcher.is_sensitive("first_name") is False

    def test_case_insensitive_matching_by_default(self):
        """
        Matcher flags uppercase and titlecase sensitive phrases.
        """
        matcher = PatternMatcher()

        assert matcher.is_sensitive("PASSWORD") is True
        assert matcher.is_sensitive("Access_Token") is True

    def test_avoids_false_positives_from_embedded_substrings(self):
        """
        Matcher avoids false positives on words containing sensitive substrings like pass or key.
        """
        matcher = PatternMatcher()

        assert matcher.is_sensitive("passenger") is False
        assert matcher.is_sensitive("bypass") is False
        assert matcher.is_sensitive("compass") is False
        assert matcher.is_sensitive("monkey") is False
        assert matcher.is_sensitive("tokenized") is False

    def test_custom_dynamic_phrases_without_hardcoded_bias(self):
        """
        Matcher works with arbitrary custom phrases provided at initialization.
        """
        matcher = PatternMatcher(phrases=["custom_secret", "ssn_code"])

        assert matcher.is_sensitive("custom_secret") is True
        assert matcher.is_sensitive("ssn_code") is True
        assert matcher.is_sensitive("password") is False


class TestContentMaskingUtils:
    """
    Test suite for ContentMaskingUtils dictionary and value sanitization.
    """

    def test_filter_sensitive_content_top_level(self):
        """
        Sensitive top-level dictionary keys are replaced with mask string.
        """
        result = ContentMaskingUtils.filter_sensitive_content(
            password="secret_password",  # pragma: allowlist secret
            username="john_doe",
            token="bearer_12345",
        )

        assert result["password"] == "********"  # pragma: allowlist secret
        assert result["token"] == "********"
        assert result["username"] == "john_doe"

    def test_filter_sensitive_content_deep_search_nested_dict(self):
        """
        Nested dictionary keys and values are sanitized recursively when deep_search is True.
        """
        payload = {
            "user": {
                "name": "Jane",
                "secret_key": "topsecret",  # pragma: allowlist secret
            },
            "meta": {
                "count": 42,
            },
        }

        result = ContentMaskingUtils.filter_sensitive_content(
            deep_search=True, **payload
        )

        assert result["user"]["secret_key"] == "********"
        assert result["user"]["name"] == "Jane"
        assert result["meta"]["count"] == 42

    def test_filter_sensitive_content_deep_search_nested_list_of_dicts(self):
        """
        List containing dictionaries is recursively processed without unpacking errors.
        """
        payload = {
            "credentials": [
                {"id": 1, "password": "pass1"},  # pragma: allowlist secret
                {"id": 2, "password": "pass2"},  # pragma: allowlist secret
            ]
        }

        result = ContentMaskingUtils.filter_sensitive_content(
            deep_search=True, **payload
        )

        assert isinstance(result["credentials"], list)
        assert len(result["credentials"]) == 2
        assert result["credentials"][0]["password"] == "********"
        assert result["credentials"][1]["password"] == "********"

    def test_filter_sensitive_content_preserves_primitives_when_not_sensitive(self):
        """
        Non-string primitives such as integers, booleans, and floats are preserved intact.
        """
        payload = {
            "age": 30,
            "is_active": True,
            "score": 99.5,
        }

        result = ContentMaskingUtils.filter_sensitive_content(
            deep_search=True, **payload
        )

        assert result["age"] == 30
        assert result["is_active"] is True
        assert result["score"] == 99.5

    def test_filter_sensitive_content_stringified_output(self):
        """
        stringified=True returns formatted string representation of masked dictionary.
        """
        result = ContentMaskingUtils.filter_sensitive_content(
            stringified=True,
            password="secret_val",  # pragma: allowlist secret
            user="alice",
        )

        assert isinstance(result, str)
        assert "password:********" in result  # pragma: allowlist secret
        assert "user:alice" in result

    def test_filter_value_masks_email_and_phone(self):
        """
        filter_value sanitizes email addresses and phone numbers within string values.
        """
        matcher = get_sensitive_matcher()

        masked_email = ContentMaskingUtils.filter_value("contact@example.com", matcher)
        assert "contact@example.com" not in masked_email

        masked_phone = ContentMaskingUtils.filter_value("+1234567890", matcher)
        assert "+1234567890" not in masked_phone
