"""
Zoom Room Dashboard - Flask Web Application
Provides real-time monitoring of Zoom Rooms status, health, and metrics
"""

from flask import Flask, jsonify, render_template, request, Response
from flask_cors import CORS
from src.zoom_api_service import ZoomAPIService
from src.utilization_analyzer import UtilizationAnalyzer
from src.utilization_recommendation_engine import UtilizationRecommendationEngine
from datetime import datetime, timedelta
import os
import csv
import io
from typing import Dict, Any

app = Flask(__name__, template_folder='dashboard/templates', static_folder='dashboard/static')
CORS(app)

# Initialize services
zoom_service = None
utilization_analyzer = None
recommendation_engine = None


def get_zoom_service() -> ZoomAPIService:
    """Get or create Zoom API service instance"""
    global zoom_service
    if zoom_service is None:
        zoom_service = ZoomAPIService()
    return zoom_service


def get_utilization_analyzer() -> UtilizationAnalyzer:
    """Get or create utilization analyzer instance"""
    global utilization_analyzer
    if utilization_analyzer is None:
        db_connection_string = os.getenv(
            'DATABASE_URL',
            'postgresql://user:password@localhost:5432/ai_av_agent'
        )
        utilization_analyzer = UtilizationAnalyzer(db_connection_string)
    return utilization_analyzer


def get_recommendation_engine() -> UtilizationRecommendationEngine:
    """Get or create recommendation engine instance"""
    global recommendation_engine
    if recommendation_engine is None:
        db_connection_string = os.getenv(
            'DATABASE_URL',
            'postgresql://user:password@localhost:5432/ai_av_agent'
        )
        recommendation_engine = UtilizationRecommendationEngine(db_connection_string)
    return recommendation_engine


# ==================== API Endpoints ====================

@app.route('/health', methods=['GET'])
def health():
    """Simple health check endpoint for Render"""
    return jsonify({'status': 'ok'})


