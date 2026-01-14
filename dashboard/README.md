# Zoom Room Dashboard

A real-time web dashboard for monitoring Zoom Rooms status, health, bandwidth utilization, and device information.

## Features

### 🎯 Key Capabilities

- **Real-time Room Monitoring**: View status of all Zoom Rooms (Available, In Meeting, Offline)
- **Health Dashboard**: Monitor room health with visual indicators
- **Device Information**: Track connected devices (cameras, microphones, speakers, etc.)
- **Bandwidth & QoS Metrics**: Access Quality of Service data including:
  - Bandwidth utilization
  - Latency and jitter
  - Packet loss statistics
  - Audio/video quality metrics
- **Alert System**: Get notified about offline or unhealthy rooms
- **Auto-refresh**: Dashboard updates every 30 seconds automatically
- **Search & Filter**: Quickly find rooms by name or filter by status

### 📊 Dashboard Views

1. **Summary Cards**: Quick overview of total, available, in-meeting, and offline rooms
2. **Health Grid**: Visual breakdown of room health status
3. **Rooms Table**: Detailed table with status, health, devices, and last active time
4. **Room Details Modal**: Deep dive into individual room configuration and devices
5. **Alerts Section**: Highlighted warnings for rooms requiring attention

## Prerequisites

### Zoom API Credentials

You'll need a Zoom Server-to-Server OAuth app:

