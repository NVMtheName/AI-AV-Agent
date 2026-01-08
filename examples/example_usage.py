#!/usr/bin/env python3
"""
Example usage of the AI AV Agent system.

Demonstrates how to:
1. Analyze logs from a file
2. Analyze logs from a string
3. Answer specific user questions
4. Generate different output formats
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import AVAgent


def example_1_basic_analysis():
    """Example 1: Basic log analysis with JSON output"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Log Analysis")
    print("=" * 80)

    agent = AVAgent(
        known_patterns_path='config/known_patterns.yaml'
    )

    # Analyze sample logs
    result = agent.analyze_from_file(
        log_file_path='examples/sample_logs.txt',
        output_format='json'
    )

    print(result)
    print("\n")


def example_2_specific_question():
    """Example 2: Answer specific operator question"""
    print("=" * 80)
    print("EXAMPLE 2: Answering Specific Question")
    print("=" * 80)

    agent = AVAgent(
        known_patterns_path='config/known_patterns.yaml'
    )

    # Read sample logs
    with open('examples/sample_logs.txt', 'r') as f:
        logs = f.read()

    # Ask specific question
    result = agent.quick_answer(
        raw_logs=logs,
        user_query="Why did Room 12 fail this morning?"
    )

    print(result)
    print("\n")


def example_3_markdown_report():
    """Example 3: Generate markdown RCA report"""
    print("=" * 80)
    print("EXAMPLE 3: Markdown RCA Report")
    print("=" * 80)

    agent = AVAgent(
        known_patterns_path='config/known_patterns.yaml'
    )

    result = agent.analyze_from_file(
        log_file_path='examples/sample_logs.txt',
        user_query="What caused the DHCP failures?",
        output_format='markdown'
    )

    print(result)
    print("\n")


def example_4_ticket_update():
    """Example 4: Generate ticket update format"""
    print("=" * 80)
    print("EXAMPLE 4: Ticket Update Format")
    print("=" * 80)

    agent = AVAgent(
        known_patterns_path='config/known_patterns.yaml'
    )

    result = agent.analyze_from_file(
        log_file_path='examples/sample_logs.txt',
        user_query="PoE issues on 3rd floor",
        output_format='ticket'
    )

    print(result)
    print("\n")


def example_5_inline_logs():
    """Example 5: Analyze inline logs (not from file)"""
    print("=" * 80)
    print("EXAMPLE 5: Analyze Inline Logs")
    print("=" * 80)

    agent = AVAgent()

    # Inline log data
    inline_logs = """
2026-01-08 10:15:00 [ERROR] Room-99 Zoom Controller: Connection timeout to zoom.us
2026-01-08 10:15:05 [NETWORK] Switch: DHCP timeout on port 24
2026-01-08 10:15:10 [CRITICAL] Room-99: All services offline
2026-01-08 10:14:55 [CONFIG] Admin: Changed VLAN settings on switch
    """

    result = agent.analyze(
        raw_logs=inline_logs,
        user_query="Why is Room 99 offline?",
        output_format='summary'
    )

    print(result)
    print("\n")


def example_6_no_query():
    """Example 6: General analysis without specific query"""
    print("=" * 80)
    print("EXAMPLE 6: General Analysis (No Specific Query)")
    print("=" * 80)

    agent = AVAgent(
        known_patterns_path='config/known_patterns.yaml'
    )

    result = agent.analyze_from_file(
        log_file_path='examples/sample_logs.txt',
        output_format='summary'
    )

    print(result)
    print("\n")


if __name__ == '__main__':
    # Check if sample logs exist
    if not os.path.exists('examples/sample_logs.txt'):
        print("ERROR: Sample logs not found. Please run from project root directory.")
        print("Usage: python examples/example_usage.py")
        sys.exit(1)

    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "AI AV Agent - Example Usage" + " " * 31 + "║")
    print("║" + " " * 15 + "Enterprise AV/IT Root Cause Analysis" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    # Run examples
    try:
        example_1_basic_analysis()
        example_2_specific_question()
        example_3_markdown_report()
        example_4_ticket_update()
        example_5_inline_logs()
        example_6_no_query()

        print("=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
