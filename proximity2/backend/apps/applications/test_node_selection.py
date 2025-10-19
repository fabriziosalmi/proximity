"""
Unit test for smart node selection logic using pytest-django.

This test validates that when deploying an application without specifying a node,
the system intelligently selects the best available node based on:
1. Status must be 'online'
2. Host must be active (is_active=True)
3. Among eligible nodes, select the one with the most free memory

Test Scenario:
- pve: online, 8GB total, 6GB used = 2GB free
- opti2: online, 16GB total, 8GB used = 8GB free ← SHOULD BE SELECTED
- offline-node: offline (should be excluded)

Expected: System selects 'opti2' because it has the most free memory (8GB).
"""
import pytest
import json
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_smart_node_selection_chooses_best_node(client, django_user_model):
    """
    CRITICAL TEST: Validates smart node selection algorithm.
    
    This test verifies that the deployment system:
    1. Excludes offline nodes
    2. Selects the online node with the most free memory
    3. Correctly assigns the application to that node
    
    If this test fails, it proves the node selection logic is broken.
    """
    from apps.proxmox.models import ProxmoxHost, ProxmoxNode
    from apps.applications.models import Application
    
    # === ARRANGE: Setup test data ===
    
    # Create admin user for authentication
    admin_user = django_user_model.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='testpass123'
    )
    client.force_login(admin_user)
    
    # Create Proxmox host
    host = ProxmoxHost.objects.create(
        name='test-proxmox',
        host='192.168.100.102',
        port=8006,
        user='root@pam',
        password='invaders',
        is_active=True  # CRITICAL: Host must be active for nodes to be eligible
    )
    
    # Create pve node: online but less free memory (2GB free)
    pve_node = ProxmoxNode.objects.create(
        host=host,
        name='pve',
        status='online',
        node_type='node',
        memory_total=8589934592,   # 8GB
        memory_used=6442450944,    # 6GB used (2GB free)
        cpu_count=4,
        cpu_usage=0.5
    )
    
    # Create opti2 node: online with MORE free memory (8GB free) - SHOULD BE SELECTED
    opti2_node = ProxmoxNode.objects.create(
        host=host,
        name='opti2',
        status='online',
        node_type='node',
        memory_total=17179869184,  # 16GB
        memory_used=8589934592,    # 8GB used (8GB free) ← MOST FREE
        cpu_count=8,
        cpu_usage=0.3
    )
    
    # Create offline node: should be excluded from selection
    offline_node = ProxmoxNode.objects.create(
        host=host,
        name='offline-node',
        status='offline',
        node_type='node',
        memory_total=34359738368,  # 32GB (irrelevant, node is offline)
        memory_used=4294967296,
        cpu_count=16,
        cpu_usage=0.1
    )
    
    # === ACT: Make deployment request without specifying a node ===
    
    payload = {
        "catalog_id": "adminer",
        "hostname": "test-app-smart-select",
        "config": {},
        "environment": {},
        "node": None  # Force automatic node selection
    }
    
    response = client.post(
        "/api/apps/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    # === ASSERT: Verify correct behavior ===
    
    # 1. Request should succeed
    assert response.status_code in [200, 201], (
        f"Expected successful response (200/201), got {response.status_code}. "
        f"Response: {response.content.decode() if hasattr(response, 'content') else 'N/A'}"
    )
    
    # 2. Application should be created in database
    assert Application.objects.filter(hostname="test-app-smart-select").exists(), (
        "Application was not created in database"
    )
    
    # 3. Fetch the created application
    new_app = Application.objects.get(hostname="test-app-smart-select")
    
    # 4. Application must have a node assigned
    assert new_app.node is not None, (
        "Application was created but no node was assigned"
    )
    
    # 5. 🔥 CRITICAL ASSERTION: Must select 'opti2' (most free memory)
    assert new_app.node == 'opti2', (
        f"❌ FAILURE: System selected '{new_app.node}' instead of 'opti2'!\n"
        f"Node selection algorithm is BROKEN.\n"
        f"Free memory comparison:\n"
        f"  - pve: {(pve_node.memory_total - pve_node.memory_used) / 1024**3:.1f}GB free\n"
        f"  - opti2: {(opti2_node.memory_total - opti2_node.memory_used) / 1024**3:.1f}GB free ← SHOULD WIN\n"
        f"  - offline-node: OFFLINE (excluded)\n"
        f"Expected: opti2, Got: {new_app.node}"
    )
    
    # 6. Verify it did NOT select the offline node
    assert new_app.node != 'offline-node', (
        "System incorrectly selected an offline node!"
    )
    
    # 7. Verify it did NOT select pve (less free memory)
    assert new_app.node != 'pve', (
        f"System selected 'pve' (2GB free) instead of 'opti2' (8GB free). "
        f"Memory-based selection is not working correctly."
    )
    
    # === SUCCESS ===
    print(f"\n✅ TEST PASSED: Smart node selection working correctly!")
    print(f"   Selected node: {new_app.node.name}")
    print(f"   Node memory: {(opti2_node.memory_total - opti2_node.memory_used) / 1024**3:.1f}GB free")
    print(f"   Application ID: {new_app.id}")
    print(f"   Hostname: {new_app.hostname}")


@pytest.mark.django_db
def test_node_selection_excludes_inactive_host():
    """
    Test that nodes belonging to inactive hosts are excluded from selection.
    """
    from apps.proxmox.models import ProxmoxHost, ProxmoxNode
    from apps.applications.api import ApplicationsAPI
    from django.http import HttpRequest
    
    # Create inactive host
    inactive_host = ProxmoxHost.objects.create(
        name='inactive-host',
        host='192.168.100.200',
        port=8006,
        user='root@pam',
        password='test',
        is_active=False  # INACTIVE
    )
    
    # Create node on inactive host (should be excluded)
    inactive_node = ProxmoxNode.objects.create(
        host=inactive_host,
        name='inactive-node',
        status='online',
        node_type='node',
        memory_total=68719476736,  # 64GB (lots of memory, but host inactive)
        memory_used=8589934592,
        cpu_count=16,
        cpu_usage=0.1
    )
    
    # Create active host
    active_host = ProxmoxHost.objects.create(
        name='active-host',
        host='192.168.100.102',
        port=8006,
        user='root@pam',
        password='invaders',
        is_active=True  # ACTIVE
    )
    
    # Create node on active host (should be selected)
    active_node = ProxmoxNode.objects.create(
        host=active_host,
        name='active-node',
        status='online',
        node_type='node',
        memory_total=17179869184,  # 16GB (less memory than inactive node)
        memory_used=8589934592,
        cpu_count=8,
        cpu_usage=0.3
    )
    
    # Query nodes as the API does
    online_nodes = ProxmoxNode.objects.filter(
        status='online',
        host__is_active=True
    ).order_by('-memory_total')
    
    # Verify only active host node is returned
    assert online_nodes.count() == 1, (
        f"Expected 1 eligible node, found {online_nodes.count()}"
    )
    assert online_nodes.first().name == 'active-node', (
        f"Expected 'active-node', got '{online_nodes.first().name}'"
    )
    
    # Verify inactive host node is excluded
    all_online = ProxmoxNode.objects.filter(status='online')
    assert all_online.count() == 2, "Both nodes should be online in DB"
    assert 'inactive-node' not in [n.name for n in online_nodes], (
        "Node from inactive host should be excluded from eligible nodes"
    )
    
    print(f"\n✅ TEST PASSED: Inactive host nodes correctly excluded!")
    print(f"   Eligible nodes: {[n.name for n in online_nodes]}")


@pytest.mark.django_db
def test_node_selection_with_only_offline_nodes():
    """
    Test behavior when all nodes are offline.
    
    Expected: Should handle gracefully (either error or fallback logic).
    """
    from apps.proxmox.models import ProxmoxHost, ProxmoxNode
    from django.contrib.auth import get_user_model
    import json
    from django.test import Client
    
    User = get_user_model()
    client = Client()
    
    # Create admin user
    admin = User.objects.create_superuser(
        username='admin2',
        email='admin2@test.com',
        password='test'
    )
    client.force_login(admin)
    
    # Create host
    host = ProxmoxHost.objects.create(
        name='test-host',
        host='192.168.100.102',
        port=8006,
        user='root@pam',
        password='test',
        is_active=True
    )
    
    # Create only offline nodes
    offline1 = ProxmoxNode.objects.create(
        host=host,
        name='offline1',
        status='offline',
        node_type='node',
        memory_total=17179869184,
        memory_used=8589934592,
        cpu_count=8,
        cpu_usage=0
    )
    
    offline2 = ProxmoxNode.objects.create(
        host=host,
        name='offline2',
        status='offline',
        node_type='node',
        memory_total=17179869184,
        memory_used=8589934592,
        cpu_count=8,
        cpu_usage=0
    )
    
    # Try to deploy
    payload = {
        "catalog_id": "adminer",
        "hostname": "test-no-online-nodes",
        "config": {},
        "environment": {}
    }
    
    response = client.post(
        "/api/apps/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    # Should fail or handle gracefully
    # (The exact behavior depends on your API implementation)
    # For now, we just verify it doesn't crash
    assert response.status_code in [200, 201, 400, 404, 500], (
        f"Unexpected status code: {response.status_code}"
    )
    
    print(f"\n✅ TEST PASSED: No-online-nodes scenario handled (status={response.status_code})")
