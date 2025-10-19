"""
Docker Setup Service for Proximity 2.0
Handles Docker installation and app deployment inside LXC containers
"""
import logging
import yaml
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DockerSetupService:
    """Service to setup Docker and deploy applications inside LXC"""
    
    def __init__(self, proxmox_service):
        self.proxmox = proxmox_service
    
    async def setup_docker_in_ubuntu(self, node: str, vmid: int) -> bool:
        """
        Install Docker inside Ubuntu 22.04 LXC container.
        
        This method installs Docker using the official Docker convenience script
        which is the most reliable method for LXC containers.
        
        Args:
            node: Proxmox node name
            vmid: LXC container ID
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"[VMID {vmid}] 🐋 Setting up Docker in Ubuntu 22.04 LXC...")
            
            # Step 1: Wait for network to be ready
            logger.info(f"[VMID {vmid}] 🌐 Waiting for network to be ready...")
            import asyncio
            await asyncio.sleep(5)
            
            # Step 2: Update apt packages and install prerequisites
            logger.info(f"[VMID {vmid}] 📦 Updating apt packages and installing prerequisites...")
            await self.proxmox.execute_in_container(
                node, vmid,
                "apt-get update && apt-get install -y ca-certificates curl gnupg lsb-release",
                timeout=180
            )
            
            # Step 3: Download and install Docker using official convenience script
            logger.info(f"[VMID {vmid}] 🐳 Installing Docker using official script...")
            await self.proxmox.execute_in_container(
                node, vmid,
                "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && sh /tmp/get-docker.sh",
                timeout=300
            )
            
            # Step 4: Start Docker service
            logger.info(f"[VMID {vmid}] ▶️  Starting Docker service...")
            await self.proxmox.execute_in_container(
                node, vmid,
                "systemctl start docker && systemctl enable docker",
                timeout=60
            )
            
            # Step 5: Wait for Docker to be ready
            logger.info(f"[VMID {vmid}] ⏳ Waiting for Docker daemon to be ready...")
            await asyncio.sleep(5)
            
            # Step 6: Verify Docker is working
            logger.info(f"[VMID {vmid}] ✅ Verifying Docker installation...")
            docker_version = await self.proxmox.execute_in_container(
                node, vmid,
                "docker --version",
                timeout=30
            )
            
            logger.info(f"[VMID {vmid}] ✓ Docker installed: {docker_version.strip()}")
            
            # Step 7: Verify Docker Compose is available
            compose_version = await self.proxmox.execute_in_container(
                node, vmid,
                "docker compose version",
                timeout=30
            )
            logger.info(f"[VMID {vmid}] ✓ Docker Compose available: {compose_version.strip()}")
            
            return True
            
        except Exception as e:
            logger.error(f"[VMID {vmid}] ❌ Failed to setup Docker: {e}")
            logger.exception(f"[VMID {vmid}] Full traceback:")
            return False
    
    async def setup_docker_in_alpine(self, node: str, vmid: int) -> bool:
        """
        Install Docker inside Alpine LXC container.
        
        Args:
            node: Proxmox node name
            vmid: LXC container ID
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"[VMID {vmid}] 🐋 Setting up Docker in Alpine LXC...")
            
            # Step 1: Update Alpine packages
            logger.info(f"[VMID {vmid}] 📦 Updating Alpine packages...")
            await self.proxmox.execute_in_container(
                node, vmid,
                "apk update",
                timeout=120
            )
            
            # Step 2: Install Docker and Docker Compose
            logger.info(f"[VMID {vmid}] 🐳 Installing Docker and Docker Compose...")
            await self.proxmox.execute_in_container(
                node, vmid,
                "apk add --no-cache docker docker-cli-compose",
                timeout=180
            )
            
            # Step 3: Enable Docker service to start on boot
            logger.info(f"[VMID {vmid}] ⚙️ Enabling Docker service...")
            await self.proxmox.execute_in_container(
                node, vmid,
                "rc-update add docker default",
                timeout=30
            )
            
            # Step 4: Start Docker service
            logger.info(f"[VMID {vmid}] ▶️  Starting Docker service...")
            await self.proxmox.execute_in_container(
                node, vmid,
                "service docker start",
                timeout=60
            )
            
            # Step 5: Wait for Docker to be ready
            logger.info(f"[VMID {vmid}] ⏳ Waiting for Docker daemon to be ready...")
            import asyncio
            await asyncio.sleep(3)
            
            # Step 6: Verify Docker is working
            logger.info(f"[VMID {vmid}] ✅ Verifying Docker installation...")
            docker_version = await self.proxmox.execute_in_container(
                node, vmid,
                "docker --version",
                timeout=30
            )
            
            logger.info(f"[VMID {vmid}] ✓ Docker installed: {docker_version.strip()}")
            return True
            
        except Exception as e:
            logger.error(f"[VMID {vmid}] ❌ Failed to setup Docker: {e}")
            return False
    
    async def deploy_app_with_docker_compose(
        self, 
        node: str, 
        vmid: int,
        app_name: str,
        docker_compose_config: Dict[str, Any]
    ) -> bool:
        """
        Deploy application using Docker Compose inside LXC.
        
        Args:
            node: Proxmox node name
            vmid: LXC container ID
            app_name: Application name
            docker_compose_config: Docker Compose configuration dict
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"[VMID {vmid}] 🚀 Deploying {app_name} with Docker Compose...")
            
            # Step 1: Create docker-compose.yml content
            compose_yaml = yaml.dump(docker_compose_config, default_flow_style=False)
            
            # Escape single quotes for shell
            compose_yaml_escaped = compose_yaml.replace("'", "'\\''")
            
            # Step 2: Write docker-compose.yml to container
            logger.info(f"[VMID {vmid}] 📝 Creating docker-compose.yml...")
            await self.proxmox.execute_in_container(
                node, vmid,
                f"mkdir -p /root && echo '{compose_yaml_escaped}' > /root/docker-compose.yml",
                timeout=30
            )
            
            # Step 3: Pull Docker images
            logger.info(f"[VMID {vmid}] 📥 Pulling Docker images (this may take a while)...")
            await self.proxmox.execute_in_container(
                node, vmid,
                "cd /root && docker compose pull",
                timeout=600  # 10 minutes for pulling images
            )
            
            # Step 4: Start services with Docker Compose
            logger.info(f"[VMID {vmid}] ▶️  Starting Docker services...")
            await self.proxmox.execute_in_container(
                node, vmid,
                "cd /root && docker compose up -d",
                timeout=300  # 5 minutes for starting
            )
            
            # Step 5: Verify services are running
            logger.info(f"[VMID {vmid}] ✅ Verifying services...")
            import asyncio
            await asyncio.sleep(5)
            
            ps_output = await self.proxmox.execute_in_container(
                node, vmid,
                "cd /root && docker compose ps",
                timeout=30
            )
            
            logger.info(f"[VMID {vmid}] ✓ {app_name} deployed successfully!")
            logger.info(f"[VMID {vmid}] 📊 Docker services:\n{ps_output}")
            
            return True
            
        except Exception as e:
            logger.error(f"[VMID {vmid}] ❌ Failed to deploy {app_name}: {e}")
            return False
    
    def generate_adminer_compose(self, port: int = 80) -> Dict[str, Any]:
        """
        Generate Docker Compose configuration for Adminer.
        
        Args:
            port: External port to expose Adminer on
            
        Returns:
            Dict with Docker Compose configuration
        """
        return {
            'version': '3.8',
            'services': {
                'adminer': {
                    'image': 'adminer:latest',
                    'restart': 'always',
                    'ports': [f'{port}:8080'],
                    'environment': {
                        'ADMINER_DEFAULT_SERVER': 'localhost'
                    }
                }
            }
        }
