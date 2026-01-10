#!/usr/bin/env python3
"""
SOC 2 Compliance Checker

This script runs compliance checks and generates compliance reports
for the AI AV Agent system.

Usage:
    python compliance-check.py                    # Run full compliance check
    python compliance-check.py --summary          # Show summary only
    python compliance-check.py --report-file FILE # Specify output file
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from compliance.compliance_monitor import ComplianceMonitor


def main():
    parser = argparse.ArgumentParser(
        description="Run SOC 2 compliance checks for AI AV Agent"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary only (no detailed report)"
    )
    parser.add_argument(
        "--report-file",
        type=str,
        help="Output file for detailed JSON report"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (only save report file)"
    )

    args = parser.parse_args()

    # Create compliance monitor
    monitor = ComplianceMonitor()

    # Generate compliance report
    report = monitor.generate_compliance_report()

    # Save report
    if args.report_file:
        report_file = Path(args.report_file)
        monitor.save_compliance_report(report, filename=report_file.name)
        if not args.quiet:
            print(f"Report saved to: {report_file}")
    else:
        report_file = monitor.save_compliance_report(report)
        if not args.quiet:
            print(f"Report saved to: {report_file}")

    # Print summary unless quiet mode
    if not args.quiet:
        monitor.print_compliance_summary(report)

    # Exit with appropriate code
    if report['overall_status'] in ['compliant', 'mostly_compliant']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
