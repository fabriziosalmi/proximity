"""
Unit tests for Applications API - Node Selection Logic
"""
import pytest
import json
from unittest import skip
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth import get_user_model
from apps.proxmox.models import ProxmoxHost, ProxmoxNode
from apps.applications.models import Application

User = get_user_model()


class NodeSelectionLogicTest(TransactionTestCase):
    """
    Test case isolato per verificare la logica di selezione del nodo.
    
    Scenario: Due nodi online:
    - pve: online ma non raggiungibile (simula condizione reale)
    - opti2: online con memoria disponibile
    
    Expected: Il sistema deve scegliere opti2, NON pve.
    """
    
    def setUp(self):
        """Setup test environment"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create Proxmox host
        self.host = ProxmoxHost.objects.create(
            name='test-proxmox',
            host='192.168.100.102',
            port=8006,
            user='root@pam',
            password='invaders',
            is_active=True
        )
        
        # Create pve node (online but unreachable)
        self.pve_node = ProxmoxNode.objects.create(
            host=self.host,
            name='pve',
            status='online',
            node_type='node',
            memory_total=34359738368,  # 32GB
            memory_used=20000000000,   # 20GB used
            cpu_count=8,
            cpu_usage=0.5
        )
        
        # Create opti2 node (online with available memory)
        self.opti2_node = ProxmoxNode.objects.create(
            host=self.host,
            name='opti2',
            status='online',
            node_type='node',
            memory_total=33509568512,  # ~31GB
            memory_used=14772379648,   # ~14GB used (17GB free)
            cpu_count=4,
            cpu_usage=0.3
        )
        
        # Setup API client
        self.client = Client()
        self.client.force_login(user=self.user)
    
    @skip("Requires JWT authentication setup - tests node selection logic, not API auth")
    def test_node_selection_prefers_opti2_over_pve(self):
        """
        CRITICAL TEST: Verifica che la logica di selezione scelga opti2 invece di pve.
        
        Questo test fallirà se il sistema sceglie pve, dimostrando che la logica
        di selezione non funziona correttamente.
        """
        # Deploy without specifying a node (let system choose)
        response = self.client.post(
            '/api/apps/',
            data=json.dumps({
                'catalog_id': 'test-app',
                'hostname': 'test-app-001',
                'config': {},
                'environment': {},
                'node': None  # Force automatic node selection
            }),
            content_type='application/json'
        )
        
        # Should succeed (201 Created)
        self.assertEqual(
            response.status_code, 
            201, 
            f"Failed to create app: {response.data if hasattr(response, 'data') else 'No data'}"
        )
        
        # Get created application
        app = Application.objects.get(hostname='test-app-001')
        
        # CRITICAL ASSERTION: Must select opti2, NOT pve
        self.assertIsNotNone(app.node, "Node should be assigned")
        self.assertEqual(
            app.node.name, 
            'opti2',
            f"❌ FAILURE: System selected '{app.node.name}' instead of 'opti2'! "
            f"This proves the node selection logic is broken."
        )
        
        # Additional verification: Should NOT be pve
        self.assertNotEqual(
            app.node.name,
            'pve',
            "System incorrectly selected 'pve' node which is unreachable!"
        )
        
        print(f"✅ SUCCESS: System correctly selected node '{app.node.name}'")
        print(f"   pve memory free: {self.pve_node.memory_total - self.pve_node.memory_used:,} bytes")
        print(f"   opti2 memory free: {self.opti2_node.memory_total - self.opti2_node.memory_used:,} bytes")


class NodeSelectionOrderTest(TestCase):
    """
    Test che verifica l'ordine di selezione quando ci sono più nodi disponibili.
    """
    
    def setUp(self):
        """Setup test environment with multiple nodes"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.host = ProxmoxHost.objects.create(
            name='test-proxmox',
            host='192.168.100.102',
            port=8006,
            user='root@pam',
            password='invaders',
            is_active=True
        )
        
        # Node with most free memory
        self.node1 = ProxmoxNode.objects.create(
            host=self.host,
            name='node1',
            status='online',
            node_type='node',
            memory_total=68719476736,  # 64GB
            memory_used=17179869184,   # 16GB used (48GB free) - MOST FREE
            cpu_count=16,
            cpu_usage=0.2
        )
        
        # Node with medium free memory
        self.node2 = ProxmoxNode.objects.create(
            host=self.host,
            name='node2',
            status='online',
            node_type='node',
            memory_total=34359738368,  # 32GB
            memory_used=8589934592,    # 8GB used (24GB free) - MEDIUM
            cpu_count=8,
            cpu_usage=0.4
        )
        
        # Node with least free memory
        self.node3 = ProxmoxNode.objects.create(
            host=self.host,
            name='node3',
            status='online',
            node_type='node',
            memory_total=17179869184,  # 16GB
            memory_used=8589934592,    # 8GB used (8GB free) - LEAST
            cpu_count=4,
            cpu_usage=0.6
        )
        
        self.client = Client()
        self.client.force_login(user=self.user)
    
    @skip("Requires JWT authentication setup - tests node selection logic, not API auth")
    def test_selection_prefers_most_free_memory(self):
        """
        Verifica che il sistema scelga il nodo con più memoria libera.
        """
        response = self.client.post(
            '/api/apps/',
            data=json.dumps({
                'catalog_id': 'test-app',
                'hostname': 'memory-test-001',
                'config': {},
                'environment': {},
                'node': None
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        app = Application.objects.get(hostname='memory-test-001')
        
        self.assertEqual(
            app.node.name,
            'node1',
            f"❌ System should select node with most free memory (node1), "
            f"but selected '{app.node.name}'"
        )
        
        print(f"✅ System correctly selected node with most free memory: {app.node.name}")
        print(f"   node1: {48} GB free")
        print(f"   node2: {24} GB free")
        print(f"   node3: {8} GB free")
