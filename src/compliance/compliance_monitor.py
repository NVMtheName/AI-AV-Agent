"""
Compliance Monitoring and Reporting Tool

This module provides tools for monitoring SOC 2 compliance status,
generating compliance reports, and tracking control effectiveness.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel

from .audit_logger import get_audit_logger, AuditEventType
from .access_control import get_access_control


class ComplianceMetric(BaseModel):
    """Compliance metric model"""
    metric_name: str
    metric_value: float
    target_value: float
    status: str  # pass, warning, fail
    timestamp: datetime
    details: Dict[str, Any] = {}


class ControlStatus(BaseModel):
    """Control status model"""
    control_id: str
    control_name: str
    status: str  # effective, needs_improvement, ineffective
    last_tested: Optional[datetime] = None
    findings: List[str] = []
    evidence: List[str] = []


class ComplianceMonitor:
    """
    SOC 2 Compliance monitoring and reporting tool.

    Features:
    - Control effectiveness monitoring
    - Compliance metrics calculation
    - Automated compliance reporting
    - Control testing tracking
    """

    def __init__(self, report_dir: str = "compliance/soc2/reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.audit_logger = get_audit_logger()
        self.access_control = get_access_control()

    def check_audit_log_compliance(
        self,
        lookback_days: int = 30
    ) -> ComplianceMetric:
        """
        Check audit logging compliance

        Args:
            lookback_days: Number of days to analyze

        Returns:
            ComplianceMetric for audit logging
        """
        try:
            # Get recent audit events
            events = self.audit_logger.get_recent_events(limit=10000)

            # Filter to lookback period
            cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
            recent_events = [e for e in events if e.timestamp >= cutoff]

            # Calculate metrics
            total_events = len(recent_events)
            error_events = sum(1 for e in recent_events if e.status == "error")
            error_rate = (error_events / total_events * 100) if total_events > 0 else 0

            # Determine status
            if error_rate < 1.0 and total_events > 0:
                status = "pass"
            elif error_rate < 5.0 or total_events == 0:
                status = "warning"
            else:
                status = "fail"

            return ComplianceMetric(
                metric_name="Audit Logging",
                metric_value=total_events,
                target_value=1.0,  # At least some events
                status=status,
                timestamp=datetime.now(timezone.utc),
                details={
                    "total_events": total_events,
                    "error_events": error_events,
                    "error_rate": round(error_rate, 2),
                    "lookback_days": lookback_days,
                }
            )
        except Exception as e:
            return ComplianceMetric(
                metric_name="Audit Logging",
                metric_value=0,
                target_value=1.0,
                status="fail",
                timestamp=datetime.now(timezone.utc),
                details={"error": str(e)}
            )

    def check_access_control_compliance(self) -> ComplianceMetric:
        """
        Check access control compliance

        Returns:
            ComplianceMetric for access control
        """
        try:
            report = self.access_control.generate_access_report()

            # Check if RBAC is properly configured
            total_users = len(report.get("all_users", {}))
            roles_defined = len(report.get("role_definitions", {}))

            # Verify all required roles exist
            required_roles = ["viewer", "analyst", "admin", "auditor"]
            roles_configured = all(
                role in report.get("role_definitions", {})
                for role in required_roles
            )

            if roles_configured and roles_defined >= 4:
                status = "pass"
            elif roles_defined >= 3:
                status = "warning"
            else:
                status = "fail"

            return ComplianceMetric(
                metric_name="Access Control",
                metric_value=roles_defined,
                target_value=4.0,  # 4 roles required
                status=status,
                timestamp=datetime.now(timezone.utc),
                details={
                    "total_users": total_users,
                    "roles_defined": roles_defined,
                    "roles_configured": roles_configured,
                    "current_user": report.get("current_user"),
                    "current_role": report.get("current_role"),
                }
            )
        except Exception as e:
            return ComplianceMetric(
                metric_name="Access Control",
                metric_value=0,
                target_value=4.0,
                status="fail",
                timestamp=datetime.now(timezone.utc),
                details={"error": str(e)}
            )

    def check_encryption_compliance(self) -> ComplianceMetric:
        """
        Check encryption implementation compliance

        Returns:
            ComplianceMetric for encryption
        """
        try:
            # Check if encryption module is available
            encryption_available = True
            key_file_exists = Path(".encryption_key").exists()

            # Check cryptography library
            try:
                import cryptography
                crypto_version = cryptography.__version__
            except ImportError:
                encryption_available = False
                crypto_version = "not installed"

            if encryption_available:
                status = "pass"
            else:
                status = "fail"

            return ComplianceMetric(
                metric_name="Encryption",
                metric_value=1.0 if encryption_available else 0.0,
                target_value=1.0,
                status=status,
                timestamp=datetime.now(timezone.utc),
                details={
                    "encryption_available": encryption_available,
                    "key_file_exists": key_file_exists,
                    "crypto_version": crypto_version,
                }
            )
        except Exception as e:
            return ComplianceMetric(
                metric_name="Encryption",
                metric_value=0,
                target_value=1.0,
                status="fail",
                timestamp=datetime.now(timezone.utc),
                details={"error": str(e)}
            )

    def check_data_retention_compliance(
        self,
        log_dir: str = "logs/audit"
    ) -> ComplianceMetric:
        """
        Check data retention compliance

        Args:
            log_dir: Directory containing audit logs

        Returns:
            ComplianceMetric for data retention
        """
        try:
            log_path = Path(log_dir)

            if not log_path.exists():
                return ComplianceMetric(
                    metric_name="Data Retention",
                    metric_value=0,
                    target_value=1.0,
                    status="warning",
                    timestamp=datetime.now(timezone.utc),
                    details={"message": "Audit log directory not yet created"}
                )

            # Find oldest audit log
            log_files = list(log_path.glob("audit_*.log"))
            if not log_files:
                return ComplianceMetric(
                    metric_name="Data Retention",
                    metric_value=0,
                    target_value=1.0,
                    status="warning",
                    timestamp=datetime.now(timezone.utc),
                    details={"message": "No audit logs found yet"}
                )

            oldest_log = min(log_files, key=lambda p: p.stat().st_mtime)
            oldest_date = datetime.fromtimestamp(oldest_log.stat().st_mtime)
            age_days = (datetime.now() - oldest_date).days

            # Check retention target (7 years = 2555 days)
            retention_target = 2555  # 7 years
            retention_percentage = min(100, (age_days / retention_target) * 100)

            if age_days >= retention_target:
                status = "pass"
            elif age_days >= 365:  # At least 1 year
                status = "warning"
            else:
                status = "warning"  # Building compliance

            return ComplianceMetric(
                metric_name="Data Retention",
                metric_value=age_days,
                target_value=retention_target,
                status=status,
                timestamp=datetime.now(timezone.utc),
                details={
                    "oldest_log": str(oldest_log),
                    "oldest_date": oldest_date.isoformat(),
                    "age_days": age_days,
                    "retention_target_days": retention_target,
                    "retention_percentage": round(retention_percentage, 2),
                    "total_log_files": len(log_files),
                }
            )
        except Exception as e:
            return ComplianceMetric(
                metric_name="Data Retention",
                metric_value=0,
                target_value=2555,
                status="fail",
                timestamp=datetime.now(timezone.utc),
                details={"error": str(e)}
            )

    def check_policy_compliance(self) -> ComplianceMetric:
        """
        Check policy documentation compliance

        Returns:
            ComplianceMetric for policy compliance
        """
        try:
            policy_dir = Path("compliance/soc2/policies")
            procedure_dir = Path("compliance/soc2/procedures")

            # Required policies
            required_policies = [
                "information_security_policy.md",
                "access_control_policy.md",
                "data_retention_disposal_policy.md",
            ]

            # Required procedures
            required_procedures = [
                "incident_response_procedure.md",
            ]

            policies_present = sum(
                1 for p in required_policies
                if (policy_dir / p).exists()
            )

            procedures_present = sum(
                1 for p in required_procedures
                if (procedure_dir / p).exists()
            )

            total_required = len(required_policies) + len(required_procedures)
            total_present = policies_present + procedures_present

            if total_present == total_required:
                status = "pass"
            elif total_present >= total_required * 0.75:
                status = "warning"
            else:
                status = "fail"

            return ComplianceMetric(
                metric_name="Policy Documentation",
                metric_value=total_present,
                target_value=total_required,
                status=status,
                timestamp=datetime.now(timezone.utc),
                details={
                    "policies_present": policies_present,
                    "policies_required": len(required_policies),
                    "procedures_present": procedures_present,
                    "procedures_required": len(required_procedures),
                    "completion_percentage": round((total_present / total_required) * 100, 2),
                }
            )
        except Exception as e:
            return ComplianceMetric(
                metric_name="Policy Documentation",
                metric_value=0,
                target_value=4,
                status="fail",
                timestamp=datetime.now(timezone.utc),
                details={"error": str(e)}
            )

    def generate_compliance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report

        Returns:
            Dictionary containing compliance status and metrics
        """
        # Collect all metrics
        metrics = [
            self.check_audit_log_compliance(),
            self.check_access_control_compliance(),
            self.check_encryption_compliance(),
            self.check_data_retention_compliance(),
            self.check_policy_compliance(),
        ]

        # Calculate overall status
        status_counts = {"pass": 0, "warning": 0, "fail": 0}
        for metric in metrics:
            status_counts[metric.status] += 1

        # Determine overall compliance status
        if status_counts["fail"] == 0 and status_counts["warning"] == 0:
            overall_status = "compliant"
        elif status_counts["fail"] == 0:
            overall_status = "mostly_compliant"
        elif status_counts["fail"] <= 1:
            overall_status = "needs_improvement"
        else:
            overall_status = "non_compliant"

        report = {
            "report_generated": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "metrics_summary": {
                "total_metrics": len(metrics),
                "passed": status_counts["pass"],
                "warnings": status_counts["warning"],
                "failed": status_counts["fail"],
            },
            "metrics": [metric.model_dump() for metric in metrics],
            "recommendations": self._generate_recommendations(metrics),
        }

        return report

    def _generate_recommendations(
        self,
        metrics: List[ComplianceMetric]
    ) -> List[str]:
        """Generate recommendations based on metrics"""
        recommendations = []

        for metric in metrics:
            if metric.status == "fail":
                if metric.metric_name == "Audit Logging":
                    recommendations.append(
                        "Critical: Audit logging is not functioning properly. "
                        "Review audit logger configuration and error logs."
                    )
                elif metric.metric_name == "Access Control":
                    recommendations.append(
                        "Critical: Access control roles are not properly configured. "
                        "Ensure all four roles (Viewer, Analyst, Admin, Auditor) are defined."
                    )
                elif metric.metric_name == "Encryption":
                    recommendations.append(
                        "Critical: Encryption capabilities are not available. "
                        "Install cryptography library: pip install cryptography>=41.0.0"
                    )
                elif metric.metric_name == "Policy Documentation":
                    recommendations.append(
                        "Important: Required policy documentation is incomplete. "
                        "Complete all required policies and procedures."
                    )

            elif metric.status == "warning":
                if metric.metric_name == "Data Retention":
                    recommendations.append(
                        "Info: Data retention period is building. Continue maintaining "
                        "audit logs to meet 7-year SOC 2 requirement."
                    )
                elif metric.metric_name == "Audit Logging":
                    recommendations.append(
                        "Warning: Elevated error rate in audit logs. "
                        "Review recent errors and address underlying issues."
                    )

        if not recommendations:
            recommendations.append(
                "All compliance controls are operating effectively. "
                "Continue monitoring and maintain current practices."
            )

        return recommendations

    def save_compliance_report(
        self,
        report: Dict[str, Any],
        filename: Optional[str] = None
    ) -> Path:
        """
        Save compliance report to file

        Args:
            report: Compliance report dictionary
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to saved report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"compliance_report_{timestamp}.json"

        report_file = self.report_dir / filename

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report_file

    def generate_and_save_report(self) -> Path:
        """
        Generate and save compliance report

        Returns:
            Path to saved report file
        """
        report = self.generate_compliance_report()
        report_file = self.save_compliance_report(report)

        # Log report generation
        self.audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_START,
            action="Compliance report generated",
            resource=str(report_file),
            details={
                "overall_status": report["overall_status"],
                "metrics_passed": report["metrics_summary"]["passed"],
                "metrics_failed": report["metrics_summary"]["failed"],
            }
        )

        return report_file

    def print_compliance_summary(self, report: Dict[str, Any]):
        """
        Print human-readable compliance summary

        Args:
            report: Compliance report dictionary
        """
        print("\n" + "="*60)
        print("SOC 2 COMPLIANCE REPORT")
        print("="*60)
        print(f"Generated: {report['report_generated']}")
        print(f"Overall Status: {report['overall_status'].upper()}")
        print()

        print("Metrics Summary:")
        summary = report['metrics_summary']
        print(f"  Total Metrics: {summary['total_metrics']}")
        print(f"  ✓ Passed: {summary['passed']}")
        print(f"  ⚠ Warnings: {summary['warnings']}")
        print(f"  ✗ Failed: {summary['failed']}")
        print()

        print("Individual Metrics:")
        for metric in report['metrics']:
            status_icon = {"pass": "✓", "warning": "⚠", "fail": "✗"}[metric['status']]
            print(f"  {status_icon} {metric['metric_name']}: {metric['status'].upper()}")

        print()
        print("Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")

        print("="*60 + "\n")


def run_compliance_check():
    """Convenience function to run compliance check"""
    monitor = ComplianceMonitor()
    report = monitor.generate_compliance_report()
    report_file = monitor.save_compliance_report(report)

    monitor.print_compliance_summary(report)
    print(f"Full report saved to: {report_file}")

    return report
