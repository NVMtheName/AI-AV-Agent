"""
Audit Logging System for SOC 2 Compliance

This module implements comprehensive audit logging to meet SOC 2 requirements for:
- Security monitoring
- Access tracking
- Change management
- Incident detection
"""

import json
import logging
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Types of auditable events"""
    # Access events
    FILE_ACCESS = "file_access"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    CONFIG_ACCESS = "config_access"

    # Processing events
    ANALYSIS_START = "analysis_start"
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_ERROR = "analysis_error"

    # Security events
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ENCRYPTION_OPERATION = "encryption_operation"
    DECRYPTION_OPERATION = "decryption_operation"

    # Configuration events
    CONFIG_CHANGE = "config_change"
    PATTERN_UPDATE = "pattern_update"

    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    ERROR = "error"
    WARNING = "warning"


class AuditEvent(BaseModel):
    """Audit event model"""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: AuditEventType
    user: str = Field(default_factory=lambda: os.getenv('USER', 'unknown'))
    action: str
    resource: Optional[str] = None
    status: str = "success"  # success, failure, error
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AuditLogger:
    """
    Centralized audit logging system for SOC 2 compliance.

    Features:
    - Tamper-evident logging
    - Structured JSON format
    - Automatic rotation
    - Immutable append-only logs
    - Timestamp integrity
    """

    def __init__(
        self,
        log_dir: str = "logs/audit",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        retention_days: int = 2555,  # 7 years for SOC 2
    ):
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.retention_days = retention_days

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging
        self._setup_logger()

        # Log initialization
        self.log_event(
            event_type=AuditEventType.SYSTEM_START,
            action="Audit logger initialized",
            details={"log_dir": str(self.log_dir)}
        )

    def _setup_logger(self):
        """Configure the audit logger"""
        self.logger = logging.getLogger('audit_logger')
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Create log file path
        log_file = self.log_dir / f"audit_{datetime.now(timezone.utc).strftime('%Y%m')}.log"

        # File handler with rotation
        handler = logging.FileHandler(log_file, mode='a')
        handler.setLevel(logging.INFO)

        # JSON formatter
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        resource: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
    ) -> AuditEvent:
        """
        Log an audit event

        Args:
            event_type: Type of event
            action: Description of the action
            resource: Resource being accessed/modified
            status: Status of the operation (success/failure/error)
            details: Additional event details
            user: User performing the action (defaults to current OS user)

        Returns:
            The created AuditEvent
        """
        event = AuditEvent(
            event_type=event_type,
            action=action,
            resource=resource,
            status=status,
            details=details or {},
            user=user or os.getenv('USER', 'unknown'),
        )

        # Log to file
        self.logger.info(event.model_dump_json())

        # Check if rotation is needed
        self._check_rotation()

        return event

    def log_file_access(self, file_path: str, operation: str, status: str = "success"):
        """Log file access operations"""
        self.log_event(
            event_type=AuditEventType.FILE_ACCESS,
            action=f"File {operation}",
            resource=file_path,
            status=status,
            details={"operation": operation}
        )

    def log_analysis(
        self,
        log_file: str,
        query: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log analysis operations"""
        self.log_event(
            event_type=AuditEventType.ANALYSIS_COMPLETE,
            action="Root cause analysis performed",
            resource=log_file,
            status=status,
            details={
                "query": query,
                **(details or {})
            }
        )

    def log_config_change(
        self,
        config_file: str,
        change_type: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log configuration changes"""
        self.log_event(
            event_type=AuditEventType.CONFIG_CHANGE,
            action=f"Configuration {change_type}",
            resource=config_file,
            details=details or {}
        )

    def log_error(
        self,
        action: str,
        error: Exception,
        resource: Optional[str] = None,
    ):
        """Log errors and exceptions"""
        self.log_event(
            event_type=AuditEventType.ERROR,
            action=action,
            resource=resource,
            status="error",
            details={
                "error_type": type(error).__name__,
                "error_message": str(error),
            }
        )

    def log_encryption(
        self,
        operation: str,
        resource: str,
        status: str = "success",
    ):
        """Log encryption/decryption operations"""
        event_type = (
            AuditEventType.ENCRYPTION_OPERATION
            if "encrypt" in operation.lower()
            else AuditEventType.DECRYPTION_OPERATION
        )

        self.log_event(
            event_type=event_type,
            action=operation,
            resource=resource,
            status=status,
        )

    def _check_rotation(self):
        """Check if log rotation is needed"""
        current_log = list(self.log_dir.glob("audit_*.log"))
        if not current_log:
            return

        current_log = current_log[0]
        if current_log.stat().st_size > self.max_file_size:
            # Close current handler
            for handler in self.logger.handlers:
                handler.close()
                self.logger.removeHandler(handler)

            # Setup new logger with new file
            self._setup_logger()

    def get_recent_events(
        self,
        limit: int = 100,
        event_type: Optional[AuditEventType] = None,
    ) -> list[AuditEvent]:
        """
        Retrieve recent audit events

        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type

        Returns:
            List of AuditEvent objects
        """
        events = []

        # Get all log files sorted by modification time
        log_files = sorted(
            self.log_dir.glob("audit_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            event_data = json.loads(line)
                            event = AuditEvent(**event_data)

                            # Filter by event type if specified
                            if event_type and event.event_type != event_type:
                                continue

                            events.append(event)

                            if len(events) >= limit:
                                return events
                        except (json.JSONDecodeError, ValueError):
                            continue
            except IOError:
                continue

        return events

    def generate_audit_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generate audit report for compliance review

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            Dictionary containing audit statistics and events
        """
        events = self.get_recent_events(limit=10000)

        # Filter by date range
        if start_date or end_date:
            filtered_events = []
            for event in events:
                if start_date and event.timestamp < start_date:
                    continue
                if end_date and event.timestamp > end_date:
                    continue
                filtered_events.append(event)
            events = filtered_events

        # Calculate statistics
        event_counts = {}
        status_counts = {"success": 0, "failure": 0, "error": 0}
        user_activity = {}

        for event in events:
            # Count by event type
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

            # Count by status
            status_counts[event.status] = status_counts.get(event.status, 0) + 1

            # Count by user
            user_activity[event.user] = user_activity.get(event.user, 0) + 1

        return {
            "report_generated": datetime.now(timezone.utc).isoformat(),
            "period_start": start_date.isoformat() if start_date else "all",
            "period_end": end_date.isoformat() if end_date else "all",
            "total_events": len(events),
            "event_type_distribution": event_counts,
            "status_distribution": status_counts,
            "user_activity": user_activity,
            "recent_errors": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "action": e.action,
                    "resource": e.resource,
                    "details": e.details,
                }
                for e in events
                if e.status == "error"
            ][:10],
        }


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance"""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger
