"""Tests for setup wizard schemas."""

from datetime import datetime
from uuid import uuid4

from groundwork.setup.schemas import InstanceConfigResponse


class TestInstanceConfigResponse:
    """Tests for InstanceConfigResponse schema."""

    def test_smtp_password_not_in_schema_fields(self) -> None:
        """InstanceConfigResponse should NOT have smtp_password field.

        This is a critical security requirement - SMTP passwords should never be
        returned in API responses.
        """
        # Verify the field is not present in the schema
        assert "smtp_password" not in InstanceConfigResponse.model_fields, (
            "SECURITY ISSUE: smtp_password field exists in InstanceConfigResponse!"
        )

    def test_smtp_password_excluded_from_serialization(self) -> None:
        """InstanceConfigResponse should NOT include smtp_password in serialized output.

        This is a critical security requirement - SMTP passwords should never be
        returned in API responses.
        """
        config_data = {
            "id": uuid4(),
            "instance_name": "Test Instance",
            "base_url": "https://example.com",
            "setup_completed": False,
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "user@example.com",
            "smtp_from_address": "noreply@example.com",
            "smtp_configured": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = InstanceConfigResponse(**config_data)
        serialized = response.model_dump()

        # The smtp_password should NOT be present in the serialized output
        assert "smtp_password" not in serialized, (
            "SECURITY ISSUE: smtp_password is being exposed in API responses!"
        )

    def test_smtp_password_excluded_from_json_serialization(self) -> None:
        """InstanceConfigResponse should NOT include smtp_password in JSON output."""
        config_data = {
            "id": uuid4(),
            "instance_name": "Test Instance",
            "base_url": "https://example.com",
            "setup_completed": False,
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "user@example.com",
            "smtp_from_address": "noreply@example.com",
            "smtp_configured": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = InstanceConfigResponse(**config_data)
        json_output = response.model_dump_json()

        # The smtp_password should NOT be present in the JSON output
        assert "smtp_password" not in json_output, (
            "SECURITY ISSUE: smtp_password is being exposed in JSON API responses!"
        )

    def test_other_smtp_fields_are_included(self) -> None:
        """Other SMTP fields should still be included in the response."""
        config_data = {
            "id": uuid4(),
            "instance_name": "Test Instance",
            "base_url": "https://example.com",
            "setup_completed": False,
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "user@example.com",
            "smtp_from_address": "noreply@example.com",
            "smtp_configured": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = InstanceConfigResponse(**config_data)
        serialized = response.model_dump()

        # These fields should all be present
        assert serialized["smtp_host"] == "smtp.example.com"
        assert serialized["smtp_port"] == 587
        assert serialized["smtp_username"] == "user@example.com"
        assert serialized["smtp_from_address"] == "noreply@example.com"
        assert serialized["smtp_configured"] is True
