"""
Root Cause Analysis (RCA) Engine

Applies expert knowledge and pattern matching to determine root causes.
Ranks causes by likelihood based on evidence from correlated events.
"""

from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import yaml
import os

from .models import (
    StructuredEvent,
    RootCause,
    RecommendedAction,
    IncidentAnalysis,
    EventCategory,
    Severity,
    UrgencyLevel,
    KnownPattern
)


class RCAEngine:
    """
    Expert system for root cause analysis of enterprise AV/IT incidents.

    Principles:
    - Prefer simple causes over exotic ones (Occam's Razor)
    - Consider recent changes first
    - Recognize recurring failure patterns
    - Distinguish symptoms from root causes
    """

    def __init__(self, known_patterns_path: Optional[str] = None):
        """
        Initialize RCA engine.

        Args:
            known_patterns_path: Path to YAML file with known failure patterns
        """
        self.known_patterns = []
        if known_patterns_path and os.path.exists(known_patterns_path):
            self.known_patterns = self._load_known_patterns(known_patterns_path)

    def _load_known_patterns(self, path: str) -> List[KnownPattern]:
        """Load known failure patterns from YAML"""
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                return [KnownPattern(**pattern) for pattern in data.get('patterns', [])]
        except Exception as e:
            print(f"Warning: Could not load known patterns: {e}")
            return []

    def analyze(
        self,
        events: List[StructuredEvent],
        correlation_data: Dict,
        user_query: Optional[str] = None
    ) -> IncidentAnalysis:
        """
        Perform comprehensive root cause analysis.

        Args:
            events: Structured events from log parser
            correlation_data: Output from EventCorrelator
            user_query: Optional user question for context

        Returns:
            Complete incident analysis with ranked causes
        """

        if not events:
            return self._empty_analysis("No events to analyze")

        # Identify the primary failure
        primary_failure = self._identify_primary_failure(events, correlation_data)

        # Find what changed before the incident
        changes = self._analyze_changes(events, correlation_data, primary_failure)

        # Generate candidate root causes
        candidate_causes = self._generate_candidate_causes(
            events,
            correlation_data,
            primary_failure,
            changes
        )

        # Rank causes by evidence and likelihood
        ranked_causes = self._rank_causes(candidate_causes)

        if not ranked_causes:
            ranked_causes = [
                RootCause(
                    description="Insufficient data to determine root cause",
                    confidence=0.1,
                    evidence=["No clear error patterns found in available logs"]
                )
            ]

        # Check for repeat issues
        is_repeat, historical_context = self._check_repeat_issue(events, correlation_data)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            ranked_causes[0],
            events,
            correlation_data
        )

        # Identify data gaps
        data_gaps = self._identify_data_gaps(events, correlation_data)

        # Generate escalation guidance
        escalation = self._generate_escalation_guidance(ranked_causes[0], events)

        # Build time window
        time_window = self._format_time_window(events)

        # Extract affected resources
        affected_resources = list(correlation_data.get('affected_resources', set()))

        # Build final analysis
        analysis = IncidentAnalysis(
            incident_summary=self._generate_summary(events, ranked_causes[0], user_query),
            time_window_analyzed=time_window,
            affected_resources=affected_resources,
            most_likely_root_cause=ranked_causes[0],
            secondary_possible_causes=ranked_causes[1:4] if len(ranked_causes) > 1 else [],
            what_changed_before_incident=changes,
            recommended_next_actions=recommendations,
            is_repeat_issue=is_repeat,
            historical_context=historical_context,
            escalation_guidance=escalation,
            data_gaps=data_gaps,
            total_events_analyzed=len(events),
            timeline=events[:10]  # Include first 10 events in timeline
        )

        return analysis

    def _identify_primary_failure(
        self,
        events: List[StructuredEvent],
        correlation_data: Dict
    ) -> Optional[StructuredEvent]:
        """Identify the most critical failure event"""

        # Check error bursts first
        bursts = correlation_data.get('error_bursts', [])
        if bursts:
            # First burst is likely the primary incident
            return bursts[0]['events'][0]

        # Check cascading failures
        cascades = correlation_data.get('cascading_failures', [])
        if cascades:
            return cascades[0]['primary_event']

        # Find first critical or error event
        for event in events:
            if event.severity in [Severity.CRITICAL, Severity.ERROR]:
                return event

        # No clear failure - return first event
        return events[0] if events else None

    def _analyze_changes(
        self,
        events: List[StructuredEvent],
        correlation_data: Dict,
        primary_failure: Optional[StructuredEvent]
    ) -> List[str]:
        """Identify changes that occurred before the incident"""

        changes = []
        change_events = correlation_data.get('change_events', [])

        if not primary_failure:
            # Just list all changes
            return [f"{e.timestamp.isoformat()}: {e.message}" for e in change_events[:5]]

        # Find changes before the primary failure
        for event in change_events:
            if event.timestamp < primary_failure.timestamp:
                time_before = primary_failure.timestamp - event.timestamp
                if time_before <= timedelta(hours=24):  # Within 24 hours
                    changes.append(
                        f"{event.timestamp.isoformat()} ({int(time_before.total_seconds()/60)} min before failure): {event.message}"
                    )

        return changes[:5]  # Top 5 recent changes

    def _generate_candidate_causes(
        self,
        events: List[StructuredEvent],
        correlation_data: Dict,
        primary_failure: Optional[StructuredEvent],
        changes: List[str]
    ) -> List[RootCause]:
        """Generate all possible root causes based on evidence"""

        candidates = []

        # Check for known patterns
        candidates.extend(self._match_known_patterns(events))

        # Network-based causes
        candidates.extend(self._analyze_network_causes(events, correlation_data))

        # Configuration change causes
        if changes:
            candidates.extend(self._analyze_configuration_causes(events, changes))

        # Hardware causes
        candidates.extend(self._analyze_hardware_causes(events, correlation_data))

        # Power-related causes
        candidates.extend(self._analyze_power_causes(events))

        # Service/software causes
        candidates.extend(self._analyze_software_causes(events, correlation_data))

        return candidates

    def _match_known_patterns(self, events: List[StructuredEvent]) -> List[RootCause]:
        """Match events against known failure patterns"""
        causes = []

        for pattern in self.known_patterns:
            match_score = 0
            evidence = []

            for symptom in pattern.symptoms:
                for event in events:
                    if symptom.lower() in event.message.lower():
                        match_score += 1
                        evidence.append(f"Pattern symptom detected: {symptom}")
                        break

            if match_score >= len(pattern.symptoms) * 0.5:  # 50% match threshold
                confidence = min(0.95, match_score / len(pattern.symptoms))
                causes.append(RootCause(
                    description=f"{pattern.name}: {pattern.typical_root_cause}",
                    confidence=confidence,
                    evidence=evidence,
                    category=None  # Pattern-based
                ))

        return causes

    def _analyze_network_causes(
        self,
        events: List[StructuredEvent],
        correlation_data: Dict
    ) -> List[RootCause]:
        """Analyze network-related root causes"""
        causes = []

        network_events = [e for e in events if e.category == EventCategory.NETWORK]
        network_errors = [e for e in network_events if e.severity in [Severity.ERROR, Severity.CRITICAL]]

        if network_errors:
            evidence = []

            # Check for specific network issues
            dhcp_issues = [e for e in network_errors if 'dhcp' in e.message.lower()]
            dns_issues = [e for e in network_errors if 'dns' in e.message.lower()]
            connectivity_issues = [e for e in network_errors if any(
                kw in e.message.lower() for kw in ['unreachable', 'timeout', 'connection refused']
            )]

            if dhcp_issues:
                evidence.append(f"DHCP failures detected: {len(dhcp_issues)} events")
                causes.append(RootCause(
                    description="DHCP server failure or IP address exhaustion",
                    confidence=0.85,
                    evidence=evidence + [e.message for e in dhcp_issues[:2]],
                    category=EventCategory.NETWORK
                ))

            if dns_issues:
                evidence.append(f"DNS resolution failures: {len(dns_issues)} events")
                causes.append(RootCause(
                    description="DNS server unreachable or misconfigured",
                    confidence=0.80,
                    evidence=evidence + [e.message for e in dns_issues[:2]],
                    category=EventCategory.NETWORK
                ))

            if connectivity_issues:
                # Check if network event precedes other failures
                cascades = correlation_data.get('cascading_failures', [])
                if cascades and cascades[0]['primary_event'].category == EventCategory.NETWORK:
                    causes.append(RootCause(
                        description="Network connectivity loss causing cascading service failures",
                        confidence=0.90,
                        evidence=[
                            f"Network failure at {cascades[0]['primary_event'].timestamp}",
                            f"Followed by {len(cascades[0]['subsequent_errors'])} service failures",
                            cascades[0]['primary_event'].message
                        ],
                        category=EventCategory.NETWORK
                    ))
                else:
                    causes.append(RootCause(
                        description="Intermittent network connectivity issues",
                        confidence=0.70,
                        evidence=[e.message for e in connectivity_issues[:3]],
                        category=EventCategory.NETWORK
                    ))

        return causes

    def _analyze_configuration_causes(
        self,
        events: List[StructuredEvent],
        changes: List[str]
    ) -> List[RootCause]:
        """Analyze configuration change causes"""
        causes = []

        if changes:
            # Configuration change followed by errors is highly suspicious
            config_events = [e for e in events if e.category == EventCategory.CONFIGURATION]

            if config_events:
                causes.append(RootCause(
                    description="Recent configuration change introduced instability",
                    confidence=0.85,
                    evidence=changes[:3] + [
                        "Configuration changes detected shortly before incident"
                    ],
                    category=EventCategory.CONFIGURATION
                ))

        return causes

    def _analyze_hardware_causes(
        self,
        events: List[StructuredEvent],
        correlation_data: Dict
    ) -> List[RootCause]:
        """Analyze AV hardware-related causes"""
        causes = []

        hw_events = [e for e in events if e.category == EventCategory.AV_HARDWARE]
        hw_errors = [e for e in hw_events if e.severity in [Severity.ERROR, Severity.CRITICAL]]

        if hw_errors:
            # Check for specific hardware failures
            camera_issues = [e for e in hw_errors if 'camera' in e.message.lower()]
            usb_issues = [e for e in hw_errors if 'usb' in e.message.lower()]
            codec_issues = [e for e in hw_errors if any(
                kw in e.message.lower() for kw in ['codec', 'zoom', 'crestron', 'q-sys']
            )]

            if camera_issues:
                causes.append(RootCause(
                    description="Camera hardware failure or disconnection",
                    confidence=0.75,
                    evidence=[e.message for e in camera_issues[:2]],
                    category=EventCategory.AV_HARDWARE
                ))

            if usb_issues:
                causes.append(RootCause(
                    description="USB device failure or power issue (check PoE/power supply)",
                    confidence=0.80,
                    evidence=[e.message for e in usb_issues[:2]],
                    category=EventCategory.AV_HARDWARE
                ))

            if codec_issues:
                causes.append(RootCause(
                    description="AV codec/controller malfunction or network connectivity loss",
                    confidence=0.75,
                    evidence=[e.message for e in codec_issues[:2]],
                    category=EventCategory.AV_HARDWARE
                ))

        return causes

    def _analyze_power_causes(self, events: List[StructuredEvent]) -> List[RootCause]:
        """Analyze power-related causes"""
        causes = []

        power_events = [e for e in events if e.category == EventCategory.POWER]
        power_errors = [e for e in power_events if e.severity in [Severity.ERROR, Severity.CRITICAL]]

        if power_errors:
            poe_issues = [e for e in power_errors if 'poe' in e.message.lower()]

            if poe_issues:
                causes.append(RootCause(
                    description="PoE (Power over Ethernet) failure - insufficient power budget or switch issue",
                    confidence=0.85,
                    evidence=[e.message for e in poe_issues[:2]],
                    category=EventCategory.POWER
                ))
            else:
                causes.append(RootCause(
                    description="Power supply interruption or brownout",
                    confidence=0.70,
                    evidence=[e.message for e in power_errors[:2]],
                    category=EventCategory.POWER
                ))

        return causes

    def _analyze_software_causes(
        self,
        events: List[StructuredEvent],
        correlation_data: Dict
    ) -> List[RootCause]:
        """Analyze software/service causes"""
        causes = []

        sw_events = [e for e in events if e.category == EventCategory.SOFTWARE]
        sw_errors = [e for e in sw_events if e.severity in [Severity.ERROR, Severity.CRITICAL]]

        if sw_errors:
            auth_issues = [e for e in sw_errors if 'auth' in e.message.lower() or 'credential' in e.message.lower()]
            firmware_issues = [e for e in sw_errors if 'firmware' in e.message.lower() or 'update' in e.message.lower()]

            if auth_issues:
                causes.append(RootCause(
                    description="Authentication failure - expired credentials or service account issue",
                    confidence=0.80,
                    evidence=[e.message for e in auth_issues[:2]],
                    category=EventCategory.SOFTWARE
                ))

            if firmware_issues:
                causes.append(RootCause(
                    description="Firmware update failure or incompatibility",
                    confidence=0.75,
                    evidence=[e.message for e in firmware_issues[:2]],
                    category=EventCategory.SOFTWARE
                ))

        return causes

    def _rank_causes(self, candidates: List[RootCause]) -> List[RootCause]:
        """Rank causes by confidence score"""
        # Remove duplicates
        unique_causes = {}
        for cause in candidates:
            if cause.description not in unique_causes:
                unique_causes[cause.description] = cause
            else:
                # Merge evidence if duplicate found
                existing = unique_causes[cause.description]
                existing.evidence.extend(cause.evidence)
                existing.confidence = max(existing.confidence, cause.confidence)

        # Sort by confidence descending
        ranked = sorted(unique_causes.values(), key=lambda c: c.confidence, reverse=True)
        return ranked

    def _check_repeat_issue(
        self,
        events: List[StructuredEvent],
        correlation_data: Dict
    ) -> tuple[bool, str]:
        """Check if this is a recurring issue"""

        patterns = correlation_data.get('temporal_patterns', {})
        recurring = patterns.get('recurring_intervals', [])

        if recurring:
            interval_data = recurring[0]
            return (
                True,
                f"This issue recurs {interval_data['pattern']} with {interval_data['occurrences']} occurrences detected. "
                f"Indicates a systemic issue requiring permanent fix, not temporary workaround."
            )

        # Check error bursts for multiple incidents
        bursts = correlation_data.get('error_bursts', [])
        if len(bursts) > 1:
            return (
                True,
                f"Multiple error bursts detected ({len(bursts)} incidents). Pattern suggests recurring problem."
            )

        return (False, "")

    def _generate_recommendations(
        self,
        root_cause: RootCause,
        events: List[StructuredEvent],
        correlation_data: Dict
    ) -> List[RecommendedAction]:
        """Generate actionable recommendations based on root cause"""

        recommendations = []

        # Category-specific recommendations
        if root_cause.category == EventCategory.NETWORK:
            recommendations.extend([
                RecommendedAction(
                    action="Verify network switch port status and PoE power budget",
                    owner="Network Team",
                    urgency=UrgencyLevel.HIGH
                ),
                RecommendedAction(
                    action="Check DHCP server logs and available IP pool",
                    owner="Network Team",
                    urgency=UrgencyLevel.HIGH
                ),
                RecommendedAction(
                    action="Test connectivity from affected device subnet to required services",
                    owner="Network Team",
                    urgency=UrgencyLevel.MEDIUM
                )
            ])

        elif root_cause.category == EventCategory.AV_HARDWARE:
            recommendations.extend([
                RecommendedAction(
                    action="Physically inspect affected AV equipment and cable connections",
                    owner="AV Team / Facilities",
                    urgency=UrgencyLevel.HIGH
                ),
                RecommendedAction(
                    action="Review equipment firmware versions and update if outdated",
                    owner="AV Team",
                    urgency=UrgencyLevel.MEDIUM
                ),
                RecommendedAction(
                    action="Test with known-good spare equipment to isolate hardware failure",
                    owner="AV Team",
                    urgency=UrgencyLevel.MEDIUM
                )
            ])

        elif root_cause.category == EventCategory.CONFIGURATION:
            recommendations.extend([
                RecommendedAction(
                    action="Review and rollback recent configuration changes",
                    owner="AV/IT Operations",
                    urgency=UrgencyLevel.HIGH
                ),
                RecommendedAction(
                    action="Compare current config against last known good configuration",
                    owner="AV/IT Operations",
                    urgency=UrgencyLevel.HIGH
                )
            ])

        elif root_cause.category == EventCategory.SOFTWARE:
            recommendations.extend([
                RecommendedAction(
                    action="Verify service account credentials and refresh authentication tokens",
                    owner="IT Security / AV Team",
                    urgency=UrgencyLevel.HIGH
                ),
                RecommendedAction(
                    action="Review software/firmware update logs for failures",
                    owner="AV Team",
                    urgency=UrgencyLevel.MEDIUM
                )
            ])

        elif root_cause.category == EventCategory.POWER:
            recommendations.extend([
                RecommendedAction(
                    action="Check PoE switch power budget and port allocation",
                    owner="Network Team",
                    urgency=UrgencyLevel.HIGH
                ),
                RecommendedAction(
                    action="Verify power supply status for affected equipment",
                    owner="Facilities / AV Team",
                    urgency=UrgencyLevel.HIGH
                )
            ])

        # Generic recommendations
        recommendations.append(
            RecommendedAction(
                action="Document incident timeline and resolution in ticketing system",
                owner="Incident Owner",
                urgency=UrgencyLevel.LOW
            )
        )

        # If repeat issue, add preventive action
        if correlation_data and correlation_data.get('temporal_patterns', {}).get('recurring_intervals'):
            recommendations.insert(0, RecommendedAction(
                action="Implement permanent fix - this is a recurring issue requiring root cause elimination",
                owner="Engineering Team",
                urgency=UrgencyLevel.HIGH
            ))

        return recommendations

    def _identify_data_gaps(
        self,
        events: List[StructuredEvent],
        correlation_data: Dict
    ) -> List[str]:
        """Identify missing data that would improve analysis"""

        gaps = []

        # Check for missing device information
        devices_without_id = [e for e in events if not e.device_id and not e.room_name]
        if len(devices_without_id) > len(events) * 0.3:
            gaps.append("Many events lack device identification - improve logging to include device IDs")

        # Check for missing timestamps
        recent_events = [e for e in events if (datetime.utcnow() - e.timestamp).days < 1]
        if not recent_events and events:
            gaps.append("No recent events found - verify log collection is current")

        # Check for single system visibility
        categories = set(e.category for e in events)
        if len(categories) == 1:
            gaps.append(f"Only {categories.pop().value} logs available - correlate with network/system logs for complete picture")

        if not correlation_data.get('change_events'):
            gaps.append("No configuration change events detected - verify change logging is enabled")

        return gaps

    def _generate_escalation_guidance(
        self,
        root_cause: RootCause,
        events: List[StructuredEvent]
    ) -> str:
        """Generate vendor escalation guidance"""

        if not root_cause.category:
            return "Gather additional diagnostic data before escalating to vendors."

        category_escalation = {
            EventCategory.NETWORK: (
                "Escalate to Network Team with:\n"
                "- Switch port configurations and PoE status\n"
                "- DHCP/DNS server logs\n"
                "- Network topology diagram\n"
                "- Recent network changes"
            ),
            EventCategory.AV_HARDWARE: (
                "Escalate to AV vendor (Zoom/Crestron/Q-SYS) with:\n"
                "- Device serial numbers and firmware versions\n"
                "- Detailed error codes and timestamps\n"
                "- Recent hardware/software changes\n"
                "- Results of hardware connectivity tests"
            ),
            EventCategory.SOFTWARE: (
                "Escalate to Software vendor with:\n"
                "- Application version and build number\n"
                "- Full error logs and stack traces\n"
                "- Steps to reproduce\n"
                "- Configuration files (sanitized)"
            ),
            EventCategory.CONFIGURATION: (
                "Internal escalation to Configuration Management with:\n"
                "- Change request tickets\n"
                "- Configuration diffs\n"
                "- Rollback procedures\n"
                "- Impact assessment"
            ),
            EventCategory.POWER: (
                "Escalate to Facilities and Network Teams with:\n"
                "- PoE switch model and power budget report\n"
                "- Power consumption per device\n"
                "- UPS/power infrastructure status\n"
                "- Recent electrical work"
            )
        }

        return category_escalation.get(
            root_cause.category,
            "Collect all available logs and error messages before escalating."
        )

    def _format_time_window(self, events: List[StructuredEvent]) -> str:
        """Format the time window analyzed"""
        if not events:
            return "No events"

        earliest = min(e.timestamp for e in events)
        latest = max(e.timestamp for e in events)

        duration = latest - earliest

        return f"{earliest.isoformat()} to {latest.isoformat()} ({duration})"

    def _generate_summary(
        self,
        events: List[StructuredEvent],
        root_cause: RootCause,
        user_query: Optional[str]
    ) -> str:
        """Generate incident summary"""

        error_count = sum(1 for e in events if e.severity in [Severity.ERROR, Severity.CRITICAL])
        affected_rooms = set(e.room_name for e in events if e.room_name)

        summary_parts = []

        if user_query:
            summary_parts.append(f"Analysis of: '{user_query}'")

        if affected_rooms:
            summary_parts.append(f"Affecting {len(affected_rooms)} room(s): {', '.join(list(affected_rooms)[:3])}")

        summary_parts.append(f"Analyzed {len(events)} events with {error_count} errors/critical events")
        summary_parts.append(f"Root cause: {root_cause.description}")

        return ". ".join(summary_parts) + "."

    def _empty_analysis(self, message: str) -> IncidentAnalysis:
        """Return empty analysis when no data available"""
        return IncidentAnalysis(
            incident_summary=message,
            time_window_analyzed="N/A",
            affected_resources=[],
            most_likely_root_cause=RootCause(
                description="No data available for analysis",
                confidence=0.0,
                evidence=[]
            ),
            data_gaps=["No log data provided"]
        )
