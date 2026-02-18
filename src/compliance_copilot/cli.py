#!/usr/bin/env python3
"""Command-line interface for Compliance Copilot."""

import sys
import argparse
import shutil
from pathlib import Path
from typing import List, Optional

from .version import get_version
from .config import ConfigLoader
from .engine import RuleEngine, RuleStatus
from .exceptions import ComplianceCopilotError
from .utils import ensure_directory, list_files
from .observability import StructuredLogger, MetricsCollector, Tracer, ErrorTracker, ErrorCategory
from .output.html_reporter import HtmlReporter
from .scheduler import ScanScheduler


# Global observability instances
logger = None
metrics = None
tracer = None
error_tracker = None
_scheduler = None


def main():
    """Main CLI entry point."""
    global logger, metrics, tracer, error_tracker
    
    parser = create_parser()
    args = parser.parse_args()
    
    # Initialize observability with safe debug flag
    debug = getattr(args, 'debug', False)
    
    logger = StructuredLogger(
        "compliance_copilot",
        level="DEBUG" if debug else "INFO"
    )
    metrics = MetricsCollector()
    tracer = Tracer()
    error_tracker = ErrorTracker()
    
    if args.command == "run":
        with tracer.trace("compliance_scan", attributes={"rules": args.rules, "data": args.data}):
            run_command(args)
    elif args.command == "init":
        init_command(args)
    elif args.command == "schedule":
        if args.schedule_command == "daily":
            schedule_daily(args)
        elif args.schedule_command == "weekly":
            schedule_weekly(args)
        elif args.schedule_command == "list":
            schedule_list()
        elif args.schedule_command == "stop":
            schedule_stop()
    elif args.command == "version":
        print(f"Compliance Copilot version {get_version()}")
    elif args.command == "metrics":
        show_metrics(args)
    elif args.command == "errors":
        show_errors(args)
    else:
        parser.print_help()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Compliance Copilot - Automated compliance checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  compliance-copilot run rules/ data/
  compliance-copilot run rules.yaml data.csv --format json
  compliance-copilot init --template soc2
  compliance-copilot schedule daily rules/ data/ --hour 9
  compliance-copilot schedule list
  compliance-copilot version
  compliance-copilot metrics
  compliance-copilot errors --last 10
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands", required=True)
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run compliance checks")
    run_parser.add_argument(
        "rules",
        help="Rules file or directory"
    )
    run_parser.add_argument(
        "data",
        help="Data file or directory"
    )
    run_parser.add_argument(
        "--output", "-o",
        default="output",
        help="Output directory (default: output)"
    )
    run_parser.add_argument(
        "--format", "-f",
        choices=["console", "json", "csv", "html", "all"],
        default="console",
        help="Output format (default: console)"
    )
    run_parser.add_argument(
        "--config",
        default="config.yaml",
        help="Config file (default: config.yaml)"
    )
    run_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new project with a template")
    init_parser.add_argument(
        "--template",
        choices=["soc2", "hipaa", "gdpr", "iso27001"],
        required=True,
        help="Compliance template to use"
    )
    init_parser.add_argument(
        "--output", "-o",
        default=".",
        help="Output directory (default: current directory)"
    )
    
    # Schedule command
    schedule_parser = subparsers.add_parser("schedule", help="Manage scheduled scans")
    schedule_subparsers = schedule_parser.add_subparsers(dest="schedule_command", help="Schedule commands", required=True)
    
    # Schedule daily
    daily_parser = schedule_subparsers.add_parser("daily", help="Add daily scan")
    daily_parser.add_argument("rules", help="Rules directory")
    daily_parser.add_argument("data", help="Data directory")
    daily_parser.add_argument("--output", "-o", default="scheduled_output", help="Output directory")
    daily_parser.add_argument("--hour", type=int, default=9, help="Hour (0-23)")
    daily_parser.add_argument("--minute", type=int, default=0, help="Minute (0-59)")
    
    # Schedule weekly
    weekly_parser = schedule_subparsers.add_parser("weekly", help="Add weekly scan")
    weekly_parser.add_argument("rules", help="Rules directory")
    weekly_parser.add_argument("data", help="Data directory")
    weekly_parser.add_argument("--output", "-o", default="scheduled_output", help="Output directory")
    weekly_parser.add_argument("--day", default="mon", help="Day of week (mon, tue, wed, thu, fri, sat, sun)")
    weekly_parser.add_argument("--hour", type=int, default=9, help="Hour (0-23)")
    weekly_parser.add_argument("--minute", type=int, default=0, help="Minute (0-59)")
    
    # Schedule list
    schedule_subparsers.add_parser("list", help="List scheduled jobs")
    
    # Schedule stop
    schedule_subparsers.add_parser("stop", help="Stop scheduler")
    
    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Show metrics")
    metrics_parser.add_argument(
        "--save",
        action="store_true",
        help="Save metrics snapshot"
    )
    
    # Errors command
    errors_parser = subparsers.add_parser("errors", help="Show errors")
    errors_parser.add_argument(
        "--last",
        type=int,
        default=10,
        help="Number of recent errors to show"
    )
    errors_parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear error history"
    )
    
    return parser


