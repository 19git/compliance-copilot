"""Alert notifier for Compliance Copilot.

Sends notifications when rules fail via:
- Email (SMTP)
- Slack (webhooks)
"""

import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .observability import StructuredLogger


class Notifier:
    """Send alerts when compliance checks fail."""
    
    def __init__(self, config: dict = None):
        """Initialize notifier with configuration.
        
        Config format:
        {
            "email": {
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "user@gmail.com",
                "password": "app-password",
                "from_addr": "alerts@compliance.com",
                "to_addrs": ["admin@company.com"]
            },
            "slack": {
                "webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz"
            }
        }
        """
        self.config = config or {}
        self.logger = StructuredLogger("notifier")
        
        # Email config
        self.email_config = self.config.get('email', {})
        
        # Slack config
        self.slack_config = self.config.get('slack', {})
    
    def send_alerts(self, failures: List[Any], scan_id: str, summary: dict):
        """Send alerts through all configured channels."""
        if not failures:
            return
        
        if self.email_config:
            self._send_email(failures, scan_id, summary)
        
        if self.slack_config:
            self._send_slack(failures, scan_id, summary)
    
    def _send_email(self, failures: List[Any], scan_id: str, summary: dict):
        """Send email alert."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['Subject'] = f"🚨 Compliance Alert: {len(failures)} Rule(s) Failed"
            msg['From'] = self.email_config.get('from_addr')
            msg['To'] = ', '.join(self.email_config.get('to_addrs', []))
            
            # Build HTML body
            html = self._build_email_html(failures, scan_id, summary)
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(
                self.email_config.get('smtp_host'),
                self.email_config.get('smtp_port')
            ) as server:
                server.starttls()
                server.login(
                    self.email_config.get('username'),
                    self.email_config.get('password')
                )
                server.send_message(msg)
            
            self.logger.info("email_alerts_sent", 
                           count=len(failures),
                           recipients=self.email_config.get('to_addrs'))
            
        except Exception as e:
            self.logger.error("email_alerts_failed", error=str(e))
    
    def _send_slack(self, failures: List[Any], scan_id: str, summary: dict):
        """Send Slack alert via webhook."""
        try:
            # Build Slack message blocks
            blocks = self._build_slack_blocks(failures, scan_id, summary)
            
            # Send to webhook
            response = requests.post(
                self.slack_config.get('webhook_url'),
                json={'blocks': blocks}
            )
            response.raise_for_status()
            
            self.logger.info("slack_alerts_sent", count=len(failures))
            
        except Exception as e:
            self.logger.error("slack_alerts_failed", error=str(e))
    
    def _build_email_html(self, failures: List[Any], scan_id: str, summary: dict) -> str:
        """Build HTML email body."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; }}
                .summary {{ margin: 20px; padding: 20px; background-color: #f5f5f5; }}
                .rule {{ margin: 20px; padding: 20px; border-left: 4px solid #f44336; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Compliance Alert: {len(failures)} Rule(s) Failed</h1>
                <p>Scan ID: {scan_id}</p>
                <p>Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
            
            <div class="summary">
                <h2>Scan Summary</h2>
                <p>Total Rules: {summary['total']}</p>
                <p>✅ Passed: {summary['passed']}</p>
                <p>❌ Failed: {summary['failed']}</p>
                <p>⚠️ Errors: {summary['errors']}</p>
            </div>
            
            <h2>Failed Rules</h2>
        """
        
        for failure in failures:
            html += f"""
            <div class="rule">
                <h3>{failure.rule_id}: {failure.rule_name}</h3>
                <p>Failed: {failure.failed_rows} of {failure.total_rows} rows</p>
                <p>Pass Rate: {failure.pass_rate:.1f}%</p>
            """
            
            if failure.violations:
                html += "<h4>Violations:</h4><table><tr>"
                # Add headers
                for col in failure.violations[0]['row_data'].keys():
                    html += f"<th>{col}</th>"
                html += "</tr>"
                
                # Add rows (max 10)
                for v in failure.violations[:10]:
                    html += "<tr>"
                    for val in v['row_data'].values():
                        html += f"<td>{val}</td>"
                    html += "</tr>"
                
                if len(failure.violations) > 10:
                    html += f"<tr><td colspan='100%'>... and {len(failure.violations) - 10} more violations</td></tr>"
                
                html += "</table>"
            
            html += "</div>"
        
        html += """
        </body>
        </html>
        """
        return html
    
    def _build_slack_blocks(self, failures: List[Any], scan_id: str, summary: dict) -> List[dict]:
        """Build Slack message blocks."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {len(failures)} Compliance Rule(s) Failed",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Scan ID:*\n{scan_id}"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Total Rules:* {summary['total']}"},
                    {"type": "mrkdwn", "text": f"*✅ Passed:* {summary['passed']}"},
                    {"type": "mrkdwn", "text": f"*❌ Failed:* {summary['failed']}"},
                    {"type": "mrkdwn", "text": f"*⚠️ Errors:* {summary['errors']}"}
                ]
            },
            {"type": "divider"}
        ]
        
        # Add failed rules
        for failure in failures[:5]:  # Limit to 5 failures to avoid Slack message size limits
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{failure.rule_id}: {failure.rule_name}*\nFailed: {failure.failed_rows} of {failure.total_rows} rows (Pass rate: {failure.pass_rate:.1f}%)"
                }
            })
            
            if failure.violations:
                # Show first violation as example
                v = failure.violations[0]
                example = ", ".join([f"{k}={v['row_data'][k]}" for k in list(v['row_data'].keys())[:3]])
                blocks.append({
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"Example violation: {example}..."}
                    ]
                })
            
            blocks.append({"type": "divider"})
        
        if len(failures) > 5:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"... and {len(failures) - 5} more failures"
                }
            })
        
        return blocks
    
    def is_configured(self) -> bool:
        """Check if at least one notification method is configured."""
        return bool(self.email_config) or bool(self.slack_config)
