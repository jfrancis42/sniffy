# Illumio PCE Integration

> **⚠️ WARNING: This feature is UNTESTED in this version (v0.4.1). It has been implemented but not yet validated against a live Illumio PCE environment. Use with caution in production. Test thoroughly in a development/staging environment first.**

Quantum-sniffer can integrate with Illumio Policy Compute Engine (PCE) to automatically label workloads with their post-quantum cryptography (PQC) status.

## Overview

The integration adds a `pqc` label to Illumio workloads with one of these values:

- `yes` - Workload supports pure post-quantum cryptography
- `hybrid` - Workload supports hybrid PQ+classical (transition mode)
- `no` - Workload uses classical crypto only (quantum-vulnerable)
- `unknown` - PQC status not yet determined

This enables you to:
- Track quantum-readiness across your infrastructure
- Build Illumio policies based on PQC status
- Generate compliance reports from PCE label data
- Visualize quantum-vulnerable workloads in Illumination

## Prerequisites

### 1. Install Illumio Python SDK

```bash
pip install illumio
```

### 2. Configure PCE Credentials

Create a `.env` file in the directory where you'll run quantum-sniffer:

```bash
# .env
ILLUMIO_PCE_HOST=pce.example.com
ILLUMIO_PCE_PORT=443
ILLUMIO_ORG_ID=1
ILLUMIO_API_KEY=api_1234567890abcdef
ILLUMIO_API_SECRET=1234567890abcdef1234567890abcdef
```

Or export as environment variables:

```bash
export ILLUMIO_PCE_HOST=pce.example.com
export ILLUMIO_API_KEY=api_1234567890abcdef
export ILLUMIO_API_SECRET=1234567890abcdef1234567890abcdef
```

### 3. Create API Credentials in PCE

1. Log into Illumio PCE web interface
2. Navigate to: Settings → API Keys
3. Create new API key with appropriate permissions:
   - **Read**: `workloads`, `labels`
   - **Write**: `workloads`, `labels`
4. Save the API key and secret to your `.env` file

## Usage

### Initialize All Workloads

Before scanning, initialize all workloads without a `pqc` label to `unknown`:

```bash
quantum-sniffer --illumio-init
```

**Output:**
```
[*] Illumio PQC Label Initialization

[*] Fetching current workload status...
[*] Total workloads: 247
[*] Without PQC label: 247

⚠️  WARNING: This operation will add 'pqc=unknown' label to
⚠️  247 workloads that don't have a PQC label.

Type 'yes' to proceed: yes

[*] Initializing workloads...

✓ Initialization complete
  Workloads updated: 247
```

**Skip confirmation** (use with caution):
```bash
quantum-sniffer --illumio-init --yes
```

### Scan and Label a Single Workload

Probe a workload and automatically update its PQC label:

```bash
quantum-sniffer --probe 10.1.1.50 --ports 22,443 --illumio-label 10.1.1.50
```

**Output:**
```
[*] quantum-sniffer - Active Probe Mode
[*] Target: 10.1.1.50
[*] Ports: 22, 443
[*] Timeout: 5.0s
[*] Workers: 10

Probing 10.1.1.50 (2 ports)...

================================================================================
PROBE RESULTS
================================================================================

✓ 10.1.1.50:22     open       🔒 Hybrid      
✓ 10.1.1.50:443    open       ⚠️  No         TLSv1.3, TLS_AES_256_GCM_SHA384

================================================================================
Summary: 2/2 ports open
         1/2 with PQ crypto support
================================================================================

[*] Illumio Workload Labeling
[*] IP Address: 10.1.1.50
[*] PQC Status: hybrid (from probe)

✓ Workload labeled successfully
  Workload: web-server-01
  Previous: unknown
  New:      hybrid
  HREF:     /orgs/1/workloads/12345678-90ab-cdef-1234-567890abcdef
```

### Scan Multiple Workloads

Use a script to scan and label multiple workloads:

```bash
#!/bin/bash
# scan-and-label.sh

for ip in 10.1.1.{50..60}; do
  echo "Scanning $ip..."
  quantum-sniffer --probe "$ip" --ports 22,443 --illumio-label "$ip" --quiet
  echo ""
done
```

### View PQC Label Summary

See the current PQC status across all workloads:

```bash
quantum-sniffer --illumio-summary
```

