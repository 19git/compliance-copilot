"""Scheduled scan runner for Compliance Copilot."""

import time
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .engine import RuleEngine, RuleStatus
from .config import ConfigLoader
from .observability import StructuredLogger, MetricsCollector
from .output.html_reporter import HtmlReporter
from .notifier import Notifier


class ScanScheduler:
    """Runs compliance scans on a schedule."""
    
    def __init__(self, config_path="config.yaml"):
        self.config_path = config_path
        self.logger = StructuredLogger("scheduler")
        self.metrics = MetricsCollector()
        self.scheduler = BackgroundScheduler()
        self.jobs = []
        
        # Load config
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load(config_path)
        
        # Initialize notifier
        self.notifier = Notifier(self.config.dict().get('alerts', {}))
    
    def add_daily_scan(self, rules_dir, data_dir, output_dir, hour=9, minute=0):
        """Add a daily scan at specified time."""
        trigger = CronTrigger(hour=hour, minute=minute)
        
        def scan_job():
            self._run_scan(rules_dir, data_dir, output_dir)
        
        job = self.scheduler.add_job(
            scan_job,
            trigger,
            id=f"daily_scan_{rules_dir}",
            replace_existing=True
        )
        self.jobs.append(job)
        self.logger.info("daily_scan_added", 
                        rules=rules_dir, 
                        time=f"{hour:02d}:{minute:02d}")
    
    def add_weekly_scan(self, rules_dir, data_dir, output_dir, day_of_week='mon', hour=9, minute=0):
        """Add a weekly scan on specified day."""
        trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        
        def scan_job():
            self._run_scan(rules_dir, data_dir, output_dir)
        
        job = self.scheduler.add_job(
            scan_job,
            trigger,
            id=f"weekly_scan_{rules_dir}",
            replace_existing=True
        )
        self.jobs.append(job)
        self.logger.info("weekly_scan_added", 
                        rules=rules_dir, 
                        day=day_of_week,
                        time=f"{hour:02d}:{minute:02d}")
    
    def _run_scan(self, rules_dir, data_dir, output_dir):
        """Internal method to run a scan."""
        scan_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.logger.info("scheduled_scan_started", scan_id=scan_id)
        
        try:
            # Initialize engine
            engine = RuleEngine(self.config.dict())
            
            # Run the scan
            results = engine.run(rules_dir, data_dir)
            
            # Generate reports
            output_path = Path(output_dir) / scan_id
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save JSON
            self._save_json(results, output_path / "results.json")
            
            # Save HTML report
            reporter = HtmlReporter()
            reporter.generate(results, output_path / "report.html")
            
            # Check for failures
            failures = [r for r in results if r.status == RuleStatus.FAIL]
            errors = [r for r in results if r.status == RuleStatus.ERROR]
            
            # Summary for alerts
            summary = {
                'total': len(results),
                'passed': len([r for r in results if r.status == RuleStatus.PASS]),
                'failed': len(failures),
                'errors': len(errors)
            }
            
            # Send alerts if there are failures and notifier is configured
            if failures and self.notifier.is_configured():
                self.notifier.send_alerts(failures, scan_id, summary)
                self.logger.info("alerts_sent", failure_count=len(failures))
            
            self.logger.info("scheduled_scan_completed", 
                           scan_id=scan_id,
                           total_rules=len(results),
                           failures=len(failures),
                           errors=len(errors))
            
        except Exception as e:
            self.logger.error("scheduled_scan_failed", 
                            scan_id=scan_id,
                            error=str(e))
    
    def _save_json(self, results, path):
        """Save results as JSON."""
        import json
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "status": r.status.value,
                    "pass_rate": r.pass_rate,
                    "violations": len(r.violations)
                }
                for r in results
            ]
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        self.logger.info("scheduler_started", jobs=len(self.jobs))
        print(f"\n⏰ Scheduler started with {len(self.jobs)} job(s)")
        if self.notifier.is_configured():
            print("📧 Alerts configured and active")
        print("Press Ctrl+C to stop")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        self.logger.info("scheduler_stopped")
    
    def list_jobs(self):
        """List all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'None',
                'trigger': str(job.trigger)
            })
        return jobs
