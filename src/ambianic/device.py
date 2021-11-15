"""Base classes for an Ambianic Edge device abstraction"""
from pydantic import BaseModel, Field


class DeviceInfo(BaseModel):
    version: str = Field(None, description="Ambianic Edge software version.")
    display_name: str = Field(
        None, description="User friendly display name for this device."
    )
    notifications_enabled: bool = Field(
        False, description="Indicates whether device notifications are enabled."
    )