**Output:**
```
[*] Illumio PQC Label Summary

[*] Fetching workload data...

================================================================================
PQC Label Summary
================================================================================
Total Workloads: 247

By PQC Status:
  Yes:          23  (Post-quantum secure)
  Hybrid:       89  (PQ + classical)
  No:           67  (Classical only - vulnerable)
  Unknown:      65  (Not yet scanned)
  Not Labeled:   3  (No PQC label)

Labeling Progress: 244/247 (98.8%)
PQ-Capable (of labeled): 112/244 (45.9%)
================================================================================
```

## Workflow Examples

### Complete Infrastructure Scan

```bash
#!/bin/bash
# complete-scan.sh - Scan entire network and label workloads

echo "Step 1: Initialize all workloads"
quantum-sniffer --illumio-init --yes

echo ""
echo "Step 2: Scan production network"
quantum-sniffer --probe 10.1.0.0/23 --ports 22,443 \
  --output-json scan-results.json \
  --output-markdown scan-report.md \
  --workers 50 \
  --timeout 3

echo ""
echo "Step 3: Label workloads from scan results"
jq -r '.results[] | select(.status == "open") | .target_ip' scan-results.json | \
  sort -u | while read ip; do
    echo "Labeling $ip..."
    quantum-sniffer --probe "$ip" --ports 22,443 --illumio-label "$ip"
  done

echo ""
echo "Step 4: View summary"
quantum-sniffer --illumio-summary
```

### Incremental Updates

Scan new workloads added to PCE:

```bash
#!/bin/bash
# update-new-workloads.sh

# Get workloads with pqc=unknown
quantum-sniffer --illumio-summary > summary.txt

# Parse and scan (pseudo-code - adapt as needed)
# For each workload with pqc=unknown:
#   quantum-sniffer --probe <ip> --illumio-label <ip>
```

### Compliance Reporting

Generate a compliance report using PCE labels:

```python
#!/usr/bin/env python3
# compliance-report.py
import sys
sys.path.insert(0, '/home/upce/quantum-sniffer')

from quantum_sniffer.integrations.illumio import IllumioIntegration
import json

illumio = IllumioIntegration()
summary = illumio.get_workload_summary()

# Print CSV report
print("Workload Name,IP Address,PQC Status,Compliant")
for wl in summary['workloads']:
    name = wl['name']
    ips = ','.join(wl['ip_addresses'])
    status = wl['pqc_status']
    compliant = 'Yes' if status in ['yes', 'hybrid'] else 'No'
    print(f'"{name}","{ips}",{status},{compliant}')
```

## Python API

Use the integration in your own Python scripts:

```python
from quantum_sniffer.integrations.illumio import IllumioIntegration

# Connect to PCE
illumio = IllumioIntegration()

# Find workload by IP
workload = illumio.find_workload_by_ip('10.1.1.50')
if workload:
    print(f"Found: {workload.name}")

# Get current PQC status
current_status = illumio.get_workload_pqc_label(workload)
print(f"Current PQC status: {current_status}")

# Update PQC label
result = illumio.update_workload_pqc_label(
    ip_address='10.1.1.50',
    pqc_value='hybrid',
    dry_run=False
)
print(f"Updated {result['workload_name']}: {result['previous_value']} → {result['new_value']}")

# Initialize all workloads
result = illumio.initialize_all_workloads_pqc_unknown(force=True)
print(f"Initialized {result['workloads_updated']} workloads")

# Get summary
summary = illumio.get_workload_summary()
print(f"Total: {summary['total']}")
print(f"PQ-capable: {summary['by_pqc_status']['yes'] + summary['by_pqc_status']['hybrid']}")
```

## Building Illumio Policies with PQC Labels

Once workloads are labeled, use them in Illumio rulesets:

### Example 1: Enforce Encryption Gateways for Classical-Only Workloads

```json
{
  "name": "Classical Workloads - Gateway Required",
  "scopes": [
    [{"key": "pqc", "value": "no"}]
  ],
  "rules": [
    {
      "description": "Force traffic through encryption gateway",
      "providers": [{"label": {"key": "pqc", "value": "no"}}],
      "consumers": [{"actors": "ams"}],
      "ingress_services": [{"href": "/orgs/1/sec_policy/draft/services/1"}],
      "resolve_labels_as": {"consumers": ["workloads"]}
    }
  ]
}
```

### Example 2: Alert on Classical Connections Between High-Value Workloads

