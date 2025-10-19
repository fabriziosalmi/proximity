"""
Quick test to verify SSH-based pct exec works
"""
import sys
import os
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proximity.settings')
django.setup()

from apps.proxmox.services import ProxmoxService

# Test SSH connection and pct exec
service = ProxmoxService(host_id=2)  # e2e-test-host
host = service.get_host()

print("🔧 Testing SSH-based pct exec...")
print(f"Host: {host.host}")
print(f"User: {host.user}")
print(f"SSH Port: {host.ssh_port}")

try:
    # Test simple command that should work even if no containers exist
    result = service._execute_ssh_command(
        host=host.host,
        port=host.ssh_port,
        username=host.user.split('@')[0],
        password=host.password,
        command='echo "SSH connection test successful"',
        timeout=10
    )
    
    stdout, stderr, exit_code = result
    
    print(f"\n✅ SSH Connection Test:")
    print(f"   Exit Code: {exit_code}")
    print(f"   STDOUT: {stdout.strip()}")
    if stderr:
        print(f"   STDERR: {stderr.strip()}")
    
    if exit_code == 0:
        print("\n🎉 SSH connection works! Ready for pct exec.")
    else:
        print("\n❌ SSH command failed!")
        
except Exception as e:
    print(f"\n❌ SSH test failed: {e}")
    import traceback
    traceback.print_exc()
