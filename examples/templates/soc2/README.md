# SOC2 Compliance Rules

These rules map to common SOC2 Trust Services Criteria.

## Data Files Needed
- `users.csv`: columns: username, access_level, department
- `systems.csv`: columns: system_name, encryption_enabled, logging_enabled
- `changes.csv`: columns: change_id, environment, change_approved

## Usage
```bash
compliance-copilot run soc2/rules.yaml /path/to/data
cat > examples/templates/soc2/README.md << 'EOF'
# SOC2 Compliance Rules

These rules map to common SOC2 Trust Services Criteria.

## Data Files Needed
- `users.csv`: columns: username, access_level, department
- `systems.csv`: columns: system_name, encryption_enabled, logging_enabled
- `changes.csv`: columns: change_id, environment, change_approved

## Usage
```bash
compliance-copilot run soc2/rules.yaml /path/to/data