```json
{
  "name": "High-Value Classical Monitoring",
  "scopes": [
    [{"key": "env", "value": "production"}],
    [{"key": "criticality", "value": "high"}]
  ],
  "rules": [
    {
      "description": "Allow but log classical crypto connections",
      "providers": [{"label": {"key": "pqc", "value": "no"}}],
      "consumers": [{"label": {"key": "pqc", "value": "no"}}],
      "ingress_services": [{"href": "/orgs/1/sec_policy/draft/services/1"}],
      "sec_connect": false,
      "machine_auth": false
    }
  ]
}
```

### Example 3: Require PQ Crypto for Compliance Workloads

```json
{
  "name": "Compliance - Require PQ",
  "scopes": [
    [{"key": "compliance", "value": "pci-dss"}]
  ],
  "rules": [
    {
      "description": "Only allow PQ-capable connections",
      "providers": [
        {"label": {"key": "pqc", "value": "yes"}},
        {"label": {"key": "pqc", "value": "hybrid"}}
      ],
      "consumers": [{"actors": "ams"}],
      "ingress_services": [{"href": "/orgs/1/sec_policy/draft/services/1"}]
    }
  ]
}
```

## Troubleshooting

### Connection Errors

**Error:** `Could not connect to PCE`

**Solution:**
- Verify `ILLUMIO_PCE_HOST` is correct
- Check firewall rules allow HTTPS (port 443) to PCE
- Verify API credentials are valid
- Test connection: `curl -k https://$ILLUMIO_PCE_HOST/api/v2/health`

### Workload Not Found

**Error:** `No workload found with IP address: 10.1.1.50`

**Cause:** Workload doesn't exist in PCE or IP doesn't match

**Solution:**
- Check workload exists: Log into PCE → Workloads → search by IP
- Verify IP matches a workload interface or public_ip
- Check if workload uses different IP (multiple interfaces)

### Permission Errors

**Error:** `403 Forbidden`

**Cause:** API key lacks required permissions

**Solution:**
- API key needs `workloads:read`, `workloads:write`, `labels:read`, `labels:write`
- Recreate API key with correct scope
- Verify org_id is correct

### Label Already Exists with Different Value

The integration handles this automatically - it will update the existing PQC label value rather than creating a duplicate.

## Integration with UPCE

Combine quantum-sniffer's Illumio integration with UPCE for complete quantum-readiness tracking:

1. **UPCE inventory** → Quantum-sniffer probes → **Illumio labels**
2. **Illumio workloads** → Quantum-sniffer scans → **UPCE traffic analysis**

See `~/quantum-sniffer/ideas.md` section #3 for details on UPCE integration.

## Security Considerations

### API Key Protection

- Store API credentials in `.env` file (not in code)
- Add `.env` to `.gitignore`
- Use restrictive file permissions: `chmod 600 .env`
- Rotate API keys regularly
- Use separate API keys for different environments (dev/staging/prod)

### Audit Trail

All label changes are logged in Illumio PCE audit logs:
- Navigation: Settings → Auditing
- Filter by: Object Type = "Workload", Event = "Update"

### Least Privilege

Create dedicated API user for quantum-sniffer:
- Grant only required permissions
- Use read-only keys for summary/reporting
- Use read-write keys only for labeling operations

## FAQ

**Q: Can I use custom label keys instead of 'pqc'?**

A: Yes, edit `quantum_sniffer/integrations/illumio.py` and change `PQC_LABEL_KEY = 'pqc'` to your preferred key.

**Q: What happens if a workload has multiple IPs?**

A: The integration searches both interface IPs and public_ip. It will find the workload if any IP matches.

**Q: Can I bulk-label from a scan JSON file?**

A: Not yet, but you can write a script using the Python API. See "Python API" section above.

**Q: Does this work with Illumio Cloud (SaaS) or only on-prem PCE?**

A: Works with both. Set `ILLUMIO_PCE_HOST` to your Cloud PCE hostname (e.g., `customer.illum.io`).

**Q: What if I scan a port that's closed?**

A: The integration will error and not update the label. Only open ports with successful probes are labeled.

**Q: Can I scan and label container workloads?**

A: Yes, if the container has a PCE workload entry with an IP address.

## References

- [Illumio API Documentation](https://docs.illumio.com/core/latest/API/index.html)
- [Illumio Python SDK](https://github.com/illumio/illumio-py)
- [Quantum-Sniffer README](README.md)
- [UPCE Integration Ideas](ideas.md)