def init_command(args):
    """Initialize a new project with a template."""
    template_dir = Path(__file__).parent.parent.parent / 'examples' / 'templates' / args.template
    if not template_dir.exists():
        print(f"❌ Template '{args.template}' not found.")
        sys.exit(1)
    
    output_dir = Path(args.output)
    target = output_dir / args.template
    if target.exists():
        print(f"❌ Directory {target} already exists.")
        sys.exit(1)
    
    shutil.copytree(template_dir, target)
    print(f"✅ Template '{args.template}' copied to {target}")
    print(f"\nNext steps:")
    print(f"  1. cd {target}")
    print(f"  2. Prepare your data files (see README.md)")
    print(f"  3. Run: compliance-copilot run rules.yaml /path/to/data")


def run_command(args):
    """Execute the run command."""
    try:
        logger.info("scan_started", rules=args.rules, data=args.data, debug=args.debug)
        metrics.increment("scans_run")
        
        with metrics.timer("scan_duration", tags={"format": args.format}):
            print("\n🔍 Compliance Copilot - Running compliance checks...\n")
            
            # Load configuration
            with tracer.span("load_config"):
                config_loader = ConfigLoader()
                config = config_loader.load(args.config)
                logger.info("config_loaded", config_file=args.config)
            
            if args.debug:
                print(f"📋 Configuration loaded from: {args.config}")
                print(f"   Rules: {args.rules}")
                print(f"   Data: {args.data}")
                print(f"   Output: {args.output}")
                print()
            
            # Create output directory
            output_dir = ensure_directory(args.output)
            
            # Initialize rule engine
            with tracer.span("init_engine"):
                engine = RuleEngine(config.dict(), debug=args.debug)
                logger.info("engine_initialized")
            
            # Run the checks
            with tracer.span("execute_rules"):
                with metrics.timer("rule_execution_total"):
                    results = engine.run(args.rules, args.data)
            
            metrics.gauge("rules_executed", len(results))
            logger.info("rules_executed", count=len(results))
            
            # Print results to console
            print(f"\n{'='*60}")
            print(f"COMPLIANCE SCAN RESULTS")
            print(f"{'='*60}")
            print()
            
            # Summary stats
            total = len(results)
            passed = sum(1 for r in results if r.status == RuleStatus.PASS)
            failed = sum(1 for r in results if r.status == RuleStatus.FAIL)
            errors = sum(1 for r in results if r.status == RuleStatus.ERROR)
            
            metrics.gauge("rules_passed", passed)
            metrics.gauge("rules_failed", failed)
            metrics.gauge("rules_errors", errors)
            
            # Print each rule result
            for result in results:
                if result.status == RuleStatus.PASS:
                    status_icon = "✅"
                    metrics.increment("rule_passed", tags={"rule": result.rule_id})
                elif result.status == RuleStatus.FAIL:
                    status_icon = "❌"
                    metrics.increment("rule_failed", tags={"rule": result.rule_id})
                    metrics.increment("violations", result.failed_rows)
                else:
                    status_icon = "⚠️"
                    metrics.increment("rule_error", tags={"rule": result.rule_id})
                
                print(f"{status_icon} {result.rule_id}: {result.rule_name}")
                
                if result.status == RuleStatus.ERROR:
                    print(f"   Error: {result.error_message}")
                    error_tracker.track(
                        Exception(result.error_message),
                        category=ErrorCategory.RULE_EXECUTION,
                        context={"rule_id": result.rule_id}
                    )
                else:
                    print(f"   Pass rate: {result.pass_rate:.1f}% ({result.passed_rows}/{result.total_rows})")
                    
                    if result.violations and args.debug:
                        print(f"   Violations: {result.failed_rows}")
                        for i, v in enumerate(result.violations[:3]):
                            print(f"     - Row {v['row_index']}")
                        if len(result.violations) > 3:
                            print(f"     ... and {len(result.violations) - 3} more")
                
                print()
            
            # Print summary
            print(f"{'='*60}")
            print(f"SUMMARY")
            print(f"{'='*60}")
            print(f"Total rules: {total}")
            print(f"✅ Passed:    {passed}")
            print(f"❌ Failed:    {failed}")
            print(f"⚠️ Errors:    {errors}")
            print()
            
            # Save results based on format
            if args.format in ["json", "all"]:
                with tracer.span("save_json"):
                    json_path = output_dir / "results.json"
                    save_json_results(results, json_path)
                    print(f"📄 JSON results saved to: {json_path}")
                    metrics.increment("reports_generated", tags={"format": "json"})
            
            if args.format in ["csv", "all"]:
                with tracer.span("save_csv"):
                    csv_path = output_dir / "violations.csv"
                    save_csv_violations(results, csv_path)
                    print(f"📄 CSV violations saved to: {csv_path}")
                    metrics.increment("reports_generated", tags={"format": "csv"})
            
            if args.format in ["html", "all"]:
                with tracer.span("save_html"):
                    html_path = output_dir / "report.html"
                    reporter = HtmlReporter()
                    reporter.generate(results, html_path)
                    print(f"📄 HTML report saved to: {html_path}")
                    metrics.increment("reports_generated", tags={"format": "html"})
            
            print(f"\n✅ Scan complete!")
            
            # Save metrics snapshot
            metrics.save_snapshot()
            logger.info("scan_completed", 
                       total_rules=total, 
                       passed=passed, 
                       failed=failed, 
                       errors=errors)
        
    except ComplianceCopilotError as e:
        logger.error("compliance_error", error=str(e))
        error_tracker.track(e, category=ErrorCategory.CONFIGURATION)
        print(f"\n❌ Error: {e}")
        if args.debug:
            print("\nDebug trace:")
            import traceback
            traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        logger.error("unexpected_error", error=str(e))
        error_tracker.track(e, category=ErrorCategory.UNKNOWN)
        print(f"\n❌ Unexpected error: {e}")
        if args.debug:
            print("\nDebug trace:")
            import traceback
            traceback.print_exc()
        sys.exit(1)


