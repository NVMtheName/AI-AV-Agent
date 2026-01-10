"""
Q-SYS Core log parser.

Deterministically parses Q-SYS audio DSP logs into UnifiedEvent format.

Q-SYS is an enterprise audio/video platform by QSC. Logs include:
- Q-SYS Core (audio processor)
- Q-SYS Designer logs
- Network logs from Q-SYS devices

Example log lines:
    2026-01-08 14:23:45.123 [INFO] Core-110f (10.1.5.50): Audio routing updated - Room CR-101
    2026-01-08 14:30:12.456 [ERROR] Core-110f (10.1.5.50): Dante network timeout - primary
    Jan 8 14:45:23 qsys-core syslog: Stream failure on input 8
"""

import re
from datetime import datetime
from typing import Optional
from pathlib import Path

from .base_parser import BaseParser
import sys
sys.path.append(str(Path(__file__).parent.parent))
from ingestion_models import UnifiedEvent, AssetInfo, EventCategory, SeverityLevel


class QSysParser(BaseParser):
    """Parser for Q-SYS audio DSP operational logs"""

    def __init__(self):
        super().__init__(
            parser_name="QSysParser",
            source_type="av",
            source_vendor="qsys"
        )

    def _compile_patterns(self):
        """Compile Q-SYS-specific regex patterns"""

        # Timestamp patterns (Q-SYS typically uses ISO-like with milliseconds)
        self._compiled_patterns['ts_qsys'] = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)'
        )
        self._compiled_patterns['ts_syslog'] = re.compile(
            r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'
        )

        # Device identification (Core model and IP)
        self._compiled_patterns['core'] = re.compile(
            r'Core[- ](\d{3}[a-z]{0,2})', re.IGNORECASE
        )
        self._compiled_patterns['device_with_ip'] = re.compile(
            r'([A-Za-z0-9-]+)\s*\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)'
        )

        # Room identification
        self._compiled_patterns['room'] = re.compile(
            r'Room\s+([A-Z]{2,}[-_]?\d+)', re.IGNORECASE
        )

        # Severity markers
        self._compiled_patterns['severity'] = re.compile(
            r'\[(DEBUG|INFO|NOTICE|WARNING|WARN|ERROR|CRITICAL|FAULT)\]', re.IGNORECASE
        )

        # Component/channel identification
        self._compiled_patterns['channel'] = re.compile(
            r'(?:input|output|channel|stream)\s+(\d+)', re.IGNORECASE
        )

        # Dante network (Q-SYS uses Dante for audio networking)
        self._compiled_patterns['dante'] = re.compile(
            r'dante', re.IGNORECASE
        )

        # IP address
        self._compiled_patterns['ip'] = re.compile(
            r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        )

    def parse_line(self, line: str, line_number: int, source_file: Optional[str] = None) -> Optional[UnifiedEvent]:
        """
        Parse a single Q-SYS log line.

        Args:
            line: Raw log line
            line_number: Line number in source file
            source_file: Source filename

        Returns:
            UnifiedEvent or None if line should be skipped
        """
        if not line.strip():
            return None

        # Extract timestamp
        ts, raw_ts = self._extract_qsys_timestamp(line)
        if not ts:
            ts = datetime.utcnow()
            raw_ts = ""

        # Extract device and IP
        device_name, device_ip = self._extract_qsys_device(line)

        # Extract room name
        room = self._extract_qsys_room(line)

        # Determine severity
        severity = self._extract_qsys_severity(line)

        # Categorize event
        category = self._categorize_qsys_event(line)

        # Generate signal
        signal = self._generate_signal(line, category)

        # Extract asset information
        asset = self._extract_qsys_asset(line, device_name, device_ip)

        # Build message
        message = self._clean_message(line)

        # Extract metadata
        metadata = {}

        # Extract Core model
        core_match = self._compiled_patterns['core'].search(line)
        if core_match:
            metadata['qsys_core_model'] = f"Core-{core_match.group(1)}"

        # Extract channel/stream info
        channel_match = self._compiled_patterns['channel'].search(line)
        if channel_match:
            metadata['channel'] = int(channel_match.group(1))

        # Check for Dante networking
        if self._compiled_patterns['dante'].search(line):
            metadata['dante_network'] = True

        # Extract original severity
        severity_match = self._compiled_patterns['severity'].search(line)
        if severity_match:
            metadata['original_severity'] = severity_match.group(1).upper()

        # Create unified event
        event = self.create_event(
            ts=ts,
            raw_ts=raw_ts,
            signal=signal,
            message=message,
            severity=severity,
            category=category,
            source_system=f"qsys_{device_name.lower().replace('-', '_') if device_name else 'core'}",
            line=line,
            line_number=line_number,
            source_file=source_file,
            asset=asset,
            room=room,
            metadata=metadata
        )

        return event

    def _extract_qsys_timestamp(self, line: str) -> tuple[datetime, str]:
        """Extract timestamp from Q-SYS log line"""
        # Try Q-SYS format first (YYYY-MM-DD HH:MM:SS.mmm)
        match = self._compiled_patterns['ts_qsys'].search(line)
        if match:
            raw_ts = match.group(1)
            ts = self.extract_timestamp(line, [self._compiled_patterns['ts_qsys'].pattern])
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

    def _extract_qsys_device(self, line: str) -> tuple[Optional[str], Optional[str]]:
        """Extract Q-SYS device name and IP address"""
        # Try "DeviceName (IP)" format
        match = self._compiled_patterns['device_with_ip'].search(line)
        if match:
            return match.group(1), match.group(2)

        # Try just Core model
        core_match = self._compiled_patterns['core'].search(line)
        if core_match:
            device_name = f"Core-{core_match.group(1)}"
            # Try to find IP separately
            ip = self.extract_ip(line)
            return device_name, ip

        # Just IP
        ip = self.extract_ip(line)
        return None, ip

    def _extract_qsys_room(self, line: str) -> Optional[str]:
        """Extract room name from Q-SYS log"""
        match = self._compiled_patterns['room'].search(line)
        if match:
            return match.group(1).upper()
        return self.extract_room_name(line)

    def _extract_qsys_severity(self, line: str) -> SeverityLevel:
        """Determine Q-SYS event severity"""
        # Check for explicit severity markers
        match = self._compiled_patterns['severity'].search(line)
        if match:
            sev = match.group(1).upper()
            severity_map = {
                'DEBUG': 'debug',
                'INFO': 'info',
                'NOTICE': 'notice',
                'WARNING': 'warning',
                'WARN': 'warning',
                'ERROR': 'error',
                'CRITICAL': 'critical',
                'FAULT': 'critical',
            }
            return severity_map.get(sev, 'info')

        # Fallback to keyword matching
        return self.extract_severity(line)

    def _categorize_qsys_event(self, line: str) -> EventCategory:
        """Categorize Q-SYS event"""
        line_lower = line.lower()

        # Audio-specific
        if any(kw in line_lower for kw in ['audio', 'stream', 'routing', 'dsp', 'gain', 'mute', 'channel', 'input', 'output']):
            return 'audio'

        # Network (Dante, AES67, etc.)
        if any(kw in line_lower for kw in ['network', 'dante', 'aes67', 'multicast', 'qlan']):
            return 'connectivity'

        # Configuration
        if any(kw in line_lower for kw in ['config', 'design', 'deploy', 'update', 'setting']):
            return 'config'

        # Control
        if any(kw in line_lower for kw in ['control', 'gpio', 'relay', 'trigger']):
            return 'control'

        # Performance
        if any(kw in line_lower for kw in ['cpu', 'load', 'latency', 'buffer', 'overrun']):
            return 'performance'

        # Hardware
        if any(kw in line_lower for kw in ['hardware', 'fan', 'temperature', 'power supply']):
            return 'hardware'

        # Power
        if any(kw in line_lower for kw in ['power', 'poe', 'shutdown', 'reboot']):
            return 'power'

        return 'audio'  # Default for Q-SYS

    def _generate_signal(self, line: str, category: EventCategory) -> str:
        """Generate stable machine-readable signal"""
        line_lower = line.lower()

        if category == 'audio':
            if 'stream' in line_lower and ('fail' in line_lower or 'timeout' in line_lower):
                return 'qsys.audio.stream_failure'
            elif 'routing' in line_lower:
                return 'qsys.audio.routing_change'
            elif 'overrun' in line_lower or 'underrun' in line_lower:
                return 'qsys.audio.buffer_error'
            elif 'clipping' in line_lower:
                return 'qsys.audio.clipping'
            else:
                return 'qsys.audio.event'

        elif category == 'connectivity':
            if 'dante' in line_lower and 'timeout' in line_lower:
                return 'qsys.network.dante_timeout'
            elif 'dante' in line_lower and 'fail' in line_lower:
                return 'qsys.network.dante_failure'
            elif 'multicast' in line_lower:
                return 'qsys.network.multicast_issue'
            else:
                return 'qsys.network.event'

        elif category == 'config':
            if 'deploy' in line_lower:
                return 'qsys.config.deployment'
            elif 'update' in line_lower:
                return 'qsys.config.update'
            else:
                return 'qsys.config.change'

        elif category == 'performance':
            if 'cpu' in line_lower:
                return 'qsys.performance.cpu_high'
            elif 'buffer' in line_lower:
                return 'qsys.performance.buffer_issue'
            else:
                return 'qsys.performance.event'

        elif category == 'hardware':
            if 'fan' in line_lower:
                return 'qsys.hardware.fan_issue'
            elif 'temperature' in line_lower or 'temp' in line_lower:
                return 'qsys.hardware.temperature'
            else:
                return 'qsys.hardware.event'

        else:
            return f'qsys.{category}.event'

    def _extract_qsys_asset(self, line: str, device_name: Optional[str], device_ip: Optional[str]) -> Optional[AssetInfo]:
        """Extract asset information from Q-SYS log"""
        asset_info = AssetInfo()

        if device_ip:
            asset_info.ip = device_ip
            asset_info.asset_id = device_ip

        if device_name:
            asset_info.hostname = device_name

        # Determine asset type
        asset_info.asset_type = 'dsp'
        asset_info.make = 'QSC'

        # Extract model from Core pattern
        core_match = self._compiled_patterns['core'].search(line)
        if core_match:
            asset_info.model = f"Q-SYS Core-{core_match.group(1)}"

        # Return None if no meaningful data
        if not any([device_ip, device_name]):
            return None

        return asset_info

    def _clean_message(self, line: str) -> str:
        """Clean up log line for human-readable message"""
        # Remove timestamp
        msg = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?\s*', '', line)
        msg = re.sub(r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s*', '', msg)

        # Remove severity markers
        msg = re.sub(r'\[(DEBUG|INFO|NOTICE|WARNING|WARN|ERROR|CRITICAL|FAULT)\]\s*', '', msg, flags=re.IGNORECASE)

        return msg.strip()
