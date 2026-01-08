"""
Data models for AV/IT incident analysis and RCA reporting.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class Severity(str, Enum):
    """Event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    """Category of operational events"""
    NETWORK = "network"
    AV_HARDWARE = "av_hardware"
    SOFTWARE = "software"
    CONFIGURATION = "configuration"
    USER_ACTION = "user_action"
    POWER = "power"
    ENVIRONMENT = "environment"
    VENDOR_SERVICE = "vendor_service"


class UrgencyLevel(str, Enum):
    """Action urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StructuredEvent(BaseModel):
    """Normalized event extracted from raw logs"""
    timestamp: datetime
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    room_name: Optional[str] = None
    service: Optional[str] = None
    event_type: str
    severity: Severity
    category: EventCategory
    message: str
    error_code: Optional[str] = None
    source_ip: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_log_line: str = ""

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RootCause(BaseModel):
    """Root cause analysis with confidence scoring"""
    description: str = Field(..., description="Clear description of the root cause")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence from logs")
    category: Optional[EventCategory] = None

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return round(v, 2)


class RecommendedAction(BaseModel):
    """Actionable recommendation with ownership"""
    action: str = Field(..., description="Specific action to take")
    owner: str = Field(..., description="Team or individual responsible")
    urgency: UrgencyLevel
    estimated_time: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class IncidentAnalysis(BaseModel):
    """Complete incident analysis and RCA report"""
    incident_summary: str
    time_window_analyzed: str
    affected_resources: List[str] = Field(default_factory=list)

    most_likely_root_cause: RootCause
    secondary_possible_causes: List[RootCause] = Field(default_factory=list)

    what_changed_before_incident: List[str] = Field(default_factory=list)
    recommended_next_actions: List[RecommendedAction] = Field(default_factory=list)

    is_repeat_issue: bool = False
    historical_context: str = ""

    escalation_guidance: str = ""
    data_gaps: List[str] = Field(default_factory=list)

    # Additional metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_events_analyzed: int = 0
    timeline: List[StructuredEvent] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary matching the specified output format"""
        return {
            "incident_summary": self.incident_summary,
            "time_window_analyzed": self.time_window_analyzed,
            "affected_resources": self.affected_resources,
            "most_likely_root_cause": {
                "description": self.most_likely_root_cause.description,
                "confidence": self.most_likely_root_cause.confidence,
                "evidence": self.most_likely_root_cause.evidence
            },
            "secondary_possible_causes": [
                {
                    "description": cause.description,
                    "confidence": cause.confidence,
                    "evidence": cause.evidence
                }
                for cause in self.secondary_possible_causes
            ],
            "what_changed_before_incident": self.what_changed_before_incident,
            "recommended_next_actions": [
                {
                    "action": action.action,
                    "owner": action.owner,
                    "urgency": action.urgency.value
                }
                for action in self.recommended_next_actions
            ],
            "is_repeat_issue": self.is_repeat_issue,
            "historical_context": self.historical_context,
            "escalation_guidance": self.escalation_guidance,
            "data_gaps": self.data_gaps
        }


class KnownPattern(BaseModel):
    """Known recurring failure pattern"""
    pattern_id: str
    name: str
    description: str
    symptoms: List[str]
    typical_root_cause: str
    affected_systems: List[str]
    frequency: str = "unknown"
    recommended_actions: List[str] = Field(default_factory=list)


class VendorContact(BaseModel):
    """Vendor escalation contact information"""
    vendor_name: str
    system_types: List[str]
    support_level: str
    contact_info: str
    escalation_criteria: List[str]
    sla_hours: Optional[int] = None
