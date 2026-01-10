"""
Network equipment syslog parser.

Deterministically parses syslog from network devices (switches, routers, APs) into UnifiedEvent format.

Supports:
- Cisco switches (Catalyst, Nexus)
- Meraki devices
- Generic RFC 3164/5424 syslog
- Netgear switches
- PoE, VLAN, link status events

Example log lines:
    Jan 8 14:23:45 switch-cr-101 %LINK-3-UPDOWN: Interface GigabitEthernet1/0/12, changed state to down
    2026-01-08T14:30:12Z meraki-ap-01 events Association succeeded for client 00:11:22:33:44:55
    Jan 8 14:45:23 10.1.1.1 %POWER-3-POE_DENIED: GigabitEthernet1/0/5: inline power denied
"""

import re
from datetime import datetime
from typing import Optional
from pathlib import Path

from .base_parser import BaseParser
import sys
sys.path.append(str(Path(__file__).parent.parent))
from ingestion_models import UnifiedEvent, AssetInfo, EventCategory, SeverityLevel


class NetworkSyslogParser(BaseParser):
    """Parser for network equipment syslog"""

    def __init__(self):
        super().__init__(
            parser_name="NetworkSyslogParser",
            source_type="network",
            source_vendor="cisco"  # Default, will be detected per-line
        )

    def _compile_patterns(self):
        """Compile network syslog patterns"""

        # RFC 3164 syslog timestamp
        self._compiled_patterns['ts_rfc3164'] = re.compile(
            r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'
        )

        # RFC 5424 syslog timestamp
        self._compiled_patterns['ts_rfc5424'] = re.compile(
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)'
        )

        # Hostname/IP (after timestamp in syslog)
        self._compiled_patterns['syslog_host'] = re.compile(
            r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+([a-zA-Z0-9._-]+)'
        )

        # Cisco message format: %FACILITY-SEVERITY-MNEMONIC:
        self._compiled_patterns['cisco_msg'] = re.compile(
            r'%([A-Z_]+)-(\d+)-([A-Z_]+):\s*(.*)', re.IGNORECASE
        )

        # Interface names
        self._compiled_patterns['interface'] = re.compile(
            r'(?:Interface\s+)?(?:GigabitEthernet|FastEthernet|TenGigabitEthernet|Ethernet|Gi|Fa|Te|Eth)(\d+/\d+(?:/\d+)?)',
            re.IGNORECASE
        )

        # MAC address
        self._compiled_patterns['mac'] = re.compile(
            r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'
        )

        # VLAN ID
        self._compiled_patterns['vlan'] = re.compile(
            r'[Vv][Ll][Aa][Nn]\s*(\d+)'
        )

        # IP address
        self._compiled_patterns['ip'] = re.compile(
            r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        )

        # PoE power values
        self._compiled_patterns['poe_power'] = re.compile(
            r'(\d+\.?\d*)\s*[Ww](?:atts?)?'
        )

    def parse_line(self, line: str, line_number: int, source_file: Optional[str] = None) -> Optional[UnifiedEvent]:
        """Parse a single syslog line"""

        if not line.strip():
            return None

        # Extract timestamp
        ts, raw_ts = self._extract_syslog_timestamp(line)
        if not ts:
            ts = datetime.utcnow()
            raw_ts = ""

        # Extract hostname/device
        hostname, device_ip = self._extract_syslog_host(line)

        # Detect vendor
        vendor = self._detect_vendor(line, hostname)

        # Parse Cisco-specific format
        cisco_parsed = self._parse_cisco_format(line)

        # Determine severity
        severity = self._determine_syslog_severity(line, cisco_parsed)

        # Categorize event
        category = self._categorize_network_event(line)

        # Generate signal
        signal = self._generate_signal(line, cisco_parsed, category)

        # Extract asset information
        asset = self._extract_network_asset(line, hostname, device_ip)

        # Extract room from hostname (e.g., "switch-cr-101" -> "CR-101")
        room = self._extract_room_from_hostname(hostname)

        # Build message
        message = self._clean_message(line)

        # Extract metadata
        metadata = {}

        if cisco_parsed:
            metadata['cisco_facility'] = cisco_parsed['facility']
            metadata['cisco_severity'] = cisco_parsed['severity']
            metadata['cisco_mnemonic'] = cisco_parsed['mnemonic']

        # Extract interface
        intf_match = self._compiled_patterns['interface'].search(line)
        if intf_match:
            metadata['interface'] = intf_match.group(0)

        # Extract VLAN
        vlan_match = self._compiled_patterns['vlan'].search(line)
        if vlan_match:
            metadata['vlan_id'] = int(vlan_match.group(1))

        # Extract MAC
        mac = self.extract_mac(line)
        if mac:
            metadata['client_mac'] = mac

        # Extract PoE power
        poe_match = self._compiled_patterns['poe_power'].search(line)
        if poe_match:
            metadata['poe_power_watts'] = float(poe_match.group(1))

        # Override vendor if detected differently
        effective_vendor = vendor if vendor != 'cisco' else self.source_vendor

        # Create event
        event = UnifiedEvent(
            ts=ts,
            source_type=self.source_type,
            source_vendor=effective_vendor,
            source_system=f"network_{hostname.lower().replace('-', '_') if hostname else 'switch'}",
            room=room,
            asset=asset,
            severity=severity,
            category=category,
            signal=signal,
            message=message,
            metadata=metadata,
            raw={
                'raw_line': line,
                'raw_ts': raw_ts,
                'source_file': source_file,
                'line_number': line_number
            },
            parser_version=self.parser_version
        )

        return event

    def _extract_syslog_timestamp(self, line: str) -> tuple[datetime, str]:
        """Extract syslog timestamp"""
        # Try RFC 5424 first (ISO 8601)
        match = self._compiled_patterns['ts_rfc5424'].search(line)
        if match:
            raw_ts = match.group(1)
            ts = self.extract_timestamp(line, [self._compiled_patterns['ts_rfc5424'].pattern])
            if ts:
                return ts, raw_ts

        # Try RFC 3164 (BSD syslog)
        match = self._compiled_patterns['ts_rfc3164'].search(line)
        if match:
            raw_ts = match.group(1)
            ts = self.extract_timestamp(line, [self._compiled_patterns['ts_rfc3164'].pattern])
            if ts:
                return ts, raw_ts

        return datetime.utcnow(), ""

    def _extract_syslog_host(self, line: str) -> tuple[Optional[str], Optional[str]]:
        """Extract hostname or IP from syslog line"""
        # Try syslog format (after timestamp)
        match = self._compiled_patterns['syslog_host'].search(line)
        if match:
            host = match.group(1)
            # Check if it's an IP
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host):
                return None, host
            else:
                return host, None

        # Try to find any IP
        ip = self.extract_ip(line)
        return None, ip

    def _detect_vendor(self, line: str, hostname: Optional[str]) -> str:
        """Detect network equipment vendor"""
        line_lower = line.lower()
        hostname_lower = hostname.lower() if hostname else ""

        if 'meraki' in line_lower or 'meraki' in hostname_lower:
            return 'meraki'
        elif 'netgear' in line_lower or 'netgear' in hostname_lower:
            return 'cisco'  # Map to cisco for now
        elif self._compiled_patterns['cisco_msg'].search(line):
            return 'cisco'
        else:
            return 'cisco'  # Default to Cisco format

    def _parse_cisco_format(self, line: str) -> Optional[dict]:
        """Parse Cisco-specific message format"""
        match = self._compiled_patterns['cisco_msg'].search(line)
        if match:
            return {
                'facility': match.group(1).upper(),
                'severity': int(match.group(2)),
                'mnemonic': match.group(3).upper(),
                'message': match.group(4)
            }
        return None

    def _determine_syslog_severity(self, line: str, cisco_parsed: Optional[dict]) -> SeverityLevel:
        """Determine severity from Cisco severity level or keywords"""

        # Use Cisco severity level if available
        if cisco_parsed and 'severity' in cisco_parsed:
            cisco_sev = cisco_parsed['severity']
            # Map Cisco 0-7 to our severity levels
            # 0=Emergency, 1=Alert, 2=Critical, 3=Error, 4=Warning, 5=Notice, 6=Info, 7=Debug
            severity_map = {
                0: 'critical',
                1: 'critical',
                2: 'critical',
                3: 'error',
                4: 'warning',
                5: 'notice',
                6: 'info',
                7: 'debug',
            }
            return severity_map.get(cisco_sev, 'info')

        # Fallback to keyword matching
        return self.extract_severity(line)

    def _categorize_network_event(self, line: str) -> EventCategory:
        """Categorize network event"""
        line_lower = line.lower()

        # Link/connectivity
        if any(kw in line_lower for kw in ['link', 'port', 'interface', 'up', 'down', 'flap']):
            return 'connectivity'

        # PoE power
        if any(kw in line_lower for kw in ['poe', 'power', 'inline power']):
            return 'power'

        # Authentication
        if any(kw in line_lower for kw in ['auth', 'dot1x', '802.1x', 'mac auth', 'radius']):
            return 'auth'

        # Configuration
        if any(kw in line_lower for kw in ['config', 'vlan', 'stp', 'spanning-tree']):
            return 'config'

        # Performance
        if any(kw in line_lower for kw in ['cpu', 'memory', 'buffer', 'queue', 'drop']):
            return 'performance'

        # Hardware
        if any(kw in line_lower for kw in ['fan', 'temperature', 'power supply', 'module']):
            return 'hardware'

        return 'connectivity'  # Default for network devices

    def _generate_signal(self, line: str, cisco_parsed: Optional[dict], category: EventCategory) -> str:
        """Generate stable signal identifier"""

        # Use Cisco mnemonic if available
        if cisco_parsed:
            facility = cisco_parsed['facility'].lower()
            mnemonic = cisco_parsed['mnemonic'].lower()
            return f"network.{facility}.{mnemonic}"

        line_lower = line.lower()

        if category == 'connectivity':
            if 'up' in line_lower and 'link' in line_lower:
                return 'network.link.up'
            elif 'down' in line_lower and 'link' in line_lower:
                return 'network.link.down'
            elif 'flap' in line_lower:
                return 'network.link.flapping'
            else:
                return 'network.connectivity.event'

        elif category == 'power':
            if 'poe' in line_lower and 'denied' in line_lower:
                return 'network.poe.denied'
            elif 'poe' in line_lower and 'fault' in line_lower:
                return 'network.poe.fault'
            else:
                return 'network.power.event'

        elif category == 'auth':
            if 'failed' in line_lower or 'fail' in line_lower:
                return 'network.auth.failed'
            elif 'success' in line_lower:
                return 'network.auth.success'
            else:
                return 'network.auth.event'

        else:
            return f'network.{category}.event'

    def _extract_network_asset(self, line: str, hostname: Optional[str], device_ip: Optional[str]) -> Optional[AssetInfo]:
        """Extract network asset information"""
        asset_info = AssetInfo()

        if device_ip:
            asset_info.ip = device_ip
            asset_info.asset_id = device_ip

        if hostname:
            asset_info.hostname = hostname
            if not asset_info.asset_id:
                asset_info.asset_id = hostname

        # Determine asset type from hostname or content
        if hostname:
            hostname_lower = hostname.lower()
            if 'switch' in hostname_lower:
                asset_info.asset_type = 'switch'
            elif 'ap' in hostname_lower or 'access-point' in hostname_lower:
                asset_info.asset_type = 'ap'
            else:
                asset_info.asset_type = 'switch'  # Default

        # Set make based on vendor detection
        line_lower = line.lower()
        if 'cisco' in line_lower or self._compiled_patterns['cisco_msg'].search(line):
            asset_info.make = 'Cisco'
        elif 'meraki' in line_lower:
            asset_info.make = 'Meraki'
        elif 'netgear' in line_lower:
            asset_info.make = 'Netgear'

        if not any([device_ip, hostname]):
            return None

        return asset_info

    def _extract_room_from_hostname(self, hostname: Optional[str]) -> Optional[str]:
        """Extract room name from hostname (e.g., switch-cr-101 -> CR-101)"""
        if not hostname:
            return None

        # Try patterns like "switch-cr-101", "ap-room-205"
        match = re.search(r'(?:cr|room|conf)[-_]?([a-z0-9]+)', hostname, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        return None

    def _clean_message(self, line: str) -> str:
        """Clean up syslog message"""
        # Remove timestamp
        msg = re.sub(r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s*', '', line)
        msg = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\s*', '', msg)

        # Remove hostname
        msg = re.sub(r'^[a-zA-Z0-9._-]+\s+', '', msg)

        return msg.strip()
