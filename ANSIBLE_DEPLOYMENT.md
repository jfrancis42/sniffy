# Ansible Deployment - Zero-Install Remote Execution

Run quantum-sniffer on remote hosts without permanent installation using Ansible.

## Overview

The Ansible playbook provides **temporary, zero-install execution**:

1. ✅ Creates temp directory on remote host
2. ✅ Copies quantum-sniffer source code
3. ✅ Creates Python virtual environment
4. ✅ Installs dependencies (scapy, cryptography)
5. ✅ Runs quantum-sniffer scan
6. ✅ Fetches results to control machine
7. ✅ **Deletes everything** (guaranteed cleanup)

**Result:** Zero permanent changes to remote systems.

## Quick Start

### 1. Navigate to ansible directory

```bash
cd ~/quantum-sniffer/ansible
```

### 2. Configure inventory

Edit `inventory.ini` with your hosts:

```ini
[production]
web-prod-1 ansible_host=10.1.1.50 ansible_user=upce
db-prod-1 ansible_host=10.1.1.100 ansible_user=upce

[staging]
web-staging-1 ansible_host=10.1.2.50 ansible_user=upce
```

Or generate from UPCE inventory:

```bash
./generate-inventory-from-upce.py > inventory-from-upce.ini
```

### 3. Test connectivity

```bash
ansible -i inventory.ini scan_targets -m ping
```

### 4. Run scan

```bash
# Scan all hosts (each scans itself)
ansible-playbook -i inventory.ini run-quantum-sniffer.yml

# Scan production only
ansible-playbook -i inventory.ini run-quantum-sniffer.yml -l production
```

### 5. View results

```bash
ls results/
# web-prod-1-2026-06-29-scan.json
# web-prod-1-2026-06-29-scan.md

# View report
less results/web-prod-1-2026-06-29-scan.md

# Query with jq
jq '.summary' results/web-prod-1-2026-06-29-scan.json
```

## What Gets Installed (Temporarily)

**On Remote Hosts:**
- `/tmp/quantum-sniffer-<timestamp>-<hostname>/` - Temporary directory
  - `quantum_sniffer/` - Source code
  - `venv/` - Python virtual environment
  - `scan-results.*` - Output files

**Duration:** Only during playbook execution (1-2 minutes)

**After Completion:** Everything deleted automatically

## Usage Examples

### Scan Different Target

```bash
# Scan specific IP
ansible-playbook -i inventory.ini run-quantum-sniffer.yml \
  -e "scan_target=10.1.1.100"

# Scan subnet
ansible-playbook -i inventory.ini run-quantum-sniffer.yml \
  -e "scan_target=10.1.1.0/24"
```

### Custom Ports

```bash
ansible-playbook -i inventory.ini run-quantum-sniffer.yml \
  -e "scan_ports=22,25,80,110,143,443,587,993,995"
```

### Fast Scanning

```bash
ansible-playbook -i inventory.ini run-quantum-sniffer.yml \
  -e "scan_timeout=3 scan_workers=20" \
  -f 10  # Parallel execution on 10 hosts
```

### Passive Capture Mode

```bash
ansible-playbook -i inventory.ini run-quantum-sniffer.yml \
  -e "scan_mode=passive" \
  --become \
  --ask-become-pass
```

## Integration with UPCE

### Generate Inventory from UPCE

```bash
cd ~/quantum-sniffer/ansible
./generate-inventory-from-upce.py > inventory-from-upce.ini

# Review generated inventory
less inventory-from-upce.ini

# Use it
ansible-playbook -i inventory-from-upce.ini run-quantum-sniffer.yml
```

The generator:
- Reads `~/common/inventory.json`
- Creates groups by labels (e.g., `label_env_prod`, `label_role_web`)
- Creates groups by OS (e.g., `os_linux`, `os_windows`)
- Creates groups by mode (e.g., `mode_enforced`, `mode_monitor`)
- Skips workloads with placeholder credentials
- Skips workloads with mode='none'

### Scan Specific Label Groups

```bash
# Scan production workloads only
ansible-playbook -i inventory-from-upce.ini run-quantum-sniffer.yml \
  -l label_env_prod

# Scan web servers only
ansible-playbook -i inventory-from-upce.ini run-quantum-sniffer.yml \
  -l label_role_web

# Scan Linux hosts only
ansible-playbook -i inventory-from-upce.ini run-quantum-sniffer.yml \
  -l os_linux
```

## Example Scripts

Pre-built scripts in `ansible/examples/`:

### Scan Production

```bash
cd ~/quantum-sniffer/ansible
./examples/scan-production.sh
```

Scans all production hosts with common ports.

### Scan and Label in Illumio

```bash
cd ~/quantum-sniffer/ansible
export ILLUMIO_PCE_HOST=pce.example.com
export ILLUMIO_API_KEY=api_123...
export ILLUMIO_API_SECRET=123...

./examples/scan-and-label.sh
```

Workflow:
1. Scans all hosts
2. Labels workloads in Illumio PCE with PQC status
3. Shows compliance summary

### Bulk Compliance Check

```bash
cd ~/quantum-sniffer/ansible
./examples/bulk-compliance-check.sh
```

Generates compliance report with:
- Total hosts scanned
- PQ-capable percentage
- List of quantum-vulnerable hosts
- Recommendations

## Files Created

```
quantum-sniffer/ansible/
├── run-quantum-sniffer.yml          # Main playbook
├── inventory.ini                    # Manual inventory (template)
├── generate-inventory-from-upce.py  # Generate from UPCE
├── README.md                        # Detailed documentation
├── examples/
│   ├── scan-production.sh           # Scan production hosts
│   ├── scan-and-label.sh            # Scan + Illumio labeling
│   └── bulk-compliance-check.sh     # Generate compliance report
└── results/                         # Scan results (created at runtime)
    ├── host1-2026-06-29-scan.json
    ├── host1-2026-06-29-scan.md
    └── ...
```

