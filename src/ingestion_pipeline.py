"""
Main ingestion pipeline orchestrator.

Coordinates:
1. File discovery (recursively scan directories)
2. Parser selection based on file type/pattern
3. Parsing (vendor-specific parsers)
4. Asset enrichment
5. Database write
6. Error handling and logging

This is the primary entry point for ingesting operational data.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import re
from datetime import datetime

from parsers import (
    ZoomRoomsParser,
    QSysParser,
    NetworkSyslogParser,
    TicketsParser,
    ChangesParser,
    BaseParser
)
from ingestion_models import UnifiedEvent, ParseResult
from asset_enrichment import AssetEnricher
from database_writer import DatabaseWriter


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Main ingestion pipeline for AI Ops Copilot.

    Discovers files, selects appropriate parsers, parses logs,
    enriches with asset data, and writes to database.
    """

    def __init__(
        self,
        db_connection_string: Optional[str] = None,
        asset_db_path: Optional[Path] = None,
        ip_room_map_path: Optional[Path] = None,
        enable_enrichment: bool = True,
        enable_db_write: bool = True
    ):
        """
        Initialize ingestion pipeline.

        Args:
            db_connection_string: Postgres connection string
            asset_db_path: Path to asset database
            ip_room_map_path: Path to IP->Room mapping
            enable_enrichment: Enable asset enrichment
            enable_db_write: Enable database writing
        """
        # Initialize parsers
        self.parsers: Dict[str, BaseParser] = {
            'zoom': ZoomRoomsParser(),
            'qsys': QSysParser(),
            'network': NetworkSyslogParser(),
            'tickets': TicketsParser(),
            'changes': ChangesParser(),
        }

        # Initialize enricher
        self.enricher = None
        if enable_enrichment:
            self.enricher = AssetEnricher(
                asset_db_path=asset_db_path,
                ip_room_map_path=ip_room_map_path
            )

        # Initialize database writer
        self.db_writer = None
        if enable_db_write and db_connection_string:
            self.db_writer = DatabaseWriter(db_connection_string)

        # File pattern matching for parser selection
        self.file_patterns = {
            'zoom': [
                r'.*zoom.*\.log',
                r'.*zr-.*\.log',
                r'.*zoomroom.*\.log',
            ],
            'qsys': [
                r'.*qsys.*\.log',
                r'.*q-sys.*\.log',
                r'.*core-\d+.*\.log',
            ],
            'network': [
                r'.*syslog.*',
                r'.*switch.*\.log',
                r'.*router.*\.log',
                r'.*meraki.*\.log',
                r'.*cisco.*\.log',
            ],
            'tickets': [
                r'.*ticket.*\.csv',
                r'.*incident.*\.csv',
                r'.*servicenow.*\.csv',
                r'.*jira.*\.csv',
            ],
            'changes': [
                r'.*change.*\.csv',
                r'.*chg.*\.csv',
            ],
        }

        self.stats = {
            'files_processed': 0,
            'total_events': 0,
            'parse_errors': 0,
            'db_writes': 0,
        }

    def ingest_directory(
        self,
        directory: Path,
        recursive: bool = True,
        file_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest all files in a directory.

        Args:
            directory: Directory to scan
            recursive: Recursively scan subdirectories
            file_pattern: Optional glob pattern to filter files

        Returns:
            Statistics dict
        """
        logger.info(f"Starting ingestion from directory: {directory}")
        logger.info(f"Recursive: {recursive}, Pattern: {file_pattern}")

        # Discover files
        if recursive:
            if file_pattern:
                files = list(directory.rglob(file_pattern))
            else:
                files = list(directory.rglob('*'))
        else:
            if file_pattern:
                files = list(directory.glob(file_pattern))
            else:
                files = list(directory.glob('*'))

        # Filter out directories
        files = [f for f in files if f.is_file()]

        logger.info(f"Found {len(files)} files to process")

        # Process each file
        for file_path in files:
            try:
                self.ingest_file(file_path)
            except Exception as e:
                logger.error(f"Failed to ingest file {file_path}: {e}")
                self.stats['parse_errors'] += 1

        logger.info("Ingestion complete")
        logger.info(f"Stats: {self.stats}")

        return self.stats

    def ingest_file(self, file_path: Path) -> ParseResult:
        """
        Ingest a single file.

        Args:
            file_path: Path to file

        Returns:
            ParseResult with events and errors
        """
        logger.info(f"Processing file: {file_path}")

        # Select parser
        parser = self._select_parser(file_path)
        if not parser:
            logger.warning(f"No parser found for file: {file_path}")
            return ParseResult(
                success=False,
                parser_name="unknown",
                source_file=str(file_path)
            )

        # Parse file
        if isinstance(parser, (TicketsParser, ChangesParser)):
            # CSV parsers use different method
            result = parser.parse_csv_file(file_path)
        else:
            result = parser.parse_file(file_path)

        self.stats['files_processed'] += 1
        self.stats['total_events'] += result.parsed_lines
        self.stats['parse_errors'] += result.failed_lines

        logger.info(
            f"Parsed {result.parsed_lines} events from {file_path} "
            f"({result.failed_lines} errors)"
        )

        # Enrich events
        if self.enricher and result.events:
            logger.info(f"Enriching {len(result.events)} events...")
            result.events = self.enricher.enrich_events(result.events)

        # Write to database
        if self.db_writer and result.events:
            try:
                rows_written = self.db_writer.write_events(result.events)
                self.stats['db_writes'] += rows_written
                logger.info(f"Wrote {rows_written} events to database")
            except Exception as e:
                logger.error(f"Failed to write events to database: {e}")
                result.success = False

        return result

    def ingest_text(
        self,
        text: str,
        parser_type: str,
        source_identifier: str = "text_input"
    ) -> ParseResult:
        """
        Ingest raw text using specified parser.

        Args:
            text: Raw log text
            parser_type: Parser type (zoom, qsys, network, etc.)
            source_identifier: Identifier for this text source

        Returns:
            ParseResult
        """
        parser = self.parsers.get(parser_type)
        if not parser:
            raise ValueError(f"Unknown parser type: {parser_type}")

        logger.info(f"Parsing text with {parser_type} parser...")
        result = parser.parse_text(text, source_identifier)

        self.stats['total_events'] += result.parsed_lines
        self.stats['parse_errors'] += result.failed_lines

        # Enrich
        if self.enricher and result.events:
            result.events = self.enricher.enrich_events(result.events)

        # Write to database
        if self.db_writer and result.events:
            try:
                rows_written = self.db_writer.write_events(result.events)
                self.stats['db_writes'] += rows_written
            except Exception as e:
                logger.error(f"Failed to write events to database: {e}")
                result.success = False

        return result

    def _select_parser(self, file_path: Path) -> Optional[BaseParser]:
        """
        Select appropriate parser based on filename.

        Args:
            file_path: File path

        Returns:
            Parser instance or None
        """
        filename = file_path.name.lower()

        # Check patterns
        for parser_type, patterns in self.file_patterns.items():
            for pattern in patterns:
                if re.match(pattern, filename, re.IGNORECASE):
                    logger.debug(f"Selected {parser_type} parser for {filename}")
                    return self.parsers[parser_type]

        # Default: try to guess from filename
        if 'zoom' in filename or 'zr' in filename:
            return self.parsers['zoom']
        elif 'qsys' in filename or 'q-sys' in filename:
            return self.parsers['qsys']
        elif 'syslog' in filename or 'switch' in filename:
            return self.parsers['network']
        elif '.csv' in filename:
            if 'ticket' in filename or 'incident' in filename:
                return self.parsers['tickets']
            elif 'change' in filename or 'chg' in filename:
                return self.parsers['changes']

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        stats = dict(self.stats)

        if self.enricher:
            stats['enrichment'] = self.enricher.stats()

        if self.db_writer:
            try:
                stats['db_event_count'] = self.db_writer.get_event_count()
            except Exception:
                pass

        return stats

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            'files_processed': 0,
            'total_events': 0,
            'parse_errors': 0,
            'db_writes': 0,
        }


def main():
    """
    Example usage of ingestion pipeline.

    Run with:
        python -m src.ingestion_pipeline
    """
    import argparse

    parser = argparse.ArgumentParser(description='AI Ops Copilot Ingestion Pipeline')
    parser.add_argument('input_path', type=Path, help='Directory or file to ingest')
    parser.add_argument('--db', type=str, help='Database connection string')
    parser.add_argument('--assets', type=Path, help='Asset database CSV/JSON')
    parser.add_argument('--ip-map', type=Path, help='IP to room mapping CSV')
    parser.add_argument('--recursive', '-r', action='store_true', help='Recursive scan')
    parser.add_argument('--pattern', '-p', type=str, help='File glob pattern')
    parser.add_argument('--no-db', action='store_true', help='Skip database write')
    parser.add_argument('--no-enrich', action='store_true', help='Skip enrichment')

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = IngestionPipeline(
        db_connection_string=args.db if not args.no_db else None,
        asset_db_path=args.assets,
        ip_room_map_path=args.ip_map,
        enable_enrichment=not args.no_enrich,
        enable_db_write=not args.no_db
    )

    # Ingest
    if args.input_path.is_dir():
        stats = pipeline.ingest_directory(
            args.input_path,
            recursive=args.recursive,
            file_pattern=args.pattern
        )
    else:
        result = pipeline.ingest_file(args.input_path)
        stats = pipeline.get_stats()

    # Print summary
    print("\n" + "="*60)
    print("INGESTION SUMMARY")
    print("="*60)
    print(f"Files processed:  {stats['files_processed']}")
    print(f"Events parsed:    {stats['total_events']}")
    print(f"Parse errors:     {stats['parse_errors']}")
    print(f"DB writes:        {stats['db_writes']}")

    if 'enrichment' in stats:
        print(f"\nEnrichment stats:")
        for key, value in stats['enrichment'].items():
            print(f"  {key}: {value}")

    print("="*60)


if __name__ == '__main__':
    main()
