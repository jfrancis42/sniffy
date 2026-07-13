#!/usr/bin/env python3
"""
Example: Illumio PCE Integration

⚠️ WARNING: This integration is UNTESTED. It has been implemented based on
Illumio SDK documentation but has not been validated against a live PCE
environment. Test in a non-production environment first.

This script demonstrates how to:
1. Scan workloads for PQ crypto support
2. Label them in Illumio PCE with pqc status
3. Generate a compliance report

Prerequisites:
- pip install illumio
- Set ILLUMIO_PCE_HOST, ILLUMIO_API_KEY, ILLUMIO_API_SECRET in environment
"""

import sys
from quantum_sniffer.integrations.illumio import IllumioIntegration
from quantum_sniffer.lib import probe_target


def example_1_initialize_all_workloads():
    """Initialize all workloads with pqc=unknown if not labeled."""
    print("=" * 80)
    print("Example 1: Initialize All Workloads")
    print("=" * 80)
    print()

    illumio = IllumioIntegration()

    # Get current status
    summary = illumio.get_workload_summary()
    print(f"Total workloads: {summary['total']}")
    print(f"Without PQC label: {summary['by_pqc_status']['not_labeled']}")
    print()

    if summary['by_pqc_status']['not_labeled'] == 0:
        print("✓ All workloads already have PQC labels")
        return

    # Initialize (dry run first)
    print("Running dry-run...")
    result = illumio.initialize_all_workloads_pqc_unknown(force=True, dry_run=True)
    print(f"Would initialize {len(result['workloads'])} workloads")
    print()

    response = input("Proceed with actual initialization? (yes/no): ")
    if response.lower() == 'yes':
        result = illumio.initialize_all_workloads_pqc_unknown(force=True, dry_run=False)
        print(f"✓ Initialized {result['workloads_updated']} workloads")
    else:
        print("Skipped.")
    print()


def example_2_scan_and_label_workload(ip_address, ports):
    """Scan a single workload and update its PQC label."""
    print("=" * 80)
    print(f"Example 2: Scan and Label Workload {ip_address}")
    print("=" * 80)
    print()

    illumio = IllumioIntegration()

    # Find workload first
    print(f"Looking up workload with IP {ip_address}...")
    workload = illumio.find_workload_by_ip(ip_address)
    if not workload:
        print(f"ERROR: No workload found with IP {ip_address}")
        return

    print(f"Found workload: {workload.name}")
    current_status = illumio.get_workload_pqc_label(workload)
    print(f"Current PQC status: {current_status or 'not labeled'}")
    print()

    # Probe for PQ support
    print(f"Probing {ip_address} ports {ports}...")
    results = probe_target(ip_address, ports=ports, timeout=5.0)

    # Determine PQC status from results
    open_results = [r for r in results if r.status.value == "open"]
    if not open_results:
        print(f"No open ports found on {ip_address}")
        return

    # Use the first open port's PQ status
    pqc_value = open_results[0].post_quantum_secure.lower()
    if pqc_value not in ['yes', 'hybrid', 'no', 'unknown']:
        pqc_value = 'unknown'

    print(f"Detected PQC status: {pqc_value}")
    print()

    # Update label
    print("Updating Illumio label...")
    result = illumio.update_workload_pqc_label(
        ip_address=ip_address,
        pqc_value=pqc_value,
        dry_run=False
    )

    print("✓ Label updated")
    print(f"  Previous: {result['previous_value'] or 'none'}")
    print(f"  New:      {result['new_value']}")
    print()


def example_3_bulk_scan_and_label(ip_addresses, ports):
    """Scan multiple workloads and label them all."""
    print("=" * 80)
    print(f"Example 3: Bulk Scan and Label ({len(ip_addresses)} workloads)")
    print("=" * 80)
    print()

    illumio = IllumioIntegration()

    for ip in ip_addresses:
        print(f"Processing {ip}...")

        # Probe
        results = probe_target(ip, ports=ports, timeout=3.0)
        open_results = [r for r in results if r.status.value == "open"]

        if not open_results:
            print(f"  ⚠️  No open ports, skipping")
            continue

        # Determine PQC status
        pqc_value = open_results[0].post_quantum_secure.lower()
        if pqc_value not in ['yes', 'hybrid', 'no', 'unknown']:
            pqc_value = 'unknown'

        # Update label
        try:
            result = illumio.update_workload_pqc_label(ip, pqc_value, dry_run=False)
            print(f"  ✓ {result['workload_name']}: {pqc_value}")
        except ValueError as e:
            print(f"  ⚠️  {e}")

    print()
    print("✓ Bulk labeling complete")
    print()


