#!/usr/bin/env python3
"""
Example: Using the ingestion pipeline to parse logs and enrich with asset data.

This demonstrates the complete ingestion workflow WITHOUT requiring a database.

Run with:
    python examples/ingestion_example.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ingestion_pipeline import IngestionPipeline
from parsers import ZoomRoomsParser


def example_1_parse_single_file():
    """Example 1: Parse a single Zoom Rooms log file"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Parse Single File")
    print("="*60)

    # Initialize pipeline without database (dry run mode)
    pipeline = IngestionPipeline(
        enable_enrichment=False,
        enable_db_write=False
    )

    # Parse sample Zoom log
    sample_file = Path(__file__).parent / "sample_data/zoom_rooms.log"

    if not sample_file.exists():
        print(f"Sample file not found: {sample_file}")
        return

    result = pipeline.ingest_file(sample_file)

    print(f"\nResults:")
    print(f"  Total lines: {result.total_lines}")
    print(f"  Parsed events: {result.parsed_lines}")
    print(f"  Failed lines: {result.failed_lines}")

    # Show first few events
    print(f"\nFirst 3 events:")
    for i, event in enumerate(result.events[:3]):
        print(f"\n  Event {i+1}:")
        print(f"    Timestamp: {event.ts}")
        print(f"    Room: {event.room}")
        print(f"    Severity: {event.severity}")
        print(f"    Category: {event.category}")
        print(f"    Signal: {event.signal}")
        print(f"    Message: {event.message[:60]}...")


def example_2_parse_with_enrichment():
    """Example 2: Parse logs with asset enrichment"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Parse with Asset Enrichment")
    print("="*60)

    # Initialize pipeline with enrichment
    assets_file = Path(__file__).parent / "sample_data/assets.csv"
    ip_map_file = Path(__file__).parent / "sample_data/ip_room_map.csv"

    pipeline = IngestionPipeline(
        asset_db_path=assets_file if assets_file.exists() else None,
        ip_room_map_path=ip_map_file if ip_map_file.exists() else None,
        enable_enrichment=True,
        enable_db_write=False
    )

    # Parse sample file
    sample_file = Path(__file__).parent / "sample_data/zoom_rooms.log"

    if not sample_file.exists():
        print(f"Sample file not found: {sample_file}")
        return

    result = pipeline.ingest_file(sample_file)

    print(f"\nParsed {result.parsed_lines} events")

    # Show enrichment in action
    print(f"\nEnriched event examples:")
    for event in result.events[:3]:
        if event.asset:
            print(f"\n  Room: {event.room}")
            print(f"    Asset ID: {event.asset.asset_id}")
            print(f"    Asset Type: {event.asset.asset_type}")
            print(f"    Make/Model: {event.asset.make} {event.asset.model}")
            print(f"    Building: {event.building}")
            print(f"    Site: {event.site}")


def example_3_parse_directory():
    """Example 3: Parse entire directory of logs"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Parse Directory")
    print("="*60)

    pipeline = IngestionPipeline(
        enable_enrichment=False,
        enable_db_write=False
    )

    sample_dir = Path(__file__).parent / "sample_data"

    if not sample_dir.exists():
        print(f"Sample directory not found: {sample_dir}")
        return

    stats = pipeline.ingest_directory(sample_dir, recursive=False)

    print(f"\nDirectory ingestion results:")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Total events: {stats['total_events']}")
    print(f"  Parse errors: {stats['parse_errors']}")


def example_4_parse_text():
    """Example 4: Parse raw text (no file)"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Parse Raw Text")
    print("="*60)

    pipeline = IngestionPipeline(
        enable_enrichment=False,
        enable_db_write=False
    )

    # Raw log text
    raw_logs = """
2026-01-08T14:23:45Z [ERROR] Room: CR-101 | Camera offline - USB enumeration failed
2026-01-08T14:24:12Z [WARNING] Room: CR-101 | Retrying camera connection
2026-01-08T14:25:01Z [INFO] Room: CR-101 | Camera reconnected successfully
    """

    result = pipeline.ingest_text(
        text=raw_logs,
        parser_type='zoom',
        source_identifier='manual_input'
    )

    print(f"\nParsed {result.parsed_lines} events from raw text")

    for event in result.events:
        print(f"  {event.ts} | {event.severity.upper():8s} | {event.room} | {event.message[:50]}")


def example_5_export_json():
    """Example 5: Export events to JSON"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Export Events to JSON")
    print("="*60)

    pipeline = IngestionPipeline(
        enable_enrichment=False,
        enable_db_write=False
    )

    sample_file = Path(__file__).parent / "sample_data/zoom_rooms.log"

    if not sample_file.exists():
        print(f"Sample file not found: {sample_file}")
        return

    result = pipeline.ingest_file(sample_file)

    # Export first event as JSON
    if result.events:
        event = result.events[0]
        print(f"\nFirst event as JSON:")
        print(event.to_json())


def example_6_csv_parsing():
    """Example 6: Parse tickets and changes CSV"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Parse CSV Files (Tickets & Changes)")
    print("="*60)

    pipeline = IngestionPipeline(
        enable_enrichment=False,
        enable_db_write=False
    )

    # Parse tickets
    tickets_file = Path(__file__).parent / "sample_data/tickets.csv"
    if tickets_file.exists():
        print("\nParsing tickets.csv...")
        result = pipeline.ingest_file(tickets_file)
        print(f"  Parsed {result.parsed_lines} ticket events")

        if result.events:
            event = result.events[0]
            print(f"\n  Sample ticket event:")
            print(f"    Ticket ID: {event.ticket_id}")
            print(f"    Room: {event.room}")
            print(f"    Severity: {event.severity}")
            print(f"    Message: {event.message}")

    # Parse changes
    changes_file = Path(__file__).parent / "sample_data/changes.csv"
    if changes_file.exists():
        print("\nParsing changes.csv...")
        result = pipeline.ingest_file(changes_file)
        print(f"  Parsed {result.parsed_lines} change events")

        if result.events:
            event = result.events[0]
            print(f"\n  Sample change event:")
            print(f"    Change ID: {event.change_id}")
            print(f"    Room: {event.room}")
            print(f"    Signal: {event.signal}")
            print(f"    Message: {event.message[:80]}...")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("AI Ops Copilot - Ingestion Pipeline Examples")
    print("="*60)

    try:
        example_1_parse_single_file()
        example_2_parse_with_enrichment()
        example_3_parse_directory()
        example_4_parse_text()
        example_5_export_json()
        example_6_csv_parsing()

        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
