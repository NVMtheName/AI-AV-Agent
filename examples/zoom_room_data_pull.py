"""
Example: Pull Comprehensive Zoom Room Data

This example demonstrates how to use the enhanced Zoom API integration
to pull complete room data including settings, events, issues, and metrics.
"""

import sys
import os
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.zoom_api_service import ZoomAPIService


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    """Main example function"""

    print("\n🎥 Zoom Room Data Pull Example")
    print("=" * 60)

    # Initialize the Zoom API service
    try:
        zoom = ZoomAPIService()
        print("✅ Successfully initialized Zoom API service")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nPlease set the required environment variables:")
        print("  - ZOOM_ACCOUNT_ID")
        print("  - ZOOM_CLIENT_ID")
        print("  - ZOOM_CLIENT_SECRET")
        return

    # =================================================================
    # Example 1: Get all rooms (basic list)
    # =================================================================
    print_section("Example 1: Get All Zoom Rooms")

    try:
        rooms = zoom.get_zoom_rooms()
        print(f"Total Rooms: {len(rooms)}")

        for room in rooms[:3]:  # Show first 3 rooms
            print(f"\n  📍 {room.get('name')}")
            print(f"     ID: {room.get('id')}")
            print(f"     Status: {room.get('status')}")
            print(f"     Type: {room.get('type')}")

        if len(rooms) > 3:
            print(f"\n  ... and {len(rooms) - 3} more rooms")

    except Exception as e:
        print(f"❌ Error: {e}")

    # =================================================================
    # Example 2: Get comprehensive room status
    # =================================================================
    print_section("Example 2: Get Comprehensive Room Status")

    try:
        comprehensive_status = zoom.get_comprehensive_room_status()
        print(f"Rooms with comprehensive data: {len(comprehensive_status)}")

        for room in comprehensive_status[:2]:  # Show first 2 rooms
            print(f"\n  📍 {room.get('name')}")
            print(f"     Status: {room.get('status')}")
            print(f"     Health: {room.get('health')}")
            print(f"     Devices: {len(room.get('devices', []))} connected")

            if room.get('error'):
                print(f"     ⚠️  Error: {room.get('error')}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # =================================================================
    # Example 3: Get full data for a specific room
    # =================================================================
    print_section("Example 3: Get Full Data for a Room")

    if rooms:
        room_id = rooms[0].get('id')
        room_name = rooms[0].get('name')

        try:
            print(f"Fetching full data for: {room_name}")

            full_data = zoom.get_full_room_data(
                room_id,
                include_settings=True,
                include_events=True,
                include_issues=True,
                date_range_days=7
            )

            print("\n✅ Successfully retrieved full room data:")
            print(f"   - Details: {'✓' if 'details' in full_data else '✗'}")
            print(f"   - Devices: {'✓' if 'devices' in full_data else '✗'}")
            print(f"   - Settings: {'✓' if 'settings' in full_data else '✗'}")
            print(f"   - Events: {'✓' if 'events' in full_data else '✗'}")
            print(f"   - Issues: {'✓' if 'issues' in full_data else '✗'}")
            print(f"   - Metrics: {'✓' if 'metrics' in full_data else '✗'}")

            # Show event count if available
            if 'events' in full_data and isinstance(full_data['events'], list):
                print(f"\n   📅 Events (last 7 days): {len(full_data['events'])}")

            # Show issue info if available
            if 'issues' in full_data:
                print(f"   ⚠️  Issues data available")

        except Exception as e:
            print(f"❌ Error: {e}")

    # =================================================================
    # Example 4: Get all locations
    # =================================================================
    print_section("Example 4: Get All Locations")

    try:
        locations = zoom.get_all_locations()
        print(f"Total Locations: {len(locations)}")

        for location in locations[:3]:  # Show first 3 locations
            print(f"\n  📍 {location.get('name')}")
            print(f"     ID: {location.get('id')}")
            print(f"     Type: {location.get('type', 'N/A')}")
            print(f"     Address: {location.get('address', 'N/A')}")

        if len(locations) > 3:
            print(f"\n  ... and {len(locations) - 3} more locations")

    except Exception as e:
        print(f"❌ Error: {e}")

    # =================================================================
    # Example 5: Get all workspaces
    # =================================================================
    print_section("Example 5: Get All Workspaces")

    try:
        workspaces = zoom.get_workspaces()
        print(f"Total Workspaces: {len(workspaces)}")

        for workspace in workspaces[:3]:  # Show first 3 workspaces
            print(f"\n  🏢 {workspace.get('name')}")
            print(f"     ID: {workspace.get('id')}")
            print(f"     Type: {workspace.get('type', 'N/A')}")
            print(f"     Capacity: {workspace.get('capacity', 'N/A')}")

        if len(workspaces) > 3:
            print(f"\n  ... and {len(workspaces) - 3} more workspaces")

    except Exception as e:
        print(f"❌ Error: {e}")

    # =================================================================
    # Example 6: Get room health summary
    # =================================================================
    print_section("Example 6: Get Room Health Summary")

    try:
        health_summary = zoom.get_room_health_summary()

        print(f"Total Rooms: {health_summary.get('total_rooms')}")

        print("\n📊 Status Breakdown:")
        for status, count in health_summary.get('by_status', {}).items():
            print(f"   {status}: {count}")

        print("\n💚 Health Breakdown:")
        for health, count in health_summary.get('by_health', {}).items():
            print(f"   {health}: {count}")

        offline_count = len(health_summary.get('offline_rooms', []))
        if offline_count > 0:
            print(f"\n⚠️  {offline_count} room(s) offline")

        unhealthy_count = len(health_summary.get('unhealthy_rooms', []))
        if unhealthy_count > 0:
            print(f"⚠️  {unhealthy_count} room(s) unhealthy")

    except Exception as e:
        print(f"❌ Error: {e}")

    # =================================================================
    # Example 7: Get room events (if rooms exist)
    # =================================================================
    print_section("Example 7: Get Room Events")

    if rooms:
        room_id = rooms[0].get('id')
        room_name = rooms[0].get('name')

        try:
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            print(f"Fetching events for: {room_name}")
            print(f"Date range: {from_date} to {to_date}")

            events = zoom.get_room_events(room_id, from_date, to_date)
            print(f"\n✅ Retrieved {len(events)} events")

            if events:
                print("\nRecent events:")
                for event in events[:3]:  # Show first 3 events
                    print(f"   - {event.get('event_type', 'Unknown')}: {event.get('time', 'N/A')}")

        except Exception as e:
            print(f"❌ Error: {e}")

    # =================================================================
    # Example 8: Get room settings (if rooms exist)
    # =================================================================
    print_section("Example 8: Get Room Settings")

    if rooms:
        room_id = rooms[0].get('id')
        room_name = rooms[0].get('name')

        try:
            print(f"Fetching settings for: {room_name}")

            settings = zoom.get_room_settings(room_id)
            print("\n✅ Successfully retrieved room settings")

            # Show some setting categories if available
            if isinstance(settings, dict):
                print(f"\nSetting categories available: {len(settings.keys())}")
                for key in list(settings.keys())[:5]:
                    print(f"   - {key}")

        except Exception as e:
            print(f"❌ Error: {e}")

    # =================================================================
    # Summary
    # =================================================================
    print_section("Summary")

    print("✅ Zoom Room Data Pull Examples Completed!")
    print("\nAvailable API Methods:")
    print("  - get_zoom_rooms() - List all rooms")
    print("  - get_room_details(room_id) - Get room details")
    print("  - get_room_devices(room_id) - Get connected devices")
    print("  - get_room_settings(room_id) - Get room settings")
    print("  - get_room_events(room_id, from, to) - Get room events")
    print("  - get_room_issues(room_id, from, to) - Get room issues")
    print("  - get_room_metrics(room_id, from, to) - Get room metrics")
    print("  - get_all_locations() - List all locations")
    print("  - get_workspaces() - List all workspaces")
    print("  - get_full_room_data(room_id) - Get comprehensive room data")
    print("  - get_comprehensive_room_status() - Get all rooms with full status")
    print("  - get_room_health_summary() - Get health summary")

    print("\n💡 Tip: Use get_full_room_data() for complete room information")
    print("💡 Tip: API calls are rate-limited to 20 req/sec per user\n")


if __name__ == '__main__':
    main()
