"""
Proxmox service - Connection and node management
Adapted from v1.0 ProxmoxService with async support via Celery
"""
import logging
import shlex
from typing import List, Dict, Any, Optional
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException
from django.utils import timezone
from django.core.cache import cache
import paramiko

from .models import ProxmoxHost, ProxmoxNode

logger = logging.getLogger(__name__)


class ProxmoxError(Exception):
    """Custom exception for Proxmox API errors."""
    pass


class ProxmoxService:
    """
    Service layer for Proxmox API interactions.
    Supports multiple hosts and connection caching.
    """
    
    def __init__(self, host_id: Optional[int] = None):
        """
        Initialize Proxmox service.
        
        Args:
            host_id: Optional Proxmox host ID. If None, uses default host.
        """
        self.host_id = host_id
        self._client = None
    
    def get_host(self) -> ProxmoxHost:
        """Get the ProxmoxHost instance."""
        if self.host_id:
            return ProxmoxHost.objects.get(pk=self.host_id, is_active=True)
        else:
            # Get default host
            host = ProxmoxHost.objects.filter(is_default=True, is_active=True).first()
            if not host:
                # Fallback to any active host
                host = ProxmoxHost.objects.filter(is_active=True).first()
            if not host:
                raise ProxmoxError("No active Proxmox host configured")
            return host
    
    def get_client(self) -> ProxmoxAPI:
        """
        Get or create Proxmox API client.
        Uses caching for connection pooling.
        """
        if self._client is not None:
            return self._client
        
        host = self.get_host()
        cache_key = f"proxmox_client_{host.id}"
        
        # Try to get from cache
        client = cache.get(cache_key)
        if client:
            self._client = client
            return client
        
        # Create new connection
        try:
            client = ProxmoxAPI(
                host.host,
                backend='https',
                user=host.user,
                password=host.password,  # TODO: Decrypt password
                verify_ssl=host.verify_ssl,
                port=host.port
            )
            
            # Test connection
            client.version.get()
            
            # Update last_seen
            host.last_seen = timezone.now()
            host.save(update_fields=['last_seen'])
            
            # Cache for 5 minutes
            cache.set(cache_key, client, 300)
            self._client = client
            
            logger.info(f"Connected to Proxmox host: {host.name}")
            return client
            
        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "auth" in error_msg:
                raise ProxmoxError(f"Authentication failed for {host.name}: {e}")
            elif "connection" in error_msg or "refused" in error_msg:
                raise ProxmoxError(
                    f"Cannot connect to {host.name} at {host.host}:{host.port}. "
                    f"Please check that Proxmox is running and accessible."
                )
            elif "ssl" in error_msg or "certificate" in error_msg:
                raise ProxmoxError(
                    f"SSL certificate error for {host.name}. "
                    f"Consider disabling SSL verification for self-signed certificates."
                )
            else:
                raise ProxmoxError(f"Failed to connect to {host.name}: {e}")
    
    def test_connection(self) -> bool:
        """Test connection to Proxmox API."""
        try:
            client = self.get_client()
            client.version.get()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """
        Get list of all Proxmox nodes for this host.
        
        Returns:
            List of node information dictionaries
        """
        try:
            client = self.get_client()
            nodes_data = client.nodes.get()
            return nodes_data
        except Exception as e:
            raise ProxmoxError(f"Failed to get nodes: {e}")
    
    def sync_nodes(self) -> int:
        """
        Sync nodes from Proxmox API to database.
        
        Returns:
            Number of nodes synced
        """
        host = self.get_host()
        nodes_data = self.get_nodes()
        synced_count = 0
        
        for node_data in nodes_data:
            node, created = ProxmoxNode.objects.update_or_create(
                host=host,
                name=node_data.get('node'),
                defaults={
                    'status': node_data.get('status', 'unknown'),
                    'node_type': node_data.get('type', 'node'),
                    'cpu_count': node_data.get('maxcpu'),
                    'cpu_usage': node_data.get('cpu'),
                    'memory_total': node_data.get('maxmem'),
                    'memory_used': node_data.get('mem'),
                    'storage_total': node_data.get('maxdisk'),
                    'storage_used': node_data.get('disk'),
                    'uptime': node_data.get('uptime'),
                    'ip_address': node_data.get('ip'),
                    'pve_version': node_data.get('pveversion'),
                }
            )
            synced_count += 1
        
        logger.info(f"Synced {synced_count} nodes for host {host.name}")
        return synced_count
    
    def get_lxc_containers(self, node_name: str) -> List[Dict[str, Any]]:
        """
        Get all LXC containers on a specific node.
        
        Args:
            node_name: Name of the Proxmox node
            
        Returns:
            List of LXC container information
        """
        try:
            client = self.get_client()
            containers = client.nodes(node_name).lxc.get()
            return containers
        except Exception as e:
            raise ProxmoxError(f"Failed to get LXC containers for node {node_name}: {e}")
    
    def get_next_vmid(self) -> int:
        """
        Get the next available VMID from Proxmox.
        
        Returns:
            Next available VMID
        """
        try:
            client = self.get_client()
            return client.cluster.nextid.get()
        except Exception as e:
            raise ProxmoxError(f"Failed to get next VMID: {e}")
    
    def create_lxc(
        self,
        node_name: str,
        vmid: int,
        hostname: str,
        ostemplate: str,
        password: str,
        memory: int = 2048,
        cores: int = 2,
        disk_size: str = "8",
        storage: str = "local-lvm",
        network_bridge: str = "vmbr0",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new LXC container.
        
        Args:
            node_name: Target Proxmox node
            vmid: Container VMID
            hostname: Container hostname
            ostemplate: OS template (e.g., 'local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst')
            password: Root password
            memory: Memory in MB
            cores: CPU cores
            disk_size: Disk size (e.g., "8" for 8GB)
            storage: Storage location
            network_bridge: Network bridge
            **kwargs: Additional Proxmox LXC options
            
        Returns:
            Task information
        """
        try:
            client = self.get_client()
            
            # Build configuration
            config = {
                'vmid': vmid,
                'ostemplate': ostemplate,
                'hostname': hostname,
                'password': password,
                'memory': memory,
                'cores': cores,
                'rootfs': f'{storage}:{disk_size}',
                'net0': f'name=eth0,bridge={network_bridge},ip=dhcp',
                'unprivileged': 0,  # Privileged container required for Docker
                'features': 'nesting=1,keyctl=1',  # Enable nesting and keyctl for Docker-in-LXC
                'start': 0,  # Don't auto-start after creation
                **kwargs
            }
            
            # Create container
            task = client.nodes(node_name).lxc.post(**config)
            logger.info(f"Created LXC {vmid} on node {node_name}: {task}")
            return task
            
        except Exception as e:
            raise ProxmoxError(f"Failed to create LXC {vmid}: {e}")
    
    def configure_lxc_for_docker(self, node_name: str, vmid: int) -> None:
        """
        Configure LXC container for Docker support by modifying /etc/pve/lxc config directly.
        
        This must be called AFTER container creation but BEFORE starting it.
        AppArmor restrictions prevent Docker from applying capabilities properly.
        
        We modify the LXC config file directly via SSH since the Proxmox API 
        doesn't support setting custom lxc.* parameters.
        
        Args:
            node_name: Proxmox node name
            vmid: Container VMID
        """
        try:
            # Get host configuration
            host = self.get_host()
            
            # Extract SSH username (remove @pam realm if present)
            # Proxmox API uses 'root@pam', but SSH requires just 'root'
            ssh_username = host.user.split('@')[0] if '@' in host.user else host.user
            
            # Modify the LXC config file directly via SSH
            config_path = f"/etc/pve/lxc/{vmid}.conf"
            
            # Commands to append AppArmor configuration if not present
            commands = [
                f"grep -q 'lxc.apparmor.profile' {config_path} || echo 'lxc.apparmor.profile: unconfined' >> {config_path}",
                f"grep -q 'lxc.cap.drop' {config_path} || echo 'lxc.cap.drop:' >> {config_path}"
            ]
            
            # Execute commands via SSH on the Proxmox node
            for cmd in commands:
                stdout, stderr, exit_code = self._execute_ssh_command(
                    host=host.host,
                    port=host.ssh_port,
                    username=ssh_username,
                    password=host.password,
                    command=cmd,
                    timeout=10
                )
                
                if exit_code != 0:
                    raise ProxmoxError(f"Command failed with exit code {exit_code}: {stderr}")
            
            logger.info(f"Configured LXC {vmid} for Docker (AppArmor: unconfined, Capabilities: all)")
            
        except Exception as e:
            raise ProxmoxError(f"Failed to configure LXC {vmid} for Docker: {e}")
    
    def start_lxc(self, node_name: str, vmid: int) -> Dict[str, Any]:
        """
        Start an LXC container.
        
        Args:
            node_name: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Task information
        """
        try:
            client = self.get_client()
            task = client.nodes(node_name).lxc(vmid).status.start.post()
            logger.info(f"Started LXC {vmid} on node {node_name}")
            return task
        except Exception as e:
            raise ProxmoxError(f"Failed to start LXC {vmid}: {e}")
    
    def stop_lxc(self, node_name: str, vmid: int, force: bool = False) -> Dict[str, Any]:
        """
        Stop an LXC container.
        
        Args:
            node_name: Proxmox node name
            vmid: Container VMID
            force: Force stop (immediate)
            
        Returns:
            Task information
        """
        try:
            client = self.get_client()
            if force:
                task = client.nodes(node_name).lxc(vmid).status.stop.post(forceStop=1)
            else:
                task = client.nodes(node_name).lxc(vmid).status.shutdown.post()
            logger.info(f"Stopped LXC {vmid} on node {node_name}")
            return task
        except Exception as e:
            raise ProxmoxError(f"Failed to stop LXC {vmid}: {e}")
    
    def delete_lxc(self, node_name: str, vmid: int, force: bool = False) -> Dict[str, Any]:
        """
        Delete an LXC container.
        
        Args:
            node_name: Proxmox node name
            vmid: Container VMID
            force: Force deletion even if running
            
        Returns:
            Task information
        """
        try:
            client = self.get_client()
            
            # Stop container first if force is True
            if force:
                try:
                    self.stop_lxc(node_name, vmid, force=True)
                    import time
                    time.sleep(2)  # Wait for container to stop
                except:
                    pass  # Ignore errors if already stopped
            
            task = client.nodes(node_name).lxc(vmid).delete()
            logger.info(f"Deleted LXC {vmid} from node {node_name}")
            return task
        except Exception as e:
            raise ProxmoxError(f"Failed to delete LXC {vmid}: {e}")
    
    def create_snapshot(self, node_name: str, vmid: int, snapname: str, description: str = "") -> str:
        """
        Create a snapshot of an LXC container.

        Args:
            node_name: Proxmox node name
            vmid: Container VMID
            snapname: Name for the snapshot
            description: Optional description for the snapshot

        Returns:
            Task UPID

        Raises:
            ProxmoxError: If snapshot creation fails
        """
        try:
            client = self.get_client()
            task_upid = client.nodes(node_name).lxc(vmid).snapshot.post(
                snapname=snapname,
                description=description or f"Temporary snapshot for cloning"
            )
            logger.info(f"Created snapshot '{snapname}' for LXC {vmid}")
            return task_upid
        except Exception as e:
            raise ProxmoxError(f"Failed to create snapshot '{snapname}' for LXC {vmid}: {e}")

    def delete_snapshot(self, node_name: str, vmid: int, snapname: str) -> str:
        """
        Delete a snapshot of an LXC container.

        Args:
            node_name: Proxmox node name
            vmid: Container VMID
            snapname: Name of the snapshot to delete

        Returns:
            Task UPID

        Raises:
            ProxmoxError: If snapshot deletion fails
        """
        try:
            client = self.get_client()
            task_upid = client.nodes(node_name).lxc(vmid).snapshot(snapname).delete()
            logger.info(f"Deleted snapshot '{snapname}' for LXC {vmid}")
            return task_upid
        except Exception as e:
            raise ProxmoxError(f"Failed to delete snapshot '{snapname}' for LXC {vmid}: {e}")

    def clone_lxc(
        self,
        node_name: str,
        source_vmid: int,
        new_vmid: int,
        new_hostname: str,
        full: bool = True,
        timeout: int = 600
    ) -> str:
        """
        Clone an LXC container with zero-downtime support.

        For running containers performing full clones, this method automatically:
        1. Creates a temporary snapshot
        2. Clones from the snapshot (allowing source to keep running)
        3. Deletes the temporary snapshot

        The try...finally block guarantees snapshot cleanup even if the clone fails.

        Args:
            node_name: Proxmox node name
            source_vmid: Source container VMID to clone from
            new_vmid: New container VMID for the clone
            new_hostname: New hostname for the clone
            full: Create a full clone (True) or linked clone (False)
            timeout: Maximum time to wait for clone operation in seconds

        Returns:
            Success message

        Raises:
            ProxmoxError: If clone operation fails
        """
        import time
        snapshot_name = f"prox_clone_temp_{int(time.time())}"
        snapshot_created = False

        try:
            client = self.get_client()

            # Step 1/4: Check container status
            logger.info(f"[Step 1/4] Checking status of source container {source_vmid}...")
            status_info = self.get_lxc_status(node_name, source_vmid)
            is_running = status_info.get('status') == 'running'
            logger.info(f"[Step 1/4] ✓ Source container is {status_info.get('status')}")

            # Step 2/4: Create snapshot if needed (running + full clone)
            if is_running and full:
                logger.info(f"[Step 2/4] Creating temporary snapshot '{snapshot_name}' for zero-downtime clone...")
                snapshot_task = self.create_snapshot(
                    node_name,
                    source_vmid,
                    snapshot_name,
                    description="Temporary snapshot for cloning operation"
                )
                self.wait_for_task(node_name, snapshot_task, timeout=120)
                snapshot_created = True
                logger.info(f"[Step 2/4] ✓ Snapshot '{snapshot_name}' created successfully")
            else:
                logger.info(f"[Step 2/4] Skipping snapshot creation (running={is_running}, full={full})")

            # Step 3/4: Perform the clone operation
            logger.info(f"[Step 3/4] Cloning LXC {source_vmid} → {new_vmid} (hostname: {new_hostname})...")

            clone_params = {
                'newid': new_vmid,
                'hostname': new_hostname,
                'full': 1 if full else 0,
                'storage': 'local-lvm',
            }

            # If snapshot exists, clone from snapshot instead of live container
            if snapshot_created:
                clone_params['snapname'] = snapshot_name
                logger.info(f"[Step 3/4] Cloning from snapshot '{snapshot_name}'")

            task_upid = client.nodes(node_name).lxc(source_vmid).clone.post(**clone_params)
            logger.info(f"[Step 3/4] Clone task initiated: {task_upid}")

            self.wait_for_task(node_name, task_upid, timeout=timeout)
            logger.info(f"[Step 3/4] ✓ Clone completed successfully")

            logger.info(f"[Step 4/4] Clone operation completed: {source_vmid} → {new_vmid}")
            return f"Container {source_vmid} successfully cloned to {new_vmid}"

        finally:
            # Step 4/4: Guaranteed cleanup - delete temporary snapshot
            if snapshot_created:
                try:
                    logger.info(f"[Step 4/4] Cleaning up temporary snapshot '{snapshot_name}'...")
                    delete_task = self.delete_snapshot(node_name, source_vmid, snapshot_name)
                    self.wait_for_task(node_name, delete_task, timeout=60)
                    logger.info(f"[Step 4/4] ✓ Snapshot '{snapshot_name}' deleted successfully")
                except Exception as cleanup_error:
                    logger.critical(
                        f"[Step 4/4] ✗ FAILED to delete temporary snapshot '{snapshot_name}': {cleanup_error}. "
                        f"Manual cleanup required: 'pct delsnapshot {source_vmid} {snapshot_name}'"
                    )
    
    def get_lxc_status(self, node_name: str, vmid: int) -> Dict[str, Any]:
        """
        Get the current status of an LXC container.
        
        Args:
            node_name: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Container status information
        """
        try:
            client = self.get_client()
            status = client.nodes(node_name).lxc(vmid).status.current.get()
            return status
        except Exception as e:
            raise ProxmoxError(f"Failed to get LXC {vmid} status: {e}")
    
    def get_lxc_metrics(self, node_name: str, vmid: int) -> Dict[str, Any]:
        """
        Get resource usage metrics for a specific LXC container.
        
        Returns metrics including CPU usage, memory usage, and disk usage.
        If the container is not running or metrics cannot be retrieved,
        returns an empty dict.
        
        Args:
            node_name: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Dictionary with metrics:
            - cpu_usage: CPU usage percentage (0-100)
            - memory_used: Used memory in bytes
            - memory_total: Total memory in bytes
            - disk_used: Used disk space in bytes
            - disk_total: Total disk space in bytes
        """
        try:
            client = self.get_client()
            status = client.nodes(node_name).lxc(vmid).status.current.get()
            
            # Proxmox returns cpu as a float between 0 and number of cores
            # We normalize it to 0.0-1.0 by dividing by the number of CPUs
            cpu_raw = status.get("cpu", 0.0)
            cpus = status.get("cpus", 1)  # Number of CPU cores allocated
            cpu_usage = (cpu_raw / cpus) if cpus > 0 else 0.0
            
            return {
                "cpu_usage": round(cpu_usage * 100, 2),  # Convert to percentage (0-100)
                "memory_used": status.get("mem", 0),
                "memory_total": status.get("maxmem", 0),
                "disk_used": status.get("disk", 0),
                "disk_total": status.get("maxdisk", 0),
            }
        except Exception as e:
            # If container is not running or any error occurs, return empty metrics
            logger.debug(f"Could not get metrics for LXC {vmid} on {node_name}: {e}")
            return {}
    
    def get_lxc_config(self, node_name: str, vmid: int) -> Dict[str, Any]:
        """
        Get the configuration of an LXC container.
        
        Args:
            node_name: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Container configuration
        """
        try:
            client = self.get_client()
            config = client.nodes(node_name).lxc(vmid).config.get()
            return config
        except Exception as e:
            raise ProxmoxError(f"Failed to get LXC {vmid} config: {e}")
    
    def update_lxc_config(
        self, 
        node_name: str, 
        vmid: int, 
        **config_params
    ) -> Dict[str, Any]:
        """
        Update LXC container configuration.
        
        Args:
            node_name: Proxmox node name
            vmid: Container VMID
            **config_params: Configuration parameters to update
            
        Returns:
            Update result
        """
        try:
            client = self.get_client()
            result = client.nodes(node_name).lxc(vmid).config.put(**config_params)
            logger.info(f"Updated LXC {vmid} config: {config_params}")
            return result
        except Exception as e:
            raise ProxmoxError(f"Failed to update LXC {vmid} config: {e}")
    
    def wait_for_task(
        self,
        node_name: str,
        upid: str,
        timeout: int = 600,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for a Proxmox task to complete.
        
        Args:
            node_name: Proxmox node name
            upid: Task UPID (Unique Process ID)
            timeout: Maximum time to wait in seconds
            poll_interval: Polling interval in seconds
            
        Returns:
            Task status information
            
        Raises:
            ProxmoxError: If task fails or times out
        """
        import time
        
        try:
            client = self.get_client()
            start_time = time.time()
            
            while True:
                # Check timeout
                if time.time() - start_time > timeout:
                    raise ProxmoxError(f"Task {upid} timed out after {timeout}s")
                
                # Get task status
                status = client.nodes(node_name).tasks(upid).status.get()
                
                # Check if task is finished
                if status.get('status') == 'stopped':
                    exitstatus = status.get('exitstatus', 'unknown')
                    
                    if exitstatus == 'OK':
                        logger.info(f"Task {upid} completed successfully")
                        return status
                    else:
                        raise ProxmoxError(
                            f"Task {upid} failed with status: {exitstatus}"
                        )
                
                # Wait before next check
                time.sleep(poll_interval)
                
        except Exception as e:
            if isinstance(e, ProxmoxError):
                raise
            raise ProxmoxError(f"Error waiting for task {upid}: {e}")
    
    def create_lxc_backup(
        self,
        node_name: str,
        vmid: int,
        storage: str = 'local',
        mode: str = 'snapshot',
        compress: str = 'zstd'
    ) -> Dict[str, Any]:
        """
        Create a backup of an LXC container using vzdump.
        
        This method triggers a backup operation and waits for it to complete.
        The backup will be stored in the specified Proxmox storage.
        
        Args:
            node_name: Proxmox node name
            vmid: Container VMID to backup
            storage: Proxmox storage name for backup (default: 'local')
            mode: Backup mode - 'snapshot' (fastest), 'suspend', or 'stop'
            compress: Compression algorithm - 'zstd', 'gzip', or 'lzo'
            
        Returns:
            Dictionary containing:
                - file_name: Name of the created backup file
                - size: Backup file size in bytes
                - task: Task information
                
        Raises:
            ProxmoxError: If backup creation fails
        """
        try:
            client = self.get_client()
            
            # Validate mode
            valid_modes = ['snapshot', 'suspend', 'stop']
            if mode not in valid_modes:
                raise ProxmoxError(
                    f"Invalid backup mode '{mode}'. Must be one of: {valid_modes}"
                )
            
            # Validate compression
            valid_compress = ['zstd', 'gzip', 'lzo']
            if compress not in valid_compress:
                raise ProxmoxError(
                    f"Invalid compression '{compress}'. Must be one of: {valid_compress}"
                )
            
            logger.info(
                f"Creating backup for LXC {vmid} on {node_name} "
                f"(storage={storage}, mode={mode}, compress={compress})"
            )
            
            # Trigger vzdump backup
            task_upid = client.nodes(node_name).vzdump.post(
                vmid=vmid,
                storage=storage,
                mode=mode,
                compress=compress,
                remove=0  # Don't remove old backups automatically
            )
            
            logger.info(f"Backup task started: {task_upid}")
            
            # Wait for backup to complete
            task_status = self.wait_for_task(node_name, task_upid, timeout=1800)
            
            # Get the backup file information
            # The backup filename follows pattern: vzdump-lxc-{vmid}-{timestamp}.{ext}
            backups = client.nodes(node_name).storage(storage).content.get(
                content='backup'
            )
            
            # Find the most recent backup for this VMID
            vmid_backups = [
                b for b in backups 
                if f"lxc-{vmid}-" in b.get('volid', '')
            ]
            
            if not vmid_backups:
                raise ProxmoxError(f"Backup file not found for LXC {vmid}")
            
            # Sort by creation time and get the latest
            latest_backup = sorted(
                vmid_backups,
                key=lambda x: x.get('ctime', 0),
                reverse=True
            )[0]
            
            # Extract filename from volid (format: storage:backup/filename)
            volid = latest_backup.get('volid', '')
            file_name = volid.split('/')[-1] if '/' in volid else volid
            size = latest_backup.get('size', 0)
            
            logger.info(
                f"Backup completed successfully: {file_name} ({size} bytes)"
            )
            
            return {
                'file_name': file_name,
                'size': size,
                'storage': storage,
                'volid': volid,
                'task': task_status
            }
            
        except Exception as e:
            if isinstance(e, ProxmoxError):
                raise
            raise ProxmoxError(f"Failed to create backup for LXC {vmid}: {e}")
    
    def restore_lxc_backup(
        self,
        node_name: str,
        vmid: int,
        backup_file: str,
        storage: str = 'local',
        force: bool = True
    ) -> Dict[str, Any]:
        """
        Restore an LXC container from a backup.
        
        This is a DESTRUCTIVE operation that will overwrite the existing container.
        The container must be stopped before restoration.
        
        Args:
            node_name: Proxmox node name
            vmid: Container VMID to restore to
            backup_file: Backup filename (or volid)
            storage: Proxmox storage name where backup is stored
            force: Force overwrite of existing container
            
        Returns:
            Task status information
            
        Raises:
            ProxmoxError: If restore operation fails
        """
        try:
            client = self.get_client()
            
            # Ensure container is stopped
            try:
                status = self.get_lxc_status(node_name, vmid)
                if status.get('status') == 'running':
                    logger.info(f"Stopping LXC {vmid} before restore")
                    self.stop_lxc(node_name, vmid, force=True)
                    # Wait for container to stop
                    import time
                    time.sleep(3)
            except Exception as e:
                logger.warning(f"Could not check/stop container before restore: {e}")
            
            # Build volid if not already in that format
            if ':' not in backup_file:
                volid = f"{storage}:backup/{backup_file}"
            else:
                volid = backup_file
            
            logger.info(
                f"Restoring LXC {vmid} from backup {backup_file} "
                f"(volid={volid}, force={force})"
            )
            
            # Trigger restore operation
            task_upid = client.nodes(node_name).lxc.post(
                vmid=vmid,
                ostemplate=volid,
                restore=1,
                force=int(force),
                storage=storage
            )
            
            logger.info(f"Restore task started: {task_upid}")
            
            # Wait for restore to complete
            task_status = self.wait_for_task(node_name, task_upid, timeout=1800)
            
            logger.info(f"Restore completed successfully for LXC {vmid}")
            
            return {
                'task': task_status,
                'vmid': vmid,
                'backup_file': backup_file
            }
            
        except Exception as e:
            if isinstance(e, ProxmoxError):
                raise
            raise ProxmoxError(
                f"Failed to restore LXC {vmid} from {backup_file}: {e}"
            )
    
    def delete_backup_file(
        self,
        node_name: str,
        storage: str,
        backup_file: str
    ) -> bool:
        """
        Delete a backup file from Proxmox storage.
        
        Args:
            node_name: Proxmox node name
            storage: Storage name
            backup_file: Backup filename or volid
            
        Returns:
            True if deletion was successful
            
        Raises:
            ProxmoxError: If deletion fails
        """
        try:
            client = self.get_client()
            
            # Build volid if not already in that format
            if ':' not in backup_file:
                volid = f"{storage}:backup/{backup_file}"
            else:
                volid = backup_file
            
            logger.info(f"Deleting backup file: {volid}")
            
            # Delete the backup
            client.nodes(node_name).storage(storage).content(volid).delete()
            
            logger.info(f"Successfully deleted backup: {volid}")
            return True
            
        except Exception as e:
            raise ProxmoxError(f"Failed to delete backup {backup_file}: {e}")
    
    def list_backups(
        self,
        node_name: str,
        storage: str = 'local',
        vmid: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List available backups in storage.
        
        Args:
            node_name: Proxmox node name
            storage: Storage name
            vmid: Optional VMID to filter backups
            
        Returns:
            List of backup information dictionaries
        """
        try:
            client = self.get_client()
            
            # Get all backups from storage
            backups = client.nodes(node_name).storage(storage).content.get(
                content='backup'
            )
            
            # Filter by VMID if specified
            if vmid is not None:
                backups = [
                    b for b in backups 
                    if f"lxc-{vmid}-" in b.get('volid', '')
                ]
            
            return backups
            
        except Exception as e:
            raise ProxmoxError(f"Failed to list backups: {e}")
    
    def _execute_ssh_command(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        command: str,
        timeout: int = 30
    ) -> tuple[str, str, int]:
        """
        Execute a command on a remote host via SSH.
        
        Args:
            host: SSH host address
            port: SSH port (default 22)
            username: SSH username
            password: SSH password
            command: Command to execute
            timeout: SSH timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
            
        Raises:
            ProxmoxError: If SSH connection or command execution fails
        """
        ssh = None
        try:
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            logger.debug(f"Connecting to {host}:{port} as {username}")
            
            # Connect to host
            ssh.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            logger.debug(f"Executing SSH command: {command}")
            
            # Execute command
            stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
            
            # Get output and exit code
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            logger.debug(f"SSH command completed with exit code {exit_code}")
            
            return stdout_data, stderr_data, exit_code
            
        except paramiko.AuthenticationException as e:
            error_msg = f"SSH authentication failed for {username}@{host}: {e}"
            logger.error(error_msg)
            raise ProxmoxError(error_msg)
        except paramiko.SSHException as e:
            error_msg = f"SSH connection error to {host}: {e}"
            logger.error(error_msg)
            raise ProxmoxError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected SSH error: {e}"
            logger.error(error_msg)
            raise ProxmoxError(error_msg)
        finally:
            if ssh:
                ssh.close()
    
    def execute_in_container(
        self, 
        node_name: str,
        vmid: int, 
        command: str,
        timeout: int = 300,
        allow_nonzero_exit: bool = False
    ) -> str:
        """
        Execute a command inside an LXC container using pct exec via SSH.
        
        This method connects to the Proxmox node via SSH and executes
        'pct exec <vmid> -- <command>' to run commands inside the container.
        
        Args:
            node_name: Proxmox node name
            vmid: LXC container ID  
            command: Command to execute inside the container
            timeout: Command timeout in seconds
            allow_nonzero_exit: If True, don't raise error on non-zero exit code
            
        Returns:
            Command output (stdout) as string
            
        Raises:
            ProxmoxError: If command execution fails or returns non-zero exit code
        """
        try:
            # Get host configuration
            host = self.get_host()
            
            # Extract username without realm (@pam) for SSH
            ssh_username = host.user.split('@')[0]
            ssh_password = host.password
            ssh_host = host.host
            ssh_port = host.ssh_port
            
            logger.debug(f"Executing in LXC {vmid} on node {node_name}: {command}")
            
            # Build pct exec command
            # Note: We don't use shlex.quote for the command itself here because
            # pct exec handles it properly. The command is passed as separate args.
            pct_command = f"pct exec {vmid} -- {command}"
            
            logger.debug(f"Full pct command: {pct_command}")
            
            # Execute via SSH
            stdout, stderr, exit_code = self._execute_ssh_command(
                host=ssh_host,
                port=ssh_port,
                username=ssh_username,
                password=ssh_password,
                command=pct_command,
                timeout=timeout
            )
            
            # Check exit code
            if exit_code != 0 and not allow_nonzero_exit:
                error_msg = (
                    f"Command in LXC {vmid} failed with exit code {exit_code}\n"
                    f"Command: {command}\n"
                    f"STDOUT: {stdout}\n"
                    f"STDERR: {stderr}"
                )
                logger.error(error_msg)
                raise ProxmoxError(error_msg)
            
            if stderr and not allow_nonzero_exit:
                logger.warning(f"Command stderr: {stderr}")
            
            logger.debug(f"Command output: {stdout[:200]}..." if len(stdout) > 200 else f"Command output: {stdout}")
            
            return stdout
            
        except ProxmoxError:
            # Re-raise ProxmoxError from SSH layer
            raise
        except Exception as e:
            error_msg = f"Unexpected error executing in LXC {vmid}: {e}"
            logger.error(error_msg)
            if not allow_nonzero_exit:
                raise ProxmoxError(error_msg)
            return ""
    
    def discover_unmanaged_lxc(self) -> List[Dict[str, Any]]:
        """
        Discover LXC containers that exist on Proxmox but are not managed by Proximity.
        
        Returns:
            List of unmanaged container information dictionaries
        """
        try:
            from apps.applications.models import Application
            
            # Get all nodes for this host
            nodes_data = self.get_nodes()
            host = self.get_host()
            
            # Get all managed VMIDs from database
            managed_vmids = set(
                Application.objects.filter(
                    host_id=host.id
                ).exclude(
                    lxc_id__isnull=True
                ).values_list('lxc_id', flat=True)
            )
            
            logger.info(f"Managed VMIDs: {managed_vmids}")
            
            # Discover containers on all nodes
            unmanaged_containers = []
            
            for node_data in nodes_data:
                node_name = node_data.get('node')
                
                try:
                    # Get all LXC containers on this node
                    containers = self.get_lxc_containers(node_name)
                    
                    for container in containers:
                        vmid = container.get('vmid')
                        
                        # Skip if already managed
                        if vmid in managed_vmids:
                            continue
                        
                        # Get detailed container config
                        try:
                            config = self.get_lxc_config(node_name, vmid)
                            
                            unmanaged_containers.append({
                                'vmid': vmid,
                                'name': container.get('name', f'ct-{vmid}'),
                                'hostname': config.get('hostname', container.get('name', f'ct-{vmid}')),
                                'status': container.get('status', 'unknown'),
                                'node': node_name,
                                'uptime': container.get('uptime', 0),
                                'memory_used': container.get('mem', 0),
                                'memory_total': container.get('maxmem', 0),
                                'disk_used': container.get('disk', 0),
                                'disk_total': container.get('maxdisk', 0),
                                'cpu_usage': container.get('cpu', 0),
                                'cores': config.get('cores', 1),
                                'ostype': config.get('ostype', 'unknown'),
                                'host_id': host.id,
                                'host_name': host.name,
                            })
                            
                            logger.info(f"Found unmanaged container: {vmid} ({container.get('name')}) on {node_name}")
                            
                        except Exception as e:
                            logger.warning(f"Failed to get config for container {vmid}: {e}")
                            # Add with basic info only
                            unmanaged_containers.append({
                                'vmid': vmid,
                                'name': container.get('name', f'ct-{vmid}'),
                                'hostname': container.get('name', f'ct-{vmid}'),
                                'status': container.get('status', 'unknown'),
                                'node': node_name,
                                'host_id': host.id,
                                'host_name': host.name,
                            })
                    
                except Exception as e:
                    logger.error(f"Failed to get containers from node {node_name}: {e}")
                    continue
            
            logger.info(f"Discovered {len(unmanaged_containers)} unmanaged containers")
            return unmanaged_containers
            
        except Exception as e:
            raise ProxmoxError(f"Failed to discover unmanaged containers: {e}")
