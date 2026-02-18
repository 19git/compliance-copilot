# HIPAA Compliance Rules

These rules align with the HIPAA Security Rule.

## Data Files Needed
- `users.csv`: columns: username, role, department, phi_access
- `systems.csv`: columns: system_name, audit_log_enabled
- `phi_records.csv`: columns: record_id, integrity_check_passed

## Usage
```bash
compliance-copilot run hipaa/rules.yaml /path/to/data
cat > examples/templates/hipaa/README.md << 'EOF'
# HIPAA Compliance Rules

These rules align with the HIPAA Security Rule.

## Data Files Needed
- `users.csv`: columns: username, role, department, phi_access
- `systems.csv`: columns: system_name, audit_log_enabled
- `phi_records.csv`: columns: record_id, integrity_check_passed

## Usage
```bash
compliance-copilot run hipaa/rules.yaml /path/to/data