## Requirements

### Control Machine (where you run ansible)

```bash
# Install Ansible
sudo apt install ansible

# Or via pip
pip install ansible
```

### Remote Hosts (target machines)

**Required:**
- Python 3.9+ (usually pre-installed)
- SSH access with key-based authentication

**Optional:**
- sudo access (only for passive capture mode)
- Internet access (for pip to download dependencies)

**NOT Required:**
- No quantum-sniffer installation
- No scapy installation
- No cryptography installation
- **Nothing permanent installed**

## Variables

Override with `-e`:

| Variable | Default | Description |
|----------|---------|-------------|
| `scan_mode` | `probe` | `probe` or `passive` |
| `scan_target` | `{{ ansible_default_ipv4.address }}` | Target to scan |
| `scan_ports` | `22,443,3389` | Comma-separated ports |
| `scan_timeout` | `5` | Connection timeout (seconds) |
| `scan_workers` | `10` | Parallel workers |

## Performance

**Typical execution time per host:**
- Temp setup: ~5 seconds
- Pip install: ~30-60 seconds (depends on internet)
- Scan: ~10-30 seconds (depends on target)
- Cleanup: ~2 seconds
- **Total:** ~1-2 minutes

**Optimization:**
- Run in parallel: `-f 10` (10 hosts simultaneously)
- Reduce timeout: `-e "scan_timeout=3"`
- Fewer ports: `-e "scan_ports=22,443"`

**Scaling to 100+ hosts:**
- Use generated UPCE inventory
- Run in batches by label/group
- Consider Ansible Tower/AWX for distributed execution

## Security

**SSH Keys:**
- Use key-based authentication (no passwords)
- Limit key scope in `authorized_keys`

**Cleanup Guaranteed:**
- Uses Ansible `always:` block
- Even if scan fails, temp directory removed
- Verify with playbook `--check` mode

**Results Security:**
- Stored on control machine only
- Contains network topology info
- Secure `ansible/results/` directory

## Troubleshooting

### Python Not Found

**Error:** `Python 3 is required but not found`

**Solution:**
```bash
ansible -i inventory.ini scan_targets -m package \
  -a "name=python3 state=present" \
  --become
```

### SSH Connection Failed

**Error:** `Failed to connect to the host via ssh`

**Solution:**
```bash
# Test SSH manually
ssh user@remote-host

# Copy SSH key if needed
ssh-copy-id user@remote-host
```

### Pip Install Fails (No Internet)

**Error:** `Could not find a version that satisfies the requirement`

**Solution:** Pre-download and copy dependencies (see ansible/README.md for details)

### Cleanup Failed

**Error:** `Temporary directory STILL EXISTS`

**Solution:** Manual cleanup:
```bash
ansible -i inventory.ini scan_targets -m shell \
  -a "rm -rf /tmp/quantum-sniffer-*"
```

## Comparison: Ansible vs. Standalone Binary

| Feature | Ansible (Option 1) | Standalone Binary (Option 2) |
|---------|-------------------|------------------------------|
| Installation on remote | None (temp venv) | None (single binary) |
| Execution time | ~1-2 min/host | ~30 sec/host |
| Internet needed | Yes (pip) | No |
| Binary size | N/A | ~50-100 MB |
| Maintenance | Easy | Rebuild per architecture |
| **Recommendation** | **General use** | High-speed/offline networks |

## Advanced Usage

### Custom Playbook Variables

Set per-host in inventory:

```ini
[production]
web-prod-1 ansible_host=10.1.1.50 scan_ports=80,443,8443
db-prod-1 ansible_host=10.1.1.100 scan_ports=3306,5432
```

### Ansible Vault for Credentials

```bash
# Create vault
ansible-vault create vault.yml

# Add variables
ansible_become_password: your-password

# Use vault
ansible-playbook -i inventory.ini run-quantum-sniffer.yml \
  --ask-vault-pass
```

### Verbose Output

```bash
# Standard verbose
ansible-playbook -i inventory.ini run-quantum-sniffer.yml -v

# Debug level
ansible-playbook -i inventory.ini run-quantum-sniffer.yml -vvv
```

## Complete Workflow Example

```bash
#!/bin/bash
# Complete scan and reporting workflow

cd ~/quantum-sniffer/ansible

# 1. Generate inventory from UPCE
./generate-inventory-from-upce.py > inventory-from-upce.ini

# 2. Test connectivity
ansible -i inventory-from-upce.ini scan_targets -m ping

# 3. Scan all hosts
ansible-playbook -i inventory-from-upce.ini run-quantum-sniffer.yml -f 10

# 4. Generate compliance report
./examples/bulk-compliance-check.sh

# 5. Label in Illumio (if configured)
if [ -n "$ILLUMIO_PCE_HOST" ]; then
  ./examples/scan-and-label.sh
fi

# 6. View results
echo "Results in: $(pwd)/results/"
ls -lh results/
```

## Documentation

- **ansible/README.md** - Detailed usage guide
- **run-quantum-sniffer.yml** - Main playbook (well-commented)
- **examples/*.sh** - Pre-built workflow scripts
- **This file** - Quick reference

## Support

- **Ansible docs:** https://docs.ansible.com/
- **Quantum-sniffer:** See main README.md
- **UPCE integration:** See ~/back-end/README.md

## License

GNU General Public License v3.0 (same as quantum-sniffer)

---

**Summary:** Ansible provides zero-install remote execution of quantum-sniffer with guaranteed cleanup. Perfect for UPCE environments where you want to scan workloads without permanently modifying them.
