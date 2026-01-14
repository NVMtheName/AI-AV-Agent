"""
Zoom API Service - Handles authentication and API calls to Zoom APIs
Supports Server-to-Server OAuth for secure API access
"""

import os
import time
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv

load_dotenv()


class ZoomAPIService:
    """Service for interacting with Zoom APIs to fetch room data and metrics"""

    BASE_URL = "https://api.zoom.us/v2"

    def __init__(self, account_id: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None):
        """
        Initialize Zoom API service with Server-to-Server OAuth credentials

        Args:
            account_id: Zoom Account ID (or from ZOOM_ACCOUNT_ID env var)
            client_id: OAuth Client ID (or from ZOOM_CLIENT_ID env var)
            client_secret: OAuth Client Secret (or from ZOOM_CLIENT_SECRET env var)
        """
        self.account_id = account_id or os.getenv('ZOOM_ACCOUNT_ID')
        self.client_id = client_id or os.getenv('ZOOM_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('ZOOM_CLIENT_SECRET')

        if not all([self.account_id, self.client_id, self.client_secret]):
            raise ValueError(
                "Missing Zoom API credentials. Please set ZOOM_ACCOUNT_ID, "
                "ZOOM_CLIENT_ID, and ZOOM_CLIENT_SECRET environment variables."
            )

        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    def _get_access_token(self) -> str:
        """
        Get or refresh Server-to-Server OAuth access token

        Returns:
            Valid access token
        """
        # Check if we have a valid token
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at - timedelta(minutes=5):
                return self.access_token

        # Request new token
        token_url = "https://zoom.us/oauth/token"
        params = {
            "grant_type": "account_credentials",
            "account_id": self.account_id
        }

        response = requests.post(
            token_url,
            params=params,
            auth=(self.client_id, self.client_secret),
            timeout=10
        )
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data['access_token']
        expires_in = token_data.get('expires_in', 3600)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        return self.access_token

    def _make_request(self, endpoint: str, method: str = 'GET',
                      params: Optional[Dict] = None,
                      json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated API request to Zoom

        Args:
            endpoint: API endpoint (e.g., '/rooms')
            method: HTTP method
            params: Query parameters
            json_data: JSON body data

        Returns:
            API response as dictionary
        """
        token = self._get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        url = f"{self.BASE_URL}{endpoint}"

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=30
        )
        response.raise_for_status()

        return response.json()

    # ==================== Zoom Rooms API Methods ====================

    def get_zoom_rooms(self, page_size: int = 30) -> List[Dict[str, Any]]:
        """
        Get list of all Zoom Rooms in the account

        Args:
            page_size: Number of rooms per page (max 300)

        Returns:
            List of Zoom Room objects
        """
        all_rooms = []
        next_page_token = None

        while True:
            params = {'page_size': page_size}
            if next_page_token:
                params['next_page_token'] = next_page_token

            response = self._make_request('/rooms', params=params)
            all_rooms.extend(response.get('rooms', []))

            next_page_token = response.get('next_page_token')
            if not next_page_token:
                break

        return all_rooms

    def get_room_details(self, room_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific Zoom Room

        Args:
            room_id: Zoom Room ID

        Returns:
            Room details including configuration and capabilities
        """
        return self._make_request(f'/rooms/{room_id}')

    def get_room_devices(self, room_id: str) -> Dict[str, Any]:
        """
        Get device information for a specific Zoom Room

        Args:
            room_id: Zoom Room ID

        Returns:
            Device details (camera, microphone, speaker, etc.)
        """
        return self._make_request(f'/rooms/{room_id}/devices')

    def get_room_location(self, location_id: str) -> Dict[str, Any]:
        """
        Get location details

        Args:
            location_id: Location ID

        Returns:
            Location information
        """
        return self._make_request(f'/rooms/locations/{location_id}')

    def get_all_locations(self, parent_location_id: Optional[str] = None,
                          location_type: Optional[str] = None,
                          page_size: int = 30) -> List[Dict[str, Any]]:
        """
        Get list of all locations in the account

        Args:
            parent_location_id: Filter by parent location ID
            location_type: Filter by location type (e.g., 'building', 'floor')
            page_size: Number of locations per page (max 300)

        Returns:
            List of location objects
        """
        all_locations = []
        next_page_token = None

        while True:
            params = {'page_size': page_size}
            if parent_location_id:
                params['parent_location_id'] = parent_location_id
            if location_type:
                params['type'] = location_type
            if next_page_token:
                params['next_page_token'] = next_page_token

            response = self._make_request('/rooms/locations', params=params)
            all_locations.extend(response.get('locations', []))

            next_page_token = response.get('next_page_token')
            if not next_page_token:
                break

        return all_locations

    def get_room_settings(self, room_id: str, setting_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get settings for a specific Zoom Room

        Args:
            room_id: Zoom Room ID
            setting_type: Optional setting type filter (e.g., 'meeting', 'alert', 'audio')

        Returns:
            Room settings configuration
        """
        params = {}
        if setting_type:
            params['setting_type'] = setting_type

        return self._make_request(f'/rooms/{room_id}/settings', params=params)

    def update_room_settings(self, room_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update settings for a specific Zoom Room

        Args:
            room_id: Zoom Room ID
            settings: Dictionary of settings to update

        Returns:
            Updated settings response
        """
        return self._make_request(f'/rooms/{room_id}/settings',
                                  method='PATCH',
                                  json_data=settings)

    def get_room_events(self, room_id: str, from_date: str, to_date: str,
                        page_size: int = 30) -> List[Dict[str, Any]]:
        """
        Get events for a specific Zoom Room

        Args:
            room_id: Zoom Room ID
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            page_size: Number of events per page

        Returns:
            List of room events
        """
        all_events = []
        next_page_token = None

        while True:
            params = {
                'from': from_date,
                'to': to_date,
                'page_size': page_size
            }
            if next_page_token:
                params['next_page_token'] = next_page_token

            response = self._make_request(f'/rooms/{room_id}/events', params=params)
            all_events.extend(response.get('events', []))

            next_page_token = response.get('next_page_token')
            if not next_page_token:
                break

        return all_events

    def get_room_issues(self, room_id: str, from_date: str, to_date: str) -> Dict[str, Any]:
        """
        Get issues/problems for a specific Zoom Room

        Args:
            room_id: Zoom Room ID
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Room issues and problems
        """
        params = {
            'from': from_date,
            'to': to_date
        }
        return self._make_request(f'/rooms/{room_id}/issues', params=params)

    # ==================== Workspace Management Methods ====================

    def get_workspaces(self, page_size: int = 30) -> List[Dict[str, Any]]:
        """
        Get list of all workspaces in the account

        Args:
            page_size: Number of workspaces per page (max 300)

        Returns:
            List of workspace objects
        """
        all_workspaces = []
        next_page_token = None

        while True:
            params = {'page_size': page_size}
            if next_page_token:
                params['next_page_token'] = next_page_token

            response = self._make_request('/rooms/workspaces', params=params)
            all_workspaces.extend(response.get('workspaces', []))

            next_page_token = response.get('next_page_token')
            if not next_page_token:
                break

        return all_workspaces

    def get_workspace_details(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific workspace

        Args:
            workspace_id: Workspace ID

        Returns:
            Workspace details including configuration and capacity
        """
        return self._make_request(f'/rooms/workspaces/{workspace_id}')

    def get_workspace_settings(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get settings for a specific workspace

        Args:
            workspace_id: Workspace ID

        Returns:
            Workspace settings configuration
        """
        return self._make_request(f'/rooms/workspaces/{workspace_id}/settings')

    def get_workspace_reservations(self, user_id: str, from_date: str, to_date: str) -> Dict[str, Any]:
        """
        Get workspace reservations for a specific user

        Args:
            user_id: User ID
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of workspace reservations
        """
        params = {
            'from': from_date,
            'to': to_date
        }
        return self._make_request(f'/rooms/workspaces/users/{user_id}/reservations', params=params)

    # ==================== Dashboard & Metrics Methods ====================

    def get_zoom_rooms_dashboard(self) -> Dict[str, Any]:
        """
        Get dashboard data for all Zoom Rooms including status and health

        Returns:
            Dashboard data with room statuses
        """
        endpoint = '/metrics/zoomrooms'
        params = {
            'page_size': 30,
            'type': 'past_day'  # Available, Offline, In Meeting, etc.
        }

        all_rooms = []
        next_page_token = None

        while True:
            if next_page_token:
                params['next_page_token'] = next_page_token

            response = self._make_request(endpoint, params=params)
            all_rooms.extend(response.get('zoom_rooms', []))

            next_page_token = response.get('next_page_token')
            if not next_page_token:
                break

        return {'zoom_rooms': all_rooms, 'total_records': len(all_rooms)}

    def get_room_metrics(self, room_id: str, from_date: str, to_date: str) -> Dict[str, Any]:
        """
        Get metrics for a specific Zoom Room

        Args:
            room_id: Zoom Room ID
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Room metrics including usage and quality
        """
        params = {
            'from': from_date,
            'to': to_date,
            'page_size': 30
        }
        return self._make_request(f'/metrics/zoomrooms/{room_id}', params=params)

    def get_meeting_quality(self, meeting_id: str) -> Dict[str, Any]:
        """
        Get quality metrics for a specific meeting

        Args:
            meeting_id: Meeting ID or UUID

        Returns:
            Quality metrics including audio/video quality, bandwidth, etc.
        """
        params = {'type': 'past'}
        return self._make_request(f'/metrics/meetings/{meeting_id}', params=params)

    def get_qos_data(self, meeting_id: str, participant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Quality of Service (QoS) data for a meeting
        Includes detailed bandwidth, latency, jitter, packet loss data

        Args:
            meeting_id: Meeting ID or UUID
            participant_id: Optional participant ID for specific participant QoS

        Returns:
            QoS metrics
        """
        params = {'type': 'past'}
        if participant_id:
            endpoint = f'/metrics/meetings/{meeting_id}/participants/{participant_id}/qos'
        else:
            endpoint = f'/metrics/meetings/{meeting_id}/participants/qos'

        return self._make_request(endpoint, params=params)

    # ==================== Dashboard Helper Methods ====================

    def get_comprehensive_room_status(self) -> List[Dict[str, Any]]:
        """
        Get comprehensive status for all Zoom Rooms including:
        - Current status (Available, In Meeting, Offline)
        - Health information
        - Device details
        - Location information

        Returns:
            List of rooms with comprehensive status
        """
        rooms = self.get_zoom_rooms()
        comprehensive_data = []

        for room in rooms:
            try:
                room_id = room.get('id')

                # Get additional details
                details = self.get_room_details(room_id)

                # Try to get device info (may fail for some rooms)
                try:
                    devices = self.get_room_devices(room_id)
                except Exception:
                    devices = {'devices': []}

                comprehensive_data.append({
                    'id': room_id,
                    'name': room.get('name'),
                    'status': room.get('status'),
                    'room_type': room.get('type'),
                    'calendar': details.get('calendar_integration'),
                    'health': details.get('health'),
                    'devices': devices.get('devices', []),
                    'location_id': room.get('location_id'),
                    'last_started_time': room.get('last_started_time')
                })
            except Exception as e:
                # Include room even if we can't get all details
                comprehensive_data.append({
                    'id': room.get('id'),
                    'name': room.get('name'),
                    'status': room.get('status', 'Unknown'),
                    'error': str(e)
                })

        return comprehensive_data

    def get_full_room_data(self, room_id: str, include_settings: bool = True,
                           include_events: bool = False,
                           include_issues: bool = False,
                           date_range_days: int = 7) -> Dict[str, Any]:
        """
        Get complete data for a single Zoom Room from all available endpoints

        Args:
            room_id: Zoom Room ID
            include_settings: Include room settings (default: True)
            include_events: Include recent events (default: False)
            include_issues: Include recent issues (default: False)
            date_range_days: Number of days to look back for events/issues (default: 7)

        Returns:
            Comprehensive room data dictionary
        """
        from datetime import datetime, timedelta

        # Calculate date range
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=date_range_days)).strftime('%Y-%m-%d')

        # Collect all data
        room_data = {
            'id': room_id,
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Basic room info
            room_data['details'] = self.get_room_details(room_id)
        except Exception as e:
            room_data['details_error'] = str(e)

        try:
            # Device information
            room_data['devices'] = self.get_room_devices(room_id)
        except Exception as e:
            room_data['devices_error'] = str(e)

        if include_settings:
            try:
                room_data['settings'] = self.get_room_settings(room_id)
            except Exception as e:
                room_data['settings_error'] = str(e)

        if include_events:
            try:
                room_data['events'] = self.get_room_events(room_id, from_date, to_date)
            except Exception as e:
                room_data['events_error'] = str(e)

        if include_issues:
            try:
                room_data['issues'] = self.get_room_issues(room_id, from_date, to_date)
            except Exception as e:
                room_data['issues_error'] = str(e)

        try:
            # Metrics data
            room_data['metrics'] = self.get_room_metrics(room_id, from_date, to_date)
        except Exception as e:
            room_data['metrics_error'] = str(e)

        return room_data

    def get_all_rooms_full_data(self, include_settings: bool = False,
                                include_events: bool = False,
                                include_issues: bool = False) -> List[Dict[str, Any]]:
        """
        Get comprehensive data for all Zoom Rooms (WARNING: API intensive)

        Args:
            include_settings: Include room settings for each room
            include_events: Include recent events for each room
            include_issues: Include recent issues for each room

        Returns:
            List of comprehensive room data dictionaries
        """
        rooms = self.get_zoom_rooms()
        all_room_data = []

        for room in rooms:
            room_id = room.get('id')
            try:
                full_data = self.get_full_room_data(
                    room_id,
                    include_settings=include_settings,
                    include_events=include_events,
                    include_issues=include_issues
                )
                all_room_data.append(full_data)
            except Exception as e:
                all_room_data.append({
                    'id': room_id,
                    'name': room.get('name'),
                    'error': str(e)
                })

        return all_room_data

    def get_room_health_summary(self) -> Dict[str, Any]:
        """
        Get summary of Zoom Room health across all rooms

        Returns:
            Summary with counts of rooms by status and health
        """
        dashboard_data = self.get_zoom_rooms_dashboard()
        rooms = dashboard_data.get('zoom_rooms', [])

        summary = {
            'total_rooms': len(rooms),
            'by_status': {},
            'by_health': {},
            'offline_rooms': [],
            'unhealthy_rooms': []
        }

        for room in rooms:
            status = room.get('status', 'Unknown')
            health = room.get('health', 'Unknown')

            # Count by status
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1

            # Count by health
            summary['by_health'][health] = summary['by_health'].get(health, 0) + 1

            # Track offline rooms
            if status == 'Offline':
                summary['offline_rooms'].append({
                    'id': room.get('id'),
                    'name': room.get('room_name'),
                    'location': room.get('location')
                })

            # Track unhealthy rooms
            if health in ['Warning', 'Critical']:
                summary['unhealthy_rooms'].append({
                    'id': room.get('id'),
                    'name': room.get('room_name'),
                    'health': health,
                    'issues': room.get('issues', [])
                })

        return summary
