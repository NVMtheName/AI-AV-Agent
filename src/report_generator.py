"""
Report generator for incident RCA reports.

Generates professional, management-ready reports from analysis results.
"""

import json
from typing import Dict, Any
from datetime import datetime

from .models import IncidentAnalysis, StructuredEvent


class ReportGenerator:
    """
    Generates structured reports and formatted output from RCA analysis.
    """

    @staticmethod
    def generate_json_report(analysis: IncidentAnalysis) -> str:
        """
        Generate JSON report in the specified format.

        Returns:
            JSON string matching the required output structure
        """
        report = analysis.to_dict()
        return json.dumps(report, indent=2)

    @staticmethod
    def generate_markdown_report(analysis: IncidentAnalysis) -> str:
        """
        Generate human-readable Markdown RCA report.

        Suitable for:
        - Management review
        - Postmortem documentation
        - Ticket updates
        """

        sections = []

        # Header
        sections.append("# Incident Root Cause Analysis Report")
        sections.append(f"\n**Generated:** {analysis.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        sections.append(f"**Time Window:** {analysis.time_window_analyzed}")
        sections.append(f"**Events Analyzed:** {analysis.total_events_analyzed}\n")

        # Incident Summary
        sections.append("## Incident Overview")
        sections.append(f"\n{analysis.incident_summary}\n")

        # Affected Resources
        if analysis.affected_resources:
            sections.append("## Affected Resources")
            sections.append("")
            for resource in analysis.affected_resources:
                sections.append(f"- {resource}")
            sections.append("")

        # Root Cause
        sections.append("## Root Cause Analysis")
        sections.append(f"\n### Most Likely Root Cause")
        sections.append(f"\n**Confidence:** {analysis.most_likely_root_cause.confidence * 100:.0f}%\n")
        sections.append(f"**Description:** {analysis.most_likely_root_cause.description}\n")

        if analysis.most_likely_root_cause.evidence:
            sections.append("**Supporting Evidence:**\n")
            for evidence in analysis.most_likely_root_cause.evidence:
                sections.append(f"- {evidence}")
            sections.append("")

        # Secondary Causes
        if analysis.secondary_possible_causes:
            sections.append("### Alternative Possible Causes")
            sections.append("")
            for i, cause in enumerate(analysis.secondary_possible_causes, 1):
                sections.append(f"{i}. **{cause.description}** (Confidence: {cause.confidence * 100:.0f}%)")
                if cause.evidence:
                    for evidence in cause.evidence[:2]:  # Top 2 pieces of evidence
                        sections.append(f"   - {evidence}")
            sections.append("")

        # What Changed
        if analysis.what_changed_before_incident:
            sections.append("## Changes Before Incident")
            sections.append("")
            for change in analysis.what_changed_before_incident:
                sections.append(f"- {change}")
            sections.append("")

        # Repeat Issue
        if analysis.is_repeat_issue:
            sections.append("## ⚠️ Recurring Issue Alert")
            sections.append(f"\n{analysis.historical_context}\n")

        # Recommendations
        if analysis.recommended_next_actions:
            sections.append("## Recommended Next Actions")
            sections.append("")

            # Group by urgency
            high = [a for a in analysis.recommended_next_actions if a.urgency.value == "high"]
            medium = [a for a in analysis.recommended_next_actions if a.urgency.value == "medium"]
            low = [a for a in analysis.recommended_next_actions if a.urgency.value == "low"]

            if high:
                sections.append("### 🔴 High Priority")
                for action in high:
                    sections.append(f"- **{action.action}**")
                    sections.append(f"  - Owner: {action.owner}")
                sections.append("")

            if medium:
                sections.append("### 🟡 Medium Priority")
                for action in medium:
                    sections.append(f"- **{action.action}**")
                    sections.append(f"  - Owner: {action.owner}")
                sections.append("")

            if low:
                sections.append("### 🟢 Low Priority")
                for action in low:
                    sections.append(f"- **{action.action}**")
                    sections.append(f"  - Owner: {action.owner}")
                sections.append("")

        # Escalation Guidance
        if analysis.escalation_guidance:
            sections.append("## Escalation Guidance")
            sections.append(f"\n{analysis.escalation_guidance}\n")

        # Data Gaps
        if analysis.data_gaps:
            sections.append("## Data Gaps / Limitations")
            sections.append("")
            for gap in analysis.data_gaps:
                sections.append(f"- {gap}")
            sections.append("")

        # Timeline (if available)
        if analysis.timeline:
            sections.append("## Event Timeline (Sample)")
            sections.append("")
            for event in analysis.timeline[:5]:
                sections.append(
                    f"- `{event.timestamp.strftime('%H:%M:%S')}` "
                    f"[{event.severity.value.upper()}] "
                    f"{event.category.value}: {event.message[:100]}"
                )
            sections.append("")

        # Footer
        sections.append("---")
        sections.append("*This report was generated by AI AV Agent - Enterprise AV/IT RCA System*")

        return "\n".join(sections)

    @staticmethod
    def generate_summary_text(analysis: IncidentAnalysis) -> str:
        """
        Generate brief text summary for quick reading.

        Suitable for:
        - Slack/Teams notifications
        - Email subjects
        - Dashboard displays
        """

        summary_parts = [
            f"INCIDENT SUMMARY:",
            f"{analysis.incident_summary}",
            "",
            f"ROOT CAUSE ({analysis.most_likely_root_cause.confidence * 100:.0f}% confidence):",
            f"{analysis.most_likely_root_cause.description}",
            ""
        ]

        if analysis.recommended_next_actions:
            high_priority = [a for a in analysis.recommended_next_actions if a.urgency.value == "high"]
            if high_priority:
                summary_parts.append("IMMEDIATE ACTIONS REQUIRED:")
                for action in high_priority[:3]:
                    summary_parts.append(f"- {action.action} ({action.owner})")

        if analysis.is_repeat_issue:
            summary_parts.append("")
            summary_parts.append("⚠️ WARNING: This is a RECURRING issue requiring permanent fix")

        return "\n".join(summary_parts)

    @staticmethod
    def generate_ticket_update(analysis: IncidentAnalysis) -> str:
        """
        Generate formatted text for ticket system updates.

        Concise format suitable for Jira, ServiceNow, etc.
        """

        lines = [
            "=== ROOT CAUSE ANALYSIS ===",
            "",
            f"Time Window: {analysis.time_window_analyzed}",
            f"Events Analyzed: {analysis.total_events_analyzed}",
            "",
            "ROOT CAUSE:",
            f"{analysis.most_likely_root_cause.description}",
            f"Confidence: {analysis.most_likely_root_cause.confidence * 100:.0f}%",
            ""
        ]

        if analysis.most_likely_root_cause.evidence:
            lines.append("Evidence:")
            for evidence in analysis.most_likely_root_cause.evidence[:3]:
                lines.append(f"  - {evidence}")
            lines.append("")

        if analysis.recommended_next_actions:
            lines.append("NEXT ACTIONS:")
            for action in analysis.recommended_next_actions[:5]:
                lines.append(f"  [{action.urgency.value.upper()}] {action.action} - {action.owner}")
            lines.append("")

        if analysis.escalation_guidance:
            lines.append("ESCALATION:")
            lines.append(f"  {analysis.escalation_guidance.split('with:')[0]}")

        return "\n".join(lines)