1. Go to [Zoom App Marketplace](https://marketplace.zoom.us/)
2. Click "Develop" → "Build App"
3. Choose "Server-to-Server OAuth"
4. Fill in app details and get your credentials:
   - Account ID
   - Client ID
   - Client Secret

### Required Scopes

Your Zoom app needs these scopes:

**Essential Scopes:**
- `dashboard_zr:read:admin` - Read Zoom Rooms dashboard data
- `room:read:admin` - Read Zoom Rooms information
- `metrics:read:admin` - Read quality metrics and QoS data

**Additional Scopes (for full functionality):**
- `room:write:admin` - Update Zoom Room settings
- `workspace:read:admin` - Read workspace information
- `workspace:write:admin` - Manage workspace settings (if needed)

**Note:** At minimum, you need the three essential scopes for basic monitoring. Add additional scopes only if you plan to use room/workspace management features.

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The following packages are required for the dashboard:
- `flask>=3.0.0` - Web framework
- `flask-cors>=4.0.0` - CORS support
- `requests>=2.31.0` - HTTP requests
- `PyJWT>=2.8.0` - JWT token generation
- `cryptography>=41.0.0` - Cryptographic operations
- `python-dotenv>=1.0.0` - Environment variable management

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Zoom credentials:

```env
# Zoom API Credentials
ZOOM_ACCOUNT_ID=your_account_id_here
ZOOM_CLIENT_ID=your_client_id_here
ZOOM_CLIENT_SECRET=your_client_secret_here

# Dashboard Configuration (optional)
DASHBOARD_PORT=5000
FLASK_DEBUG=False
```

## Usage

### Starting the Dashboard

```bash
python zoom_dashboard_app.py
```

The dashboard will be available at:
- **Dashboard UI**: http://localhost:5000
- **API Health Check**: http://localhost:5000/api/health

### Using the Zoom API Service Programmatically

```python
from src import ZoomAPIService

# Initialize service (reads from environment variables)
zoom = ZoomAPIService()

# ========== Basic Room Operations ==========

# Get all Zoom Rooms
rooms = zoom.get_zoom_rooms()

# Get room details
room_details = zoom.get_room_details(room_id='abc123')

# Get device information
devices = zoom.get_room_devices(room_id='abc123')

# Get comprehensive room data (all endpoints combined)
full_data = zoom.get_full_room_data(
    room_id='abc123',
    include_settings=True,
    include_events=True,
    include_issues=True,
    date_range_days=7
)

# ========== Room Settings ==========

# Get room settings
settings = zoom.get_room_settings(room_id='abc123')

# Update room settings
updated_settings = zoom.update_room_settings(
    room_id='abc123',
    settings={'meeting': {'auto_start': True}}
)

# ========== Room Events & Issues ==========

# Get room events
events = zoom.get_room_events(
    room_id='abc123',
    from_date='2024-01-01',
    to_date='2024-01-07'
)

# Get room issues/problems
issues = zoom.get_room_issues(
    room_id='abc123',
    from_date='2024-01-01',
    to_date='2024-01-07'
)

# ========== Locations & Workspaces ==========

# Get all locations
locations = zoom.get_all_locations()

# Get location details
location = zoom.get_room_location(location_id='loc123')

# Get all workspaces
workspaces = zoom.get_workspaces()

# Get workspace details
workspace = zoom.get_workspace_details(workspace_id='ws123')

# Get workspace settings
ws_settings = zoom.get_workspace_settings(workspace_id='ws123')

# ========== Dashboard & Metrics ==========

# Get dashboard metrics
dashboard = zoom.get_zoom_rooms_dashboard()

# Get health summary
summary = zoom.get_room_health_summary()

# Get comprehensive status for all rooms
comprehensive_status = zoom.get_comprehensive_room_status()

# Get room metrics (last 7 days)
metrics = zoom.get_room_metrics(
    room_id='abc123',
    from_date='2024-01-01',
    to_date='2024-01-07'
)

# ========== Meeting Quality & QoS ==========

# Get meeting quality data
quality = zoom.get_meeting_quality(meeting_id='meeting123')

# Get QoS data (bandwidth, latency, jitter, packet loss)
qos_data = zoom.get_qos_data(meeting_id='meeting123')
```

## API Endpoints

### Health Check
```
GET /api/health
```

### Rooms
```
GET /api/zoom/rooms                    # List all rooms
GET /api/zoom/rooms?detailed=true      # List with full details
GET /api/zoom/rooms/<room_id>          # Get specific room details
GET /api/zoom/rooms/<room_id>/full     # Get comprehensive room data
```

### Room Settings
```
GET   /api/zoom/rooms/<room_id>/settings              # Get room settings
PATCH /api/zoom/rooms/<room_id>/settings              # Update room settings
GET   /api/zoom/rooms/<room_id>/settings?setting_type=meeting  # Filter by type
```

### Room Events & Issues
```
GET /api/zoom/rooms/<room_id>/events   # Get room events (date range)
GET /api/zoom/rooms/<room_id>/issues   # Get room issues (date range)
```

### Locations
```
GET /api/zoom/locations                # List all locations
GET /api/zoom/locations/<location_id>  # Get location details
GET /api/zoom/locations?parent_location_id=<id>  # Filter by parent
GET /api/zoom/locations?location_type=building   # Filter by type
```

### Workspaces
```
GET /api/zoom/workspaces                           # List all workspaces
GET /api/zoom/workspaces/<workspace_id>            # Get workspace details
GET /api/zoom/workspaces/<workspace_id>/settings   # Get workspace settings
```

### Dashboard & Metrics
```
GET /api/zoom/dashboard                # Dashboard overview
GET /api/zoom/health-summary           # Health summary across all rooms
GET /api/zoom/rooms/<room_id>/metrics  # Room metrics (with date range)
```

### Quality of Service
```
GET /api/zoom/meetings/<meeting_id>/quality        # Meeting quality metrics
GET /api/zoom/meetings/<meeting_id>/qos            # QoS data (bandwidth, etc.)
GET /api/zoom/meetings/<meeting_id>/qos?participant_id=<id>  # Participant QoS
```

### Query Parameters

**Room Full Data Endpoint**:
- `include_settings`: Include settings (default: true)
- `include_events`: Include events (default: false)
- `include_issues`: Include issues (default: false)
- `date_range_days`: Days to look back (default: 7)

Example:
```
GET /api/zoom/rooms/abc123/full?include_events=true&include_issues=true&date_range_days=30
```

**Room Metrics/Events/Issues Endpoints**:
- `from_date`: Start date (YYYY-MM-DD, default: 7 days ago)
- `to_date`: End date (YYYY-MM-DD, default: today)

Example:
```
GET /api/zoom/rooms/abc123/metrics?from_date=2024-01-01&to_date=2024-01-07
GET /api/zoom/rooms/abc123/events?from_date=2024-01-01&to_date=2024-01-07
GET /api/zoom/rooms/abc123/issues?from_date=2024-01-01&to_date=2024-01-07
```

## Dashboard Features

### 1. Summary Cards
- **Total Rooms**: Count of all registered Zoom Rooms
- **Available**: Rooms ready for meetings
- **In Meeting**: Rooms currently occupied
- **Offline**: Rooms that need attention

### 2. Health Status Grid
Visual breakdown showing count of rooms by health status:
- Good/Normal
- Warning
- Critical

### 3. Rooms Table
Comprehensive table with:
- Status indicator (color-coded badge)
- Room name
- Room type
- Health status
- Location
- Number of devices
- Last active timestamp
- Details button

### 4. Search & Filter
- **Search**: Filter rooms by name or location
- **Status Filter**: Show only rooms with specific status

### 5. Room Details Modal
Click "Details" on any room to see:
- Complete room configuration
- Calendar integration status
- Connected devices with model information
- Room ID and location details

### 6. Alerts Section
Automatically shows:
- Offline rooms
- Rooms with Warning or Critical health status
- Quick access to details for problem rooms

### 7. Auto-Refresh
- Dashboard automatically refreshes every 30 seconds
- Manual refresh button available
- Last updated timestamp displayed

## Monitoring Features

### Bandwidth Utilization

Get bandwidth and QoS data for meetings:

```python
# Get QoS data for a meeting
qos_data = zoom.get_qos_data(meeting_id='meeting_uuid')

# QoS data includes:
# - Bandwidth: audio/video send/receive rates
# - Latency: round-trip time
# - Jitter: packet delay variation
# - Packet Loss: percentage of lost packets
# - Bitrate: audio/video bitrate
```

### Room Health Monitoring

```python
# Get comprehensive health summary
summary = zoom.get_room_health_summary()

# Returns:
# - total_rooms: Total count
# - by_status: Breakdown by status (Available, InMeeting, Offline)
# - by_health: Breakdown by health (Good, Warning, Critical)
# - offline_rooms: List of offline rooms with details
# - unhealthy_rooms: List of rooms with issues
```

### Device Tracking

```python
# Get all devices for a room
devices = zoom.get_room_devices(room_id='room123')

# Devices include:
# - Cameras
# - Microphones
# - Speakers
# - Controllers
# - Displays
# With model, status, and configuration info
```

## Troubleshooting

### Missing Credentials Error

If you see:
```
ERROR: Missing required environment variables: ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET
```

**Solution**: Ensure your `.env` file exists and contains valid credentials.

### 401 Unauthorized

**Cause**: Invalid API credentials
**Solution**:
1. Verify credentials in Zoom Marketplace
2. Check that your Server-to-Server OAuth app is activated
3. Ensure scopes are properly configured

### No Rooms Found

**Cause**: Account has no Zoom Rooms or insufficient permissions
**Solution**:
1. Verify your Zoom account has Zoom Rooms licenses
2. Check that API scopes include `room:read:admin`
3. Ensure the app is authorized for your account

### QoS Data Not Available

**Cause**: Meeting is too old or QoS reporting not enabled
**Solution**:
- QoS data is only available for recent meetings (typically last 30 days)
- Ensure QoS reporting is enabled in Zoom account settings

## Security Considerations

1. **Environment Variables**: Never commit `.env` file to version control
2. **API Credentials**: Keep credentials secure and rotate regularly
3. **HTTPS**: Use HTTPS in production (configure reverse proxy)
4. **CORS**: Adjust CORS settings in production as needed
5. **Scopes**: Only request necessary API scopes

## Performance

- **Auto-refresh**: 30-second intervals (configurable in `dashboard.js`)
- **Pagination**: API handles large room counts automatically
- **Caching**: OAuth tokens are cached until expiration
- **Responsive**: Dashboard works on desktop and mobile devices

## Integration with AI AV Agent

The Zoom API service integrates with the existing AI AV Agent for enhanced analysis:

```python
from src import AVAgent, ZoomAPIService

# Initialize services
av_agent = AVAgent()
zoom_service = ZoomAPIService()

# Get Zoom room data
rooms = zoom_service.get_zoom_rooms()
offline_rooms = [r for r in rooms if r['status'] == 'Offline']

# Analyze Zoom-related logs
logs = """
2024-01-09 10:15:00 zoom-room-12 ERROR: Authentication failed
2024-01-09 10:15:01 zoom-room-12 ERROR: Unable to connect to cloud
"""

analysis = av_agent.analyze(logs, "Why is Room 12 offline?")
print(analysis)
```

## File Structure

```
AI-AV-Agent/
├── src/
│   ├── zoom_api_service.py          # Zoom API integration service
│   └── __init__.py                  # Updated to export ZoomAPIService
├── dashboard/
│   ├── templates/
│   │   └── index.html               # Main dashboard HTML
│   └── static/
│       ├── css/
│       │   └── dashboard.css        # Dashboard styles
│       └── js/
│           └── dashboard.js         # Dashboard functionality
├── zoom_dashboard_app.py            # Flask application
├── .env.example                     # Environment variables template
├── .env                             # Your credentials (create this)
└── ZOOM_DASHBOARD_README.md         # This file
```

## Support

For issues or questions:
1. Check Zoom API documentation: https://marketplace.zoom.us/docs/api-reference/
2. Review Zoom Room API: https://marketplace.zoom.us/docs/api-reference/zoom-api/methods#tag/Rooms
3. Verify account permissions and scopes

## License

This integration is part of the AI AV Agent project.
