"""
Application Services - Business logic for application lifecycle management.
"""
import logging
from datetime import timedelta
from typing import Dict, Any, Set
from django.db import transaction
from django.utils import timezone

from apps.proxmox.services import ProxmoxService, ProxmoxError
from apps.proxmox.models import ProxmoxHost
from apps.applications.models import Application
from apps.applications.port_manager import PortManagerService

logger = logging.getLogger(__name__)


class ApplicationService:
    """
    Service layer for application business logic.
    """

    @staticmethod
    def reconcile_applications() -> Dict[str, Any]:
        """
        Reconcile applications in the database with actual containers in Proxmox.
        
        DOCTRINE POINT #2: INTELLIGENT RECONCILIATION SERVICE
        
        This method identifies and cleans up "orphan" applications - database records
        that reference containers (VMIDs) that no longer exist in Proxmox. It now
        operates with STATE AWARENESS:
        
        - EXPECTED orphans (status='removing' or 'error'): Logged as INFO, cleaned silently
        - ANOMALOUS orphans (status='running', 'stopped', etc.): Logged as CRITICAL WARNING,
          Sentry alert triggered, indicates manual external deletion
        
        The reconciliation process:
        1. Fetches all LXC containers from all Proxmox hosts and nodes
        2. Compares with database applications that have a VMID assigned
        3. Identifies orphans (apps with VMIDs not found in Proxmox)
        4. Analyzes orphan states to determine severity
        5. Performs SOFT cleanup (releases ports, deletes records only)

        Returns:
            Dictionary with reconciliation results:
                - success: bool
                - total_apps: int (total apps with VMIDs in database)
                - real_vmids_count: int (total VMIDs found in Proxmox)
                - orphans_found: int (orphan apps found)
                - expected_orphans: int (orphans in transient states)
                - anomalous_orphans: int (orphans in stable states - CRITICAL)
                - orphans_purged: int (orphan apps successfully deleted)
                - errors: list (any errors during cleanup)
        """
        logger.info("=" * 100)
        logger.info("[RECONCILIATION] Starting INTELLIGENT application reconciliation process...")
        logger.info("[RECONCILIATION] DOCTRINE: State-aware cleanup with anomaly detection")
        logger.info("=" * 100)

        orphans_found = 0
        expected_orphans = 0  # Apps in 'removing' or 'error' state
        anomalous_orphans = 0  # Apps in stable states - CRITICAL!
        orphans_purged = 0
        errors = []

        try:
            # STEP 1: Collect all real VMIDs from all Proxmox hosts
            logger.info("[RECONCILIATION] STEP 1/5: Fetching all LXC containers from Proxmox...")
            real_vmids = set()

            # Get all active Proxmox hosts
            hosts = ProxmoxHost.objects.filter(is_active=True)
            logger.info(f"[RECONCILIATION] Found {hosts.count()} active Proxmox host(s)")

            for host in hosts:
                try:
                    logger.info(f"[RECONCILIATION]   → Scanning host: {host.name} (ID: {host.id})")
                    proxmox_service = ProxmoxService(host_id=host.id)

                    # Get all nodes for this host
                    nodes_data = proxmox_service.get_nodes()
                    logger.info(f"[RECONCILIATION]     → Found {len(nodes_data)} node(s)")

                    for node_data in nodes_data:
                        node_name = node_data.get('node')
                        try:
                            logger.info(f"[RECONCILIATION]       → Scanning node: {node_name}")

                            # Get all LXC containers on this node
                            containers = proxmox_service.get_lxc_containers(node_name)
                            logger.info(f"[RECONCILIATION]         → Found {len(containers)} LXC container(s)")

                            # Collect VMIDs
                            for container in containers:
                                vmid = container.get('vmid')
                                if vmid:
                                    real_vmids.add(int(vmid))

                        except Exception as node_error:
                            logger.error(
                                f"[RECONCILIATION]       ✗ Failed to scan node {node_name}: {node_error}"
                            )
                            errors.append(f"Node {node_name}: {str(node_error)}")

                except Exception as host_error:
                    logger.error(f"[RECONCILIATION]   ✗ Failed to scan host {host.name}: {host_error}")
                    errors.append(f"Host {host.name}: {str(host_error)}")

            logger.info(f"[RECONCILIATION] ✓ STEP 1 COMPLETE: Found {len(real_vmids)} real VMIDs across all hosts")
            logger.info(f"[RECONCILIATION]   Real VMIDs: {sorted(real_vmids)}")

            # STEP 2: Get all applications with assigned VMIDs from database
            logger.info("[RECONCILIATION] STEP 2/5: Fetching applications from database...")
            apps_with_vmids = Application.objects.filter(lxc_id__isnull=False)
            total_apps = apps_with_vmids.count()
            logger.info(f"[RECONCILIATION] ✓ Found {total_apps} application(s) with assigned VMIDs")

            if total_apps == 0:
                logger.info("[RECONCILIATION] No applications with VMIDs found - nothing to reconcile")
                return {
                    'success': True,
                    'total_apps': 0,
                    'real_vmids_count': len(real_vmids),
                    'orphans_found': 0,
                    'expected_orphans': 0,
                    'anomalous_orphans': 0,
                    'orphans_purged': 0,
                    'errors': errors
                }

            # STEP 3: Identify orphan applications
            logger.info("[RECONCILIATION] STEP 3/5: Identifying orphan applications...")
            orphan_apps = []

            for app in apps_with_vmids:
                if app.lxc_id not in real_vmids:
                    orphan_apps.append(app)

            orphans_found = len(orphan_apps)
            logger.info(f"[RECONCILIATION] ✓ STEP 3 COMPLETE: Found {orphans_found} orphan application(s)")

            if orphans_found == 0:
                logger.info("[RECONCILIATION] ✅ No orphans found - database is in sync with Proxmox")
                return {
                    'success': True,
                    'total_apps': total_apps,
                    'real_vmids_count': len(real_vmids),
                    'orphans_found': 0,
                    'expected_orphans': 0,
                    'anomalous_orphans': 0,
                    'orphans_purged': 0,
                    'errors': errors
                }

            # STEP 4: DOCTRINE - Analyze orphan states (expected vs anomalous)
            logger.info(f"[RECONCILIATION] STEP 4/5: ANALYZING ORPHAN STATES (State-Aware Classification)...")
            
            # States that are EXPECTED to become orphans
            EXPECTED_ORPHAN_STATES = ['removing', 'error']
            
            # States that should NOT normally be orphans (indicates external deletion)
            ANOMALOUS_ORPHAN_STATES = ['running', 'stopped', 'deploying', 'cloning', 'updating']
            
            for app in orphan_apps:
                if app.status in EXPECTED_ORPHAN_STATES:
                    # EXPECTED: App was already in a failure/removal state
                    expected_orphans += 1
                    logger.info(
                        f"[RECONCILIATION]   ✓ EXPECTED ORPHAN: '{app.hostname}' "
                        f"(VMID: {app.lxc_id}, Status: {app.status}) - "
                        f"Container removal expected"
                    )
                else:
                    # ANOMALOUS: App was in a stable/active state but container is gone!
                    anomalous_orphans += 1
                    logger.critical(
                        f"[RECONCILIATION]   🚨 ANOMALOUS ORPHAN DETECTED: '{app.hostname}' "
                        f"(VMID: {app.lxc_id}, Status: {app.status}) - "
                        f"Container was MANUALLY DELETED from Proxmox!"
                    )
                    
                    # Send high-severity alert to Sentry
                    try:
                        import sentry_sdk
                        sentry_sdk.capture_message(
                            f"CRITICAL: Container manually deleted from Proxmox",
                            level='error',
                            extras={
                                'app_id': app.id,
                                'app_hostname': app.hostname,
                                'app_status': app.status,
                                'vmid': app.lxc_id,
                                'node': app.node,
                                'host_id': app.host_id,
                                'severity': 'CRITICAL',
                                'anomaly_type': 'external_deletion',
                                'expected_states': EXPECTED_ORPHAN_STATES,
                                'actual_state': app.status
                            }
                        )
                        logger.info(f"[RECONCILIATION]     → Sentry alert triggered for {app.hostname}")
                    except Exception as sentry_error:
                        logger.warning(f"[RECONCILIATION]     → Could not send Sentry alert: {sentry_error}")
            
            logger.info(f"[RECONCILIATION] ✓ STEP 4 COMPLETE: Orphan Analysis")
            logger.info(f"[RECONCILIATION]   - Expected orphans (removing/error): {expected_orphans}")
            logger.info(f"[RECONCILIATION]   - Anomalous orphans (stable states): {anomalous_orphans} 🚨")

            # STEP 5: Clean up orphan applications (SOFT cleanup - DB only)
            logger.info(f"[RECONCILIATION] STEP 5/5: Performing SOFT cleanup of {orphans_found} orphan(s)...")
            logger.info(f"[RECONCILIATION] Strategy: Release ports and remove DB records only (no Proxmox operations)")
            port_manager = PortManagerService()

            for app in orphan_apps:
                try:
                    is_anomalous = app.status not in EXPECTED_ORPHAN_STATES
                    orphan_type = "ANOMALOUS" if is_anomalous else "EXPECTED"
                    
                    logger.info(
                        f"[RECONCILIATION]   → Purging {orphan_type} orphan: {app.hostname} "
                        f"(ID: {app.id}, VMID: {app.lxc_id}, Status: {app.status})"
                    )

                    with transaction.atomic():
                        # SOFT CLEANUP: Only touch our database and port allocations
                        # Never attempt to interact with Proxmox (container is already gone)
                        
                        # Release ports if assigned
                        if app.public_port or app.internal_port:
                            logger.info(
                                f"[RECONCILIATION]     → Releasing ports: "
                                f"public={app.public_port}, internal={app.internal_port}"
                            )
                            port_manager.release_ports(app.public_port, app.internal_port)

                        # Delete related deployment logs (cascade handled by foreign key)
                        # Delete related backups if any (cascade handled by foreign key)

                        # Delete the application record
                        app_hostname = app.hostname
                        app.delete()

                        logger.info(f"[RECONCILIATION]     ✓ Successfully purged: {app_hostname}")
                        orphans_purged += 1

                except Exception as cleanup_error:
                    logger.error(
                        f"[RECONCILIATION]     ✗ Failed to purge {app.hostname}: {cleanup_error}",
                        exc_info=True
                    )
                    errors.append(f"Cleanup {app.hostname}: {str(cleanup_error)}")

            logger.info(f"[RECONCILIATION] ✓ STEP 5 COMPLETE: Purged {orphans_purged}/{orphans_found} orphan(s)")

            # Final summary
            logger.info("=" * 100)
            logger.info("[RECONCILIATION] ✅ INTELLIGENT RECONCILIATION COMPLETE")
            logger.info(f"[RECONCILIATION] Summary:")
            logger.info(f"[RECONCILIATION]   - Total apps in database: {total_apps}")
            logger.info(f"[RECONCILIATION]   - Real VMIDs in Proxmox: {len(real_vmids)}")
            logger.info(f"[RECONCILIATION]   - Orphans found: {orphans_found}")
            logger.info(f"[RECONCILIATION]     • Expected orphans (removing/error): {expected_orphans}")
            logger.info(f"[RECONCILIATION]     • Anomalous orphans (stable states): {anomalous_orphans} {'🚨' if anomalous_orphans > 0 else ''}")
            logger.info(f"[RECONCILIATION]   - Orphans purged: {orphans_purged}")
            logger.info(f"[RECONCILIATION]   - Errors: {len(errors)}")
            if anomalous_orphans > 0:
                logger.info(f"[RECONCILIATION]   ⚠️  WARNING: {anomalous_orphans} anomalous orphan(s) detected - manual investigation recommended")
            logger.info("=" * 100)

            return {
                'success': True,
                'total_apps': total_apps,
                'real_vmids_count': len(real_vmids),
                'orphans_found': orphans_found,
                'expected_orphans': expected_orphans,
                'anomalous_orphans': anomalous_orphans,
                'orphans_purged': orphans_purged,
                'errors': errors
            }

        except Exception as e:
            logger.error("=" * 100)
            logger.error(f"[RECONCILIATION] ❌ RECONCILIATION FAILED: {e}")
            logger.error("=" * 100)
            logger.exception("[RECONCILIATION] Full traceback:")

            return {
                'success': False,
                'total_apps': 0,
                'real_vmids_count': 0,
                'orphans_found': orphans_found,
                'expected_orphans': expected_orphans,
                'anomalous_orphans': anomalous_orphans,
                'orphans_purged': orphans_purged,
                'errors': errors + [f"Fatal error: {str(e)}"]
            }

    @staticmethod
    def cleanup_stuck_applications() -> Dict[str, Any]:
        """
        Clean up applications stuck in transitional states for too long.

        This "janitor" service scans for applications that have been in transitional
        states (deploying, cloning, removing, restoring) for longer than the allowed
        timeout period. These "zombie" applications are marked as error to prevent
        them from being stuck in limbo indefinitely.

        The reconciliation service will handle actual cleanup of orphaned containers.
        This service focuses on ending the transitional state safely.

        Transitional states monitored:
        - deploying: New deployment in progress
        - cloning: Clone operation in progress
        - removing: Deletion in progress
        - updating: Update operation in progress

        Returns:
            Dictionary with cleanup results:
                - success: bool
                - total_transitional: int (apps currently in transitional states)
                - stuck_found: int (stuck apps identified)
                - stuck_marked_error: int (stuck apps marked as error)
                - errors: list (any errors during cleanup)
        """
        # Configuration
        STUCK_TIMEOUT = timedelta(hours=1)  # Apps stuck for more than 1 hour
        TRANSITIONAL_STATES = ['deploying', 'cloning', 'removing', 'updating']

        logger.info("=" * 100)
        logger.info("[JANITOR] Starting stuck applications cleanup process...")
        logger.info(f"[JANITOR] Timeout threshold: {STUCK_TIMEOUT}")
        logger.info(f"[JANITOR] Monitored states: {TRANSITIONAL_STATES}")
        logger.info("=" * 100)

        stuck_found = 0
        stuck_marked_error = 0
        errors = []

        try:
            # Calculate the cutoff time
            cutoff_time = timezone.now() - STUCK_TIMEOUT

            # Find all apps in transitional states
            transitional_apps = Application.objects.filter(status__in=TRANSITIONAL_STATES)
            total_transitional = transitional_apps.count()

            logger.info(f"[JANITOR] STEP 1/2: Found {total_transitional} application(s) in transitional states")

            if total_transitional == 0:
                logger.info("[JANITOR] ✅ No transitional applications found - system is healthy")
                return {
                    'success': True,
                    'total_transitional': 0,
                    'stuck_found': 0,
                    'stuck_marked_error': 0,
                    'errors': []
                }

            # Find stuck applications (state_changed_at older than cutoff)
            stuck_apps = transitional_apps.filter(state_changed_at__lt=cutoff_time)
            stuck_found = stuck_apps.count()

            logger.info(f"[JANITOR] STEP 2/2: Found {stuck_found} stuck application(s)")

            if stuck_found == 0:
                logger.info("[JANITOR] ✅ No stuck applications found - all transitions are within timeout")
                return {
                    'success': True,
                    'total_transitional': total_transitional,
                    'stuck_found': 0,
                    'stuck_marked_error': 0,
                    'errors': []
                }

            # Mark stuck applications as error
            for app in stuck_apps:
                try:
                    time_stuck = timezone.now() - app.state_changed_at
                    hours_stuck = int(time_stuck.total_seconds() / 3600)
                    minutes_stuck = int((time_stuck.total_seconds() % 3600) / 60)

                    logger.warning(
                        f"[JANITOR]   ⚠️  STUCK APP FOUND: '{app.hostname}' "
                        f"(ID: {app.id}, Status: {app.status}) - "
                        f"Stuck for {hours_stuck}h {minutes_stuck}m"
                    )

                    with transaction.atomic():
                        # Re-fetch to avoid race conditions
                        app_to_update = Application.objects.select_for_update().get(pk=app.pk)

                        # Only update if still in a transitional state
                        if app_to_update.status in TRANSITIONAL_STATES:
                            old_status = app_to_update.status
                            app_to_update.status = 'error'
                            app_to_update.save(update_fields=['status'])

                            logger.info(
                                f"[JANITOR]     ✓ Marked as ERROR: {app.hostname} "
                                f"(was: {old_status}, stuck since: {app.state_changed_at})"
                            )
                            stuck_marked_error += 1

                            # Log to deployment logs
                            from apps.applications.models import DeploymentLog
                            DeploymentLog.objects.create(
                                application=app_to_update,
                                level='error',
                                message=f'Operation timed out after {hours_stuck}h {minutes_stuck}m. '
                                       f'Previous state: {old_status}',
                                step='janitor_cleanup'
                            )
                        else:
                            logger.info(
                                f"[JANITOR]     ⊘ Skipped (status changed): {app.hostname} "
                                f"(now: {app_to_update.status})"
                            )

                except Exception as cleanup_error:
                    logger.error(
                        f"[JANITOR]     ✗ Failed to mark {app.hostname} as error: {cleanup_error}",
                        exc_info=True
                    )
                    errors.append(f"Cleanup {app.hostname}: {str(cleanup_error)}")

            # Final summary
            logger.info("=" * 100)
            logger.info("[JANITOR] ✅ CLEANUP COMPLETE")
            logger.info(f"[JANITOR] Summary:")
            logger.info(f"[JANITOR]   - Total transitional apps: {total_transitional}")
            logger.info(f"[JANITOR]   - Stuck apps found: {stuck_found}")
            logger.info(f"[JANITOR]   - Stuck apps marked as error: {stuck_marked_error}")
            logger.info(f"[JANITOR]   - Errors: {len(errors)}")
            logger.info("=" * 100)

            return {
                'success': True,
                'total_transitional': total_transitional,
                'stuck_found': stuck_found,
                'stuck_marked_error': stuck_marked_error,
                'errors': errors
            }

        except Exception as e:
            logger.error("=" * 100)
            logger.error(f"[JANITOR] ❌ CLEANUP FAILED: {e}")
            logger.error("=" * 100)
            logger.exception("[JANITOR] Full traceback:")

            return {
                'success': False,
                'total_transitional': 0,
                'stuck_found': stuck_found,
                'stuck_marked_error': stuck_marked_error,
                'errors': errors + [f"Fatal error: {str(e)}"]
            }
