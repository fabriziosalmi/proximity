import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from proxmoxer import ProxmoxAPI

from core.config import settings
from models.schemas import NodeInfo, LXCInfo, LXCStatus

logger = logging.getLogger(__name__)


class ProxmoxError(Exception):
    """Custom exception for Proxmox API errors"""
    pass


class ProxmoxService:
    """Async wrapper around Proxmox API for container and node management"""
    
    def __init__(self, network_manager=None):
        self._proxmox: Optional[ProxmoxAPI] = None
        self._connect_lock = asyncio.Lock()
        self.network_manager = network_manager  # Injected NetworkManager instance
    
    async def _get_client(self) -> ProxmoxAPI:
        """Get or create Proxmox API client with connection pooling"""
        if self._proxmox is None:
            async with self._connect_lock:
                if self._proxmox is None:
                    try:
                        # Note: proxmoxer is synchronous, we wrap calls in asyncio.to_thread
                        self._proxmox = await asyncio.to_thread(
                            ProxmoxAPI,
                            settings.PROXMOX_HOST,
                            user=settings.PROXMOX_USER,
                            password=settings.PROXMOX_PASSWORD,
                            verify_ssl=settings.PROXMOX_VERIFY_SSL,
                            port=settings.PROXMOX_PORT
                        )
                        logger.info(f"Connected to Proxmox at {settings.PROXMOX_HOST}")
                    except Exception as e:
                        if "authentication" in str(e).lower() or "auth" in str(e).lower():
                            raise ProxmoxError(f"Authentication failed: {e}")
                        raise ProxmoxError(f"Failed to connect to Proxmox: {e}")
        return self._proxmox

    async def test_connection(self) -> bool:
        """Test connection to Proxmox API"""
        try:
            client = await self._get_client()
            await asyncio.to_thread(client.version.get)
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def get_version(self) -> Dict[str, Any]:
        """Get Proxmox version information"""
        try:
            client = await self._get_client()
            return await asyncio.to_thread(client.version.get)
        except Exception as e:
            raise ProxmoxError(f"Failed to get version: {e}")

    async def get_nodes(self) -> List[NodeInfo]:
        """Get list of all Proxmox nodes"""
        try:
            client = await self._get_client()
            nodes_data = await asyncio.to_thread(client.nodes.get)
            return [NodeInfo(**node) for node in nodes_data]
        except Exception as e:
            raise ProxmoxError(f"Failed to get nodes: {e}")

    async def get_node_status(self, node: str) -> NodeInfo:
        """Get detailed status of a specific node"""
        try:
            client = await self._get_client()
            node_data = await asyncio.to_thread(client.nodes(node).status.get)
            # Remove 'node' from response to avoid duplicate
            node_data.pop('node', None)
            return NodeInfo(node=node, **node_data)
        except Exception as e:
            raise ProxmoxError(f"Failed to get node {node} status: {e}")

    async def get_next_vmid(self) -> int:
        """Get next available VMID"""
        try:
            client = await self._get_client()
            return await asyncio.to_thread(client.cluster.nextid.get)
        except Exception as e:
            raise ProxmoxError(f"Failed to get next VMID: {e}")

    async def get_lxc_containers(self, node: Optional[str] = None) -> List[LXCInfo]:
        """Get list of LXC containers, optionally filtered by node"""
        try:
            client = await self._get_client()
            containers = []
            
            if node:
                nodes_to_check = [node]
            else:
                nodes = await self.get_nodes()
                nodes_to_check = [n.node for n in nodes]
            
            for node_name in nodes_to_check:
                try:
                    node_containers = await asyncio.to_thread(
                        client.nodes(node_name).lxc.get
                    )
                    for container in node_containers:
                        # Extract and convert status first to avoid duplicate keyword argument
                        container_dict = dict(container)
                        status_str = container_dict.pop('status', 'stopped')
                        container_dict['node'] = node_name
                        container_dict['status'] = LXCStatus(status_str)
                        containers.append(LXCInfo(**container_dict))
                except Exception as e:
                    logger.warning(f"Failed to get containers from node {node_name}: {e}")
                    continue
            
            return containers
        except Exception as e:
            raise ProxmoxError(f"Failed to get LXC containers: {e}")

    async def get_lxc_status(self, node: str, vmid: int) -> LXCInfo:
        """Get status of a specific LXC container"""
        try:
            client = await self._get_client()
            container_data = await asyncio.to_thread(
                client.nodes(node).lxc(vmid).status.current.get
            )
            # Extract status to avoid duplicate keyword argument
            status_str = container_data.pop('status', 'stopped')
            # Remove vmid and node if they exist in container_data to avoid duplicates
            container_data.pop('vmid', None)
            container_data.pop('node', None)
            
            return LXCInfo(
                node=node,
                vmid=vmid,
                status=LXCStatus(status_str),
                **container_data
            )
        except Exception as e:
            raise ProxmoxError(f"Failed to get LXC {vmid} status: {e}")

    async def get_lxc_ip(self, node: str, vmid: int) -> Optional[str]:
        """Get IP address of a specific LXC container"""
        try:
            # Use execute_in_container to get the IP from eth0 interface
            command = "ip -4 addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1"
            result = await self.execute_in_container(node, vmid, command)
            
            # execute_in_container returns a string directly
            if result:
                ip = result.strip()
                if ip and ip != "":
                    logger.debug(f"Got IP for LXC {vmid}: {ip}")
                    return ip
            
            logger.warning(f"No IP found for LXC {vmid}")
            return None
        except Exception as e:
            logger.warning(f"Failed to get LXC {vmid} IP: {e}")
            return None

    async def create_lxc(self, node: str, vmid: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new LXC container with automatic storage selection.
        
        Containers are now provisioned exclusively on the prox-net isolated network
        with DHCP-assigned IPs and DNS resolution via the managed dnsmasq service.
        """
        try:
            client = await self._get_client()
            
            # Get required disk size from config or use default
            required_size_gb = 8  # Default minimum
            if 'rootfs' in config:
                # Parse size from rootfs if provided (format: "storage:size")
                rootfs_parts = config['rootfs'].split(':')
                if len(rootfs_parts) > 1 and rootfs_parts[1].endswith('G'):
                    try:
                        required_size_gb = int(rootfs_parts[1].rstrip('G'))
                    except ValueError:
                        pass
            
            # Automatically select best storage if not explicitly provided
            if 'rootfs' not in config or ':' not in config['rootfs']:
                logger.info(f"Automatically selecting storage for node {node}...")
                storage_info = await self.get_best_storage(node, required_size_gb)
                config['rootfs'] = f"{storage_info['storage']}:{storage_info['size_gb']}"
                logger.info(f"Selected storage: {config['rootfs']}")
            
            # Ensure Alpine template exists (uses cache if available)
            logger.info(f"Checking for Alpine template on node {node}...")
            template_to_use = await self.ensure_alpine_template(node, version='3.22')
            logger.info(f"✓ Template ready: {template_to_use}")
            
            # Get network configuration from NetworkManager
            # This provisions the container on prox-net with DHCP
            hostname = config.get('hostname', f"ct{vmid}")
            
            if self.network_manager:
                net_config = await self.network_manager.get_container_network_config(hostname, node)
                logger.info(f"Using managed network config: {net_config}")
            else:
                # Fallback to default bridge (vmbr0) with DHCP when NetworkManager not available
                # This happens in development environments (macOS, Windows) or if network init failed
                net_config = "name=eth0,bridge=vmbr0,ip=dhcp,firewall=1"
                logger.warning(f"NetworkManager not available - using default bridge (vmbr0) with DHCP")
                logger.info(f"Container will use default Proxmox networking instead of isolated network")
            
            # Merge with default configuration
            lxc_config = {
                'vmid': vmid,
                'ostemplate': template_to_use,
                'hostname': hostname,  # Hostname for DNS resolution
                'cores': settings.LXC_CORES,
                'memory': settings.LXC_MEMORY,
                'net0': net_config,  # Managed network on prox-net
                'features': 'nesting=1,keyctl=1',  # Required for Docker
                'unprivileged': 1,
                'onboot': 1,
                **config
            }
            
            # Remove any static IP configuration from the override
            if 'net0' in config:
                logger.warning("Ignoring net0 override - using managed network configuration")
            
            task_id = await asyncio.to_thread(
                client.nodes(node).lxc.create, **lxc_config
            )
            
            logger.info(f"LXC creation started: node={node}, vmid={vmid}, hostname={hostname}, network=prox-net, task={task_id}")
            return {"task_id": task_id, "vmid": vmid, "node": node, "hostname": hostname}
            
        except Exception as e:
            if "already exists" in str(e).lower():
                raise ProxmoxError(f"LXC {vmid} already exists on node {node}")
            raise ProxmoxError(f"Failed to create LXC {vmid}: {e}")

    async def start_lxc(self, node: str, vmid: int) -> str:
        """Start an LXC container"""
        try:
            client = await self._get_client()
            task_id = await asyncio.to_thread(
                client.nodes(node).lxc(vmid).status.start.post
            )
            logger.info(f"LXC start initiated: node={node}, vmid={vmid}, task={task_id}")
            return task_id
        except Exception as e:
            raise ProxmoxError(f"Failed to start LXC {vmid}: {e}")

    async def stop_lxc(self, node: str, vmid: int, force: bool = False) -> str:
        """Stop an LXC container"""
        try:
            client = await self._get_client()
            if force:
                task_id = await asyncio.to_thread(
                    client.nodes(node).lxc(vmid).status.shutdown.post,
                    forceStop=1
                )
            else:
                task_id = await asyncio.to_thread(
                    client.nodes(node).lxc(vmid).status.shutdown.post
                )
            logger.info(f"LXC stop initiated: node={node}, vmid={vmid}, task={task_id}")
            return task_id
        except Exception as e:
            raise ProxmoxError(f"Failed to stop LXC {vmid}: {e}")

    async def destroy_lxc(self, node: str, vmid: int, force: bool = False) -> str:
        """Destroy an LXC container
        
        Args:
            node: Proxmox node name
            vmid: VM ID to destroy
            force: If True, forcefully stops the container before destroying
        """
        try:
            client = await self._get_client()
            
            # If force is True, ensure container is stopped first
            if force:
                try:
                    status = await self.get_lxc_status(node, vmid)
                    if status.status == LXCStatus.RUNNING:
                        logger.info(f"Force stopping LXC {vmid} before destruction...")
                        # Use force stop (shutdown with immediate kill if needed)
                        stop_task = await asyncio.to_thread(
                            client.nodes(node).lxc(vmid).status.shutdown.post,
                            forceStop=1,
                            timeout=10
                        )
                        await self.wait_for_task(node, stop_task, timeout=60)
                        await asyncio.sleep(3)  # Give it time to fully stop
                        logger.info(f"✓ LXC {vmid} stopped successfully")
                except ProxmoxError:
                    # Re-raise ProxmoxError as-is
                    raise
                except Exception as stop_error:
                    # For other errors, try to continue with forced deletion
                    logger.warning(f"Failed to stop LXC {vmid}, will try forced deletion: {stop_error}")
                    # Try to force kill if shutdown failed
                    try:
                        await asyncio.to_thread(
                            client.nodes(node).lxc(vmid).status.stop.post
                        )
                        await asyncio.sleep(2)
                    except Exception:
                        pass  # Ignore errors, will try to delete anyway
            
            # Attempt to destroy the container
            # If it's still running and force=True, use purge parameter
            delete_params = {}
            if force:
                delete_params['purge'] = 1  # Purge all data
                delete_params['force'] = 1  # Force deletion even if running
            
            task_id = await asyncio.to_thread(
                client.nodes(node).lxc(vmid).delete,
                **delete_params
            )
            logger.info(f"LXC destruction initiated: node={node}, vmid={vmid}, task={task_id}")
            return task_id
        except Exception as e:
            raise ProxmoxError(f"Failed to destroy LXC {vmid}: {e}")

    async def execute_command_via_ssh(self, node: str, command: str, timeout: int = 300, allow_nonzero_exit: bool = False) -> str:
        """Execute a command on Proxmox host via SSH
        
        Args:
            node: Proxmox node (not used for SSH, but kept for API consistency)
            command: Shell command to execute
            timeout: Command timeout in seconds
            allow_nonzero_exit: If True, don't raise error on non-zero exit codes
            
        Returns:
            Command output (stdout + stderr)
        """
        try:
            import paramiko
            from io import StringIO
            
            ssh_host = settings.PROXMOX_SSH_HOST or settings.PROXMOX_HOST
            ssh_password = settings.PROXMOX_SSH_PASSWORD or settings.PROXMOX_PASSWORD
            
            logger.debug(f"Connecting to {ssh_host}:{settings.PROXMOX_SSH_PORT} as {settings.PROXMOX_SSH_USER}")
            
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            await asyncio.to_thread(
                ssh.connect,
                hostname=ssh_host,
                port=settings.PROXMOX_SSH_PORT,
                username=settings.PROXMOX_SSH_USER,
                password=ssh_password,
                timeout=30,
                banner_timeout=30
            )
            
            # Execute command
            logger.debug(f"Executing: {command}")
            stdin, stdout, stderr = await asyncio.to_thread(
                ssh.exec_command,
                command,
                timeout=timeout
            )
            
            # Read output
            stdout_text = await asyncio.to_thread(stdout.read)
            stderr_text = await asyncio.to_thread(stderr.read)
            exit_code = stdout.channel.recv_exit_status()
            
            ssh.close()
            
            output = stdout_text.decode('utf-8', errors='replace')
            error = stderr_text.decode('utf-8', errors='replace')
            
            # Combine output for return
            combined_output = output + error
            
            if exit_code != 0 and not allow_nonzero_exit:
                raise ProxmoxError(
                    f"Command failed with exit code {exit_code}:\n"
                    f"Command: {command}\n"
                    f"Output: {output}\n"
                    f"Error: {error}"
                )
            
            logger.debug(f"Command output (exit={exit_code}): {combined_output}")
            return combined_output
            
        except ImportError:
            raise ProxmoxError(
                "SSH execution requires 'paramiko' library. "
                "Install it with: pip install paramiko"
            )
        except Exception as e:
            raise ProxmoxError(f"Failed to execute command via SSH: {e}")
    
    async def execute_on_node(self, node: str, command: str, timeout: int = 300, allow_nonzero_exit: bool = False) -> str:
        """Execute a command directly on a specific Proxmox cluster node
        
        In a Proxmox cluster, nodes can be accessed from any cluster member via their node name.
        This method SSH's to the main Proxmox host, then uses SSH to reach the target node.
        
        Args:
            node: Proxmox node name (e.g., 'opti2', 'pve')
            command: Shell command to execute on the node
            timeout: Command timeout in seconds
            allow_nonzero_exit: If True, don't raise error on non-zero exit codes
            
        Returns:
            Command output (stdout + stderr)
        """
        # Escape single quotes in the command for SSH
        escaped_command = command.replace("'", "'\\''")
        
        # SSH from main host to the target node, then execute the command
        ssh_command = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@{node} '{escaped_command}'"
        
        logger.debug(f"Executing on node {node} via cluster SSH: {command}")
        return await self.execute_command_via_ssh(node, ssh_command, timeout, allow_nonzero_exit)
    
    async def execute_in_container(self, node: str, vmid: int, command: str, timeout: int = 300, allow_nonzero_exit: bool = False) -> str:
        """Execute a command inside an LXC container using pct exec via SSH
        
        Args:
            node: Proxmox node
            vmid: Container ID
            command: Command to execute inside the container
            timeout: Command timeout in seconds
            allow_nonzero_exit: If True, don't raise error on non-zero exit codes
            
        Returns:
            Command output
        """
        # Escape single quotes in the command
        escaped_command = command.replace("'", "'\\''")
        
        # Build pct exec command
        pct_command = f"pct exec {vmid} -- sh -c '{escaped_command}'"
        
        logger.info(f"Executing in LXC {vmid}: {command}")
        return await self.execute_command_via_ssh(node, pct_command, timeout, allow_nonzero_exit)
    
    async def setup_docker_in_alpine(self, node: str, vmid: int) -> None:
        """Setup Docker inside Alpine LXC container using pct exec via SSH
        
        This method uses SSH to connect to the Proxmox host and executes
        commands inside the container using 'pct exec'.
        
        The container must be created with proper features (nesting=1, keyctl=1)
        for Docker to work correctly.
        """
        try:
            logger.info(f"Setting up Docker in Alpine LXC {vmid} on node {node}...")
            
            # Wait for container to be fully started and network ready
            logger.info("Waiting for container to be ready...")
            await asyncio.sleep(5)
            
            # Step 1: Update Alpine packages
            logger.info("Updating Alpine packages...")
            await self.execute_in_container(
                node, vmid,
                "apk update",
                timeout=120
            )
            
            # Step 2: Install Docker and Docker Compose
            logger.info("Installing Docker and Docker Compose...")
            await self.execute_in_container(
                node, vmid,
                "apk add --no-cache docker docker-cli-compose",
                timeout=180
            )
            
            # Step 3: Enable Docker service
            logger.info("Enabling Docker service...")
            await self.execute_in_container(
                node, vmid,
                "rc-update add docker default",
                timeout=30
            )
            
            # Step 4: Start Docker service
            logger.info("Starting Docker service...")
            await self.execute_in_container(
                node, vmid,
                "service docker start",
                timeout=60
            )
            
            # Step 5: Wait for Docker to be ready
            logger.info("Waiting for Docker to be ready...")
            await asyncio.sleep(3)
            
            # Step 6: Verify Docker is working
            logger.info("Verifying Docker installation...")
            docker_info = await self.execute_in_container(
                node, vmid,
                "docker info",
                timeout=30
            )
            
            logger.info(f"✓ Docker successfully installed and running in LXC {vmid}")
            
        except ProxmoxError:
            # Re-raise ProxmoxError as-is
            raise
        except Exception as e:
            raise ProxmoxError(f"Failed to setup Docker in Alpine LXC {vmid}: {e}")

    async def get_lxc_config(self, node: str, vmid: int) -> Dict[str, Any]:
        """Get LXC container configuration"""
        try:
            client = await self._get_client()
            return await asyncio.to_thread(
                client.nodes(node).lxc(vmid).config.get
            )
        except Exception as e:
            raise ProxmoxError(f"Failed to get LXC {vmid} config: {e}")

    async def update_lxc_config(self, node: str, vmid: int, config: Dict[str, Any]) -> str:
        """Update LXC container configuration"""
        try:
            client = await self._get_client()
            task_id = await asyncio.to_thread(
                client.nodes(node).lxc(vmid).config.put, **config
            )
            logger.info(f"LXC config update initiated: node={node}, vmid={vmid}, task={task_id}")
            return task_id
        except Exception as e:
            raise ProxmoxError(f"Failed to update LXC {vmid} config: {e}")

    async def wait_for_task(self, node: str, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for a Proxmox task to complete"""
        try:
            client = await self._get_client()
            
            start_time = asyncio.get_event_loop().time()
            while True:
                task_status = await asyncio.to_thread(
                    client.nodes(node).tasks(task_id).status.get
                )
                
                if task_status.get('status') == 'stopped':
                    if task_status.get('exitstatus') == 'OK':
                        logger.info(f"Task {task_id} completed successfully")
                        return task_status
                    else:
                        error_log = await asyncio.to_thread(
                            client.nodes(node).tasks(task_id).log.get
                        )
                        error_msg = '\n'.join([line.get('t', '') for line in error_log[-10:]])
                        raise ProxmoxError(f"Task {task_id} failed: {error_msg}")
                
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise ProxmoxError(f"Task {task_id} timed out after {timeout} seconds")
                
                await asyncio.sleep(2)
                
        except Exception as e:
            if isinstance(e, ProxmoxError):
                raise
            raise ProxmoxError(f"Failed to wait for task {task_id}: {e}")

    async def get_best_node(self) -> str:
        """Get the best node for deployment based on available resources"""
        try:
            nodes = await self.get_nodes()
            if not nodes:
                raise ProxmoxError("No nodes available")
            
            # Simple selection based on memory usage
            best_node = min(nodes, key=lambda n: (n.mem or 0) / (n.maxmem or 1))
            return best_node.node
            
        except Exception as e:
            raise ProxmoxError(f"Failed to select best node: {e}")

    async def get_node_architecture(self, node: str) -> str:
        """Get the CPU architecture of a node (amd64 or arm64)"""
        try:
            client = await self._get_client()
            cpu_info = await asyncio.to_thread(
                client.nodes(node).status.get
            )
            
            # Check CPU model/flags to determine architecture
            cpu_model = cpu_info.get('cpuinfo', {}).get('model', '').lower()
            
            # Check for ARM indicators
            if 'arm' in cpu_model or 'aarch64' in cpu_model:
                return 'arm64'
            
            # Default to amd64 (x86_64)
            return 'amd64'
            
        except Exception as e:
            logger.warning(f"Failed to detect architecture for node {node}, defaulting to amd64: {e}")
            return 'amd64'

    async def get_available_templates(self, node: str, storage: str = 'local') -> List[str]:
        """Get list of available LXC templates on a storage"""
        try:
            client = await self._get_client()
            
            # Get all content from storage
            content = await asyncio.to_thread(
                client.nodes(node).storage(storage).content.get
            )
            
            # Filter for vztmpl (template) content
            templates = [
                item['volid'] 
                for item in content 
                if item.get('content') == 'vztmpl'
            ]
            
            return templates
            
        except Exception as e:
            logger.warning(f"Failed to get templates from {storage} on node {node}: {e}")
            return []

    async def download_alpine_template(self, node: str, storage: str = 'local', version: str = '3.22') -> str:
        """
        Download Alpine Linux template if not present.
        
        Args:
            node: Proxmox node name
            storage: Storage to download template to
            version: Alpine version (default 3.22)
            
        Returns:
            Template volume ID (e.g., 'local:vztmpl/alpine-3.22-default_20240101_amd64.tar.xz')
        """
        try:
            # Get node architecture
            arch = await self.get_node_architecture(node)
            logger.info(f"Node {node} architecture: {arch}")
            
            # Check existing templates
            existing_templates = await self.get_available_templates(node, storage)
            
            # Look for Alpine template matching version and architecture
            alpine_pattern = f"alpine-{version}"
            matching_templates = [
                t for t in existing_templates 
                if alpine_pattern in t.lower() and arch in t.lower()
            ]
            
            if matching_templates:
                logger.info(f"Found existing Alpine template: {matching_templates[0]}")
                return matching_templates[0]
            
            # Download Alpine template (will be cached after download)
            logger.info(f"📥 Downloading Alpine {version} ({arch}) to {storage} on {node}...")
            logger.info(f"⏳ This may take a few minutes (cached for future deployments)")
            
            # Construct template filename based on Alpine naming convention
            # Format: alpine-{version}-default_{date}_{arch}.tar.xz
            template_filename = f"alpine-{version}-default_{arch}.tar.xz"
            
            # Use Proxmox API to download template
            client = await self._get_client()
            
            # Use pveam (Proxmox VE Appliance Manager) to download template
            # This is the proper way to download templates in Proxmox
            try:
                # Try using pveam download
                task_id = await asyncio.to_thread(
                    client.nodes(node).aplinfo.post,
                    storage=storage,
                    template=template_filename
                )
                
                logger.info(f"Download task started: {task_id}")
                
                # Wait for download to complete (with longer timeout for downloads)
                await self.wait_for_task(node, task_id, timeout=600)
            except Exception as download_error:
                logger.warning(f"Appliance manager download failed: {download_error}")
                logger.info("Attempting alternative download method...")
                
                # Fallback: try direct URL download
                download_url = f"http://download.proxmox.com/images/system/{template_filename}"
                task_id = await asyncio.to_thread(
                    client.nodes(node).storage(storage).download_url.post,
                    content='vztmpl',
                    filename=template_filename,
                    url=download_url
                )
                
                logger.info(f"Alternative download started: {task_id}")
                await self.wait_for_task(node, task_id, timeout=600)
            
            # Get updated template list
            updated_templates = await self.get_available_templates(node, storage)
            
            # Find the newly downloaded template
            new_templates = [
                t for t in updated_templates 
                if t not in existing_templates and alpine_pattern in t.lower()
            ]
            
            if new_templates:
                logger.info(f"✓ Template downloaded and CACHED successfully: {new_templates[0]}")
                logger.info(f"💾 Template is now cached in {storage} for future deployments")
                return new_templates[0]
            else:
                # If not found with strict pattern, try finding any new Alpine template
                new_alpine = [
                    t for t in updated_templates 
                    if t not in existing_templates and 'alpine' in t.lower()
                ]
                if new_alpine:
                    logger.info(f"✓ Template downloaded and CACHED: {new_alpine[0]}")
                    return new_alpine[0]
                raise ProxmoxError("Template download completed but template not found in storage")
                
        except Exception as e:
            if isinstance(e, ProxmoxError):
                raise
            raise ProxmoxError(f"Failed to download Alpine template: {e}")

    async def ensure_alpine_template(self, node: str, version: str = '3.22') -> str:
        """
        Ensure an Alpine template exists on the node, downloading if necessary.
        Template is cached in Proxmox storage after first download.
        
        Returns:
            Template volume ID
        """
        try:
            arch = await self.get_node_architecture(node)
            logger.info(f"Searching for Alpine {version} template ({arch}) in cache...")
            
            # Get all available storages
            storage_list = await self.get_node_storage(node)
            
            # First, check ALL storages for existing Alpine templates (CACHE CHECK)
            alpine_pattern = f"alpine-{version}"
            for storage_info in storage_list:
                storage_name = storage_info['storage']
                try:
                    existing_templates = await self.get_available_templates(node, storage_name)
                    matching_templates = [
                        t for t in existing_templates 
                        if alpine_pattern in t.lower() and arch in t.lower()
                    ]
                    
                    if matching_templates:
                        logger.info(f"✓ CACHE HIT: Using cached template from {storage_name}: {matching_templates[0]}")
                        return matching_templates[0]
                except Exception as e:
                    logger.debug(f"Could not check templates on storage {storage_name}: {e}")
                    continue
            
            # Second pass: Look for ANY Alpine template (version-agnostic fallback)
            logger.info(f"Alpine {version} not found, searching for any Alpine template...")
            for storage_info in storage_list:
                storage_name = storage_info['storage']
                try:
                    existing_templates = await self.get_available_templates(node, storage_name)
                    alpine_templates = [
                        t for t in existing_templates 
                        if 'alpine' in t.lower() and arch in t.lower()
                    ]
                    
                    if alpine_templates:
                        logger.info(f"✓ CACHE HIT: Using alternative Alpine template: {alpine_templates[0]}")
                        return alpine_templates[0]
                except Exception as e:
                    continue
            
            # No existing template found, try to download (CACHE MISS)
            logger.warning(f"⚠️  CACHE MISS: No Alpine template found in cache")
            logger.info(f"Downloading Alpine {version} template (this is a one-time download)...")
            
            # Find storages that support templates (vztmpl content)
            template_storages = [
                s for s in storage_list 
                if 'vztmpl' in s.get('content', [])
            ]
            
            if not template_storages:
                # No storage supports templates - check if 'local' storage exists and try anyway
                local_storage = next(
                    (s for s in storage_list if s['storage'] == 'local'),
                    None
                )
                
                if local_storage:
                    logger.warning("No storage with 'vztmpl' content found, attempting download to 'local' storage...")
                    try:
                        template = await self.download_alpine_template(node, 'local', version)
                        return template
                    except Exception as e:
                        logger.error(f"Failed to download to 'local' storage: {e}")
                
                # Last resort: list available templates on any storage and use the first Alpine template found
                logger.warning("Cannot download template. Searching for ANY Alpine template as fallback...")
                for storage_info in storage_list:
                    storage_name = storage_info['storage']
                    try:
                        existing_templates = await self.get_available_templates(node, storage_name)
                        # Look for any Alpine template (less strict matching)
                        alpine_templates = [
                            t for t in existing_templates 
                            if 'alpine' in t.lower()
                        ]
                        
                        if alpine_templates:
                            logger.warning(f"⚠️  Using fallback template: {alpine_templates[0]}")
                            return alpine_templates[0]
                    except Exception as e:
                        continue
                
                raise ProxmoxError(
                    f"No Alpine templates found on node {node} and no storage supports template downloads. "
                    f"Please manually upload an Alpine template to one of these storages: {[s['storage'] for s in storage_list]}"
                )
            
            # Try to download to first available template storage
            for storage_info in template_storages:
                storage_name = storage_info['storage']
                try:
                    template = await self.download_alpine_template(node, storage_name, version)
                    return template
                except Exception as e:
                    logger.warning(f"Failed to download to storage {storage_name}: {e}")
                    continue
            
            raise ProxmoxError(f"Failed to download Alpine template to any available storage on node {node}")
            
        except Exception as e:
            if isinstance(e, ProxmoxError):
                raise
            raise ProxmoxError(f"Failed to ensure Alpine template: {e}")

    async def get_node_storage(self, node: str) -> List[Dict[str, Any]]:
        """Get all storage pools available on a node with their capacity"""
        try:
            client = await self._get_client()
            storage_list = await asyncio.to_thread(
                client.nodes(node).storage.get
            )
            
            storage_info = []
            for storage in storage_list:
                storage_name = storage.get('storage')
                storage_type = storage.get('type')
                
                # Get detailed storage info
                try:
                    details = await asyncio.to_thread(
                        client.nodes(node).storage(storage_name).status.get
                    )
                    
                    storage_info.append({
                        'storage': storage_name,
                        'type': storage_type,
                        'total': details.get('total', 0),
                        'used': details.get('used', 0),
                        'avail': details.get('avail', 0),
                        'active': details.get('active', 1),
                        'enabled': details.get('enabled', 1),
                        'content': storage.get('content', '').split(',')
                    })
                except Exception as e:
                    logger.warning(f"Could not get details for storage {storage_name}: {e}")
                    continue
            
            return storage_info
            
        except Exception as e:
            raise ProxmoxError(f"Failed to get storage for node {node}: {e}")

    async def get_best_storage(self, node: str, min_size_gb: int = 8) -> Dict[str, Any]:
        """
        Get the best storage pool for LXC container creation based on available space.
        
        Args:
            node: Proxmox node name
            min_size_gb: Minimum required size in GB (default 8GB)
            
        Returns:
            Dict with storage name and recommended size
        """
        try:
            storage_list = await self.get_node_storage(node)
            
            # Filter for storages that support rootdir (LXC containers)
            suitable_storages = [
                s for s in storage_list 
                if s.get('active') and 
                   s.get('enabled') and 
                   ('rootdir' in s.get('content', []) or 'images' in s.get('content', []))
            ]
            
            if not suitable_storages:
                raise ProxmoxError(f"No suitable storage found on node {node}")
            
            min_size_bytes = min_size_gb * 1024 * 1024 * 1024  # Convert GB to bytes
            
            # Filter by available space
            available_storages = [
                s for s in suitable_storages 
                if s.get('avail', 0) >= min_size_bytes
            ]
            
            if not available_storages:
                # Create a list of available storages for error message
                storage_list_str = ", ".join([
                    f"{s['storage']}: {s.get('avail', 0) / (1024**3):.1f}GB" 
                    for s in suitable_storages
                ])
                raise ProxmoxError(
                    f"No storage with at least {min_size_gb}GB available on node {node}. "
                    f"Available storages: {storage_list_str}"
                )
            
            # Select storage with most available space
            best_storage = max(available_storages, key=lambda s: s.get('avail', 0))
            
            avail_gb = best_storage.get('avail', 0) / (1024 ** 3)
            
            # Calculate recommended size (use min_size or 20% of available, whichever is larger, up to 50GB)
            recommended_size = min(max(min_size_gb, int(avail_gb * 0.2)), 50)
            
            logger.info(
                f"Selected storage '{best_storage['storage']}' on node {node}: "
                f"{avail_gb:.1f}GB available, allocating {recommended_size}GB"
            )
            
            return {
                'storage': best_storage['storage'],
                'size_gb': recommended_size,
                'avail_gb': avail_gb,
                'type': best_storage.get('type')
            }
            
        except Exception as e:
            if isinstance(e, ProxmoxError):
                raise
            raise ProxmoxError(f"Failed to select best storage: {e}")


# Singleton instance
proxmox_service = ProxmoxService()