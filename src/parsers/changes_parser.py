"""
Changes CSV parser.

Deterministically parses change records (firmware updates, config changes, deployments) into UnifiedEvent format.

Expected CSV columns:
- change_id / number
- change_type (firmware_update, config_change, hardware_replacement, etc.)
- scheduled_at / planned_start
- executed_at / actual_start
- completed_at / actual_end
- status (scheduled, in_progress, completed, failed, rolled_back)
- target_type (device, system, service)
- target_identifier (IP, hostname, room)
- change_description
- changed_by
- previous_version / new_version
- room / location

Example CSV:
    change_id,change_type,scheduled_at,status,target_identifier,change_description,changed_by,new_version,room
    CHG0012345,firmware_update,2026-01-08 14:00:00,completed,10.1.5.50,Upgrade Q-SYS Core to 9.8.1,ops_team,9.8.1,CR-101
"""

import re
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

from .base_parser import CSVParser
import sys
sys.path.append(str(Path(__file__).parent.parent))
from ingestion_models import UnifiedEvent, EventCategory, SeverityLevel


class ChangesParser(CSVParser):
    """Parser for change record CSV exports"""

    def __init__(self, source_system: str = "manual"):
        """
        Initialize changes parser.

        Args:
            source_system: Source change management system
        """
        super().__init__(
            parser_name="ChangesParser",
            source_type="change",
            source_vendor="manual"
        )
        self.source_system = source_system

    def parse_row(self, row: Dict[str, str], row_number: int, source_file: Optional[str] = None) -> Optional[UnifiedEvent]:
        """
        Parse a change record CSV row into UnifiedEvent.

        Args:
            row: CSV row as dictionary
            row_number: Row number
            source_file: Source filename

        Returns:
            UnifiedEvent or None
        """

        # Extract change ID (required)
        change_id = self._get_change_id(row)
        if not change_id:
            raise ValueError("Missing change_id")

        # Extract change type
        change_type = self._get_change_type(row)

        # Extract timestamps
        scheduled_at = self._get_scheduled_at(row)
        if not scheduled_at:
            raise ValueError("Missing scheduled_at timestamp")

        executed_at = self._get_executed_at(row)
        completed_at = self._get_completed_at(row)

        # Use executed_at as the event timestamp, fallback to scheduled_at
        event_ts = executed_at or scheduled_at

        # Extract status
        status = self._get_status(row)

        # Extract target information
        target_type = self.safe_get(row, 'target_type') or 'device'
        target_identifier = self._get_target_identifier(row)

        # Extract description and who made the change
        description = self._get_description(row)
        changed_by = self.safe_get(row, 'changed_by') or self.safe_get(row, 'requested_by') or 'unknown'

        # Extract version information
        previous_version = self.safe_get(row, 'previous_version') or self.safe_get(row, 'from_version')
        new_version = self.safe_get(row, 'new_version') or self.safe_get(row, 'to_version')

        # Extract location
        room = self._get_room(row)
        building = self.safe_get(row, 'building')
        floor = self.safe_get(row, 'floor')
        site = self.safe_get(row, 'site')

        # Categorize change
        category = self._categorize_change(change_type, description)

        # Determine severity based on status and risk
        severity = self._determine_change_severity(status, row)

        # Generate signal
        signal = self._generate_change_signal(change_type, status)

        # Build message
        message = self._build_message(change_id, change_type, target_identifier, description, status)

        # Metadata
        metadata = {
            'change_id': change_id,
            'change_type': change_type,
            'status': status,
            'target_type': target_type,
            'target_identifier': target_identifier,
            'description': description,
            'changed_by': changed_by,
        }

        # Add optional fields
        if previous_version:
            metadata['previous_version'] = previous_version
        if new_version:
            metadata['new_version'] = new_version

        for field in ['risk_level', 'expected_impact', 'actual_impact', 'approval_id', 'rollback_plan']:
            value = self.safe_get(row, field)
            if value:
                metadata[field] = value

        # Add timestamps to metadata
        metadata['scheduled_at'] = str(scheduled_at)
        if executed_at:
            metadata['executed_at'] = str(executed_at)
        if completed_at:
            metadata['completed_at'] = str(completed_at)

        # Create unified event
        event = self.create_event(
            ts=event_ts,
            raw_ts=str(event_ts),
            signal=signal,
            message=message,
            severity=severity,
            category=category,
            source_system=self.source_system,
            line=str(row),
            line_number=row_number,
            source_file=source_file,
            room=room,
            building=building,
            floor=floor,
            site=site,
            metadata=metadata,
            change_id=change_id
        )

        # Add tags
        event.tags = self._extract_tags(change_type, status, target_type)

        return event

    def _get_change_id(self, row: Dict[str, str]) -> Optional[str]:
        """Extract change ID"""
        for field in ['change_id', 'number', 'chg_number', 'id']:
            value = self.safe_get(row, field)
            if value:
                return value
        return None

    def _get_change_type(self, row: Dict[str, str]) -> str:
        """Extract change type"""
        for field in ['change_type', 'type', 'category']:
            value = self.safe_get(row, field)
            if value:
                return value
        return 'general_change'

    def _get_scheduled_at(self, row: Dict[str, str]) -> Optional[datetime]:
        """Extract scheduled time"""
        for field in ['scheduled_at', 'planned_start', 'scheduled_start', 'start_date']:
            value = self.safe_get(row, field)
            if value:
                return self.parse_csv_timestamp(value)
        return None

    def _get_executed_at(self, row: Dict[str, str]) -> Optional[datetime]:
        """Extract execution time"""
        for field in ['executed_at', 'actual_start', 'work_start', 'implemented_at']:
            value = self.safe_get(row, field)
            if value:
                return self.parse_csv_timestamp(value)
        return None

    def _get_completed_at(self, row: Dict[str, str]) -> Optional[datetime]:
        """Extract completion time"""
        for field in ['completed_at', 'actual_end', 'work_end', 'closed_at']:
            value = self.safe_get(row, field)
            if value:
                return self.parse_csv_timestamp(value)
        return None

    def _get_status(self, row: Dict[str, str]) -> str:
        """Extract change status"""
        for field in ['status', 'state', 'change_state']:
            value = self.safe_get(row, field)
            if value:
                return value.lower()
        return 'unknown'

    def _get_target_identifier(self, row: Dict[str, str]) -> str:
        """Extract target device/system identifier"""
        for field in ['target_identifier', 'target', 'ci_name', 'device', 'hostname', 'ip']:
            value = self.safe_get(row, field)
            if value:
                return value
        return 'unknown'

    def _get_description(self, row: Dict[str, str]) -> str:
        """Extract change description"""
        for field in ['change_description', 'description', 'short_description', 'summary']:
            value = self.safe_get(row, field)
            if value:
                return value
        return 'No description'

    def _get_room(self, row: Dict[str, str]) -> Optional[str]:
        """Extract room/location"""
        for field in ['room', 'location', 'affected_location']:
            value = self.safe_get(row, field)
            if value:
                # Try to extract room code
                room_match = re.search(r'([A-Z]{2,}[-_]?\d+)', value, re.IGNORECASE)
                if room_match:
                    return room_match.group(1).upper()
                return value
        return None

    def _categorize_change(self, change_type: str, description: str) -> EventCategory:
        """Map change to EventCategory"""
        text = f"{change_type} {description}".lower()

        if any(kw in text for kw in ['firmware', 'software', 'patch', 'update', 'upgrade']):
            return 'config'
        elif any(kw in text for kw in ['config', 'setting', 'parameter']):
            return 'config'
        elif any(kw in text for kw in ['hardware', 'replace', 'install', 'cable']):
            return 'hardware'
        elif any(kw in text for kw in ['network', 'vlan', 'switch', 'router']):
            return 'connectivity'
        elif any(kw in text for kw in ['power', 'poe', 'ups']):
            return 'power'
        else:
            return 'config'

    def _determine_change_severity(self, status: str, row: Dict[str, str]) -> SeverityLevel:
        """Determine severity based on change status and risk"""
        status_lower = status.lower()

        # Failed changes are errors
        if any(kw in status_lower for kw in ['failed', 'error', 'rolled_back']):
            return 'error'

        # Check risk level
        risk = self.safe_get(row, 'risk_level')
        if risk:
            risk_lower = risk.lower()
            if 'high' in risk_lower or 'critical' in risk_lower:
                return 'warning'
            elif 'medium' in risk_lower:
                return 'notice'

        # Completed or scheduled changes are informational
        if any(kw in status_lower for kw in ['completed', 'successful', 'closed']):
            return 'info'

        # In-progress changes are notices
        if 'progress' in status_lower or 'implementing' in status_lower:
            return 'notice'

        return 'info'

    def _generate_change_signal(self, change_type: str, status: str) -> str:
        """Generate signal for change event"""
        type_clean = re.sub(r'[^a-z0-9_]', '_', change_type.lower())
        status_clean = re.sub(r'[^a-z0-9_]', '_', status.lower())
        return f"change.{type_clean}.{status_clean}"

    def _build_message(self, change_id: str, change_type: str, target: str, description: str, status: str) -> str:
        """Build human-readable message"""
        return f"Change {change_id} ({change_type}): {description} on {target} - Status: {status}"

    def _extract_tags(self, change_type: str, status: str, target_type: str) -> list[str]:
        """Extract tags from change data"""
        tags = []

        # Add type and status
        tags.append(f"change_type:{change_type.lower().replace(' ', '_')}")
        tags.append(f"status:{status.lower().replace(' ', '_')}")
        tags.append(f"target_type:{target_type.lower()}")

        # Add keywords from change type
        keywords = ['firmware', 'config', 'hardware', 'network', 'software', 'update', 'upgrade']
        change_type_lower = change_type.lower()
        for keyword in keywords:
            if keyword in change_type_lower:
                tags.append(keyword)

        return tags
