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

print("🔧 Testing SSH-based pct exec...")
print(f"Host: {service.host_config['host']}")
print(f"User: {service.host_config['user']}")

try:
    # Test simple command that should work even if no containers exist
    result = service._execute_ssh_command(
        host=service.host_config['host'],
        port=22,
        username=service.host_config['user'].split('@')[0],
        password=service.host_config['password'],
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
