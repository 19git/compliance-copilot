# Compliance Copilot 🚀

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0--alpha-orange)]()

A powerful, extensible compliance automation tool that checks if your data follows your rules.

## ✨ Features

- ✅ **Multi-format support**: Read CSV, Excel, JSON, Parquet, PDF
- 📝 **YAML-based rules**: Simple, human-readable rule definitions
- 🔌 **Pluggable architecture**: Add custom connectors easily
- 📊 **Multiple outputs**: Console, JSON, CSV, beautiful HTML reports
- ⏰ **Scheduled scans**: Daily/weekly automated checks
- 📧 **Alerts**: Email and Slack notifications on failures
- 📈 **Observability**: Built-in logging, metrics, and tracing
- 🧩 **Template library**: Pre-built SOC2, HIPAA, GDPR, ISO27001 rules

## 🚀 Quick Start

```bash
# Install
pip install compliance-copilot

# Create a rule file (rules.yaml)
cat > rules.yaml << 'YAML'
rules:
  - id: "MFA-001"
    name: "MFA Required for Admins"
    condition: "mfa_enabled == True"
    data_source: "users.csv"
    filter: "role == 'admin'"
    severity: "HIGH"
YAML

# Create a data file (users.csv)
cat > users.csv << 'CSV'
username,mfa_enabled,role,last_login
alice@example.com,True,admin,2024-02-15
bob@example.com,False,user,2024-02-14
CSV

# Run it!
compliance-copilot run rules.yaml users.csv