def schedule_daily(args):
    """Add a daily scheduled scan."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ScanScheduler()
    
    _scheduler.add_daily_scan(
        rules_dir=args.rules,
        data_dir=args.data,
        output_dir=args.output,
        hour=args.hour,
        minute=args.minute
    )
    _scheduler.start()
    
    # Keep running until interrupted
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _scheduler.stop()
        print("\n✅ Scheduler stopped")


def schedule_weekly(args):
    """Add a weekly scheduled scan."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ScanScheduler()
    
    _scheduler.add_weekly_scan(
        rules_dir=args.rules,
        data_dir=args.data,
        output_dir=args.output,
        day_of_week=args.day,
        hour=args.hour,
        minute=args.minute
    )
    _scheduler.start()
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _scheduler.stop()
        print("\n✅ Scheduler stopped")


def schedule_list():
    """List all scheduled jobs."""
    global _scheduler
    if _scheduler is None:
        print("❌ No scheduler running")
        return
    
    jobs = _scheduler.list_jobs()
    if not jobs:
        print("No scheduled jobs")
        return
    
    print("\n📅 SCHEDULED JOBS")
    print("="*60)
    for job in jobs:
        print(f"Job ID: {job['id']}")
        print(f"  Next run: {job['next_run']}")
        print(f"  Trigger: {job['trigger']}")
        print()


