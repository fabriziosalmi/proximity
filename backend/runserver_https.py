#!/usr/bin/env python
"""
Django HTTPS Development Server
Starts Django with SSL certificate for local HTTPS testing
"""
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proximity.settings')
    
    # Check if certificates exist
    cert_file = os.path.join(os.path.dirname(__file__), 'cert.pem')
    key_file = os.path.join(os.path.dirname(__file__), 'key.pem')
    
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("❌ SSL certificates not found!")
        print(f"Expected files: {cert_file}, {key_file}")
        sys.exit(1)
    
    print("🔒 Starting Django with HTTPS...")
    print(f"   Certificate: {cert_file}")
    print(f"   Key: {key_file}")
    
    # Import after setting environment
    from django.core.management import execute_from_command_line
    
    # Run Django with SSL using django-extensions runserver_plus
    sys.argv = [
        'manage.py',
        'runserver_plus',
        '0.0.0.0:8000',
        '--cert-file', cert_file,
        '--key-file', key_file
    ]
    execute_from_command_line(sys.argv)
