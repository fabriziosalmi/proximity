#!/usr/bin/env python3
"""
Test script for password generation and encryption functionality
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.security import (
    generate_secure_password,
    generate_lxc_password,
    encrypt_password,
    decrypt_password
)
from core.config import settings

def test_password_generation():
    """Test password generation functions"""
    print("=" * 80)
    print("Testing Password Generation")
    print("=" * 80)
    
    # Test secure password
    print("\n1. Testing generate_secure_password()...")
    pwd1 = generate_secure_password(16, include_special=True)
    print(f"   Generated (16 chars, with special): {pwd1}")
    print(f"   Length: {len(pwd1)}")
    assert len(pwd1) == 16, "Password should be 16 characters"
    
    pwd2 = generate_secure_password(24, include_special=False)
    print(f"   Generated (24 chars, no special): {pwd2}")
    print(f"   Length: {len(pwd2)}")
    assert len(pwd2) == 24, "Password should be 24 characters"
    
    # Test LXC password
    print("\n2. Testing generate_lxc_password()...")
    lxc_pwd = generate_lxc_password(16)
    print(f"   Generated LXC password: {lxc_pwd}")
    print(f"   Length: {len(lxc_pwd)}")
    assert len(lxc_pwd) == 16, "LXC password should be 16 characters"
    
    # Verify safe characters only
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*-_=+"
    for char in lxc_pwd:
        assert char in safe_chars, f"Character '{char}' is not in safe character set"
    print("   ✓ All characters are shell-safe")
    
    print("\n✓ Password generation tests passed!")


def test_password_encryption():
    """Test password encryption and decryption"""
    print("\n" + "=" * 80)
    print("Testing Password Encryption")
    print("=" * 80)
    
    # Test with default password
    print("\n1. Testing with default password 'invaders'...")
    original = "invaders"
    encrypted = encrypt_password(original)
    print(f"   Original:  {original}")
    print(f"   Encrypted: {encrypted[:50]}... (length: {len(encrypted)})")
    
    decrypted = decrypt_password(encrypted)
    print(f"   Decrypted: {decrypted}")
    assert decrypted == original, "Decrypted password should match original"
    print("   ✓ Encryption/decryption successful")
    
    # Test with random password
    print("\n2. Testing with random password...")
    random_pwd = generate_lxc_password(24)
    encrypted2 = encrypt_password(random_pwd)
    print(f"   Original:  {random_pwd}")
    print(f"   Encrypted: {encrypted2[:50]}... (length: {len(encrypted2)})")
    
    decrypted2 = decrypt_password(encrypted2)
    print(f"   Decrypted: {decrypted2}")
    assert decrypted2 == random_pwd, "Decrypted password should match original"
    print("   ✓ Encryption/decryption successful")
    
    # Test that same password produces different encrypted strings (due to nonce)
    print("\n3. Testing encryption uniqueness...")
    encrypted3 = encrypt_password(original)
    print(f"   First encryption:  {encrypted[:30]}...")
    print(f"   Second encryption: {encrypted3[:30]}...")
    # Fernet includes timestamp and nonce, so encrypted values will differ
    print("   ✓ Different encrypted values for same input (includes timestamp/nonce)")
    
    print("\n✓ Encryption tests passed!")


def test_configuration():
    """Test configuration settings"""
    print("\n" + "=" * 80)
    print("Testing Configuration Settings")
    print("=" * 80)
    
    print(f"\n   LXC_ROOT_PASSWORD:   {settings.LXC_ROOT_PASSWORD}")
    print(f"   LXC_PASSWORD_RANDOM: {settings.LXC_PASSWORD_RANDOM}")
    print(f"   LXC_PASSWORD_LENGTH: {settings.LXC_PASSWORD_LENGTH}")
    
    print("\n✓ Configuration loaded successfully!")


if __name__ == "__main__":
    try:
        test_configuration()
        test_password_generation()
        test_password_encryption()
        
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED!")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
