#!/usr/bin/env python
"""
Sentry Integration Test Script

This script performs a comprehensive test of Sentry integration,
sending a test error with rich context and metadata to verify
the complete observability stack.

Usage:
    python scripts/test_sentry_integration.py
    
Or from Docker:
    docker exec proximity2_backend python scripts/test_sentry_integration.py
"""

import os
import sys
import django
import sentry_sdk
from datetime import datetime
import logging

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proximity.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.proxmox.models import ProxmoxHost, ProxmoxNode
from apps.applications.models import Application

User = get_user_model()

# Setup logging
logger = logging.getLogger(__name__)

def test_sentry_with_full_context():
    """
    Send a comprehensive test error to Sentry with:
    - User context
    - Custom tags
    - Breadcrumbs
    - Extra data
    - Transaction context
    """
    
    print("=" * 80)
    print("🧪 SENTRY INTEGRATION TEST - Full Context")
    print("=" * 80)
    
    # Step 1: Get or create a test user for context
    print("\n📋 Step 1: Setting up user context...")
    try:
        test_user = User.objects.filter(username='sentry_test_user').first()
        if not test_user:
            test_user = User.objects.create_user(
                username='sentry_test_user',
                email='sentry.test@proximity.local',
                password='test123'
            )
            print(f"   ✅ Created test user: {test_user.username}")
        else:
            print(f"   ✅ Using existing test user: {test_user.username}")
        
        # Set user context in Sentry
        sentry_sdk.set_user({
            "id": test_user.id,
            "username": test_user.username,
            "email": test_user.email,
            "ip_address": "192.168.100.1",  # Simulated IP
        })
        print("   ✅ Sentry user context set")
        
    except Exception as e:
        print(f"   ⚠️  Warning: Could not set user context: {e}")
    
    # Step 2: Add custom tags
    print("\n🏷️  Step 2: Adding custom tags...")
    sentry_sdk.set_tag("environment", os.getenv("SENTRY_ENVIRONMENT", "development"))
    sentry_sdk.set_tag("service", "proximity-backend")
    sentry_sdk.set_tag("test_type", "integration_test")
    sentry_sdk.set_tag("component", "sentry_verification")
    sentry_sdk.set_tag("severity", "high")
    print("   ✅ Tags added: environment, service, test_type, component, severity")
    
    # Step 3: Add breadcrumbs (user activity trail)
    print("\n🍞 Step 3: Adding breadcrumbs...")
    sentry_sdk.add_breadcrumb(
        category='navigation',
        message='User navigated to Sentry test page',
        level='info',
        data={'page': '/admin/sentry-test', 'method': 'GET'}
    )
    sentry_sdk.add_breadcrumb(
        category='user.action',
        message='User clicked "Test Sentry Integration" button',
        level='info',
        data={'button_id': 'sentry-test-btn', 'timestamp': datetime.now().isoformat()}
    )
    sentry_sdk.add_breadcrumb(
        category='database',
        message='Querying Proxmox hosts',
        level='info',
        data={'query': 'ProxmoxHost.objects.all()', 'count': ProxmoxHost.objects.count()}
    )
    sentry_sdk.add_breadcrumb(
        category='http',
        message='API call to Proxmox server',
        level='info',
        data={'url': 'https://192.168.100.102:8006/api2/json/nodes', 'method': 'GET'}
    )
    print("   ✅ Breadcrumbs added: navigation, user action, database, http")
    
    # Step 4: Set context (extra data)
    print("\n📦 Step 4: Adding context data...")
    sentry_sdk.set_context("application_state", {
        "total_hosts": ProxmoxHost.objects.count(),
        "total_nodes": ProxmoxNode.objects.count(),
        "total_applications": Application.objects.count(),
        "active_deployments": Application.objects.filter(status='running').count(),
        "failed_deployments": Application.objects.filter(status='error').count(),
    })
    
    sentry_sdk.set_context("test_metadata", {
        "test_name": "Full Sentry Integration Test",
        "test_timestamp": datetime.now().isoformat(),
        "test_purpose": "Verify Sentry observability stack",
        "expected_outcome": "Error captured with full context in Sentry dashboard",
    })
    
    sentry_sdk.set_context("system_info", {
        "django_debug": os.getenv("DEBUG", "False"),
        "sentry_dsn_configured": bool(os.getenv("SENTRY_DSN")),
        "sentry_environment": os.getenv("SENTRY_ENVIRONMENT", "unknown"),
        "traces_sample_rate": os.getenv("SENTRY_TRACES_SAMPLE_RATE", "unknown"),
    })
    print("   ✅ Context added: application_state, test_metadata, system_info")
    
    # Step 5: Start a transaction for performance monitoring
    print("\n⚡ Step 5: Starting performance transaction...")
    with sentry_sdk.start_transaction(
        op="test",
        name="sentry_integration_test",
        description="Comprehensive Sentry integration verification"
    ) as transaction:
        
        transaction.set_tag("transaction_type", "integration_test")
        
        # Simulate some work with spans
        with sentry_sdk.start_span(op="db.query", description="Query database"):
            hosts = list(ProxmoxHost.objects.all())
            print(f"   ✅ Span: Database query completed ({len(hosts)} hosts)")
        
        with sentry_sdk.start_span(op="processing", description="Process data"):
            import time
            time.sleep(0.1)  # Simulate processing
            print("   ✅ Span: Data processing completed")
        
        # Step 6: Capture the test error
        print("\n💥 Step 6: Raising test error with full context...")
        try:
            # This will trigger the error
            result = 1 / 0
        except ZeroDivisionError as e:
            # Capture with additional context
            sentry_sdk.capture_exception(e)
            print("   ✅ Error captured and sent to Sentry!")
            
            # Also log it
            print(f"\n   Error Type: {type(e).__name__}")
            print(f"   Error Message: {str(e)}")
            
    # Step 7: Send a custom message
    print("\n📨 Step 7: Sending custom message...")
    sentry_sdk.capture_message(
        "Sentry Integration Test Completed Successfully",
        level="info",
        extras={
            "test_completion_time": datetime.now().isoformat(),
            "all_steps_passed": True,
        }
    )
    print("   ✅ Custom message sent")
    
    # Step 8: Test logging integration
    print("\n📝 Step 8: Testing logging integration...")
    logger.info('User triggered test log', extra={
        'log_source': 'sentry_test',
        'test_type': 'integration',
        'user': 'sentry_test_user'
    })
    print("   ✅ Log sent via Python logging")
    
    logger.warning('Test warning message', extra={
        'log_source': 'sentry_test',
        'severity': 'medium'
    })
    print("   ✅ Warning log sent")
    
    logger.error('Test error log (not an exception)', extra={
        'log_source': 'sentry_test',
        'severity': 'high'
    })
    print("   ✅ Error log sent")
    
    # Step 9: Test with different log levels
    print("\n📊 Step 9: Testing multiple log levels...")
    for level, message in [
        ('debug', 'Debug level test message'),
        ('info', 'Info level test message'),
        ('warning', 'Warning level test message'),
        ('error', 'Error level test message'),
    ]:
        getattr(logger, level)(message, extra={'log_source': 'sentry_test', 'level': level})
    print("   ✅ All log levels tested (debug, info, warning, error)")
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE - Check your Sentry dashboard!")
    print("=" * 80)
    print("\n📊 What was sent to Sentry:")
    print("   • 1 x Exception (ZeroDivisionError)")
    print("   • 1 x Info Message (Test completion)")
    print("   • 1 x Transaction (with 2 spans)")
    print("   • 4 x Breadcrumbs (navigation trail)")
    print("   • 5 x Tags (metadata)")
    print("   • 3 x Context objects (extra data)")
    print("   • 1 x User context (authenticated user)")
    print("   • 6 x Log messages (info, warning, error, debug)")
    
    print("\n🔗 Check Sentry Dashboard:")
    print("   https://sentry.io/organizations/fabriziosalmi/issues/")
    
    print("\n💡 Expected in Sentry:")
    print("   • Error: ZeroDivisionError: division by zero")
    print("   • User: sentry_test_user (sentry.test@proximity.local)")
    print("   • Tags: environment, service, test_type, component, severity")
    print("   • Breadcrumbs showing navigation → button click → DB query → API call")
    print("   • Context: Application state, test metadata, system info")
    print("   • Transaction: sentry_integration_test with timing data")
    print("   • Logs: Multiple log entries with different severity levels")
    
    print("\n" + "=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        test_sentry_with_full_context()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