def schedule_stop():
    """Stop the scheduler."""
    global _scheduler
    if _scheduler is None:
        print("❌ No scheduler running")
        return
    
    _scheduler.stop()
    _scheduler = None
    print("✅ Scheduler stopped")


def show_metrics(args):
    """Show metrics command."""
    print("\n📊 COMPLIANCE COPILOT METRICS")
    print("="*60)
    
    summary = metrics.summary()
    
    print(f"\nSession started: {metrics.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Uptime: {summary['uptime_seconds']:.1f} seconds")
    print()
    
    if summary['counters']:
        print("📈 Counters:")
        for key, value in summary['counters'].items():
            print(f"  {key}: {value}")
    
    if summary['gauges']:
        print("\n📊 Gauges:")
        for key, value in summary['gauges'].items():
            print(f"  {key}: {value}")
    
    if summary['timers']:
        print("\n⏱️ Timers:")
        for name, stats in summary['timers'].items():
            print(f"  {name}:")
            print(f"    Count: {stats['count']}")
            print(f"    Avg: {stats['avg_ms']:.2f}ms")
            print(f"    Total: {stats['total_ms']:.2f}ms")
            if stats.get('p95_ms'):
                print(f"    P95: {stats['p95_ms']:.2f}ms")
    
    print()
    
    if args.save:
        path = metrics.save_snapshot()
        print(f"✅ Metrics snapshot saved to: {path}")


def show_errors(args):
    """Show errors command."""
    if args.clear:
        error_tracker.clear()
        print("✅ Error history cleared")
        return
    
    print("\n❌ RECENT ERRORS")
    print("="*60)
    
    recent = error_tracker.get_recent(args.last)
    
    if not recent:
        print("No errors recorded")
        return
    
    for i, error in enumerate(recent, 1):
        print(f"\n{i}. [{error['timestamp']}] {error['category']} - {error['severity']}")
        print(f"   {error['user_message']}")
        if error['context']:
            print(f"   Context: {error['context']}")
    
    print(f"\nTotal errors in session: {len(error_tracker.errors)}")
    
    # Show summary by category
    summary = error_tracker.summary()
    if summary:
        print("\n📊 Error Summary:")
        for category, count in summary.items():
            print(f"  {category}: {count}")
    
    print()


def save_json_results(results, path):
    """Save results as JSON."""
    import json
    from datetime import datetime
    
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.status == RuleStatus.PASS),
            "failed": sum(1 for r in results if r.status == RuleStatus.FAIL),
            "errors": sum(1 for r in results if r.status == RuleStatus.ERROR)
        },
        "results": [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "status": r.status.value,
                "pass_rate": r.pass_rate,
                "total_rows": r.total_rows,
                "passed_rows": r.passed_rows,
                "failed_rows": r.failed_rows,
                "execution_time_ms": r.execution_time_ms,
                "error": r.error_message
            }
            for r in results
        ]
    }
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def save_csv_violations(results, path):
    """Save violations as CSV."""
    import csv
    
    # Collect all violations
    rows = []
    for result in results:
        for violation in result.violations:
            rows.append({
                "rule_id": result.rule_id,
                "rule_name": result.rule_name,
                "row_index": violation["row_index"],
                **violation["row_data"]
            })
    
    if not rows:
        # Create empty file with headers
        with open(path, 'w') as f:
            f.write("rule_id,rule_name,row_index\n")
        return
    
    # Get all column names
    fieldnames = set()
    for row in rows:
        fieldnames.update(row.keys())
    
    # Write CSV
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
