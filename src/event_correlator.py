"""
Event correlation engine for temporal and causal analysis.

Identifies relationships between events to support root cause analysis.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

from .models import StructuredEvent, EventCategory, Severity


class EventCorrelator:
    """
    Correlates events across time to identify causal relationships.

    Principles:
    - Temporal proximity suggests correlation
    - Network events often precede service failures
    - Configuration changes are suspect when near failures
    - Repeated patterns indicate systemic issues
    """

    def __init__(self, correlation_window_seconds: int = 300):
        """
        Initialize correlator.

        Args:
            correlation_window_seconds: Time window for correlating events (default 5 min)
        """
        self.correlation_window = timedelta(seconds=correlation_window_seconds)

    def correlate_events(self, events: List[StructuredEvent]) -> Dict[str, any]:
        """
        Analyze events and identify correlations.

        Returns:
            Dictionary with correlation analysis results
        """
        if not events:
            return {
                'timeline': [],
                'clusters': [],
                'cascading_failures': [],
                'temporal_patterns': {},
                'affected_resources': set()
            }

        # Sort events chronologically
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        analysis = {
            'timeline': sorted_events,
            'clusters': self._identify_clusters(sorted_events),
            'cascading_failures': self._detect_cascading_failures(sorted_events),
            'temporal_patterns': self._analyze_temporal_patterns(sorted_events),
            'affected_resources': self._identify_affected_resources(sorted_events),
            'change_events': self._identify_changes(sorted_events),
            'error_bursts': self._detect_error_bursts(sorted_events)
        }

        return analysis

    def _identify_clusters(self, events: List[StructuredEvent]) -> List[Dict]:
        """
        Group events that occur close together in time.

        Returns clusters of related events.
        """
        clusters = []
        current_cluster = []
        cluster_start = None

        for event in events:
            if not current_cluster:
                current_cluster = [event]
                cluster_start = event.timestamp
            else:
                time_since_cluster_start = event.timestamp - cluster_start
                if time_since_cluster_start <= self.correlation_window:
                    current_cluster.append(event)
                else:
                    # Close current cluster
                    if len(current_cluster) > 1:
                        clusters.append({
                            'start_time': cluster_start,
                            'end_time': current_cluster[-1].timestamp,
                            'duration': current_cluster[-1].timestamp - cluster_start,
                            'event_count': len(current_cluster),
                            'events': current_cluster,
                            'severity_distribution': self._count_severities(current_cluster),
                            'categories': self._count_categories(current_cluster)
                        })
                    # Start new cluster
                    current_cluster = [event]
                    cluster_start = event.timestamp

        # Don't forget the last cluster
        if len(current_cluster) > 1:
            clusters.append({
                'start_time': cluster_start,
                'end_time': current_cluster[-1].timestamp,
                'duration': current_cluster[-1].timestamp - cluster_start,
                'event_count': len(current_cluster),
                'events': current_cluster,
                'severity_distribution': self._count_severities(current_cluster),
                'categories': self._count_categories(current_cluster)
            })

        return clusters

    def _detect_cascading_failures(self, events: List[StructuredEvent]) -> List[Dict]:
        """
        Detect cascading failure patterns where one failure triggers others.

        Common pattern: Network failure -> Service unavailable -> AV hardware offline
        """
        cascades = []

        # Look for sequences where errors of different categories follow each other
        error_events = [e for e in events if e.severity in [Severity.ERROR, Severity.CRITICAL]]

        for i in range(len(error_events) - 1):
            primary_event = error_events[i]
            subsequent_errors = []

            # Find errors within correlation window after primary
            for j in range(i + 1, len(error_events)):
                candidate = error_events[j]
                time_diff = candidate.timestamp - primary_event.timestamp

                if time_diff <= self.correlation_window:
                    # Different category suggests cascade
                    if candidate.category != primary_event.category:
                        subsequent_errors.append(candidate)
                else:
                    break

            if subsequent_errors:
                cascades.append({
                    'primary_event': primary_event,
                    'subsequent_errors': subsequent_errors,
                    'duration': subsequent_errors[-1].timestamp - primary_event.timestamp,
                    'categories_affected': [primary_event.category] + [e.category for e in subsequent_errors]
                })

        return cascades

    def _analyze_temporal_patterns(self, events: List[StructuredEvent]) -> Dict:
        """
        Analyze when events occur to detect patterns.

        Looks for:
        - Events at specific times of day
        - Recurring intervals
        - Day-of-week patterns
        """
        patterns = {
            'hour_distribution': defaultdict(int),
            'day_distribution': defaultdict(int),
            'recurring_intervals': []
        }

        for event in events:
            patterns['hour_distribution'][event.timestamp.hour] += 1
            patterns['day_distribution'][event.timestamp.strftime('%A')] += 1

        # Detect recurring intervals (e.g., every hour, every day)
        error_timestamps = [e.timestamp for e in events if e.severity in [Severity.ERROR, Severity.CRITICAL]]

        if len(error_timestamps) >= 3:
            intervals = []
            for i in range(len(error_timestamps) - 1):
                interval = (error_timestamps[i + 1] - error_timestamps[i]).total_seconds()
                intervals.append(interval)

            # Check for consistent intervals
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)

                # If low variance, it's recurring
                if variance < (avg_interval * 0.1):  # 10% variance threshold
                    patterns['recurring_intervals'].append({
                        'average_interval_seconds': avg_interval,
                        'occurrences': len(error_timestamps),
                        'pattern': self._classify_interval(avg_interval)
                    })

        return patterns

    def _classify_interval(self, seconds: float) -> str:
        """Classify interval into human-readable pattern"""
        if 3500 <= seconds <= 3700:  # ~1 hour
            return "hourly"
        elif 85000 <= seconds <= 88000:  # ~24 hours
            return "daily"
        elif 600 <= seconds <= 900:  # ~15 minutes
            return "every_15_minutes"
        elif seconds < 60:
            return "rapid_succession"
        else:
            return f"every_{int(seconds/60)}_minutes"

    def _identify_affected_resources(self, events: List[StructuredEvent]) -> Set[str]:
        """Identify all affected rooms, devices, and services"""
        resources = set()

        for event in events:
            if event.room_name:
                resources.add(f"Room: {event.room_name}")
            if event.device_id:
                resources.add(f"Device: {event.device_id}")
            if event.service:
                resources.add(f"Service: {event.service}")
            if event.device_type:
                resources.add(f"Type: {event.device_type}")

        return resources

    def _identify_changes(self, events: List[StructuredEvent]) -> List[StructuredEvent]:
        """
        Identify configuration changes or state changes.

        Changes before failures are highly suspicious.
        """
        change_keywords = ['config', 'update', 'modify', 'change', 'deploy', 'restart', 'reboot']

        changes = []
        for event in events:
            message_lower = event.message.lower()
            if any(keyword in message_lower for keyword in change_keywords):
                changes.append(event)

        return changes

    def _detect_error_bursts(self, events: List[StructuredEvent]) -> List[Dict]:
        """
        Detect sudden bursts of errors (many errors in short time).

        Indicates acute failure vs. gradual degradation.
        """
        bursts = []
        error_events = [e for e in events if e.severity in [Severity.ERROR, Severity.CRITICAL]]

        if not error_events:
            return bursts

        # Use sliding window to detect bursts
        window = timedelta(seconds=60)  # 1-minute window
        threshold = 5  # 5+ errors in 1 minute = burst

        for i, event in enumerate(error_events):
            errors_in_window = 1
            for j in range(i + 1, len(error_events)):
                if error_events[j].timestamp - event.timestamp <= window:
                    errors_in_window += 1
                else:
                    break

            if errors_in_window >= threshold:
                burst_events = error_events[i:i + errors_in_window]
                bursts.append({
                    'start_time': event.timestamp,
                    'error_count': errors_in_window,
                    'duration': burst_events[-1].timestamp - event.timestamp,
                    'events': burst_events,
                    'categories': list(set(e.category for e in burst_events))
                })

        return bursts

    def _count_severities(self, events: List[StructuredEvent]) -> Dict[str, int]:
        """Count events by severity"""
        counts = defaultdict(int)
        for event in events:
            counts[event.severity.value] += 1
        return dict(counts)

    def _count_categories(self, events: List[StructuredEvent]) -> Dict[str, int]:
        """Count events by category"""
        counts = defaultdict(int)
        for event in events:
            counts[event.category.value] += 1
        return dict(counts)

    def find_events_before_failure(
        self,
        events: List[StructuredEvent],
        failure_event: StructuredEvent,
        lookback_seconds: int = 600
    ) -> List[StructuredEvent]:
        """
        Find all events that occurred before a specific failure.

        Critical for identifying triggering events.
        """
        lookback = timedelta(seconds=lookback_seconds)
        cutoff_time = failure_event.timestamp - lookback

        preceding_events = [
            e for e in events
            if cutoff_time <= e.timestamp < failure_event.timestamp
        ]

        return sorted(preceding_events, key=lambda e: e.timestamp)
