# AI-AV-Agent

**Enterprise AV/IT Root Cause Analysis System**

An expert AI agent specialized in analyzing operational logs from enterprise AV, network, and IT systems to identify root causes and provide actionable recommendations.

## 🎯 Overview

AI-AV-Agent acts as a virtual operations engineer with 15+ years of experience, providing:

- **Automated Root Cause Analysis** - Analyzes logs and correlates events to identify the most likely root cause
- **Expert Pattern Recognition** - Recognizes recurring failure patterns across enterprise AV systems
- **Actionable Recommendations** - Provides concrete next steps with ownership and urgency levels
- **Vendor Escalation Guidance** - Knows when and how to escalate to appropriate vendors
- **Multi-Format Reporting** - Outputs in JSON, Markdown, summary, or ticket-update formats

### Specialized In

- **Enterprise AV Systems**: Zoom Rooms, Q-SYS, Crestron, Cisco, Analogway
- **Corporate Networking**: VLANs, PoE, multicast, QoS, DNS, DHCP
- **Monitoring Systems**: Netgear, Domotz monitoring agent, EcoStruxure
- **Facilities Operations**: Power, environmental, and incident response

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AI-AV-Agent.git
cd AI-AV-Agent

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from src import AVAgent

# Initialize agent
agent = AVAgent(known_patterns_path='config/known_patterns.yaml')

# Analyze logs from file
result = agent.analyze_from_file(
    log_file_path='examples/sample_logs.txt',
    user_query="Why did Room 12 fail this morning?",
    output_format='json'
)

print(result)
```

### Command Line Usage

```bash
# Run the example
python examples/example_usage.py

# Analyze specific logs
python -c "
from src import AVAgent
agent = AVAgent()
result = agent.analyze_from_file('your_logs.txt', output_format='summary')
print(result)
"
```

## 📋 Features

### 1. Log Parsing & Normalization

Automatically parses and normalizes logs from various sources:

- Syslog format
- ISO 8601 timestamps
- Device identification (IP, hostname, room name)
- Severity classification
- Error code extraction

**Supported Systems:**
- Zoom Rooms
- Crestron control processors
- Q-SYS audio DSP
- Cisco networking equipment
- Netgear switches
- Generic syslog

### 2. Event Correlation

Identifies relationships between events:

- **Temporal Clustering** - Groups events that occur close in time
- **Cascading Failure Detection** - Identifies when one failure triggers others
- **Pattern Recognition** - Detects recurring intervals and patterns
- **Change Tracking** - Flags configuration changes before incidents

### 3. Root Cause Analysis

Expert system that:

- Ranks causes by likelihood with confidence scores (0.0-1.0)
- Provides explicit evidence from logs for each cause
- Distinguishes between symptoms and root causes
- Applies real-world operational heuristics
- Checks against known failure patterns

### 4. Structured Output

```json
{
  "incident_summary": "Analysis of 'Why did Room 12 fail?'...",
  "time_window_analyzed": "2026-01-08T08:15:23 to 2026-01-08T08:19:01",
  "affected_resources": ["Room: Room12", "Device: 10.1.2.150"],
  "most_likely_root_cause": {
    "description": "DHCP server failure or IP address exhaustion",
    "confidence": 0.85,
    "evidence": [
      "DHCP pool 'conference-vlan' utilization: 98%",
      "DHCP timeout - no IP address received",
      "DHCP DISCOVER - no available addresses"
    ]
  },
  "secondary_possible_causes": [...],
  "what_changed_before_incident": [...],
  "recommended_next_actions": [
    {
      "action": "Verify network switch port status and PoE power budget",
      "owner": "Network Team",
      "urgency": "high"
    }
  ],
  "is_repeat_issue": false,
  "historical_context": "",
  "escalation_guidance": "Escalate to Network Team with: ...",
  "data_gaps": []
}
```

## 🔧 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                           │
│           "Why did Room 12 fail this morning?"              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      AVAgent (Main)                         │
│                    Orchestrates pipeline                    │
└────────────┬──────────────────┬──────────────┬──────────────┘
             │                  │              │
             ▼                  ▼              ▼
    ┌────────────────┐  ┌──────────────┐  ┌─────────────┐
    │  Log Parser    │  │   Event      │  │ RCA Engine  │
    │   Normalize    │─▶│  Correlator  │─▶│   Analyze   │
    │   Events       │  │  Find Links  │  │  Root Cause │
    └────────────────┘  └──────────────┘  └──────┬──────┘
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │ Report Generator│
                                         │  JSON/Markdown  │
                                         └─────────────────┘
```

### Core Components

- **`log_parser.py`** - Parses raw logs into structured events
- **`event_correlator.py`** - Identifies temporal and causal relationships
- **`rca_engine.py`** - Applies expert knowledge to determine root causes
- **`report_generator.py`** - Formats output in multiple formats
- **`models.py`** - Pydantic data models for type safety

## 📊 Example Scenarios

### Scenario 1: DHCP Exhaustion

**Input:**
```
2026-01-08 08:15:23 [NETWORK] Switch: DHCP pool utilization: 98%
2026-01-08 08:16:45 [ZOOM] Room12: DHCP timeout - no IP address
```

**Output:**
```json
{
  "most_likely_root_cause": {
    "description": "DHCP server failure or IP address exhaustion",
    "confidence": 0.85,
    "evidence": ["DHCP pool 98% full", "Multiple DHCP timeouts"]
  }
}
```

### Scenario 2: PoE Budget Exceeded