@app.route('/api/health', methods=['GET'])
def health_check():
    """Detailed health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Zoom Room Dashboard',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/zoom/rooms', methods=['GET'])
def get_rooms():
    """
    Get list of all Zoom Rooms
    Query params:
        - detailed: Include full room details (default: false)
    """
    try:
        service = get_zoom_service()
        detailed = request.args.get('detailed', 'false').lower() == 'true'

        if detailed:
            rooms = service.get_comprehensive_room_status()
        else:
            rooms = service.get_zoom_rooms()

        return jsonify({
            'success': True,
            'data': rooms,
            'count': len(rooms),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/rooms/<room_id>', methods=['GET'])
def get_room_detail(room_id: str):
    """Get detailed information for a specific Zoom Room"""
    try:
        service = get_zoom_service()
        room_details = service.get_room_details(room_id)

        # Also get devices
        try:
            devices = service.get_room_devices(room_id)
            room_details['devices'] = devices.get('devices', [])
        except Exception:
            room_details['devices'] = []

        return jsonify({
            'success': True,
            'data': room_details,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard overview with room metrics and status"""
    try:
        service = get_zoom_service()
        dashboard_data = service.get_zoom_rooms_dashboard()

        return jsonify({
            'success': True,
            'data': dashboard_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/health-summary', methods=['GET'])
def get_health_summary():
    """Get health summary across all Zoom Rooms"""
    try:
        service = get_zoom_service()
        summary = service.get_room_health_summary()

        return jsonify({
            'success': True,
            'data': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/rooms/<room_id>/metrics', methods=['GET'])
def get_room_metrics(room_id: str):
    """
    Get metrics for a specific Zoom Room
    Query params:
        - from_date: Start date (YYYY-MM-DD, default: 7 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
    """
    try:
        service = get_zoom_service()

        # Parse date range
        to_date = request.args.get('to_date', datetime.now().strftime('%Y-%m-%d'))
        from_date = request.args.get(
            'from_date',
            (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        )

        metrics = service.get_room_metrics(room_id, from_date, to_date)

        return jsonify({
            'success': True,
            'data': metrics,
            'date_range': {
                'from': from_date,
                'to': to_date
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/meetings/<meeting_id>/quality', methods=['GET'])
def get_meeting_quality(meeting_id: str):
    """Get quality metrics for a specific meeting"""
    try:
        service = get_zoom_service()
        quality = service.get_meeting_quality(meeting_id)

        return jsonify({
            'success': True,
            'data': quality,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/meetings/<meeting_id>/qos', methods=['GET'])
def get_meeting_qos(meeting_id: str):
    """
    Get Quality of Service (QoS) data for a meeting
    Query params:
        - participant_id: Optional participant ID
    """
    try:
        service = get_zoom_service()
        participant_id = request.args.get('participant_id')

        qos_data = service.get_qos_data(meeting_id, participant_id)

        return jsonify({
            'success': True,
            'data': qos_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/locations', methods=['GET'])
def get_locations():
    """
    Get list of all locations
    Query params:
        - parent_location_id: Filter by parent location
        - location_type: Filter by location type
    """
    try:
        service = get_zoom_service()
        parent_id = request.args.get('parent_location_id')
        location_type = request.args.get('location_type')

        locations = service.get_all_locations(
            parent_location_id=parent_id,
            location_type=location_type
        )

        return jsonify({
            'success': True,
            'data': locations,
            'count': len(locations),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/locations/<location_id>', methods=['GET'])
def get_location_detail(location_id: str):
    """Get detailed information for a specific location"""
    try:
        service = get_zoom_service()
        location = service.get_room_location(location_id)

        return jsonify({
            'success': True,
            'data': location,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/workspaces', methods=['GET'])
def get_workspaces():
    """Get list of all workspaces"""
    try:
        service = get_zoom_service()
        workspaces = service.get_workspaces()

        return jsonify({
            'success': True,
            'data': workspaces,
            'count': len(workspaces),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/workspaces/<workspace_id>', methods=['GET'])
def get_workspace_detail(workspace_id: str):
    """Get detailed information for a specific workspace"""
    try:
        service = get_zoom_service()
        workspace = service.get_workspace_details(workspace_id)

        return jsonify({
            'success': True,
            'data': workspace,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/workspaces/<workspace_id>/settings', methods=['GET'])
def get_workspace_settings(workspace_id: str):
    """Get settings for a specific workspace"""
    try:
        service = get_zoom_service()
        settings = service.get_workspace_settings(workspace_id)

        return jsonify({
            'success': True,
            'data': settings,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/rooms/<room_id>/settings', methods=['GET'])
def get_room_settings(room_id: str):
    """
    Get settings for a specific Zoom Room
    Query params:
        - setting_type: Optional setting type filter
    """
    try:
        service = get_zoom_service()
        setting_type = request.args.get('setting_type')

        settings = service.get_room_settings(room_id, setting_type)

        return jsonify({
            'success': True,
            'data': settings,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/rooms/<room_id>/settings', methods=['PATCH'])
def update_room_settings(room_id: str):
    """Update settings for a specific Zoom Room"""
    try:
        service = get_zoom_service()
        settings_data = request.get_json()

        if not settings_data:
            return jsonify({
                'success': False,
                'error': 'No settings data provided'
            }), 400

        result = service.update_room_settings(room_id, settings_data)

        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/rooms/<room_id>/events', methods=['GET'])
def get_room_events(room_id: str):
    """
    Get events for a specific Zoom Room
    Query params:
        - from_date: Start date (YYYY-MM-DD, default: 7 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
    """
    try:
        service = get_zoom_service()

        to_date = request.args.get('to_date', datetime.now().strftime('%Y-%m-%d'))
        from_date = request.args.get(
            'from_date',
            (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        )

        events = service.get_room_events(room_id, from_date, to_date)

        return jsonify({
            'success': True,
            'data': events,
            'count': len(events),
            'date_range': {
                'from': from_date,
                'to': to_date
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/rooms/<room_id>/issues', methods=['GET'])
def get_room_issues(room_id: str):
    """
    Get issues for a specific Zoom Room
    Query params:
        - from_date: Start date (YYYY-MM-DD, default: 7 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
    """
    try:
        service = get_zoom_service()

        to_date = request.args.get('to_date', datetime.now().strftime('%Y-%m-%d'))
        from_date = request.args.get(
            'from_date',
            (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        )

        issues = service.get_room_issues(room_id, from_date, to_date)

        return jsonify({
            'success': True,
            'data': issues,
            'date_range': {
                'from': from_date,
                'to': to_date
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/zoom/rooms/<room_id>/full', methods=['GET'])
def get_full_room_data(room_id: str):
    """
    Get comprehensive data for a Zoom Room from all available endpoints
    Query params:
        - include_settings: Include settings (default: true)
        - include_events: Include events (default: false)
        - include_issues: Include issues (default: false)
        - date_range_days: Days to look back (default: 7)
    """
    try:
        service = get_zoom_service()

        include_settings = request.args.get('include_settings', 'true').lower() == 'true'
        include_events = request.args.get('include_events', 'false').lower() == 'true'
        include_issues = request.args.get('include_issues', 'false').lower() == 'true'
        date_range_days = int(request.args.get('date_range_days', 7))

        full_data = service.get_full_room_data(
            room_id,
            include_settings=include_settings,
            include_events=include_events,
            include_issues=include_issues,
            date_range_days=date_range_days
        )

        return jsonify({
            'success': True,
            'data': full_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== Utilization Analytics API Endpoints ====================

@app.route('/api/utilization/summary', methods=['GET'])
def get_utilization_summary():
    """
    Get utilization summary across all rooms
    Query params:
        - from_date: Start date (YYYY-MM-DD, default: 30 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
        - room_id: Optional room filter
    """
    try:
        analyzer = get_utilization_analyzer()

        to_date = datetime.strptime(
            request.args.get('to_date', datetime.now().strftime('%Y-%m-%d')),
            '%Y-%m-%d'
        )
        from_date = datetime.strptime(
            request.args.get(
                'from_date',
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            ),
            '%Y-%m-%d'
        )
        room_id = request.args.get('room_id')

        summary = analyzer.get_utilization_summary(from_date, to_date, room_id)

        return jsonify({
            'success': True,
            'data': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/utilization/rooms/<room_id>/daily', methods=['GET'])
def get_room_daily_utilization(room_id: str):
    """
    Get daily utilization data for a specific room
    Query params:
        - from_date: Start date (YYYY-MM-DD, default: 30 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
    """
    try:
        analyzer = get_utilization_analyzer()

        to_date = request.args.get('to_date', datetime.now().strftime('%Y-%m-%d'))
        from_date = request.args.get(
            'from_date',
            (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        )

        conn = analyzer._get_connection()
        try:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        date,
                        room_name,
                        building,
                        total_scheduled_hours,
                        total_actual_hours,
                        scheduled_utilization_rate,
                        actual_utilization_rate,
                        total_scheduled_meetings,
                        total_completed_meetings,
                        total_no_shows,
                        total_ghost_bookings,
                        no_show_rate,
                        avg_participants_per_meeting,
                        peak_hour_start,
                        peak_hour_meetings
                    FROM room_utilization_daily
                    WHERE room_id = %s
                        AND date BETWEEN %s AND %s
                    ORDER BY date ASC
                """, (room_id, from_date, to_date))

                daily_data = cur.fetchall()

                return jsonify({
                    'success': True,
                    'data': daily_data,
                    'count': len(daily_data),
                    'date_range': {'from': from_date, 'to': to_date},
                    'timestamp': datetime.now().isoformat()
                })
        finally:
            conn.close()
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/utilization/rooms/<room_id>/hourly', methods=['GET'])
def get_room_hourly_utilization(room_id: str):
    """
    Get hourly utilization data for heatmap visualization
    Query params:
        - from_date: Start date (YYYY-MM-DD, default: 30 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
    """
    try:
        analyzer = get_utilization_analyzer()

        to_date = request.args.get('to_date', datetime.now().strftime('%Y-%m-%d'))
        from_date = request.args.get(
            'from_date',
            (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        )

        conn = analyzer._get_connection()
        try:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        date,
                        hour,
                        room_name,
                        hourly_utilization_rate,
                        total_meetings,
                        total_minutes_actual,
                        is_business_hour
                    FROM room_utilization_hourly
                    WHERE room_id = %s
                        AND date BETWEEN %s AND %s
                    ORDER BY date ASC, hour ASC
                """, (room_id, from_date, to_date))

                hourly_data = cur.fetchall()

                return jsonify({
                    'success': True,
                    'data': hourly_data,
                    'count': len(hourly_data),
                    'date_range': {'from': from_date, 'to': to_date},
                    'timestamp': datetime.now().isoformat()
                })
        finally:
            conn.close()
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/utilization/heatmap', methods=['GET'])
def get_utilization_heatmap():
    """
    Get heatmap data for all rooms
    Query params:
        - from_date: Start date (YYYY-MM-DD, default: 7 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
        - building: Optional building filter
    """
    try:
        analyzer = get_utilization_analyzer()

        to_date = request.args.get('to_date', datetime.now().strftime('%Y-%m-%d'))
        from_date = request.args.get(
            'from_date',
            (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        )
        building = request.args.get('building')

        conn = analyzer._get_connection()
        try:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_clause = "WHERE date BETWEEN %s AND %s"
                params = [from_date, to_date]

                if building:
                    where_clause += " AND building = %s"
                    params.append(building)

                cur.execute(f"""
                    SELECT
                        room_id,
                        room_name,
                        building,
                        date,
                        hour,
                        hourly_utilization_rate,
                        total_meetings,
                        is_business_hour
                    FROM room_utilization_hourly
                    {where_clause}
                    ORDER BY room_name ASC, date ASC, hour ASC
                """, params)

                heatmap_data = cur.fetchall()

                return jsonify({
                    'success': True,
                    'data': heatmap_data,
                    'count': len(heatmap_data),
                    'date_range': {'from': from_date, 'to': to_date},
                    'timestamp': datetime.now().isoformat()
                })
        finally:
            conn.close()
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/utilization/ranking', methods=['GET'])
def get_room_ranking():
    """
    Get room ranking by utilization
    Query params:
        - from_date: Start date (YYYY-MM-DD, default: 30 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
        - building: Optional building filter
    """
    try:
        analyzer = get_utilization_analyzer()

        to_date = datetime.strptime(
            request.args.get('to_date', datetime.now().strftime('%Y-%m-%d')),
            '%Y-%m-%d'
        )
        from_date = datetime.strptime(
            request.args.get(
                'from_date',
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            ),
            '%Y-%m-%d'
        )
        building = request.args.get('building')

        ranking = analyzer.get_room_ranking(from_date, to_date, building)

        return jsonify({
            'success': True,
            'data': ranking,
            'count': len(ranking),
            'date_range': {
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d')
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/utilization/rooms/<room_id>/peak-times', methods=['GET'])
def get_room_peak_times(room_id: str):
    """
    Get peak usage times for a specific room
    Query params:
        - from_date: Start date (YYYY-MM-DD, default: 30 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
    """
    try:
        analyzer = get_utilization_analyzer()

        to_date = datetime.strptime(
            request.args.get('to_date', datetime.now().strftime('%Y-%m-%d')),
            '%Y-%m-%d'
        )
        from_date = datetime.strptime(
            request.args.get(
                'from_date',
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            ),
            '%Y-%m-%d'
        )

        peak_times = analyzer.find_peak_usage_times(room_id, from_date, to_date)

        return jsonify({
            'success': True,
            'data': peak_times,
            'date_range': {
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d')
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/utilization/recommendations', methods=['GET'])
def get_utilization_recommendations():
    """
    Get utilization optimization recommendations
    Query params:
        - room_id: Optional room filter
        - priority: Optional priority filter (low, medium, high, critical)
    """
    try:
        engine = get_recommendation_engine()

        room_id = request.args.get('room_id')
        priority = request.args.get('priority')

        recommendations = engine.get_active_recommendations(room_id, priority)

        return jsonify({
            'success': True,
            'data': recommendations,
            'count': len(recommendations),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/utilization/recommendations/generate', methods=['POST'])
def generate_recommendations():
    """
    Generate new recommendations based on recent data
    JSON body params:
        - from_date: Start date (YYYY-MM-DD, default: 30 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
        - min_days: Minimum days of data (default: 20)
    """
    try:
        engine = get_recommendation_engine()
        data = request.get_json() or {}

        to_date = datetime.strptime(
            data.get('to_date', datetime.now().strftime('%Y-%m-%d')),
            '%Y-%m-%d'
        )
        from_date = datetime.strptime(
            data.get(
                'from_date',
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            ),
            '%Y-%m-%d'
        )
        min_days = data.get('min_days', 20)

        recommendations = engine.generate_all_recommendations(
            from_date, to_date, min_days
        )

        # Store recommendations in database
        engine.store_recommendations(recommendations, from_date, to_date)

        return jsonify({
            'success': True,
            'data': {
                'recommendations_generated': len(recommendations),
                'analysis_period': {
                    'from': from_date.strftime('%Y-%m-%d'),
                    'to': to_date.strftime('%Y-%m-%d')
                }
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/utilization/export', methods=['GET'])
def export_utilization_data():
    """
    Export utilization data as CSV
    Query params:
        - from_date: Start date (YYYY-MM-DD, default: 30 days ago)
        - to_date: End date (YYYY-MM-DD, default: today)
        - room_id: Optional room filter
        - format: Export format (csv, default: csv)
    """
    try:
        analyzer = get_utilization_analyzer()

        to_date = request.args.get('to_date', datetime.now().strftime('%Y-%m-%d'))
        from_date = request.args.get(
            'from_date',
            (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        )
        room_id = request.args.get('room_id')

        conn = analyzer._get_connection()
        try:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_clause = "WHERE date BETWEEN %s AND %s"
                params = [from_date, to_date]

                if room_id:
                    where_clause += " AND room_id = %s"
                    params.append(room_id)

                cur.execute(f"""
                    SELECT
                        room_id,
                        room_name,
                        building,
                        date,
                        total_scheduled_hours,
                        total_actual_hours,
                        scheduled_utilization_rate,
                        actual_utilization_rate,
                        total_scheduled_meetings,
                        total_completed_meetings,
                        total_no_shows,
                        no_show_rate,
                        total_ghost_bookings,
                        total_early_departures,
                        avg_participants_per_meeting
                    FROM room_utilization_daily
                    {where_clause}
                    ORDER BY date DESC, room_name ASC
                """, params)

                data = cur.fetchall()

                # Create CSV
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

                # Create response
                response = Response(
                    output.getvalue(),
                    mimetype='text/csv',
                    headers={
                        'Content-Disposition': f'attachment; filename=utilization_report_{from_date}_to_{to_date}.csv'
                    }
                )
                return response
        finally:
            conn.close()
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== Web UI Routes ====================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/utilization')
def utilization_dashboard():
    """Utilization analytics dashboard page"""
    return render_template('utilization.html')


@app.route('/room/<room_id>')
def room_detail(room_id: str):
    """Room detail page"""
    return render_template('room_detail.html', room_id=room_id)


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found'
        }), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    return render_template('500.html'), 500


# ==================== Main ====================

if __name__ == '__main__':
    # Check for required environment variables
    required_vars = ['ZOOM_ACCOUNT_ID', 'ZOOM_CLIENT_ID', 'ZOOM_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following in your .env file:")
        print("ZOOM_ACCOUNT_ID=your_account_id")
        print("ZOOM_CLIENT_ID=your_client_id")
        print("ZOOM_CLIENT_SECRET=your_client_secret")
        exit(1)

    # Run the Flask app
    # Read PORT from environment (Render uses PORT, local dev can use DASHBOARD_PORT)
    port = int(os.getenv('PORT', os.getenv('DASHBOARD_PORT', 5000)))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"\n🚀 Starting Zoom Room Dashboard on http://localhost:{port}")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"🔌 API Health: http://localhost:{port}/api/health\n")

    app.run(host='0.0.0.0', port=port, debug=debug)
