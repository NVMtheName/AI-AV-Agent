"""
Log parser and event normalizer for enterprise AV/IT systems.

Supports common log formats from:
- Zoom Rooms
- Q-SYS
- Crestron
- Cisco networking equipment
- Domotz monitoring
- Generic syslog
"""

import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from dateutil import parser as date_parser

from .models import StructuredEvent, Severity, EventCategory


class LogParser:
    """
    Parses raw operational logs and normalizes them into structured events.

    Does NOT perform root cause analysis - only extracts factual events.
    """

    # Common timestamp patterns
    TIMESTAMP_PATTERNS = [
        r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?',  # ISO 8601
        r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',  # Syslog format
        r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',  # MM/DD/YYYY HH:MM:SS
    ]

    # Device identification patterns
    DEVICE_PATTERNS = {
        'room': r'(?:room|conference|meeting)[\s_-]?(\w+\d+)',
        'zoom_room': r'zoom[\s_-]?room[\s_-]?(\w+)',
        'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'mac_address': r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b',
        'hostname': r'(?:host|device|node):\s*([a-zA-Z0-9_-]+)',
    }

    # Error/severity indicators
    SEVERITY_KEYWORDS = {
        Severity.CRITICAL: [
            'critical', 'fatal', 'emergency', 'down', 'failed', 'offline',
            'unreachable', 'unresponsive', 'crash', 'panic'
        ],
        Severity.ERROR: [
            'error', 'fail', 'exception', 'denied', 'timeout', 'refused',
            'unavailable', 'disconnected', 'lost'
        ],
        Severity.WARNING: [
            'warn', 'warning', 'degraded', 'slow', 'retry', 'delay',
            'latency', 'jitter', 'packet loss'
        ],
        Severity.INFO: [
            'info', 'start', 'stop', 'connect', 'success', 'complete',
            'configured', 'enabled', 'disabled'
        ]
    }

    # System categorization
    CATEGORY_KEYWORDS = {
        EventCategory.NETWORK: [
            'network', 'ethernet', 'wifi', 'dhcp', 'dns', 'vlan', 'switch',
            'router', 'ping', 'tcp', 'udp', 'port', 'gateway', 'multicast',
            'qos', 'bandwidth', 'latency', 'packet'
        ],
        EventCategory.AV_HARDWARE: [
            'camera', 'microphone', 'speaker', 'display', 'projector',
            'hdmi', 'usb', 'codec', 'dsp', 'amplifier', 'zoom room',
            'crestron', 'q-sys', 'cisco', 'touch panel'
        ],
        EventCategory.SOFTWARE: [
            'software', 'firmware', 'application', 'service', 'process',
            'update', 'patch', 'version', 'driver', 'api', 'authentication'
        ],
        EventCategory.CONFIGURATION: [
            'config', 'setting', 'parameter', 'provision', 'deploy',
            'change', 'modify', 'update setting'
        ],
        EventCategory.POWER: [
            'power', 'poe', 'voltage', 'battery', 'shutdown', 'reboot',
            'restart', 'boot'
        ],
    }

    def __init__(self):
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Pre-compile regex patterns for performance"""
        patterns = {}
        for name, pattern in self.DEVICE_PATTERNS.items():
            patterns[name] = re.compile(pattern, re.IGNORECASE)
        for ts_pattern in self.TIMESTAMP_PATTERNS:
            patterns[f'ts_{len(patterns)}'] = re.compile(ts_pattern)
        return patterns

    def parse_logs(self, raw_logs: str) -> List[StructuredEvent]:
        """
        Parse raw log text into structured events.

        Args:
            raw_logs: Raw log text (multi-line)

        Returns:
            List of structured events with metadata
        """
        events = []
        lines = raw_logs.strip().split('\n')

        for line_num, line in enumerate(lines, 1):
            if not line.strip() or line.strip().startswith('#'):
                continue  # Skip empty lines and comments

            try:
                event = self._parse_line(line, line_num)
                if event:
                    events.append(event)
            except Exception as e:
                # Log parsing errors but continue processing
                print(f"Warning: Failed to parse line {line_num}: {e}")
                continue

        return events

    def _parse_line(self, line: str, line_num: int) -> Optional[StructuredEvent]:
        """Parse a single log line into a structured event"""

        # Extract timestamp
        timestamp = self._extract_timestamp(line)

        # Extract device/room information
        device_info = self._extract_device_info(line)

        # Determine severity
        severity = self._determine_severity(line)

        # Categorize event
        category = self._categorize_event(line)

        # Extract error codes
        error_code = self._extract_error_code(line)

        # Extract service/component
        service = self._extract_service(line)

        # Build event
        event = StructuredEvent(
            timestamp=timestamp,
            device_id=device_info.get('device_id'),
            device_type=device_info.get('device_type'),
            room_name=device_info.get('room_name'),
            service=service,
            event_type=self._classify_event_type(line, severity),
            severity=severity,
            category=category,
            message=line.strip(),
            error_code=error_code,
            source_ip=device_info.get('ip_address'),
            raw_log_line=line,
            metadata={
                'line_number': line_num,
                'parsed_device_info': device_info
            }
        )

        return event

    def _extract_timestamp(self, line: str) -> datetime:
        """Extract timestamp from log line"""
        for pattern_name, pattern in self.compiled_patterns.items():
            if pattern_name.startswith('ts_'):
                match = pattern.search(line)
                if match:
                    try:
                        return date_parser.parse(match.group(0))
                    except:
                        pass

        # Default to current time if no timestamp found
        return datetime.utcnow()

    def _extract_device_info(self, line: str) -> Dict[str, Optional[str]]:
        """Extract device/room identification"""
        info = {
            'device_id': None,
            'device_type': None,
            'room_name': None,
            'ip_address': None
        }

        # Room name
        room_match = self.compiled_patterns['room'].search(line)
        if room_match:
            info['room_name'] = room_match.group(1)

        # IP address
        ip_match = self.compiled_patterns['ip_address'].search(line)
        if ip_match:
            info['ip_address'] = ip_match.group(0)
            info['device_id'] = ip_match.group(0)

        # Hostname
        host_match = self.compiled_patterns['hostname'].search(line)
        if host_match:
            info['device_id'] = host_match.group(1)

        # Device type detection
        line_lower = line.lower()
        if 'zoom' in line_lower:
            info['device_type'] = 'Zoom Room'
        elif 'crestron' in line_lower:
            info['device_type'] = 'Crestron'
        elif 'q-sys' in line_lower or 'qsys' in line_lower:
            info['device_type'] = 'Q-SYS'
        elif 'cisco' in line_lower:
            info['device_type'] = 'Cisco'
        elif 'switch' in line_lower or 'netgear' in line_lower:
            info['device_type'] = 'Network Switch'

        return info

    def _determine_severity(self, line: str) -> Severity:
        """Determine event severity based on keywords"""
        line_lower = line.lower()

        # Check in priority order: critical -> error -> warning -> info
        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            if any(keyword in line_lower for keyword in keywords):
                return severity

        return Severity.INFO

    def _categorize_event(self, line: str) -> EventCategory:
        """Categorize event by system type"""
        line_lower = line.lower()

        # Score each category
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in line_lower)
            if score > 0:
                scores[category] = score

        if scores:
            # Return category with highest score
            return max(scores.items(), key=lambda x: x[1])[0]

        # Default to software if unclear
        return EventCategory.SOFTWARE

    def _extract_error_code(self, line: str) -> Optional[str]:
        """Extract error codes (e.g., ERR-1234, Error 500)"""
        patterns = [
            r'(?:error|err)[\s:-]*(\d+)',
            r'(?:code|status)[\s:-]*(\d+)',
            r'\b(ERR-\d+)\b',
            r'\b(0x[0-9A-Fa-f]+)\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_service(self, line: str) -> Optional[str]:
        """Extract service or component name"""
        # Common service patterns
        service_pattern = r'\[([A-Za-z0-9_-]+)\]'
        match = re.search(service_pattern, line)
        if match:
            return match.group(1)

        # Check for explicit service mentions
        service_keywords = ['zoom', 'dhcp', 'dns', 'ssh', 'http', 'https', 'ntp']
        line_lower = line.lower()
        for keyword in service_keywords:
            if keyword in line_lower:
                return keyword.upper()

        return None

    def _classify_event_type(self, line: str, severity: Severity) -> str:
        """Classify the type of event"""
        line_lower = line.lower()

        event_types = {
            'connection': ['connect', 'disconnect', 'connection', 'link up', 'link down'],
            'authentication': ['auth', 'login', 'logout', 'credential'],
            'configuration_change': ['config', 'configured', 'setting changed'],
            'boot': ['boot', 'startup', 'restart', 'reboot'],
            'timeout': ['timeout', 'timed out'],
            'packet_loss': ['packet loss', 'dropped packets'],
            'service_failure': ['service failed', 'service down'],
        }

        for event_type, keywords in event_types.items():
            if any(keyword in line_lower for keyword in keywords):
                return event_type

        # Fallback based on severity
        if severity == Severity.CRITICAL or severity == Severity.ERROR:
            return 'error'
        elif severity == Severity.WARNING:
            return 'warning'
        else:
            return 'informational'
