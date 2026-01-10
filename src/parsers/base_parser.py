"""
Base parser framework for deterministic log ingestion.

All vendor-specific parsers inherit from BaseParser and implement
vendor-specific parsing logic in a deterministic, code-based manner.

NO AI/LLM inference in parsing - only regex, string matching, and logic.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any, Pattern
import re
import logging
from pathlib import Path
from dateutil import parser as date_parser

import sys
sys.path.append(str(Path(__file__).parent.parent))

from ingestion_models import (
    UnifiedEvent, ParseResult, RawPayload, AssetInfo,
    SourceType, SourceVendor, SeverityLevel, EventCategory
)


logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Abstract base class for all vendor-specific parsers.

    Enforces:
    - Deterministic parsing (code-based, no AI)
    - Raw data preservation
    - Error handling and logging
    - Consistent interface
    """

    def __init__(self, parser_name: str, source_type: SourceType, source_vendor: SourceVendor):
        """
        Initialize parser with identification info.

        Args:
            parser_name: Human-readable parser name
            source_type: Type of source (av, network, etc.)
            source_vendor: Vendor identifier
        """
        self.parser_name = parser_name
        self.source_type = source_type
        self.source_vendor = source_vendor
        self.parser_version = "1.0.0"

        # Compile regex patterns at initialization for performance
        self._compiled_patterns: Dict[str, Pattern] = {}
        self._compile_patterns()

    @abstractmethod
    def _compile_patterns(self):
        """
        Pre-compile regex patterns for performance.
        Subclasses must implement to define vendor-specific patterns.
        """
        pass

    @abstractmethod
    def parse_line(self, line: str, line_number: int, source_file: Optional[str] = None) -> Optional[UnifiedEvent]:
        """
        Parse a single log line into a UnifiedEvent.

        Must be deterministic - same input always produces same output.

        Args:
            line: Raw log line
            line_number: Line number in source file
            source_file: Source filename for tracking

        Returns:
            UnifiedEvent if successfully parsed, None if line should be skipped
        """
        pass

    def parse_file(self, file_path: Path) -> ParseResult:
        """
        Parse an entire log file.

        Args:
            file_path: Path to log file

        Returns:
            ParseResult with events and error tracking
        """
        result = ParseResult(
            success=True,
            parser_name=self.parser_name,
            source_file=str(file_path)
        )

        logger.info(f"[{self.parser_name}] Parsing file: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line_num, line in enumerate(f, start=1):
                    result.total_lines += 1

                    # Skip empty lines and comments
                    line = line.rstrip('\n\r')
                    if not line.strip() or line.strip().startswith('#'):
                        continue

                    try:
                        event = self.parse_line(line, line_num, str(file_path))
                        if event:
                            result.add_event(event)
                    except Exception as e:
                        error_msg = f"Parse error: {str(e)}"
                        logger.warning(f"[{self.parser_name}] Line {line_num}: {error_msg}")
                        result.add_error(line_num, error_msg, line)

        except Exception as e:
            logger.error(f"[{self.parser_name}] Failed to read file {file_path}: {e}")
            result.success = False
            result.add_error(0, f"File read error: {str(e)}")

        logger.info(
            f"[{self.parser_name}] Parsed {result.parsed_lines}/{result.total_lines} lines "
            f"({result.failed_lines} errors)"
        )

        return result

    def parse_text(self, text: str, source_identifier: str = "text_input") -> ParseResult:
        """
        Parse raw text (multi-line logs).

        Args:
            text: Raw log text
            source_identifier: Identifier for this text source

        Returns:
            ParseResult with events and errors
        """
        result = ParseResult(
            success=True,
            parser_name=self.parser_name,
            source_file=source_identifier
        )

        lines = text.split('\n')
        result.total_lines = len(lines)

        for line_num, line in enumerate(lines, start=1):
            line = line.rstrip('\n\r')
            if not line.strip() or line.strip().startswith('#'):
                continue

            try:
                event = self.parse_line(line, line_num, source_identifier)
                if event:
                    result.add_event(event)
            except Exception as e:
                error_msg = f"Parse error: {str(e)}"
                logger.warning(f"[{self.parser_name}] Line {line_num}: {error_msg}")
                result.add_error(line_num, error_msg, line)

        return result

    # =========================================================================
    # Helper methods for common parsing tasks
    # =========================================================================

    def extract_timestamp(
        self,
        line: str,
        patterns: Optional[List[str]] = None,
        default_now: bool = False
    ) -> Optional[datetime]:
        """
        Extract timestamp from line using regex patterns.

        Args:
            line: Log line
            patterns: Optional list of regex patterns to try
            default_now: If True, return current time if no timestamp found

        Returns:
            Parsed datetime or None
        """
        if patterns is None:
            # Default timestamp patterns
            patterns = [
                r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?',  # ISO 8601
                r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',  # Syslog
                r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',  # MM/DD/YYYY
                r'\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}',  # YYYY/MM/DD
            ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    ts_str = match.group(0)
                    dt = date_parser.parse(ts_str, fuzzy=False)
                    # Normalize to UTC
                    if dt.tzinfo is not None:
                        dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
                    return dt
                except Exception:
                    continue

        if default_now:
            return datetime.utcnow()
        return None

    def extract_severity(
        self,
        line: str,
        severity_map: Optional[Dict[str, SeverityLevel]] = None
    ) -> SeverityLevel:
        """
        Determine severity from keywords in the line.

        Args:
            line: Log line
            severity_map: Optional custom keyword->severity mapping

        Returns:
            SeverityLevel
        """
        line_lower = line.lower()

        if severity_map is None:
            # Default severity keywords
            severity_map = {
                'critical': 'critical',
                'fatal': 'critical',
                'emergency': 'critical',
                'alert': 'critical',
                'error': 'error',
                'err': 'error',
                'fail': 'error',
                'failed': 'error',
                'exception': 'error',
                'warn': 'warning',
                'warning': 'warning',
                'notice': 'notice',
                'info': 'info',
                'informational': 'info',
                'debug': 'debug',
            }

        # Check in priority order
        for keyword in ['critical', 'fatal', 'emergency']:
            if keyword in line_lower:
                return 'critical'
        for keyword in ['error', 'err', 'fail', 'exception']:
            if keyword in line_lower:
                return 'error'
        for keyword in ['warn', 'warning']:
            if keyword in line_lower:
                return 'warning'
        for keyword in ['notice']:
            if keyword in line_lower:
                return 'notice'
        for keyword in ['debug']:
            if keyword in line_lower:
                return 'debug'

        return 'info'

    def extract_ip(self, line: str) -> Optional[str]:
        """Extract first IPv4 address from line"""
        pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        match = re.search(pattern, line)
        return match.group(0) if match else None

    def extract_mac(self, line: str) -> Optional[str]:
        """Extract MAC address from line"""
        pattern = r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'
        match = re.search(pattern, line)
        return match.group(0) if match else None

    def extract_room_name(self, line: str, patterns: Optional[List[str]] = None) -> Optional[str]:
        """
        Extract room name from line.

        Args:
            line: Log line
            patterns: Optional custom room patterns

        Returns:
            Room name or None
        """
        if patterns is None:
            patterns = [
                r'(?:room|conf|meeting|cr)[\s_-]?([A-Z0-9]{2,}[-_]?\d+)',  # CR-101, Room 12, etc.
                r'\b([A-Z]{2,}\d{3,})\b',  # ABC123 format
            ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        return None

    def create_event(
        self,
        ts: datetime,
        raw_ts: str,
        signal: str,
        message: str,
        severity: SeverityLevel,
        category: EventCategory,
        source_system: str,
        line: str,
        line_number: int,
        source_file: Optional[str] = None,
        asset: Optional[AssetInfo] = None,
        room: Optional[str] = None,
        building: Optional[str] = None,
        floor: Optional[str] = None,
        site: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> UnifiedEvent:
        """
        Create a UnifiedEvent with all required fields.

        Convenience method to reduce boilerplate in parsers.
        """
        return UnifiedEvent(
            ts=ts,
            source_type=self.source_type,
            source_vendor=self.source_vendor,
            source_system=source_system,
            site=site,
            building=building,
            floor=floor,
            room=room,
            asset=asset,
            severity=severity,
            category=category,
            signal=signal,
            message=message,
            metadata=metadata or {},
            raw=RawPayload(
                raw_line=line,
                raw_ts=raw_ts,
                source_file=source_file,
                line_number=line_number
            ),
            parser_version=self.parser_version,
            **kwargs
        )

    def batch_parse_files(self, file_paths: List[Path]) -> List[ParseResult]:
        """
        Parse multiple files in batch.

        Args:
            file_paths: List of file paths to parse

        Returns:
            List of ParseResults
        """
        results = []
        for file_path in file_paths:
            result = self.parse_file(file_path)
            results.append(result)
        return results


class CSVParser(BaseParser):
    """
    Base class for CSV-based parsers (tickets, changes, etc.)

    Handles CSV reading and provides helpers for field extraction.
    """

    def __init__(self, parser_name: str, source_type: SourceType, source_vendor: SourceVendor):
        super().__init__(parser_name, source_type, source_vendor)

    def _compile_patterns(self):
        """CSV parsers typically don't need regex patterns"""
        pass

    @abstractmethod
    def parse_row(self, row: Dict[str, str], row_number: int, source_file: Optional[str] = None) -> Optional[UnifiedEvent]:
        """
        Parse a CSV row into a UnifiedEvent.

        Args:
            row: CSV row as dictionary (field_name -> value)
            row_number: Row number in CSV
            source_file: Source filename

        Returns:
            UnifiedEvent or None
        """
        pass

    def parse_line(self, line: str, line_number: int, source_file: Optional[str] = None) -> Optional[UnifiedEvent]:
        """Not used for CSV - use parse_csv_file instead"""
        raise NotImplementedError("CSV parsers should use parse_csv_file, not parse_line")

    def parse_csv_file(self, file_path: Path, delimiter: str = ',') -> ParseResult:
        """
        Parse a CSV file.

        Args:
            file_path: Path to CSV file
            delimiter: CSV delimiter (default: comma)

        Returns:
            ParseResult with events and errors
        """
        import csv

        result = ParseResult(
            success=True,
            parser_name=self.parser_name,
            source_file=str(file_path)
        )

        logger.info(f"[{self.parser_name}] Parsing CSV file: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                reader = csv.DictReader(f, delimiter=delimiter)

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    result.total_lines += 1

                    try:
                        event = self.parse_row(row, row_num, str(file_path))
                        if event:
                            result.add_event(event)
                    except Exception as e:
                        error_msg = f"Parse error: {str(e)}"
                        logger.warning(f"[{self.parser_name}] Row {row_num}: {error_msg}")
                        result.add_error(row_num, error_msg, str(row)[:200])

        except Exception as e:
            logger.error(f"[{self.parser_name}] Failed to read CSV file {file_path}: {e}")
            result.success = False
            result.add_error(0, f"CSV read error: {str(e)}")

        logger.info(
            f"[{self.parser_name}] Parsed {result.parsed_lines}/{result.total_lines} rows "
            f"({result.failed_lines} errors)"
        )

        return result

    def safe_get(self, row: Dict[str, str], key: str, default: Optional[str] = None) -> Optional[str]:
        """Safely get a value from CSV row, handling missing keys and empty strings"""
        value = row.get(key, default)
        if value is not None:
            value = value.strip()
            if value == '':
                return None
        return value

    def parse_csv_timestamp(self, ts_str: Optional[str], default_now: bool = False) -> Optional[datetime]:
        """Parse timestamp from CSV field"""
        if not ts_str:
            return datetime.utcnow() if default_now else None

        try:
            dt = date_parser.parse(ts_str, fuzzy=False)
            if dt.tzinfo is not None:
                dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            return dt
        except Exception:
            return datetime.utcnow() if default_now else None
