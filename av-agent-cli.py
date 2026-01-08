#!/usr/bin/env python3
"""
AI AV Agent - Command Line Interface

Quick CLI for analyzing AV/IT operational logs.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import AVAgent


def main():
    parser = argparse.ArgumentParser(
        description='AI AV Agent - Enterprise AV/IT Root Cause Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Analyze logs with a specific question
  %(prog)s logs.txt -q "Why did Room 12 fail?"

  # Generate markdown report
  %(prog)s logs.txt -f markdown -o report.md

  # Quick summary
  %(prog)s logs.txt -f summary

  # Use custom patterns file
  %(prog)s logs.txt --patterns my_patterns.yaml
        '''
    )

    parser.add_argument(
        'logfile',
        type=str,
        help='Path to log file to analyze'
    )

    parser.add_argument(
        '-q', '--query',
        type=str,
        default=None,
        help='Natural language question (e.g., "Why did Room 12 fail?")'
    )

    parser.add_argument(
        '-f', '--format',
        type=str,
        choices=['json', 'markdown', 'summary', 'ticket'],
        default='json',
        help='Output format (default: json)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output file (default: stdout)'
    )

    parser.add_argument(
        '--patterns',
        type=str,
        default='config/known_patterns.yaml',
        help='Path to known patterns YAML file'
    )

    parser.add_argument(
        '--correlation-window',
        type=int,
        default=300,
        help='Event correlation window in seconds (default: 300)'
    )

    args = parser.parse_args()

    # Check if log file exists
    if not Path(args.logfile).exists():
        print(f"Error: Log file not found: {args.logfile}", file=sys.stderr)
        sys.exit(1)

    # Check if patterns file exists (optional)
    patterns_path = args.patterns if Path(args.patterns).exists() else None
    if args.patterns != 'config/known_patterns.yaml' and not patterns_path:
        print(f"Warning: Patterns file not found: {args.patterns}", file=sys.stderr)

    # Initialize agent
    try:
        agent = AVAgent(
            known_patterns_path=patterns_path,
            correlation_window_seconds=args.correlation_window
        )
    except Exception as e:
        print(f"Error initializing agent: {e}", file=sys.stderr)
        sys.exit(1)

    # Analyze logs
    try:
        result = agent.analyze_from_file(
            log_file_path=args.logfile,
            user_query=args.query,
            output_format=args.format
        )
    except Exception as e:
        print(f"Error analyzing logs: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Output result
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"Analysis written to: {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(result)


if __name__ == '__main__':
    main()
