"""
LXC Template Management Service

Automatically creates and manages optimized LXC templates for Proximity.
The template includes Alpine Linux with Docker pre-installed for faster deployments.
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime

from services.proxmox_service import ProxmoxService, ProxmoxError
from core.config import settings

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing LXC templates"""
    
    TEMPLATE_NAME = "proximity-alpine-docker.tar.zst"
    TEMPLATE_STORAGE = "local"
    TEMP_VMID = 9999  # Temporary container ID for template creation
    BASE_ALPINE_TEMPLATE = "alpine-3.19-default_20231225_amd64.tar.xz"
    
    def __init__(self, proxmox_service: ProxmoxService):
        self.proxmox_service = proxmox_service
        self._creation_in_progress = False
        self._creation_start_time: Optional[datetime] = None
    
    async def ensure_template_exists(self) -> bool:
        """
        Ensure the optimized Proximity template exists.
        Creates it automatically if missing.
        
        Returns:
            bool: True if template exists or was created successfully
        """
        try:
            # Check if template already exists
            if await self.template_exists():
                logger.info(f"✓ Proximity template '{self.TEMPLATE_NAME}' already exists")
                return True
            
            # Template doesn't exist - create it
            logger.warning(f"⚠ Proximity template '{self.TEMPLATE_NAME}' not found")
            logger.info("🔧 Creating optimized Alpine+Docker template (this will take 2-3 minutes)...")
            
            success = await self.create_template()
            
            if success:
                logger.info(f"✓ Template '{self.TEMPLATE_NAME}' created successfully!")
                return True
            else:
                logger.error(f"✗ Failed to create template '{self.TEMPLATE_NAME}'")
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring template exists: {e}")
            return False
    
    async def template_exists(self) -> bool:
        """
        Check if the Proximity template exists in Proxmox storage.
        
        Returns:
            bool: True if template exists
        """
        try:
            # Get list of templates from storage
            templates = await self.proxmox_service.list_templates(self.TEMPLATE_STORAGE)
            
            # Check if our template is in the list
            template_path = f"{self.TEMPLATE_STORAGE}:vztmpl/{self.TEMPLATE_NAME}"
            
            for template in templates:
                if template.get('volid') == template_path:
                    return True
                if self.TEMPLATE_NAME in template.get('volid', ''):
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Could not check if template exists: {e}")
            return False
    
    async def create_template(self) -> bool:
        """
        Create the optimized Proximity template with Docker pre-installed.
        
        Steps:
        1. Create temporary LXC container with base Alpine
        2. Update Alpine and install Docker
        3. Configure Docker to start on boot
        4. Stop container
        5. Create template from container
        6. Cleanup temporary container
        
        Returns:
            bool: True if template was created successfully
        """
        if self._creation_in_progress:
            logger.warning("Template creation already in progress")
            return False
        
        self._creation_in_progress = True
        self._creation_start_time = datetime.now()
        temp_container_created = False
        
        try:
            node = await self.proxmox_service.get_best_node()
            
            # Step 1: Check if base Alpine template exists
            logger.info(f"📦 Step 1/7: Checking for base Alpine template...")
            base_template = await self._find_alpine_template()
            if not base_template:
                logger.error("✗ No Alpine base template found. Please download Alpine 3.19 template first.")
                logger.info("Run: pveam update && pveam download local alpine-3.19-default_20231225_amd64.tar.xz")
                return False
            logger.info(f"✓ Found base template: {base_template}")
            
            # Step 2: Create temporary container
            logger.info(f"📦 Step 2/7: Creating temporary container (VMID {self.TEMP_VMID})...")
            await self._create_temp_container(node, base_template)
            temp_container_created = True
            logger.info(f"✓ Temporary container created")
            
            # Step 3: Start container
            logger.info(f"📦 Step 3/7: Starting container...")
            start_task = await self.proxmox_service.start_lxc(node, self.TEMP_VMID)
            await self.proxmox_service.wait_for_task(node, start_task)
            await asyncio.sleep(5)  # Wait for network
            logger.info(f"✓ Container started")
            
            # Step 4: Install Docker
            logger.info(f"📦 Step 4/7: Installing Docker (this takes ~60 seconds)...")
            await self._install_docker(node)
            logger.info(f"✓ Docker installed and configured")
            
            # Step 5: Stop container
            logger.info(f"📦 Step 5/7: Stopping container...")
            await self._stop_temp_container(node)
            logger.info(f"✓ Container stopped")
            
            # Step 6: Create template
            logger.info(f"📦 Step 6/7: Creating template archive (this takes ~30 seconds)...")
            await self._create_template_archive(node)
            logger.info(f"✓ Template archive created")
            
            # Step 7: Cleanup
            logger.info(f"📦 Step 7/7: Cleaning up temporary container...")
            await self._cleanup_temp_container(node)
            temp_container_created = False
            logger.info(f"✓ Cleanup complete")
            
            elapsed = (datetime.now() - self._creation_start_time).total_seconds()
            logger.info(f"✓ Template creation completed in {elapsed:.1f} seconds")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Template creation failed: {e}", exc_info=True)
            
            # Cleanup on failure
            if temp_container_created:
                try:
                    logger.info("Cleaning up temporary container after failure...")
                    node = await self.proxmox_service.get_best_node()
                    await self._cleanup_temp_container(node)
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed: {cleanup_error}")
            
            return False
            
        finally:
            self._creation_in_progress = False
    
    async def _find_alpine_template(self) -> Optional[str]:
        """Find an available Alpine Linux template"""
        try:
            templates = await self.proxmox_service.list_templates(self.TEMPLATE_STORAGE)
            
            # Look for Alpine 3.19 first (preferred)
            for template in templates:
                volid = template.get('volid', '')
                if 'alpine-3.19' in volid.lower():
                    return volid
            
            # Fall back to any Alpine 3.x
            for template in templates:
                volid = template.get('volid', '')
                if 'alpine-3' in volid.lower():
                    logger.warning(f"Using older Alpine template: {volid}")
                    return volid
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding Alpine template: {e}")
            return None
    
    async def _create_temp_container(self, node: str, base_template: str):
        """Create temporary container for template creation"""
        config = {
            'hostname': 'proximity-template-builder',
            'password': 'temppass',  # Temporary password
            'cores': 2,
            'memory': 2048,
            'net0': 'name=eth0,bridge=vmbr0,ip=dhcp,firewall=1',
            'features': 'nesting=1,keyctl=1',
            'unprivileged': 1,
            'onboot': 0,  # Don't auto-start
            'description': 'Temporary container for Proximity template creation'
        }
        
        result = await self.proxmox_service.create_lxc(node, self.TEMP_VMID, config)
        await self.proxmox_service.wait_for_task(node, result['task_id'])
    
    async def _install_docker(self, node: str):
        """Install and configure Docker in the temporary container"""
        
        # Update Alpine and install Docker
        install_script = """
apk update && \
apk upgrade && \
apk add --no-cache docker docker-compose docker-cli-compose ca-certificates curl bash && \
rc-update add docker boot && \
service docker start && \
sleep 5 && \
docker --version && \
docker compose version
"""
        
        result = await self.proxmox_service.execute_in_container(
            node, 
            self.TEMP_VMID, 
            install_script.strip(),
            timeout=180  # 3 minutes for installation
        )
        
        logger.debug(f"Docker installation output: {result}")
        
        # Verify Docker is installed
        if 'Docker version' not in result and 'docker' not in result.lower():
            raise ProxmoxError("Docker installation verification failed")
    
    async def _stop_temp_container(self, node: str):
        """Stop the temporary container"""
        stop_task = await self.proxmox_service.stop_lxc(node, self.TEMP_VMID)
        await self.proxmox_service.wait_for_task(node, stop_task)
        await asyncio.sleep(3)  # Wait for clean shutdown
    
    async def _create_template_archive(self, node: str):
        """Create template archive from stopped container"""
        # Use vzdump to create template
        vzdump_command = f"""
vzdump {self.TEMP_VMID} \
  --compress zstd \
  --dumpdir /var/lib/vz/template/cache \
  --mode stop \
  --notes-template 'Proximity Alpine Docker Template - Created {datetime.now().isoformat()}'
"""
        
        # Execute vzdump via SSH or Proxmox API
        # For now, we'll use pct command to create a simple backup
        result = await self.proxmox_service.execute_command(
            node,
            f"vzdump {self.TEMP_VMID} --compress zstd --dumpdir /var/lib/vz/template/cache --mode stop",
            timeout=120
        )
        
        # Rename the created backup to our template name
        # Find the created file
        list_cmd = f"ls -t /var/lib/vz/template/cache/vzdump-lxc-{self.TEMP_VMID}-*.tar.zst | head -1"
        backup_file = await self.proxmox_service.execute_command(node, list_cmd)
        backup_file = backup_file.strip()
        
        if backup_file:
            # Move/rename to template name
            rename_cmd = f"mv '{backup_file}' /var/lib/vz/template/cache/{self.TEMPLATE_NAME}"
            await self.proxmox_service.execute_command(node, rename_cmd)
    
    async def _cleanup_temp_container(self, node: str):
        """Remove temporary container"""
        try:
            destroy_task = await self.proxmox_service.destroy_lxc(node, self.TEMP_VMID, force=True)
            await self.proxmox_service.wait_for_task(node, destroy_task)
        except Exception as e:
            logger.warning(f"Could not destroy temp container {self.TEMP_VMID}: {e}")
    
    async def get_template_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the Proximity template.
        
        Returns:
            dict: Template information or None if not found
        """
        try:
            templates = await self.proxmox_service.list_templates(self.TEMPLATE_STORAGE)
            template_path = f"{self.TEMPLATE_STORAGE}:vztmpl/{self.TEMPLATE_NAME}"
            
            for template in templates:
                if template.get('volid') == template_path or self.TEMPLATE_NAME in template.get('volid', ''):
                    return {
                        'name': self.TEMPLATE_NAME,
                        'path': template.get('volid'),
                        'size': template.get('size'),
                        'storage': self.TEMPLATE_STORAGE
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting template info: {e}")
            return None
