#!/usr/bin/env python3
"""
Integration test for LXC password functionality

This test verifies:
1. Password generation works correctly
2. Passwords are encrypted before storage
3. Passwords can be retrieved and decrypted
4. Configuration settings are respected
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.security import generate_lxc_password, encrypt_password, decrypt_password
from core.config import settings

def test_default_password_flow():
    """Test flow with default password"""
    print("=" * 80)
    print("Test 1: Default Password Flow")
    print("=" * 80)
    
    # Simulate what happens in proxmox_service.py
    root_password = None  # No password provided
    
    if root_password is None:
        if settings.LXC_PASSWORD_RANDOM:
            root_password = generate_lxc_password(settings.LXC_PASSWORD_LENGTH)
            print(f"✓ Generated random password: {root_password}")
        else:
            root_password = settings.LXC_ROOT_PASSWORD
            print(f"✓ Using default password: {root_password}")
    
    # Simulate what happens in app_service.py
    encrypted_password = encrypt_password(root_password)
    print(f"✓ Encrypted password: {encrypted_password[:50]}... (length: {len(encrypted_password)})")
    
    # Simulate retrieval
    decrypted_password = decrypt_password(encrypted_password)
    print(f"✓ Decrypted password: {decrypted_password}")
    
    assert decrypted_password == root_password, "Password mismatch!"
    print("✓ Test passed!\n")


def test_custom_password_flow():
    """Test flow with custom password"""
    print("=" * 80)
    print("Test 2: Custom Password Flow")
    print("=" * 80)
    
    # Simulate providing a custom password
    root_password = "my-custom-password-123!"
    print(f"✓ Using custom password: {root_password}")
    
    # Simulate what happens in app_service.py
    encrypted_password = encrypt_password(root_password)
    print(f"✓ Encrypted password: {encrypted_password[:50]}... (length: {len(encrypted_password)})")
    
    # Simulate retrieval
    decrypted_password = decrypt_password(encrypted_password)
    print(f"✓ Decrypted password: {decrypted_password}")
    
    assert decrypted_password == root_password, "Password mismatch!"
    print("✓ Test passed!\n")


def test_random_password_flow():
    """Test flow with random password generation"""
    print("=" * 80)
    print("Test 3: Random Password Flow")
    print("=" * 80)
    
    # Simulate random password generation (force it even if config says no)
    root_password = generate_lxc_password(settings.LXC_PASSWORD_LENGTH)
    print(f"✓ Generated random password: {root_password}")
    print(f"  Length: {len(root_password)}")
    
    # Verify it's unique each time
    root_password2 = generate_lxc_password(settings.LXC_PASSWORD_LENGTH)
    print(f"✓ Generated another: {root_password2}")
    assert root_password != root_password2, "Random passwords should be different!"
    
    # Simulate encryption and storage
    encrypted_password = encrypt_password(root_password)
    print(f"✓ Encrypted password: {encrypted_password[:50]}... (length: {len(encrypted_password)})")
    
    # Simulate retrieval
    decrypted_password = decrypt_password(encrypted_password)
    print(f"✓ Decrypted password: {decrypted_password}")
    
    assert decrypted_password == root_password, "Password mismatch!"
    print("✓ Test passed!\n")


def test_config_settings():
    """Test that configuration is loaded correctly"""
    print("=" * 80)
    print("Test 4: Configuration Settings")
    print("=" * 80)
    
    print(f"✓ LXC_ROOT_PASSWORD: {settings.LXC_ROOT_PASSWORD}")
    print(f"✓ LXC_PASSWORD_RANDOM: {settings.LXC_PASSWORD_RANDOM}")
    print(f"✓ LXC_PASSWORD_LENGTH: {settings.LXC_PASSWORD_LENGTH}")
    
    assert settings.LXC_ROOT_PASSWORD == "invaders", "Default password should be 'invaders'"
    assert settings.LXC_PASSWORD_RANDOM == False, "Random generation should be disabled by default"
    assert settings.LXC_PASSWORD_LENGTH == 16, "Password length should be 16"
    
    print("✓ All configuration values are correct!\n")


def test_multiple_containers():
    """Test that each container can have a different password"""
    print("=" * 80)
    print("Test 5: Multiple Containers with Different Passwords")
    print("=" * 80)
    
    containers = []
    
    # Simulate deploying 3 containers with random passwords
    for i in range(3):
        password = generate_lxc_password(16)
        encrypted = encrypt_password(password)
        
        containers.append({
            'id': f'container-{i+1}',
            'password_plain': password,
            'password_encrypted': encrypted
        })
        
        print(f"✓ Container {i+1}: password={password}, encrypted={encrypted[:30]}...")
    
    # Verify all passwords are different
    passwords = [c['password_plain'] for c in containers]
    assert len(set(passwords)) == 3, "All passwords should be unique!"
    print("✓ All 3 containers have unique passwords")
    
    # Verify each can be decrypted correctly
    for container in containers:
        decrypted = decrypt_password(container['password_encrypted'])
        assert decrypted == container['password_plain'], f"Password mismatch for {container['id']}"
        print(f"✓ {container['id']} password decryption successful")
    
    print("✓ Test passed!\n")


if __name__ == "__main__":
    try:
        test_config_settings()
        test_default_password_flow()
        test_custom_password_flow()
        test_random_password_flow()
        test_multiple_containers()
        
        print("=" * 80)
        print("✓ ALL INTEGRATION TESTS PASSED!")
        print("=" * 80)
        print()
        print("Summary:")
        print("  - Configuration loading works correctly")
        print("  - Default password flow works")
        print("  - Custom password flow works")
        print("  - Random password generation works")
        print("  - Multiple containers can have different passwords")
        print("  - Encryption/decryption is reliable")
        print()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
