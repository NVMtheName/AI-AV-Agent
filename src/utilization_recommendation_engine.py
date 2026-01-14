"""
Utilization Recommendation Engine - Generates optimization recommendations
Analyzes utilization patterns and provides actionable insights
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """Structure for a utilization recommendation"""
    recommendation_type: str
    priority: str
    title: str
    description: str
    recommended_action: str
    room_id: str
    room_name: str
    building: Optional[str] = None
    utilization_rate: Optional[Decimal] = None
    no_show_rate: Optional[Decimal] = None
    avg_occupancy: Optional[Decimal] = None
    estimated_hours_saved: Optional[Decimal] = None
    supporting_data: Optional[Dict[str, Any]] = None


class UtilizationRecommendationEngine:
    """Generates optimization recommendations based on utilization patterns"""

    def __init__(self, db_connection_string: str):
        """
        Initialize recommendation engine

        Args:
            db_connection_string: PostgreSQL connection string
        """
        self.db_connection_string = db_connection_string

        # Configurable thresholds
        self.low_utilization_threshold = 30.0  # < 30% utilization
        self.high_utilization_threshold = 80.0  # > 80% utilization
        self.high_no_show_threshold = 20.0     # > 20% no-show rate
        self.ghost_booking_threshold = 5       # > 5 ghost bookings
        self.capacity_mismatch_threshold = 0.5  # avg participants < 50% of capacity

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_connection_string)

    def analyze_underutilized_rooms(self, from_date: datetime, to_date: datetime,
                                   min_days: int = 20) -> List[Recommendation]:
        """
        Identify consistently underutilized rooms

        Args:
            from_date: Start date for analysis
            to_date: End date for analysis
            min_days: Minimum days of data required

        Returns:
            List of recommendations for underutilized rooms
        """
        recommendations = []
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        room_id,
                        room_name,
                        building,
                        AVG(actual_utilization_rate) as avg_utilization,
                        COUNT(*) as days_analyzed,
                        SUM(total_completed_meetings) as total_meetings,
                        AVG(avg_participants_per_meeting) as avg_participants,
                        SUM(total_actual_hours) as total_hours_used,
                        AVG(total_available_hours) as avg_available_hours
                    FROM room_utilization_daily
                    WHERE date BETWEEN %s AND %s
                    GROUP BY room_id, room_name, building
                    HAVING
                        COUNT(*) >= %s
                        AND AVG(actual_utilization_rate) < %s
                    ORDER BY avg_utilization ASC
                """, (from_date.date(), to_date.date(), min_days, self.low_utilization_threshold))

                underutilized_rooms = cur.fetchall()

                for room in underutilized_rooms:
                    utilization = float(room['avg_utilization'])
                    days_analyzed = room['days_analyzed']
                    avg_hours = float(room['avg_available_hours'])
                    hours_used = float(room['total_hours_used'])
                    potential_savings = (avg_hours - hours_used) / days_analyzed

                    # Determine priority
                    if utilization < 10:
                        priority = 'critical'
                    elif utilization < 20:
                        priority = 'high'
                    else:
                        priority = 'medium'

                    recommendations.append(Recommendation(
                        recommendation_type='underutilized_repurpose',
                        priority=priority,
                        title=f"Room '{room['room_name']}' is significantly underutilized",
                        description=f"This room has an average utilization rate of {utilization:.1f}% "
                                   f"over {days_analyzed} days, indicating it may not be meeting "
                                   f"organizational needs in its current configuration.",
                        recommended_action=f"Consider repurposing this space for alternative uses such as "
                                          f"hot-desking, quiet work areas, or collaboration spaces. "
                                          f"Alternatively, evaluate if the room size or equipment matches user needs.",
                        room_id=room['room_id'],
                        room_name=room['room_name'],
                        building=room['building'],
                        utilization_rate=Decimal(str(utilization)),
                        avg_occupancy=Decimal(str(room['avg_participants'] or 0)),
                        estimated_hours_saved=Decimal(str(potential_savings * days_analyzed)),
                        supporting_data={
                            'days_analyzed': days_analyzed,
                            'total_meetings': room['total_meetings'],
                            'avg_participants': float(room['avg_participants'] or 0),
                            'total_hours_used': hours_used
                        }
                    ))

        finally:
            conn.close()

        return recommendations

    def analyze_overutilized_rooms(self, from_date: datetime, to_date: datetime,
                                  min_days: int = 20) -> List[Recommendation]:
        """
        Identify consistently overutilized rooms that may need expansion

        Args:
            from_date: Start date for analysis
            to_date: End date for analysis
            min_days: Minimum days of data required

        Returns:
            List of recommendations for overutilized rooms
        """
        recommendations = []
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        room_id,
                        room_name,
                        building,
                        AVG(actual_utilization_rate) as avg_utilization,
                        COUNT(*) as days_analyzed,
                        SUM(total_completed_meetings) as total_meetings,
                        AVG(avg_participants_per_meeting) as avg_participants,
                        MAX(max_participants_in_day) as max_participants
                    FROM room_utilization_daily
                    WHERE date BETWEEN %s AND %s
                    GROUP BY room_id, room_name, building
                    HAVING
                        COUNT(*) >= %s
                        AND AVG(actual_utilization_rate) > %s
                    ORDER BY avg_utilization DESC
                """, (from_date.date(), to_date.date(), min_days, self.high_utilization_threshold))

                overutilized_rooms = cur.fetchall()

                for room in overutilized_rooms:
                    utilization = float(room['avg_utilization'])
                    days_analyzed = room['days_analyzed']

                    # Determine priority
                    if utilization > 95:
                        priority = 'critical'
                    elif utilization > 90:
                        priority = 'high'
                    else:
                        priority = 'medium'

                    recommendations.append(Recommendation(
                        recommendation_type='overbooked_expansion',
                        priority=priority,
                        title=f"Room '{room['room_name']}' has very high utilization",
                        description=f"This room has an average utilization rate of {utilization:.1f}% "
                                   f"over {days_analyzed} days, indicating high demand that may not "
                                   f"be fully met. Users may struggle to book this room when needed.",
                        recommended_action=f"Consider adding a similar room nearby, extending available hours, "
                                          f"or implementing a room rotation policy. Also review booking patterns "
                                          f"to identify if meetings could be scheduled in alternative spaces.",
                        room_id=room['room_id'],
                        room_name=room['room_name'],
                        building=room['building'],
                        utilization_rate=Decimal(str(utilization)),
                        avg_occupancy=Decimal(str(room['avg_participants'] or 0)),
                        supporting_data={
                            'days_analyzed': days_analyzed,
                            'total_meetings': room['total_meetings'],
                            'avg_participants': float(room['avg_participants'] or 0),
                            'max_participants': room['max_participants']
                        }
                    ))

        finally:
            conn.close()

        return recommendations

    def analyze_high_no_show_rooms(self, from_date: datetime, to_date: datetime,
                                  min_days: int = 20) -> List[Recommendation]:
        """
        Identify rooms with high no-show rates

        Args:
            from_date: Start date for analysis
            to_date: End date for analysis
            min_days: Minimum days of data required

        Returns:
            List of recommendations for high no-show rooms
        """
        recommendations = []
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        room_id,
                        room_name,
                        building,
                        AVG(no_show_rate) as avg_no_show_rate,
                        COUNT(*) as days_analyzed,
                        SUM(total_no_shows) as total_no_shows,
                        SUM(total_scheduled_meetings) as total_scheduled,
                        SUM(total_ghost_bookings) as total_ghost_bookings,
                        SUM(total_scheduled_hours) - SUM(total_actual_hours) as wasted_hours
                    FROM room_utilization_daily
                    WHERE date BETWEEN %s AND %s
                    GROUP BY room_id, room_name, building
                    HAVING
                        COUNT(*) >= %s
                        AND AVG(no_show_rate) > %s
                        AND SUM(total_scheduled_meetings) > 10
                    ORDER BY avg_no_show_rate DESC
                """, (from_date.date(), to_date.date(), min_days, self.high_no_show_threshold))

                high_no_show_rooms = cur.fetchall()

                for room in high_no_show_rooms:
                    no_show_rate = float(room['avg_no_show_rate'])
                    days_analyzed = room['days_analyzed']
                    wasted_hours = float(room['wasted_hours'])
                    ghost_bookings = room['total_ghost_bookings']

                    # Determine priority
                    if no_show_rate > 40 or wasted_hours > 50:
                        priority = 'high'
                    elif no_show_rate > 30:
                        priority = 'medium'
                    else:
                        priority = 'low'

                    action_items = []
                    if no_show_rate > 30:
                        action_items.append("Implement a no-show policy with reminders 15 minutes before meetings")
                    if ghost_bookings > 10:
                        action_items.append("Require meeting check-in within 10 minutes of scheduled start time")
                    action_items.append("Send booking confirmations and calendar reminders")
                    action_items.append("Consider automatic release of unused bookings after grace period")

                    recommendations.append(Recommendation(
                        recommendation_type='high_no_show_policy',
                        priority=priority,
                        title=f"Room '{room['room_name']}' has high no-show rate",
                        description=f"This room has a {no_show_rate:.1f}% no-show rate over {days_analyzed} days, "
                                   f"resulting in {wasted_hours:.1f} hours of wasted booking time. "
                                   f"This prevents others from using the room and reduces overall efficiency.",
                        recommended_action=" ".join(action_items),
                        room_id=room['room_id'],
                        room_name=room['room_name'],
                        building=room['building'],
                        no_show_rate=Decimal(str(no_show_rate)),
                        estimated_hours_saved=Decimal(str(wasted_hours * 0.7)),  # Estimate 70% recovery
                        supporting_data={
                            'days_analyzed': days_analyzed,
                            'total_no_shows': room['total_no_shows'],
                            'total_scheduled': room['total_scheduled'],
                            'ghost_bookings': ghost_bookings,
                            'wasted_hours': wasted_hours
                        }
                    ))

        finally:
            conn.close()

        return recommendations

    def analyze_optimal_timing(self, from_date: datetime, to_date: datetime) -> List[Recommendation]:
        """
        Analyze peak usage patterns and suggest optimal meeting times

        Args:
            from_date: Start date for analysis
            to_date: End date for analysis

        Returns:
            List of timing recommendations
        """
        recommendations = []
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Find rooms with uneven utilization across hours
                cur.execute("""
                    SELECT
                        room_id,
                        room_name,
                        building,
                        hour,
                        AVG(hourly_utilization_rate) as avg_utilization,
                        COUNT(*) as days_count
                    FROM room_utilization_hourly
                    WHERE
                        date BETWEEN %s AND %s
                        AND is_business_hour = TRUE
                    GROUP BY room_id, room_name, building, hour
                    HAVING COUNT(*) >= 15
                """, (from_date.date(), to_date.date()))

                hourly_data = cur.fetchall()

                # Group by room
                rooms_data = {}
                for row in hourly_data:
                    room_id = row['room_id']
                    if room_id not in rooms_data:
                        rooms_data[room_id] = {
                            'room_name': row['room_name'],
                            'building': row['building'],
                            'hours': []
                        }
                    rooms_data[room_id]['hours'].append({
                        'hour': row['hour'],
                        'utilization': float(row['avg_utilization'])
                    })

                # Analyze each room for timing opportunities
                for room_id, data in rooms_data.items():
                    if len(data['hours']) < 8:  # Need at least 8 hours of data
                        continue

                    hours = sorted(data['hours'], key=lambda x: x['utilization'])
                    low_hours = [h for h in hours if h['utilization'] < 40]
                    high_hours = [h for h in hours if h['utilization'] > 70]

                    if len(low_hours) >= 2 and len(high_hours) >= 2:
                        low_hour_times = [f"{h['hour']:02d}:00" for h in low_hours[:3]]
                        high_hour_times = [f"{h['hour']:02d}:00" for h in high_hours[:3]]

                        recommendations.append(Recommendation(
                            recommendation_type='optimal_timing',
                            priority='low',
                            title=f"Optimize meeting scheduling for '{data['room_name']}'",
                            description=f"Analysis shows significant utilization variance throughout the day. "
                                       f"Peak hours ({', '.join(high_hour_times)}) are heavily booked while "
                                       f"off-peak hours ({', '.join(low_hour_times)}) are underutilized.",
                            recommended_action=f"Encourage users to schedule meetings during off-peak hours "
                                              f"({', '.join(low_hour_times)}). Consider implementing dynamic "
                                              f"pricing or priority booking for peak times, or send scheduling "
                                              f"suggestions when users book during busy periods.",
                            room_id=room_id,
                            room_name=data['room_name'],
                            building=data['building'],
                            supporting_data={
                                'low_utilization_hours': low_hours,
                                'high_utilization_hours': high_hours
                            }
                        ))

        finally:
            conn.close()

        return recommendations

    def analyze_capacity_mismatch(self, from_date: datetime, to_date: datetime,
                                 min_days: int = 20) -> List[Recommendation]:
        """
        Identify rooms where capacity doesn't match typical usage

        Args:
            from_date: Start date for analysis
            to_date: End date for analysis
            min_days: Minimum days of data required

        Returns:
            List of capacity mismatch recommendations
        """
        recommendations = []
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get room capacity from configuration
                cur.execute("""
                    SELECT
                        d.room_id,
                        d.room_name,
                        d.building,
                        c.max_capacity,
                        c.recommended_capacity,
                        AVG(d.avg_participants_per_meeting) as avg_participants,
                        COUNT(*) as days_analyzed,
                        MAX(d.max_participants_in_day) as max_participants_observed
                    FROM room_utilization_daily d
                    LEFT JOIN room_configuration c ON d.room_id = c.room_id
                    WHERE
                        d.date BETWEEN %s AND %s
                        AND c.max_capacity IS NOT NULL
                    GROUP BY
                        d.room_id, d.room_name, d.building,
                        c.max_capacity, c.recommended_capacity
                    HAVING COUNT(*) >= %s
                """, (from_date.date(), to_date.date(), min_days))

                rooms = cur.fetchall()

                for room in rooms:
                    max_capacity = room['max_capacity']
                    avg_participants = float(room['avg_participants'] or 0)
                    capacity_usage_ratio = avg_participants / max_capacity if max_capacity > 0 else 0

                    # Check if room is consistently underutilized in terms of capacity
                    if capacity_usage_ratio < self.capacity_mismatch_threshold:
                        recommendations.append(Recommendation(
                            recommendation_type='capacity_mismatch',
                            priority='medium',
                            title=f"Room '{room['room_name']}' capacity exceeds typical usage",
                            description=f"This room has a capacity of {max_capacity} people but averages only "
                                       f"{avg_participants:.1f} participants per meeting ({capacity_usage_ratio*100:.1f}% "
                                       f"capacity usage). This suggests the room may be larger than necessary for "
                                       f"typical use cases.",
                            recommended_action=f"Consider converting this to a smaller meeting space and creating "
                                              f"an additional room, or reserving this room for larger meetings only. "
                                              f"Alternatively, promote this room for larger team gatherings.",
                            room_id=room['room_id'],
                            room_name=room['room_name'],
                            building=room['building'],
                            avg_occupancy=Decimal(str(avg_participants)),
                            supporting_data={
                                'max_capacity': max_capacity,
                                'avg_participants': avg_participants,
                                'capacity_usage_ratio': capacity_usage_ratio,
                                'days_analyzed': room['days_analyzed'],
                                'max_participants_observed': room['max_participants_observed']
                            }
                        ))

        finally:
            conn.close()

        return recommendations

    def generate_all_recommendations(self, from_date: datetime, to_date: datetime,
                                    min_days: int = 20) -> List[Recommendation]:
        """
        Generate all types of recommendations

        Args:
            from_date: Start date for analysis
            to_date: End date for analysis
            min_days: Minimum days of data required

        Returns:
            Complete list of all recommendations
        """
        logger.info(f"Generating recommendations for period {from_date.date()} to {to_date.date()}")

        all_recommendations = []

        # Underutilized rooms
        logger.info("Analyzing underutilized rooms...")
        all_recommendations.extend(
            self.analyze_underutilized_rooms(from_date, to_date, min_days)
        )

        # Overutilized rooms
        logger.info("Analyzing overutilized rooms...")
        all_recommendations.extend(
            self.analyze_overutilized_rooms(from_date, to_date, min_days)
        )

        # High no-show rates
        logger.info("Analyzing no-show patterns...")
        all_recommendations.extend(
            self.analyze_high_no_show_rooms(from_date, to_date, min_days)
        )

        # Optimal timing
        logger.info("Analyzing timing patterns...")
        all_recommendations.extend(
            self.analyze_optimal_timing(from_date, to_date)
        )

        # Capacity mismatches
        logger.info("Analyzing capacity usage...")
        all_recommendations.extend(
            self.analyze_capacity_mismatch(from_date, to_date, min_days)
        )

        logger.info(f"Generated {len(all_recommendations)} recommendations")
        return all_recommendations

    def store_recommendations(self, recommendations: List[Recommendation],
                            analysis_start_date: datetime,
                            analysis_end_date: datetime) -> None:
        """
        Store recommendations in database

        Args:
            recommendations: List of recommendations to store
            analysis_start_date: Start date of analysis period
            analysis_end_date: End date of analysis period
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                for rec in recommendations:
                    days_analyzed = (analysis_end_date - analysis_start_date).days

                    cur.execute("""
                        INSERT INTO utilization_recommendations (
                            recommendation_id, room_id, room_name, building,
                            recommendation_type, priority, title, description,
                            recommended_action, utilization_rate, no_show_rate,
                            avg_occupancy, analysis_start_date, analysis_end_date,
                            days_analyzed, estimated_hours_saved, supporting_data
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        str(uuid.uuid4()),
                        rec.room_id,
                        rec.room_name,
                        rec.building,
                        rec.recommendation_type,
                        rec.priority,
                        rec.title,
                        rec.description,
                        rec.recommended_action,
                        float(rec.utilization_rate) if rec.utilization_rate else None,
                        float(rec.no_show_rate) if rec.no_show_rate else None,
                        float(rec.avg_occupancy) if rec.avg_occupancy else None,
                        analysis_start_date.date(),
                        analysis_end_date.date(),
                        days_analyzed,
                        float(rec.estimated_hours_saved) if rec.estimated_hours_saved else None,
                        psycopg2.extras.Json(rec.supporting_data) if rec.supporting_data else None
                    ))

            conn.commit()
            logger.info(f"Stored {len(recommendations)} recommendations")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing recommendations: {e}")
            raise
        finally:
            conn.close()

    def get_active_recommendations(self, room_id: Optional[str] = None,
                                  priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get active recommendations from database

        Args:
            room_id: Optional room filter
            priority: Optional priority filter

        Returns:
            List of active recommendations
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_clauses = ["status = 'pending'"]
                params = []

                if room_id:
                    where_clauses.append("room_id = %s")
                    params.append(room_id)

                if priority:
                    where_clauses.append("priority = %s")
                    params.append(priority)

                where_clause = " AND ".join(where_clauses)

                query = f"""
                    SELECT
                        recommendation_id,
                        room_id,
                        room_name,
                        building,
                        recommendation_type,
                        priority,
                        title,
                        description,
                        recommended_action,
                        utilization_rate,
                        no_show_rate,
                        avg_occupancy,
                        estimated_hours_saved,
                        created_at,
                        supporting_data
                    FROM utilization_recommendations
                    WHERE {where_clause}
                    ORDER BY
                        CASE priority
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        created_at DESC
                """

                cur.execute(query, params)
                return cur.fetchall()
        finally:
            conn.close()
