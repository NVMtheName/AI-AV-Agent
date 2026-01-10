"""
Main AV Agent orchestrator.

Coordinates log parsing, correlation, and RCA to answer user queries.
"""

from typing import Optional, Dict, Any
import json

from .log_parser import LogParser
from .event_correlator import EventCorrelator
from .rca_engine import RCAEngine
from .report_generator import ReportGenerator
from .models import IncidentAnalysis
from .compliance.audit_logger import get_audit_logger, AuditEventType
from .compliance.access_control import get_access_control, AccessLevel


class AVAgent:
    """
    Expert AV/IT Operations Agent for root cause analysis.

    Specializes in:
    - Enterprise AV systems (Zoom Rooms, Q-SYS, Crestron, Cisco)
    - Corporate networking (VLANs, PoE, multicast, QoS, DNS, DHCP)
    - Facilities operations and incident response
    - Root cause analysis and postmortems
    """

    def __init__(
        self,
        known_patterns_path: Optional[str] = None,
        correlation_window_seconds: int = 300,
        enable_compliance: bool = True
    ):
        """
        Initialize AV Agent.

        Args:
            known_patterns_path: Path to YAML file with known failure patterns
            correlation_window_seconds: Time window for event correlation (default 5 min)
            enable_compliance: Enable SOC 2 compliance controls (audit logging, access control)
        """
        self.log_parser = LogParser()
        self.correlator = EventCorrelator(correlation_window_seconds)
        self.rca_engine = RCAEngine(known_patterns_path)
        self.report_generator = ReportGenerator()

        # Initialize compliance controls
        self.enable_compliance = enable_compliance
        if enable_compliance:
            self.audit_logger = get_audit_logger()
            self.access_control = get_access_control()
            self.audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_START,
                action="AVAgent initialized",
                details={"compliance_enabled": True}
            )
        else:
            self.audit_logger = None
            self.access_control = None

    def analyze(
        self,
        raw_logs: str,
        user_query: Optional[str] = None,
        output_format: str = "json"
    ) -> str:
        """
        Perform complete incident analysis.

        Args:
            raw_logs: Raw log text from AV/IT systems
            user_query: Natural language question from operator (e.g., "Why did Room 12 fail?")
            output_format: Output format - "json", "markdown", "summary", or "ticket"

        Returns:
            Formatted analysis report
        """

        # Audit log the analysis start
        if self.enable_compliance and self.audit_logger:
            self.audit_logger.log_event(
                event_type=AuditEventType.ANALYSIS_START,
                action="Starting root cause analysis",
                details={"query": user_query, "format": output_format}
            )

        try:
            # Step 1: Parse and normalize logs
            events = self.log_parser.parse_logs(raw_logs)

            if not events:
                empty_result = {
                    "incident_summary": "No events found in provided logs",
                    "time_window_analyzed": "N/A",
                    "affected_resources": [],
                    "most_likely_root_cause": {
                        "description": "No log data to analyze",
                        "confidence": 0.0,
                        "evidence": []
                    },
                    "secondary_possible_causes": [],
                    "what_changed_before_incident": [],
                    "recommended_next_actions": [],
                    "is_repeat_issue": False,
                    "historical_context": "",
                    "escalation_guidance": "",
                    "data_gaps": ["No log data provided or logs could not be parsed"]
                }
                if self.enable_compliance and self.audit_logger:
                    self.audit_logger.log_event(
                        event_type=AuditEventType.ANALYSIS_COMPLETE,
                        action="Analysis completed with no events",
                        status="success",
                        details={"events_found": 0}
                    )
                return json.dumps(empty_result, indent=2)

            # Step 2: Correlate events
            correlation_data = self.correlator.correlate_events(events)

            # Step 3: Perform RCA
            analysis = self.rca_engine.analyze(events, correlation_data, user_query)

            # Audit log successful analysis
            if self.enable_compliance and self.audit_logger:
                self.audit_logger.log_event(
                    event_type=AuditEventType.ANALYSIS_COMPLETE,
                    action="Root cause analysis completed",
                    status="success",
                    details={
                        "events_analyzed": len(events),
                        "root_cause_confidence": analysis.most_likely_root_cause.confidence if analysis.most_likely_root_cause else 0.0,
                        "query": user_query,
                    }
                )

            # Step 4: Generate output
            return self._format_output(analysis, output_format)

        except Exception as e:
            # Audit log the error
            if self.enable_compliance and self.audit_logger:
                self.audit_logger.log_error(
                    action="Root cause analysis failed",
                    error=e
                )
            raise

    def _format_output(self, analysis: IncidentAnalysis, format_type: str) -> str:
        """Format analysis output based on requested type"""

        if format_type == "markdown":
            return self.report_generator.generate_markdown_report(analysis)
        elif format_type == "summary":
            return self.report_generator.generate_summary_text(analysis)
        elif format_type == "ticket":
            return self.report_generator.generate_ticket_update(analysis)
        else:  # Default to JSON
            return self.report_generator.generate_json_report(analysis)

    def analyze_from_file(
        self,
        log_file_path: str,
        user_query: Optional[str] = None,
        output_format: str = "json"
    ) -> str:
        """
        Analyze logs from a file.

        Args:
            log_file_path: Path to log file
            user_query: Natural language question
            output_format: Output format

        Returns:
            Formatted analysis report
        """
        try:
            # Check access control
            if self.enable_compliance and self.access_control:
                if not self.access_control.validate_file_access(log_file_path, "read"):
                    error_msg = f"Access denied: Insufficient permissions to read {log_file_path}"
                    if self.audit_logger:
                        self.audit_logger.log_event(
                            event_type=AuditEventType.FILE_ACCESS,
                            action="File access denied",
                            resource=log_file_path,
                            status="failure",
                            details={"operation": "read", "reason": "insufficient_permissions"}
                        )
                    return json.dumps({
                        "error": error_msg,
                        "incident_summary": "Cannot analyze - access denied"
                    }, indent=2)

            # Log file access
            if self.enable_compliance and self.audit_logger:
                self.audit_logger.log_file_access(log_file_path, "read", "success")

            with open(log_file_path, 'r') as f:
                raw_logs = f.read()

            return self.analyze(raw_logs, user_query, output_format)

        except FileNotFoundError:
            if self.enable_compliance and self.audit_logger:
                self.audit_logger.log_event(
                    event_type=AuditEventType.FILE_ACCESS,
                    action="File access failed - file not found",
                    resource=log_file_path,
                    status="failure"
                )
            return json.dumps({
                "error": f"Log file not found: {log_file_path}",
                "incident_summary": "Cannot analyze - log file not found"
            }, indent=2)
        except Exception as e:
            if self.enable_compliance and self.audit_logger:
                self.audit_logger.log_error(
                    action="File read error",
                    error=e,
                    resource=log_file_path
                )
            return json.dumps({
                "error": f"Failed to read log file: {str(e)}",
                "incident_summary": "Cannot analyze - file read error"
            }, indent=2)

    def quick_answer(self, raw_logs: str, user_query: str) -> str:
        """
        Quick text answer to user question.

        Args:
            raw_logs: Raw log text
            user_query: User's question (e.g., "Why did Room 12 fail?")

        Returns:
            Concise text answer
        """
        result = self.analyze(raw_logs, user_query, output_format="summary")
        return result
