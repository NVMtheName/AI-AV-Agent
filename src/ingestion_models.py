"""
Unified event models for ingestion and normalization pipeline.

This module defines the canonical event format that ALL vendor-specific parsers
must normalize to. Preserves raw data for auditability.
"""

from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from uuid import uuid4
import json


# Type definitions for the unified schema
SourceType = Literal["av", "network", "compute", "app", "ticket", "change"]
SourceVendor = Literal[
    "zoom", "qsys", "crestron", "cisco", "meraki", "extron", "biamp",
    "windows", "linux", "macos",
    "servicenow", "jira", "manual",
    "unknown"
]
AssetType = Literal[
    "display", "codec", "dsp", "controller", "switch", "ap", "pc",
    "sensor", "camera", "microphone", "speaker", "other"
]
SeverityLevel = Literal["debug", "info", "notice", "warning", "error", "critical"]
EventCategory = Literal[
    "connectivity", "power", "audio", "video", "control", "auth",
    "performance", "config", "hardware", "user_action", "vendor_service"
]


class AssetInfo(BaseModel):
    """Asset identification and metadata"""
    asset_id: Optional[str] = None
    asset_type: Optional[AssetType] = None
    make: Optional[str] = None  # Manufacturer
    model: Optional[str] = None
    serial: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    hostname: Optional[str] = None
    firmware_version: Optional[str] = None

    class Config:
        extra = "allow"  # Allow additional vendor-specific fields


class RawPayload(BaseModel):
    """Preserves original raw data for auditability"""
    raw_line: str  # Original log line or CSV row
    raw_ts: Optional[str] = None  # Original timestamp string before normalization
    source_file: Optional[str] = None  # Source filename
    line_number: Optional[int] = None
    raw_fields: Dict[str, Any] = Field(default_factory=dict)  # Additional raw data

    class Config:
        extra = "allow"


class UnifiedEvent(BaseModel):
    """
    Canonical normalized event format.

    ALL parsers must convert vendor-specific logs to this schema.
    Designed for deterministic code-based parsing (no AI/LLM inference).
    """

    # Core identification
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    ts: datetime  # Normalized to UTC

    # Source classification
    source_type: SourceType
    source_vendor: SourceVendor
    source_system: str  # e.g., "zoom_rooms_controller", "qsys_core_110f", "cisco_catalyst_9300"

    # Location hierarchy (enterprise building structure)
    site: Optional[str] = None  # Campus or location code
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None

    # Asset information
    asset: Optional[AssetInfo] = None

    # Event classification
    severity: SeverityLevel
    category: EventCategory

    # Event content
    signal: str  # Stable machine-readable identifier (e.g., "dhcp.timeout", "zoom.offline")
    message: str  # Human-readable message

    # Correlation
    incident_id: Optional[str] = None  # Links to incident/ticket
    ticket_id: Optional[str] = None
    change_id: Optional[str] = None
    correlation_ids: Dict[str, str] = Field(default_factory=dict)  # Flexible correlation

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional structured data
    tags: list[str] = Field(default_factory=list)  # Searchable tags

    # Raw data preservation (MANDATORY for auditability)
    raw: RawPayload

    # Ingestion metadata
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    parser_version: str = "1.0.0"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @field_validator('ts', mode='before')
    @classmethod
    def normalize_timestamp(cls, v):
        """Ensure timestamp is datetime object in UTC"""
        if isinstance(v, str):
            from dateutil import parser as date_parser
            dt = date_parser.parse(v)
            # Convert to UTC if timezone-aware
            if dt.tzinfo is not None:
                dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            return dt
        elif isinstance(v, datetime):
            if v.tzinfo is not None:
                return v.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            return v
        raise ValueError(f"Cannot parse timestamp: {v}")

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary with ISO timestamps"""
        data = self.model_dump()
        data['ts'] = self.ts.isoformat() + 'Z'
        data['ingested_at'] = self.ingested_at.isoformat() + 'Z'
        return data

    def to_json(self) -> str:
        """Export as JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class TicketEvent(BaseModel):
    """
    Specialized model for ticket/incident imports.
    Gets converted to UnifiedEvent but preserves ticket-specific fields.
    """
    ticket_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    status: str  # open, in_progress, resolved, closed
    priority: str  # low, medium, high, critical
    category: str

    title: str
    description: str

    # Location
    site: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None

    # Assignment
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None

    # Impact
    affected_users: Optional[int] = None
    business_impact: Optional[str] = None

    # Metadata
    source_system: str  # servicenow, jira, etc.
    tags: list[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    # Raw data
    raw_csv_row: Dict[str, str] = Field(default_factory=dict)


class ChangeEvent(BaseModel):
    """
    Specialized model for change records (firmware updates, config changes, etc.)
    Gets converted to UnifiedEvent but preserves change-specific fields.
    """
    change_id: str
    change_type: str  # firmware_update, config_change, hardware_replacement, etc.

    scheduled_at: datetime
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    status: str  # scheduled, in_progress, completed, failed, rolled_back

    # What changed
    target_type: str  # device, system, service
    target_identifier: str  # IP, hostname, room name

    # Change details
    change_description: str
    changed_by: str  # User or system that made the change

    # Version tracking
    previous_version: Optional[str] = None
    new_version: Optional[str] = None

    # Configuration
    previous_config: Optional[str] = None  # JSON or config dump
    new_config: Optional[str] = None

    # Location
    site: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None

    # Impact assessment
    risk_level: Optional[str] = None  # low, medium, high
    expected_impact: Optional[str] = None
    actual_impact: Optional[str] = None

    # Metadata
    source_system: str
    approval_id: Optional[str] = None
    rollback_plan: Optional[str] = None

    # Raw data
    raw_csv_row: Dict[str, str] = Field(default_factory=dict)


class ParseResult(BaseModel):
    """
    Result container for parser operations.
    Includes success/failure tracking and error details.
    """
    success: bool
    events: list[UnifiedEvent] = Field(default_factory=list)

    # Error tracking
    total_lines: int = 0
    parsed_lines: int = 0
    failed_lines: int = 0
    errors: list[Dict[str, Any]] = Field(default_factory=list)

    # Parser metadata
    parser_name: str
    source_file: Optional[str] = None
    parsed_at: datetime = Field(default_factory=datetime.utcnow)

    def add_error(self, line_number: int, error_msg: str, raw_line: str = ""):
        """Record a parsing error"""
        self.errors.append({
            "line_number": line_number,
            "error": error_msg,
            "raw_line": raw_line[:200]  # Truncate long lines
        })
        self.failed_lines += 1

    def add_event(self, event: UnifiedEvent):
        """Add a successfully parsed event"""
        self.events.append(event)
        self.parsed_lines += 1