def example_4_compliance_report():
    """Generate a compliance report from PQC labels."""
    print("=" * 80)
    print("Example 4: Compliance Report")
    print("=" * 80)
    print()

    illumio = IllumioIntegration()
    summary = illumio.get_workload_summary()

    print("PQC Compliance Report")
    print("=" * 80)
    print()

    # Summary statistics
    total = summary['total']
    by_status = summary['by_pqc_status']

    print(f"Total Workloads: {total}")
    print()
    print("By PQC Status:")
    print(f"  Post-Quantum (Yes):     {by_status['yes']:4d} ({by_status['yes']/total*100:.1f}%)")
    print(f"  Hybrid (PQ+Classical):  {by_status['hybrid']:4d} ({by_status['hybrid']/total*100:.1f}%)")
    print(f"  Classical Only (No):    {by_status['no']:4d} ({by_status['no']/total*100:.1f}%)")
    print(f"  Unknown:                {by_status['unknown']:4d} ({by_status['unknown']/total*100:.1f}%)")
    print(f"  Not Labeled:            {by_status['not_labeled']:4d} ({by_status['not_labeled']/total*100:.1f}%)")
    print()

    # Compliance calculation
    secure_count = by_status['yes'] + by_status['hybrid']
    labeled_count = total - by_status['not_labeled']

    if labeled_count > 0:
        compliance_pct = (secure_count / labeled_count) * 100
        print(f"Compliance Rate: {secure_count}/{labeled_count} ({compliance_pct:.1f}%)")
    print()

    # List quantum-vulnerable workloads
    vulnerable = [w for w in summary['workloads'] if w['pqc_status'] == 'no']
    if vulnerable:
        print(f"Quantum-Vulnerable Workloads ({len(vulnerable)}):")
        print("-" * 80)
        for w in vulnerable[:10]:  # Show first 10
            ips = ', '.join(w['ip_addresses']) if w['ip_addresses'] else 'no IP'
            print(f"  {w['name']:30s} {ips}")
        if len(vulnerable) > 10:
            print(f"  ... and {len(vulnerable) - 10} more")
    print()


def example_5_query_specific_workload(workload_name):
    """Query PQC status of a specific workload by name."""
    print("=" * 80)
    print(f"Example 5: Query Workload '{workload_name}'")
    print("=" * 80)
    print()

    illumio = IllumioIntegration()
    summary = illumio.get_workload_summary()

    # Find workload by name
    workload_info = None
    for w in summary['workloads']:
        if w['name'] == workload_name:
            workload_info = w
            break

    if not workload_info:
        print(f"Workload '{workload_name}' not found")
        return

    print(f"Workload: {workload_info['name']}")
    print(f"Hostname: {workload_info['hostname'] or 'N/A'}")
    print(f"IP Addresses: {', '.join(workload_info['ip_addresses']) or 'none'}")
    print(f"PQC Status: {workload_info['pqc_status']}")
    print()

    status = workload_info['pqc_status']
    if status == 'yes':
        print("✓ This workload is quantum-safe")
    elif status == 'hybrid':
        print("⚠️  This workload supports PQ but also classical (transition mode)")
    elif status == 'no':
        print("❌ This workload is quantum-vulnerable (classical crypto only)")
    elif status == 'unknown':
        print("❓ This workload has not been scanned yet")
    else:
        print("❓ This workload does not have a PQC label")
    print()


if __name__ == '__main__':
    print()
    print("=" * 80)
    print("Quantum-Sniffer + Illumio PCE Integration Examples")
    print("=" * 80)
    print()

    # Check connection
    try:
        illumio = IllumioIntegration()
        print("✓ Connected to Illumio PCE")
        print()
    except Exception as e:
        print(f"ERROR: Could not connect to Illumio PCE: {e}")
        print()
        print("Make sure these environment variables are set:")
        print("  ILLUMIO_PCE_HOST")
        print("  ILLUMIO_API_KEY")
        print("  ILLUMIO_API_SECRET")
        sys.exit(1)

    # Run examples (uncomment the ones you want to run)

    # Example 1: Initialize all workloads (CAUTION: modifies all unlabeled workloads)
    # example_1_initialize_all_workloads()

    # Example 2: Scan and label a single workload
    # Replace with an actual IP from your environment
    # example_2_scan_and_label_workload('10.1.1.50', [22, 443])

    # Example 3: Bulk scan and label multiple workloads
    # Replace with actual IPs from your environment
    # example_3_bulk_scan_and_label(['10.1.1.50', '10.1.1.51', '10.1.1.52'], [22, 443])

    # Example 4: Generate compliance report
    example_4_compliance_report()

    # Example 5: Query specific workload
    # Replace with an actual workload name from your environment
    # example_5_query_specific_workload('web-server-01')

    print("=" * 80)
    print("Examples complete")
    print("=" * 80)
    print()
