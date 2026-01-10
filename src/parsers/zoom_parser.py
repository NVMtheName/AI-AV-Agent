"""
Zoom Rooms log parser.

Deterministically parses Zoom Rooms logs into UnifiedEvent format.

Supported log formats:
- Zoom Rooms Controller logs
- Zoom Rooms client logs
- ZR Health API exports

Example log lines:
    2026-01-08T14:23:45Z [INFO] Room: CR-101 | ZoomRoom connected successfully
    2026-01-08T14:30:12Z [ERROR] Room: CR-205 | Network connection lost - DHCP timeout
    Jan 8 14:45:23 zr-cr-101 zrclient[1234]: Camera offline - USB enumeration failed
"""

import re
from datetime import datetime
from typing import Optional
from pathlib import Path

from .base_parser import BaseParser
import sys
sys.path.append(str(Path(__file__).parent.parent))
from ingestion_models import UnifiedEvent, AssetInfo, EventCategory, SeverityLevel


class ZoomRoomsParser(BaseParser):
    """Parser for Zoom Rooms operational logs"""

    def __init__(self):
        super().__init__(
            parser_name="ZoomRoomsParser",
            source_type="av",
            source_vendor="zoom"
        )

    def _compile_patterns(self):
        """Compile Zoom-specific regex patterns"""

        # Timestamp patterns (Zoom uses ISO 8601 and syslog formats)
        self._compiled_patterns['ts_iso'] = re.compile(
            r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)'
        )
        self._compiled_patterns['ts_syslog'] = re.compile(
            r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'
        )

        # Room identification
        self._compiled_patterns['room'] = re.compile(
            r'Room:\s*([A-Z0-9][-A-Z0-9]*\d+)', re.IGNORECASE
        )
        self._compiled_patterns['zr_hostname'] = re.compile(
            r'(?:zr-|zoomroom-)([a-z0-9-]+)', re.IGNORECASE
        )

        # Component identification
        self._compiled_patterns['component'] = re.compile(
            r'\[([A-Z_]+)\]', re.IGNORECASE
        )

        # IP address
        self._compiled_patterns['ip'] = re.compile(
            r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        )

        # Error codes
        self._compiled_patterns['error_code'] = re.compile(
            r'(?:Error|Code)[\s:]+([\d]+|0x[0-9A-Fa-f]+)', re.IGNORECASE
        )

        # Version info
        self._compiled_patterns['version'] = re.compile(
            r'(?:version|ver|v)[\s:]+(\d+\.\d+\.\d+(?:\.\d+)?)', re.IGNORECASE
        )

    def parse_line(self, line: str, line_number: int, source_file: Optional[str] = None) -> Optional[UnifiedEvent]:
        """
        Parse a single Zoom Rooms log line.

        Args:
            line: Raw log line
            line_number: Line number in source file
            source_file: Source filename

        Returns:
            UnifiedEvent or None if line should be skipped
        """
        # Skip empty lines
        if not line.strip():
            return None

        # Extract timestamp
        ts, raw_ts = self._extract_zoom_timestamp(line)
        if not ts:
            ts = datetime.utcnow()
            raw_ts = ""

        # Extract room name
        room = self._extract_zoom_room(line)

        # Extract component/service
        component = self._extract_component(line)

        # Determine severity
        severity = self.extract_severity(line, self._zoom_severity_map())

        # Categorize event
        category = self._categorize_zoom_event(line)

        # Generate signal (stable machine identifier)
        signal = self._generate_signal(line, component, category)

        # Extract asset information
        asset = self._extract_zoom_asset(line)

        # Build message (cleaned up log line)
        message = self._clean_message(line)

        # Extract metadata
        metadata = {
            'component': component,
            'original_severity': self._extract_original_severity(line)
        }

        # Add error code if present
        error_code_match = self._compiled_patterns['error_code'].search(line)
        if error_code_match:
            metadata['error_code'] = error_code_match.group(1)

        # Add version if present
        version_match = self._compiled_patterns['version'].search(line)
        if version_match:
            metadata['zoom_version'] = version_match.group(1)

        # Create unified event
        event = self.create_event(
            ts=ts,
            raw_ts=raw_ts,
            signal=signal,
            message=message,
            severity=severity,
            category=category,
            source_system=f"zoom_rooms_{component.lower() if component else 'controller'}",
            line=line,
            line_number=line_number,
            source_file=source_file,
            asset=asset,
            room=room,
            metadata=metadata
        )

        return event

    def _extract_zoom_timestamp(self, line: str) -> tuple[datetime, str]:
        """Extract timestamp from Zoom log line"""
        # Try ISO 8601 first (Zoom's preferred format)
        match = self._compiled_patterns['ts_iso'].search(line)
        if match:
            raw_ts = match.group(1)
            ts = self.extract_timestamp(line, [self._compiled_patterns['ts_iso'].pattern])
            if ts:
                return ts, raw_ts

        # Try syslog format
        match = self._compiled_patterns['ts_syslog'].search(line)
        if match:
            raw_ts = match.group(1)
            ts = self.extract_timestamp(line, [self._compiled_patterns['ts_syslog'].pattern])
            if ts:
                return ts, raw_ts

        return datetime.utcnow(), ""

    def _extract_zoom_room(self, line: str) -> Optional[str]:
        """Extract room name from Zoom log"""
        # Try explicit "Room: XXX" format
        match = self._compiled_patterns['room'].search(line)
        if match:
            return match.group(1).upper()

        # Try hostname format (zr-cr-101 -> CR-101)
        match = self._compiled_patterns['zr_hostname'].search(line)
        if match:
            room_code = match.group(1).replace('-', '_').upper()
            return room_code

        # Try generic room pattern from base class
        return self.extract_room_name(line)

    def _extract_component(self, line: str) -> str:
        """Extract Zoom component/service name"""
        match = self._compiled_patterns['component'].search(line)
        if match:
            return match.group(1).upper()

        # Check for common Zoom components in text
        line_lower = line.lower()
        if 'zrclient' in line_lower or 'client' in line_lower:
            return 'CLIENT'
        elif 'controller' in line_lower:
            return 'CONTROLLER'
        elif 'camera' in line_lower:
            return 'CAMERA'
        elif 'microphone' in line_lower or 'audio' in line_lower:
            return 'AUDIO'
        elif 'display' in line_lower or 'screen' in line_lower:
            return 'DISPLAY'
        elif 'network' in line_lower:
            return 'NETWORK'

        return 'UNKNOWN'

    def _zoom_severity_map(self) -> dict:
        """Zoom-specific severity keywords"""
        return {
            'critical': 'critical',
            'fatal': 'critical',
            'offline': 'critical',
            'unreachable': 'critical',
            'error': 'error',
            'err': 'error',
            'failed': 'error',
            'fail': 'error',
            'timeout': 'error',
            'disconnected': 'error',
            'warn': 'warning',
            'warning': 'warning',
            'degraded': 'warning',
            'info': 'info',
            'notice': 'notice',
            'debug': 'debug',
        }

    def _categorize_zoom_event(self, line: str) -> EventCategory:
        """Categorize Zoom event by analyzing content"""
        line_lower = line.lower()

        # Network-related
        if any(kw in line_lower for kw in ['network', 'dhcp', 'dns', 'connection', 'ping', 'tcp', 'udp']):
            return 'connectivity'

        # Camera/video
        if any(kw in line_lower for kw in ['camera', 'video', 'usb', 'hdmi', 'display', 'screen']):
            return 'video'

        # Audio
        if any(kw in line_lower for kw in ['audio', 'microphone', 'speaker', 'sound', 'dsp']):
            return 'audio'

        # Authentication
        if any(kw in line_lower for kw in ['auth', 'login', 'credential', 'token', 'sso']):
            return 'auth'

        # Power
        if any(kw in line_lower for kw in ['power', 'poe', 'battery', 'shutdown', 'reboot']):
            return 'power'

        # Configuration
        if any(kw in line_lower for kw in ['config', 'setting', 'provision', 'update']):
            return 'config'

        # Control
        if any(kw in line_lower for kw in ['controller', 'control', 'touch panel', 'button']):
            return 'control'

        # Performance
        if any(kw in line_lower for kw in ['latency', 'jitter', 'packet loss', 'bandwidth', 'cpu', 'memory']):
            return 'performance'

        # Hardware
        if any(kw in line_lower for kw in ['hardware', 'device', 'peripheral', 'sensor']):
            return 'hardware'

        # Default to vendor service for Zoom-specific issues
        return 'vendor_service'

    def _generate_signal(self, line: str, component: str, category: EventCategory) -> str:
        """
        Generate stable machine-readable signal identifier.

        Format: zoom.{category}.{specific_event}

        Examples:
            zoom.connectivity.dhcp_timeout
            zoom.video.camera_offline
            zoom.auth.login_failed
        """
        line_lower = line.lower()

        # Build signal based on category and content
        if category == 'connectivity':
            if 'dhcp' in line_lower and 'timeout' in line_lower:
                return 'zoom.connectivity.dhcp_timeout'
            elif 'dns' in line_lower and 'fail' in line_lower:
                return 'zoom.connectivity.dns_failure'
            elif 'network' in line_lower and 'lost' in line_lower:
                return 'zoom.connectivity.network_lost'
            elif 'disconnect' in line_lower:
                return 'zoom.connectivity.disconnected'
            else:
                return 'zoom.connectivity.general'

        elif category == 'video':
            if 'camera' in line_lower and ('offline' in line_lower or 'fail' in line_lower):
                return 'zoom.video.camera_offline'
            elif 'usb' in line_lower and 'enum' in line_lower:
                return 'zoom.video.usb_enumeration_failed'
            elif 'display' in line_lower or 'hdmi' in line_lower:
                return 'zoom.video.display_issue'
            else:
                return 'zoom.video.general'

        elif category == 'audio':
            if 'microphone' in line_lower and ('fail' in line_lower or 'offline' in line_lower):
                return 'zoom.audio.microphone_offline'
            elif 'speaker' in line_lower and 'fail' in line_lower:
                return 'zoom.audio.speaker_failure'
            else:
                return 'zoom.audio.general'

        elif category == 'auth':
            if 'login' in line_lower and 'fail' in line_lower:
                return 'zoom.auth.login_failed'
            elif 'token' in line_lower and ('expir' in line_lower or 'invalid' in line_lower):
                return 'zoom.auth.token_invalid'
            else:
                return 'zoom.auth.general'

        elif category == 'power':
            if 'poe' in line_lower:
                return 'zoom.power.poe_failure'
            elif 'reboot' in line_lower or 'restart' in line_lower:
                return 'zoom.power.reboot'
            else:
                return 'zoom.power.general'

        else:
            # Generic signal
            return f'zoom.{category}.event'

    def _extract_zoom_asset(self, line: str) -> Optional[AssetInfo]:
        """Extract asset information from Zoom log"""
        asset_info = AssetInfo()

        # Extract IP
        ip = self.extract_ip(line)
        if ip:
            asset_info.ip = ip
            asset_info.asset_id = ip

        # Extract MAC
        mac = self.extract_mac(line)
        if mac:
            asset_info.mac = mac

        # Determine asset type from content
        line_lower = line.lower()
        if 'camera' in line_lower:
            asset_info.asset_type = 'camera'
            asset_info.make = 'Zoom'
        elif 'microphone' in line_lower:
            asset_info.asset_type = 'microphone'
        elif 'speaker' in line_lower:
            asset_info.asset_type = 'speaker'
        elif 'display' in line_lower:
            asset_info.asset_type = 'display'
        elif 'controller' in line_lower or 'zrc' in line_lower:
            asset_info.asset_type = 'controller'
            asset_info.make = 'Zoom'
            asset_info.model = 'Zoom Rooms Controller'
        elif 'codec' in line_lower:
            asset_info.asset_type = 'codec'
        else:
            asset_info.asset_type = 'other'

        # Return None if no meaningful data extracted
        if not any([asset_info.ip, asset_info.mac, asset_info.asset_type != 'other']):
            return None

        return asset_info

    def _clean_message(self, line: str) -> str:
        """Clean up log line for human-readable message"""
        # Remove timestamp prefix
        msg = re.sub(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\s*', '', line)
        msg = re.sub(r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s*', '', msg)

        # Remove syslog prefix (hostname, PID)
        msg = re.sub(r'^[a-z0-9-]+\s+\w+\[\d+\]:\s*', '', msg, flags=re.IGNORECASE)

        return msg.strip()

    def _extract_original_severity(self, line: str) -> Optional[str]:
        """Extract original severity label from log (INFO, ERROR, etc.)"""
        match = re.search(r'\[(DEBUG|INFO|NOTICE|WARN|WARNING|ERROR|CRITICAL|FATAL)\]', line, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None
