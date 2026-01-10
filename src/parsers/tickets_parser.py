"""
Tickets CSV parser.

Deterministically parses ticket/incident exports (ServiceNow, Jira, etc.) into UnifiedEvent format.

Expected CSV columns (flexible field mapping):
- ticket_id / number / incident_number
- created_at / opened_at / created
- status / state
- priority / severity
- category / type
- title / short_description / summary
- description
- room / location
- assigned_to / assignee
- etc.

Example CSV:
    ticket_id,created_at,status,priority,category,title,room,assigned_to
    INC0012345,2026-01-08 14:23:45,open,high,av_hardware,Camera offline in CR-101,CR-101,AV Team
"""

import re
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

from .base_parser import CSVParser
import sys
sys.path.append(str(Path(__file__).parent.parent))
from ingestion_models import UnifiedEvent, EventCategory, SeverityLevel


class TicketsParser(CSVParser):
    """Parser for ticket/incident CSV exports"""

    def __init__(self, source_system: str = "servicenow"):
        """
        Initialize tickets parser.

        Args:
            source_system: Source ticketing system (servicenow, jira, etc.)
        """
        super().__init__(
            parser_name="TicketsParser",
            source_type="ticket",
            source_vendor="servicenow"  # Will be overridden by source_system
        )
        self.source_system = source_system

    def parse_row(self, row: Dict[str, str], row_number: int, source_file: Optional[str] = None) -> Optional[UnifiedEvent]:
        """
        Parse a ticket CSV row into UnifiedEvent.

        Args:
            row: CSV row as dictionary
            row_number: Row number in CSV
            source_file: Source filename

        Returns:
            UnifiedEvent or None
        """

        # Extract ticket ID (required)
        ticket_id = self._get_ticket_id(row)
        if not ticket_id:
            raise ValueError("Missing ticket_id")

        # Extract timestamps
        created_at = self._get_created_at(row)
        if not created_at:
            raise ValueError("Missing created_at timestamp")

        # Extract status and priority
        status = self._get_status(row)
        priority = self._get_priority(row)

        # Extract category
        category_str = self._get_category(row)
        category = self._map_ticket_category(category_str)

        # Extract title and description
        title = self._get_title(row)
        description = self._get_description(row)

        # Extract location
        room = self._get_room(row)
        building = self.safe_get(row, 'building')
        floor = self.safe_get(row, 'floor')
        site = self.safe_get(row, 'site')

        # Extract assignment
        assigned_to = self.safe_get(row, 'assigned_to') or self.safe_get(row, 'assignee')
        assigned_team = self.safe_get(row, 'assigned_team') or self.safe_get(row, 'assignment_group')

        # Determine severity from priority
        severity = self._map_priority_to_severity(priority)

        # Generate signal
        signal = self._generate_ticket_signal(category_str, status)

        # Build message
        message = f"Ticket {ticket_id}: {title}"

        # Metadata
        metadata = {
            'ticket_id': ticket_id,
            'status': status,
            'priority': priority,
            'category': category_str,
            'title': title,
            'description': description,
            'assigned_to': assigned_to,
            'assigned_team': assigned_team,
        }

        # Add optional fields
        for field in ['affected_users', 'business_impact', 'resolved_at', 'updated_at']:
            value = self.safe_get(row, field)
            if value:
                metadata[field] = value

        # Create unified event
        event = self.create_event(
            ts=created_at,
            raw_ts=str(created_at),
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
            ticket_id=ticket_id
        )

        # Add tags
        event.tags = self._extract_tags(row, title, description)

        return event

    def _get_ticket_id(self, row: Dict[str, str]) -> Optional[str]:
        """Extract ticket ID from various possible field names"""
        for field in ['ticket_id', 'number', 'incident_number', 'id', 'issue_key']:
            value = self.safe_get(row, field)
            if value:
                return value
        return None

    def _get_created_at(self, row: Dict[str, str]) -> Optional[datetime]:
        """Extract creation timestamp"""
        for field in ['created_at', 'opened_at', 'created', 'opened', 'sys_created_on']:
            value = self.safe_get(row, field)
            if value:
                return self.parse_csv_timestamp(value)
        return None

    def _get_status(self, row: Dict[str, str]) -> str:
        """Extract ticket status"""
        for field in ['status', 'state', 'incident_state']:
            value = self.safe_get(row, field)
            if value:
                return value.lower()
        return 'unknown'

    def _get_priority(self, row: Dict[str, str]) -> str:
        """Extract priority/severity"""
        for field in ['priority', 'severity', 'impact', 'urgency']:
            value = self.safe_get(row, field)
            if value:
                return value.lower()
        return 'medium'

    def _get_category(self, row: Dict[str, str]) -> str:
        """Extract category"""
        for field in ['category', 'type', 'subcategory', 'classification']:
            value = self.safe_get(row, field)
            if value:
                return value
        return 'general'

    def _get_title(self, row: Dict[str, str]) -> str:
        """Extract title/summary"""
        for field in ['title', 'short_description', 'summary', 'subject']:
            value = self.safe_get(row, field)
            if value:
                return value
        return 'No title'

    def _get_description(self, row: Dict[str, str]) -> Optional[str]:
        """Extract description"""
        for field in ['description', 'details', 'comments', 'work_notes']:
            value = self.safe_get(row, field)
            if value:
                return value
        return None

    def _get_room(self, row: Dict[str, str]) -> Optional[str]:
        """Extract room/location"""
        for field in ['room', 'location', 'affected_location', 'ci_name']:
            value = self.safe_get(row, field)
            if value:
                # Try to extract room code
                room_match = re.search(r'([A-Z]{2,}[-_]?\d+)', value, re.IGNORECASE)
                if room_match:
                    return room_match.group(1).upper()
                return value
        return None

    def _map_ticket_category(self, category_str: str) -> EventCategory:
        """Map ticket category to EventCategory"""
        if not category_str:
            return 'hardware'

        cat_lower = category_str.lower()

        if any(kw in cat_lower for kw in ['network', 'connectivity', 'wifi', 'ethernet']):
            return 'connectivity'
        elif any(kw in cat_lower for kw in ['av', 'audio', 'video', 'camera', 'microphone']):
            return 'audio'  # or 'video'
        elif any(kw in cat_lower for kw in ['power', 'poe']):
            return 'power'
        elif any(kw in cat_lower for kw in ['auth', 'access', 'login']):
            return 'auth'
        elif any(kw in cat_lower for kw in ['config', 'setting']):
            return 'config'
        elif any(kw in cat_lower for kw in ['control', 'touch panel']):
            return 'control'
        elif any(kw in cat_lower for kw in ['hardware', 'device']):
            return 'hardware'
        elif any(kw in cat_lower for kw in ['user', 'training']):
            return 'user_action'
        else:
            return 'hardware'

    def _map_priority_to_severity(self, priority: str) -> SeverityLevel:
        """Map ticket priority to event severity"""
        priority_lower = priority.lower()

        if any(kw in priority_lower for kw in ['critical', 'p1', '1', 'urgent']):
            return 'critical'
        elif any(kw in priority_lower for kw in ['high', 'p2', '2']):
            return 'error'
        elif any(kw in priority_lower for kw in ['medium', 'p3', '3', 'moderate']):
            return 'warning'
        elif any(kw in priority_lower for kw in ['low', 'p4', '4']):
            return 'notice'
        else:
            return 'info'

    def _generate_ticket_signal(self, category: str, status: str) -> str:
        """Generate signal for ticket event"""
        cat_clean = re.sub(r'[^a-z0-9_]', '_', category.lower())
        status_clean = re.sub(r'[^a-z0-9_]', '_', status.lower())
        return f"ticket.{cat_clean}.{status_clean}"

    def _extract_tags(self, row: Dict[str, str], title: str, description: Optional[str]) -> list[str]:
        """Extract tags from ticket data"""
        tags = []

        # Add status and priority as tags
        status = self._get_status(row)
        priority = self._get_priority(row)
        tags.append(f"status:{status}")
        tags.append(f"priority:{priority}")

        # Add category
        category = self._get_category(row)
        if category:
            tags.append(f"category:{category.lower().replace(' ', '_')}")

        # Extract keywords from title and description
        text = f"{title} {description or ''}"
        text_lower = text.lower()

        # Common AV/IT keywords
        keywords = [
            'camera', 'microphone', 'display', 'projector', 'zoom',
            'network', 'wifi', 'ethernet', 'dhcp', 'dns',
            'poe', 'power', 'offline', 'timeout', 'error'
        ]

        for keyword in keywords:
            if keyword in text_lower:
                tags.append(keyword)

        return tags
