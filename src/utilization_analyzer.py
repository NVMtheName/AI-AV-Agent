"""
Room Utilization Analyzer - Calculates room utilization metrics and analytics
Processes meeting data to generate insights about room usage patterns
"""

from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MeetingData:
    """Structured meeting data for analysis"""
    meeting_id: str
    room_id: str
    room_name: str
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    participants: int = 0
    status: str = 'scheduled'


@dataclass
class UtilizationMetrics:
    """Utilization metrics for a room"""
    room_id: str
    room_name: str
    date: datetime
    scheduled_hours: Decimal
    actual_hours: Decimal
    scheduled_utilization_rate: Decimal
    actual_utilization_rate: Decimal
    total_meetings: int
    completed_meetings: int
    no_shows: int
    ghost_bookings: int
    early_departures: int
    avg_participants: Decimal
    no_show_rate: Decimal


class UtilizationAnalyzer:
    """Analyzes room utilization data and generates insights"""

    def __init__(self, db_connection_string: str):
        """
        Initialize utilization analyzer

        Args:
            db_connection_string: PostgreSQL connection string
        """
        self.db_connection_string = db_connection_string
        self.business_hours_start = time(8, 0)  # 8 AM
        self.business_hours_end = time(18, 0)   # 6 PM
        self.no_show_grace_minutes = 15
        self.early_departure_threshold_minutes = 10

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_connection_string)

    def calculate_business_hours(self, date: datetime) -> Decimal:
        """
        Calculate available business hours for a date

        Args:
            date: Date to calculate hours for

        Returns:
            Number of business hours available
        """
        # Default 10 hours (8 AM to 6 PM)
        start = datetime.combine(date, self.business_hours_start)
        end = datetime.combine(date, self.business_hours_end)
        hours = (end - start).total_seconds() / 3600
        return Decimal(str(hours))

    def classify_meeting_status(self, meeting: MeetingData) -> Tuple[str, bool, bool, bool]:
        """
        Classify meeting status based on scheduled vs actual times

        Args:
            meeting: Meeting data

        Returns:
            Tuple of (status, is_no_show, is_ghost_booking, is_early_departure)
        """
        is_no_show = False
        is_ghost_booking = False
        is_early_departure = False
        status = 'scheduled'

        now = datetime.now()

        # Check if meeting is in the past
        if meeting.scheduled_end < now:
            if meeting.actual_start is None:
                # Meeting was scheduled but never started
                status = 'no_show'
                is_no_show = True
            elif meeting.actual_end is not None:
                # Meeting completed
                status = 'completed'

                # Check for ghost booking (zero participants)
                if meeting.participants == 0:
                    is_ghost_booking = True

                # Check for early departure
                if meeting.actual_end < meeting.scheduled_end:
                    time_diff = (meeting.scheduled_end - meeting.actual_end).total_seconds() / 60
                    if time_diff > self.early_departure_threshold_minutes:
                        is_early_departure = True
            else:
                # Meeting started but no end time recorded (edge case)
                status = 'in_progress'
        elif meeting.actual_start is not None:
            status = 'in_progress'

        return status, is_no_show, is_ghost_booking, is_early_departure

    def calculate_actual_duration(self, meeting: MeetingData) -> Decimal:
        """
        Calculate actual meeting duration in hours

        Args:
            meeting: Meeting data

        Returns:
            Actual duration in hours
        """
        if meeting.actual_start and meeting.actual_end:
            duration_seconds = (meeting.actual_end - meeting.actual_start).total_seconds()
            return Decimal(str(duration_seconds / 3600))
        return Decimal('0')

    def calculate_scheduled_duration(self, meeting: MeetingData) -> Decimal:
        """
        Calculate scheduled meeting duration in hours

        Args:
            meeting: Meeting data

        Returns:
            Scheduled duration in hours
        """
        duration_seconds = (meeting.scheduled_end - meeting.scheduled_start).total_seconds()
        return Decimal(str(duration_seconds / 3600))

    def analyze_daily_utilization(self, room_id: str, date: datetime,
                                  meetings: List[MeetingData]) -> UtilizationMetrics:
        """
        Analyze daily utilization for a room

        Args:
            room_id: Room ID
            date: Date to analyze
            meetings: List of meetings for this room on this date

        Returns:
            Daily utilization metrics
        """
        total_scheduled_hours = Decimal('0')
        total_actual_hours = Decimal('0')
        total_meetings = len(meetings)
        completed_meetings = 0
        no_shows = 0
        ghost_bookings = 0
        early_departures = 0
        total_participants = 0

        for meeting in meetings:
            # Calculate scheduled duration
            scheduled_duration = self.calculate_scheduled_duration(meeting)
            total_scheduled_hours += scheduled_duration

            # Classify meeting
            status, is_no_show, is_ghost_booking, is_early_departure = \
                self.classify_meeting_status(meeting)

            if status == 'completed':
                completed_meetings += 1
                actual_duration = self.calculate_actual_duration(meeting)
                total_actual_hours += actual_duration
                total_participants += meeting.participants

            if is_no_show:
                no_shows += 1
            if is_ghost_booking:
                ghost_bookings += 1
            if is_early_departure:
                early_departures += 1

        # Calculate rates
        business_hours = self.calculate_business_hours(date)
        scheduled_rate = (total_scheduled_hours / business_hours * 100) if business_hours > 0 else Decimal('0')
        actual_rate = (total_actual_hours / business_hours * 100) if business_hours > 0 else Decimal('0')
        no_show_rate = (Decimal(no_shows) / Decimal(total_meetings) * 100) if total_meetings > 0 else Decimal('0')
        avg_participants = (Decimal(total_participants) / Decimal(completed_meetings)) if completed_meetings > 0 else Decimal('0')

        room_name = meetings[0].room_name if meetings else ''

        return UtilizationMetrics(
            room_id=room_id,
            room_name=room_name,
            date=date,
            scheduled_hours=total_scheduled_hours,
            actual_hours=total_actual_hours,
            scheduled_utilization_rate=scheduled_rate,
            actual_utilization_rate=actual_rate,
            total_meetings=total_meetings,
            completed_meetings=completed_meetings,
            no_shows=no_shows,
            ghost_bookings=ghost_bookings,
            early_departures=early_departures,
            avg_participants=avg_participants,
            no_show_rate=no_show_rate
        )

    def calculate_hourly_utilization(self, room_id: str, date: datetime,
                                    meetings: List[MeetingData]) -> List[Dict[str, Any]]:
        """
        Calculate hourly utilization breakdown for heatmap visualization

        Args:
            room_id: Room ID
            date: Date to analyze
            meetings: List of meetings for this room on this date

        Returns:
            List of hourly utilization data (24 hours)
        """
        hourly_data = []

        for hour in range(24):
            hour_start = datetime.combine(date, time(hour, 0))
            hour_end = hour_start + timedelta(hours=1)

            meetings_in_hour = 0
            minutes_scheduled = 0
            minutes_actual = 0
            meetings_started = 0
            meetings_ended = 0
            meetings_ongoing = 0

            for meeting in meetings:
                # Check if meeting overlaps with this hour
                if meeting.scheduled_start < hour_end and meeting.scheduled_end > hour_start:
                    meetings_in_hour += 1

                    # Calculate overlap minutes for scheduled time
                    overlap_start = max(meeting.scheduled_start, hour_start)
                    overlap_end = min(meeting.scheduled_end, hour_end)
                    overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
                    minutes_scheduled += int(overlap_minutes)

                    # Check for actual time
                    if meeting.actual_start and meeting.actual_end:
                        if meeting.actual_start < hour_end and meeting.actual_end > hour_start:
                            actual_overlap_start = max(meeting.actual_start, hour_start)
                            actual_overlap_end = min(meeting.actual_end, hour_end)
                            actual_overlap_minutes = (actual_overlap_end - actual_overlap_start).total_seconds() / 60
                            minutes_actual += int(actual_overlap_minutes)

                    # Check if meeting started in this hour
                    if hour_start <= meeting.scheduled_start < hour_end:
                        meetings_started += 1

                    # Check if meeting ended in this hour
                    if meeting.actual_end and hour_start <= meeting.actual_end < hour_end:
                        meetings_ended += 1

                    # Check if meeting was ongoing during this hour
                    if meeting.actual_start:
                        if meeting.actual_start < hour_end and (
                            not meeting.actual_end or meeting.actual_end > hour_start
                        ):
                            meetings_ongoing += 1

            # Determine if business hour
            is_business_hour = self.business_hours_start <= time(hour, 0) < self.business_hours_end

            # Calculate utilization rate
            utilization_rate = min((minutes_actual / 60.0) * 100, 100.0)

            room_name = meetings[0].room_name if meetings else ''

            hourly_data.append({
                'room_id': room_id,
                'room_name': room_name,
                'date': date.date(),
                'hour': hour,
                'is_business_hour': is_business_hour,
                'total_meetings': meetings_in_hour,
                'total_minutes_scheduled': minutes_scheduled,
                'total_minutes_actual': minutes_actual,
                'hourly_utilization_rate': round(utilization_rate, 2),
                'meetings_started': meetings_started,
                'meetings_ended': meetings_ended,
                'meetings_ongoing': meetings_ongoing
            })

        return hourly_data

    def find_peak_usage_times(self, room_id: str, from_date: datetime,
                             to_date: datetime) -> Dict[str, Any]:
        """
        Identify peak usage times for a room

        Args:
            room_id: Room ID
            from_date: Start date
            to_date: End date

        Returns:
            Peak usage analysis
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get hourly utilization data
                cur.execute("""
                    SELECT
                        hour,
                        AVG(hourly_utilization_rate) as avg_utilization,
                        SUM(total_meetings) as total_meetings,
                        COUNT(*) as days_count
                    FROM room_utilization_hourly
                    WHERE room_id = %s
                        AND date BETWEEN %s AND %s
                        AND is_business_hour = TRUE
                    GROUP BY hour
                    ORDER BY avg_utilization DESC
                """, (room_id, from_date.date(), to_date.date()))

                hourly_stats = cur.fetchall()

                # Find peak hour
                peak_hour = hourly_stats[0] if hourly_stats else None

                # Get day of week analysis
                cur.execute("""
                    SELECT
                        EXTRACT(DOW FROM date) as day_of_week,
                        TO_CHAR(date, 'Day') as day_name,
                        AVG(actual_utilization_rate) as avg_utilization,
                        SUM(total_completed_meetings) as total_meetings
                    FROM room_utilization_daily
                    WHERE room_id = %s
                        AND date BETWEEN %s AND %s
                    GROUP BY EXTRACT(DOW FROM date), TO_CHAR(date, 'Day')
                    ORDER BY avg_utilization DESC
                """, (room_id, from_date.date(), to_date.date()))

                daily_stats = cur.fetchall()

                return {
                    'peak_hour': peak_hour,
                    'hourly_breakdown': hourly_stats,
                    'daily_breakdown': daily_stats,
                    'busiest_day': daily_stats[0] if daily_stats else None
                }
        finally:
            conn.close()

    def get_room_ranking(self, from_date: datetime, to_date: datetime,
                        building: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get room ranking by utilization

        Args:
            from_date: Start date
            to_date: End date
            building: Optional building filter

        Returns:
            List of rooms ranked by utilization
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_clause = "WHERE date BETWEEN %s AND %s"
                params = [from_date.date(), to_date.date()]

                if building:
                    where_clause += " AND building = %s"
                    params.append(building)

                query = f"""
                    SELECT
                        room_id,
                        room_name,
                        building,
                        AVG(actual_utilization_rate) as avg_utilization_rate,
                        SUM(total_completed_meetings) as total_meetings,
                        AVG(no_show_rate) as avg_no_show_rate,
                        AVG(avg_participants_per_meeting) as avg_participants,
                        COUNT(*) as days_analyzed,
                        ROW_NUMBER() OVER (ORDER BY AVG(actual_utilization_rate) DESC) as rank
                    FROM room_utilization_daily
                    {where_clause}
                    GROUP BY room_id, room_name, building
                    ORDER BY avg_utilization_rate DESC
                """

                cur.execute(query, params)
                return cur.fetchall()
        finally:
            conn.close()

    def store_daily_utilization(self, metrics: UtilizationMetrics) -> None:
        """
        Store daily utilization metrics in database

        Args:
            metrics: Utilization metrics to store
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO room_utilization_daily (
                        room_id, date, room_name, building,
                        total_scheduled_hours, total_actual_hours,
                        total_scheduled_meetings, total_completed_meetings,
                        total_no_shows, total_ghost_bookings, total_early_departures,
                        avg_participants_per_meeting
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (room_id, date)
                    DO UPDATE SET
                        total_scheduled_hours = EXCLUDED.total_scheduled_hours,
                        total_actual_hours = EXCLUDED.total_actual_hours,
                        total_scheduled_meetings = EXCLUDED.total_scheduled_meetings,
                        total_completed_meetings = EXCLUDED.total_completed_meetings,
                        total_no_shows = EXCLUDED.total_no_shows,
                        total_ghost_bookings = EXCLUDED.total_ghost_bookings,
                        total_early_departures = EXCLUDED.total_early_departures,
                        avg_participants_per_meeting = EXCLUDED.avg_participants_per_meeting,
                        calculated_at = NOW()
                """, (
                    metrics.room_id,
                    metrics.date.date(),
                    metrics.room_name,
                    None,  # building - to be enriched
                    float(metrics.scheduled_hours),
                    float(metrics.actual_hours),
                    metrics.total_meetings,
                    metrics.completed_meetings,
                    metrics.no_shows,
                    metrics.ghost_bookings,
                    metrics.early_departures,
                    float(metrics.avg_participants)
                ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing daily utilization: {e}")
            raise
        finally:
            conn.close()

    def store_hourly_utilization(self, hourly_data: List[Dict[str, Any]]) -> None:
        """
        Store hourly utilization data in database

        Args:
            hourly_data: List of hourly utilization records
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                execute_batch(cur, """
                    INSERT INTO room_utilization_hourly (
                        room_id, date, hour, room_name,
                        is_business_hour, total_meetings,
                        total_minutes_scheduled, total_minutes_actual,
                        meetings_started, meetings_ended, meetings_ongoing
                    ) VALUES (
                        %(room_id)s, %(date)s, %(hour)s, %(room_name)s,
                        %(is_business_hour)s, %(total_meetings)s,
                        %(total_minutes_scheduled)s, %(total_minutes_actual)s,
                        %(meetings_started)s, %(meetings_ended)s, %(meetings_ongoing)s
                    )
                    ON CONFLICT (room_id, date, hour)
                    DO UPDATE SET
                        total_meetings = EXCLUDED.total_meetings,
                        total_minutes_scheduled = EXCLUDED.total_minutes_scheduled,
                        total_minutes_actual = EXCLUDED.total_minutes_actual,
                        meetings_started = EXCLUDED.meetings_started,
                        meetings_ended = EXCLUDED.meetings_ended,
                        meetings_ongoing = EXCLUDED.meetings_ongoing,
                        calculated_at = NOW()
                """, hourly_data)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing hourly utilization: {e}")
            raise
        finally:
            conn.close()

    def get_utilization_summary(self, from_date: datetime, to_date: datetime,
                               room_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of utilization metrics

        Args:
            from_date: Start date
            to_date: End date
            room_id: Optional room filter

        Returns:
            Summary statistics
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_clause = "WHERE date BETWEEN %s AND %s"
                params = [from_date.date(), to_date.date()]

                if room_id:
                    where_clause += " AND room_id = %s"
                    params.append(room_id)

                query = f"""
                    SELECT
                        COUNT(DISTINCT room_id) as total_rooms,
                        SUM(total_completed_meetings) as total_meetings,
                        AVG(actual_utilization_rate) as avg_utilization,
                        SUM(total_no_shows) as total_no_shows,
                        AVG(no_show_rate) as avg_no_show_rate,
                        SUM(total_ghost_bookings) as total_ghost_bookings,
                        AVG(avg_participants_per_meeting) as avg_participants
                    FROM room_utilization_daily
                    {where_clause}
                """

                cur.execute(query, params)
                summary = cur.fetchone()

                # Get underutilized rooms (< 30%)
                cur.execute(f"""
                    SELECT
                        room_id,
                        room_name,
                        AVG(actual_utilization_rate) as avg_utilization
                    FROM room_utilization_daily
                    {where_clause}
                    GROUP BY room_id, room_name
                    HAVING AVG(actual_utilization_rate) < 30
                    ORDER BY avg_utilization ASC
                """, params)

                underutilized_rooms = cur.fetchall()

                # Get overutilized rooms (> 80%)
                cur.execute(f"""
                    SELECT
                        room_id,
                        room_name,
                        AVG(actual_utilization_rate) as avg_utilization
                    FROM room_utilization_daily
                    {where_clause}
                    GROUP BY room_id, room_name
                    HAVING AVG(actual_utilization_rate) > 80
                    ORDER BY avg_utilization DESC
                """, params)

                overutilized_rooms = cur.fetchall()

                return {
                    'summary': dict(summary) if summary else {},
                    'underutilized_rooms': underutilized_rooms,
                    'overutilized_rooms': overutilized_rooms,
                    'period': {
                        'from_date': from_date.date().isoformat(),
                        'to_date': to_date.date().isoformat()
                    }
                }
        finally:
            conn.close()

    def refresh_materialized_views(self) -> None:
        """Refresh all utilization materialized views"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT refresh_utilization_views()")
            conn.commit()
            logger.info("Materialized views refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing materialized views: {e}")
            raise
        finally:
            conn.close()
