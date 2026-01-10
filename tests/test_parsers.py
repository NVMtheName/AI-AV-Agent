"""
Basic tests for ingestion parsers.
Run with: pytest tests/test_parsers.py -v
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parsers import ZoomRoomsParser, QSysParser, NetworkSyslogParser
from ingestion_models import UnifiedEvent


class TestZoomRoomsParser:
    """Test Zoom Rooms log parser"""

    def setup_method(self):
        self.parser = ZoomRoomsParser()

    def test_parse_info_line(self):
        """Test parsing INFO level Zoom log"""
        line = "2026-01-08T08:15:23Z [INFO] Room: CR-101 | ZoomRoom connected successfully"
        event = self.parser.parse_line(line, 1)

        assert event is not None
        assert event.source_type == "av"
        assert event.source_vendor == "zoom"
        assert event.room == "CR-101"
        assert event.severity == "info"
        assert "connected" in event.message.lower()
        assert "zoom" in event.signal

    def test_parse_error_line(self):
        """Test parsing ERROR level Zoom log"""
        line = "2026-01-08T08:31:23Z [ERROR] Room: CR-205 | DHCP timeout - no IP address received"
        event = self.parser.parse_line(line, 1)

        assert event is not None
        assert event.severity == "error"
        assert event.room == "CR-205"
        assert "dhcp" in event.signal.lower() or "timeout" in event.signal.lower()
        assert event.category == "connectivity"

    def test_parse_critical_line(self):
        """Test parsing CRITICAL level Zoom log"""
        line = "2026-01-08T08:31:45Z [CRITICAL] Room: CR-205 | ZoomRoom offline - network connection lost"
        event = self.parser.parse_line(line, 1)

        assert event is not None
        assert event.severity == "critical"
        assert event.room == "CR-205"
        assert event.category == "connectivity"

    def test_raw_preservation(self):
        """Test that raw data is preserved"""
        line = "2026-01-08T08:15:23Z [INFO] Room: CR-101 | Test message"
        event = self.parser.parse_line(line, 123, "test.log")

        assert event.raw.raw_line == line
        assert event.raw.line_number == 123
        assert event.raw.source_file == "test.log"
        assert event.raw.raw_ts is not None


class TestQSysParser:
    """Test Q-SYS DSP log parser"""

    def setup_method(self):
        self.parser = QSysParser()

    def test_parse_qsys_log(self):
        """Test parsing Q-SYS log line"""
        line = "2026-01-08 14:23:45.123 [INFO] Core-110f (10.1.5.50): Audio routing updated - Room CR-101"
        event = self.parser.parse_line(line, 1)

        assert event is not None
        assert event.source_type == "av"
        assert event.source_vendor == "qsys"
        assert event.room == "CR-101"
        assert event.category == "audio"
        assert event.asset is not None
        assert event.asset.ip == "10.1.5.50"

    def test_parse_error(self):
        """Test parsing Q-SYS error"""
        line = "2026-01-08 14:30:12.456 [ERROR] Core-110f (10.1.5.50): Dante network timeout - primary"
        event = self.parser.parse_line(line, 1)

        assert event is not None
        assert event.severity == "error"
        assert event.category == "connectivity"
        assert "dante" in event.message.lower()


class TestNetworkSyslogParser:
    """Test network syslog parser"""

    def setup_method(self):
        self.parser = NetworkSyslogParser()

    def test_parse_cisco_syslog(self):
        """Test parsing Cisco syslog format"""
        line = "Jan 8 08:15:23 switch-cr-101 %LINK-3-UPDOWN: Interface GigabitEthernet1/0/12, changed state to up"
        event = self.parser.parse_line(line, 1)

        assert event is not None
        assert event.source_type == "network"
        assert event.category == "connectivity"
        assert event.asset is not None
        assert event.asset.hostname == "switch-cr-101"

    def test_parse_poe_denied(self):
        """Test parsing PoE denial"""
        line = "Jan 8 08:45:23 10.1.1.1 %POWER-3-POE_DENIED: GigabitEthernet1/0/8: inline power denied"
        event = self.parser.parse_line(line, 1)

        assert event is not None
        assert event.category == "power"
        assert "poe" in event.signal.lower()
        assert event.severity in ["error", "critical"]

    def test_parse_meraki_syslog(self):
        """Test parsing Meraki syslog"""
        line = "2026-01-08T10:15:23Z meraki-ap-floor3 events Association succeeded for client 00:11:22:33:44:66"
        event = self.parser.parse_line(line, 1)

        assert event is not None
        assert event.source_type == "network"


class TestParserIntegration:
    """Integration tests for parser framework"""

    def test_parse_file(self):
        """Test parsing entire file"""
        parser = ZoomRoomsParser()
        sample_file = Path(__file__).parent.parent / "examples/sample_data/zoom_rooms.log"

        if sample_file.exists():
            result = parser.parse_file(sample_file)

            assert result.success is True
            assert result.parsed_lines > 0
            assert len(result.events) > 0

            # Check that events have required fields
            for event in result.events:
                assert event.event_id is not None
                assert event.ts is not None
                assert event.source_type is not None
                assert event.source_vendor is not None
                assert event.severity is not None
                assert event.category is not None
                assert event.signal is not None
                assert event.message is not None
                assert event.raw.raw_line is not None


def test_unified_event_creation():
    """Test UnifiedEvent creation and validation"""
    from datetime import datetime
    from ingestion_models import UnifiedEvent, RawPayload, AssetInfo

    event = UnifiedEvent(
        ts=datetime.utcnow(),
        source_type="av",
        source_vendor="zoom",
        source_system="zoom_rooms_controller",
        room="CR-101",
        severity="error",
        category="connectivity",
        signal="zoom.connectivity.dhcp_timeout",
        message="DHCP timeout",
        raw=RawPayload(
            raw_line="test line",
            raw_ts="2026-01-08T14:23:45Z",
            line_number=1
        )
    )

    assert event.event_id is not None
    assert event.source_type == "av"
    assert event.to_dict() is not None
    assert event.to_json() is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