**Input:**
```
2026-01-08 09:30:45 [NETWORK] Switch Port 18: PoE power denied
2026-01-08 09:30:46 [CRITICAL] Room08-Camera: Device offline - power lost
```

**Output:**
```json
{
  "most_likely_root_cause": {
    "description": "PoE (Power over Ethernet) failure - insufficient power budget",
    "confidence": 0.85,
    "evidence": ["PoE power denied", "Camera offline - power lost"]
  },
  "recommended_next_actions": [
    {
      "action": "Check PoE switch power budget and port allocation",
      "owner": "Network Team",
      "urgency": "high"
    }
  ]
}
```

## 🛠 Configuration

### Known Patterns (`config/known_patterns.yaml`)

Define recurring failure patterns for faster identification:

```yaml
patterns:
  - pattern_id: "DHCP-EXHAUSTION"
    name: "DHCP IP Pool Exhaustion"
    symptoms:
      - "DHCP timeout"
      - "No IP address assigned"
    typical_root_cause: "DHCP scope too small or lease time too long"
    recommended_actions:
      - "Expand DHCP scope range"
      - "Reduce lease time"
```

### Vendor Contacts (`config/vendor_contacts.yaml`)

Customize with your organization's vendor contacts:

```yaml
vendors:
  - vendor_name: "Zoom Video Communications"
    system_types: ["Zoom Rooms"]
    contact_info: "support.zoom.us | 1-888-799-9666"
    escalation_criteria:
      - "Multiple Zoom Rooms offline (3+)"
      - "Authentication failures across fleet"
```

## 🎓 Advanced Usage

### Custom Correlation Window

```python
# Increase correlation window for analyzing slower failures
agent = AVAgent(correlation_window_seconds=600)  # 10 minutes
```

### Different Output Formats

```python
# JSON (default) - structured data
result = agent.analyze(logs, output_format='json')

# Markdown - human-readable RCA report
result = agent.analyze(logs, output_format='markdown')

# Summary - brief text for notifications
result = agent.analyze(logs, output_format='summary')

# Ticket - formatted for Jira/ServiceNow
result = agent.analyze(logs, output_format='ticket')
```

### Programmatic Integration

```python
from src import AVAgent
import json

agent = AVAgent(known_patterns_path='config/known_patterns.yaml')

# Get structured analysis
result_json = agent.analyze(raw_logs, output_format='json')
analysis = json.loads(result_json)

# Access specific fields
root_cause = analysis['most_likely_root_cause']['description']
confidence = analysis['most_likely_root_cause']['confidence']

if confidence > 0.8:
    # High confidence - take automated action
    escalate_to_team(analysis['recommended_next_actions'][0])
```

## 🔍 Understanding Output

### Confidence Scores

- **0.9 - 1.0**: Very high confidence - strong evidence, clear pattern
- **0.8 - 0.89**: High confidence - good evidence, likely cause
- **0.7 - 0.79**: Moderate confidence - some evidence, plausible
- **0.5 - 0.69**: Low confidence - limited evidence, investigate further
- **< 0.5**: Very low confidence - insufficient data

### Urgency Levels

- **High**: Immediate action required, business impact ongoing
- **Medium**: Important but not critical, schedule within hours
- **Low**: Documentation, prevention, future improvements

## 🧪 Testing

```bash
# Run the example usage to test the system
python examples/example_usage.py

# The script will:
# 1. Parse sample logs
# 2. Correlate events
# 3. Perform RCA
# 4. Generate multiple output formats
```

## 📁 Project Structure

```
AI-AV-Agent/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── src/
│   ├── __init__.py               # Package initialization
│   ├── agent.py                  # Main orchestrator
│   ├── log_parser.py             # Log parsing and normalization
│   ├── event_correlator.py       # Event correlation engine
│   ├── rca_engine.py             # Root cause analysis engine
│   ├── report_generator.py       # Report formatting
│   └── models.py                 # Data models (Pydantic)
├── config/
│   ├── known_patterns.yaml       # Known failure patterns
│   └── vendor_contacts.yaml      # Vendor escalation info
├── examples/
│   ├── sample_logs.txt           # Sample operational logs
│   └── example_usage.py          # Usage examples
└── tests/
    └── (test files)
```

## 🤝 Contributing

This is an expert system based on real-world operational experience. Contributions are welcome:

1. **Add new failure patterns** to `config/known_patterns.yaml`
2. **Improve log parsing** for additional AV/IT systems
3. **Enhance RCA logic** with additional heuristics
4. **Add test cases** for specific scenarios

## 📝 Design Principles

### Never Guess or Hallucinate

- Only makes claims supported by evidence from logs
- Clearly states uncertainty when data is insufficient
- Identifies data gaps that would improve analysis

### Real-World Operational Thinking

- Prefers simple causes over exotic ones (Occam's Razor)
- Considers recent changes first
- Recognizes recurring failure patterns
- Distinguishes symptoms from root causes

### Actionable Output

- Provides concrete next steps
- Assigns ownership (team/vendor)
- Includes urgency levels
- Explains escalation criteria

## 🔒 Security & Privacy

- No data is sent to external services
- Runs entirely locally
- Sanitize logs before sharing (remove sensitive IPs, credentials)
- Review vendor contact information before committing

## 📜 License

[Specify your license]

## 🆘 Support

For issues or questions:
- Check `examples/example_usage.py` for usage patterns
- Review sample logs in `examples/sample_logs.txt`
- Consult configuration files in `config/`

---

**Built for AV/IT operations teams who need fast, accurate root cause analysis.**
