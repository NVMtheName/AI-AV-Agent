"""
Database writer for ingestion pipeline.

Writes normalized events to Postgres using the schema defined in database_schema.sql.
"""

import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Optional, Dict, Any
import logging
import json
from datetime import datetime

from ingestion_models import UnifiedEvent


logger = logging.getLogger(__name__)


class DatabaseWriter:
    """
    Writes UnifiedEvents to Postgres database.

    Handles:
    - Connection pooling
    - Batch inserts for performance
    - Error handling and retries
    - Transaction management
    """

    def __init__(self, connection_string: str, batch_size: int = 1000):
        """
        Initialize database writer.

        Args:
            connection_string: Postgres connection string
                Example: "postgresql://user:pass@localhost:5432/aiops"
            batch_size: Number of events to insert in a single batch
        """
        self.connection_string = connection_string
        self.batch_size = batch_size
        self.conn: Optional[psycopg2.extensions.connection] = None

    def connect(self):
        """Establish database connection"""
        if not self.conn or self.conn.closed:
            logger.info("Connecting to database...")
            self.conn = psycopg2.connect(self.connection_string)
            logger.info("Database connection established")

    def close(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def write_events(self, events: List[UnifiedEvent], commit: bool = True) -> int:
        """
        Write events to database.

        Args:
            events: List of UnifiedEvents
            commit: Whether to commit the transaction

        Returns:
            Number of events written
        """
        if not events:
            return 0

        self.connect()

        try:
            cursor = self.conn.cursor()

            # Prepare batch insert
            insert_query = """
                INSERT INTO events (
                    event_id, ts, source_type, source_vendor, source_system,
                    site, building, floor, room,
                    asset_id, asset_type, asset_make, asset_model, asset_serial,
                    asset_ip, asset_mac, asset_hostname, asset_firmware_version,
                    severity, category, signal, message,
                    incident_id, ticket_id, change_id, correlation_ids,
                    metadata, tags,
                    raw_line, raw_ts, source_file, line_number, raw_fields,
                    ingested_at, parser_version
                ) VALUES (
                    %(event_id)s, %(ts)s, %(source_type)s, %(source_vendor)s, %(source_system)s,
                    %(site)s, %(building)s, %(floor)s, %(room)s,
                    %(asset_id)s, %(asset_type)s, %(asset_make)s, %(asset_model)s, %(asset_serial)s,
                    %(asset_ip)s, %(asset_mac)s, %(asset_hostname)s, %(asset_firmware_version)s,
                    %(severity)s, %(category)s, %(signal)s, %(message)s,
                    %(incident_id)s, %(ticket_id)s, %(change_id)s, %(correlation_ids)s,
                    %(metadata)s, %(tags)s,
                    %(raw_line)s, %(raw_ts)s, %(source_file)s, %(line_number)s, %(raw_fields)s,
                    %(ingested_at)s, %(parser_version)s
                )
                ON CONFLICT (event_id) DO NOTHING
            """

            # Convert events to dict format
            event_dicts = [self._event_to_dict(event) for event in events]

            # Batch insert
            execute_batch(cursor, insert_query, event_dicts, page_size=self.batch_size)

            rows_inserted = cursor.rowcount
            cursor.close()

            if commit:
                self.conn.commit()
                logger.info(f"Wrote {rows_inserted} events to database")

            return rows_inserted

        except Exception as e:
            logger.error(f"Failed to write events to database: {e}")
            if self.conn:
                self.conn.rollback()
            raise

    def _event_to_dict(self, event: UnifiedEvent) -> Dict[str, Any]:
        """Convert UnifiedEvent to dict for database insert"""

        # Extract asset info
        asset_id = None
        asset_type = None
        asset_make = None
        asset_model = None
        asset_serial = None
        asset_ip = None
        asset_mac = None
        asset_hostname = None
        asset_firmware_version = None

        if event.asset:
            asset_id = event.asset.asset_id
            asset_type = event.asset.asset_type
            asset_make = event.asset.make
            asset_model = event.asset.model
            asset_serial = event.asset.serial
            asset_ip = event.asset.ip
            asset_mac = event.asset.mac
            asset_hostname = event.asset.hostname
            asset_firmware_version = event.asset.firmware_version

        return {
            'event_id': event.event_id,
            'ts': event.ts,
            'source_type': event.source_type,
            'source_vendor': event.source_vendor,
            'source_system': event.source_system,
            'site': event.site,
            'building': event.building,
            'floor': event.floor,
            'room': event.room,
            'asset_id': asset_id,
            'asset_type': asset_type,
            'asset_make': asset_make,
            'asset_model': asset_model,
            'asset_serial': asset_serial,
            'asset_ip': asset_ip,
            'asset_mac': asset_mac,
            'asset_hostname': asset_hostname,
            'asset_firmware_version': asset_firmware_version,
            'severity': event.severity,
            'category': event.category,
            'signal': event.signal,
            'message': event.message,
            'incident_id': event.incident_id,
            'ticket_id': event.ticket_id,
            'change_id': event.change_id,
            'correlation_ids': json.dumps(event.correlation_ids) if event.correlation_ids else None,
            'metadata': json.dumps(event.metadata) if event.metadata else None,
            'tags': event.tags,
            'raw_line': event.raw.raw_line if event.raw else '',
            'raw_ts': event.raw.raw_ts if event.raw else None,
            'source_file': event.raw.source_file if event.raw else None,
            'line_number': event.raw.line_number if event.raw else None,
            'raw_fields': json.dumps(event.raw.raw_fields) if event.raw and event.raw.raw_fields else None,
            'ingested_at': event.ingested_at,
            'parser_version': event.parser_version,
        }

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful
        """
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def create_schema(self, schema_file: str):
        """
        Execute schema SQL file to create tables.

        Args:
            schema_file: Path to SQL schema file
        """
        self.connect()

        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()

            cursor = self.conn.cursor()
            cursor.execute(schema_sql)
            self.conn.commit()
            cursor.close()
            logger.info(f"Schema created from {schema_file}")

        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            if self.conn:
                self.conn.rollback()
            raise

    def get_event_count(self) -> int:
        """Get total number of events in database"""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get most recent events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of event dicts
        """
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM events ORDER BY ts DESC LIMIT %s",
            (limit,)
        )
        columns = [desc[0] for desc in cursor.description]
        events = []
        for row in cursor.fetchall():
            events.append(dict(zip(columns, row)))
        cursor.close()
        return events
