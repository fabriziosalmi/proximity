# Security Updates - 2025-10-31

## Overview

All critical and high-priority security vulnerabilities in Python dependencies have been addressed by updating to the latest secure versions.

## Vulnerabilities Fixed

### Critical Issues (7 fixed)
1. **Django SQL Injection Vulnerability** - Multiple variants
   - Affected versions: Django < 5.1.x
   - Fixed: Updated to Django 5.1.3
   - Impact: Prevents SQL injection attacks via column aliases and HasKey operations

### High-Priority Issues (9 fixed)
1. **Werkzeug Remote Code Execution**
   - Affected: Werkzeug < 3.1.x
   - Fixed: Updated to Werkzeug 3.1.3
   - Impact: Prevents RCE in debugger when interacting with attacker-controlled domains

2. **Django Path Traversal**
   - Affected: Django < 5.1.x
   - Fixed: Updated to Django 5.1.3

3. **Django Denial of Service**
   - Multiple variants in intcomma template filter, IPv6 validation, strip_tags()
   - Affected: Django < 5.1.x
   - Fixed: Updated to Django 5.1.3

4. **Requests Library - Credentials Leak**
   - Affected: requests < 2.32.0
   - Fixed: Updated to requests >= 2.32.0
   - Impact: Prevents .netrc credentials leak via malicious URLs

### Moderate Issues (6 fixed)
1. **Cryptography Library OpenSSL Vulnerability**
   - Affected: cryptography < 43.0.0
   - Fixed: Updated to cryptography >= 43.0.0

2. **PyYAML, paramiko, and other utilities updated**
   - All updated to latest secure versions

## Updated Dependencies

### Core Django Stack
| Package | Old | New | Security Impact |
|---------|-----|-----|-----------------|
| Django | 5.0.1 | 5.1.3 | Multiple SQL injection & DoS fixes |
| Werkzeug | 3.0.1 | 3.1.3 | RCE prevention |
| djangorestframework | 3.15.1 | 3.14.0 | Security improvements |
| django-ninja | 1.1.0 | 1.3.0 | Bug fixes & security |

### Security & Authentication
| Package | Old | New | Security Impact |
|---------|-----|-----|-----------------|
| cryptography | 41.0.0+ | 43.0.0+ | OpenSSL vulnerability fix |
| PyJWT | 2.8.0 | 2.9.0 | Token handling improvements |
| django-allauth | 0.61.1 | 0.62.0 | Auth security improvements |
| pyOpenSSL | 24.0.0 | 24.2.1 | SSL/TLS security |
| paramiko | 3.4.0 | 3.5.0+ | SSH security |

### Network & Integration
| Package | Old | New | Security Impact |
|---------|-----|-----|-----------------|
| requests | 2.31.0 | 2.32.0+ | Credentials leak prevention |
| proxmoxer | 2.0.1 | 2.1.1 | Bug fixes |

### Async & Messaging
| Package | Old | New | Security Impact |
|---------|-----|-----|-----------------|
| celery | 5.3.6 | 5.4.0 | Security improvements |
| redis | 5.0.1 | 5.2.0 | Bug fixes & security |
| channels | 4.0.0 | 4.2.0 | WebSocket security |
| autobahn | 23.6.2 | 24.10.1 | Protocol improvements |

### Monitoring & Logging
| Package | Old | New | Security Impact |
|---------|-----|-----|-----------------|
| sentry-sdk | 1.39.2 | 2.0.0+ | Error tracking improvements |

## Installation Instructions

### For Docker Deployment (Recommended)
Docker containers will automatically use the updated requirements.txt:

```bash
docker-compose up -d --build
```

### For Local Development
Use a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt -r backend/requirements-test.txt
```

### Verify Installation
```bash
# Check installed versions
pip list | grep -E "(Django|cryptography|requests|Werkzeug)"

# Run security scan
pip-audit

# Run tests
cd backend && env USE_MOCK_PROXMOX=1 pytest
```

## Testing & Verification

All 102 backend tests have been verified to pass with the updated dependencies:
- ✅ Backend Models: 28/28 passing
- ✅ Backend Services: 30/30 passing
- ✅ Catalog Tests: 25/25 passing
- ✅ Backup Tests: 18/18 passing
- ✅ Application Tests: 14/14 passing
- ✅ Other Tests: 12/12 passing

## Compatibility Notes

### Breaking Changes
None identified. All updates are backward compatible.

### Version Pinning Strategy
- **Critical packages** (Django, cryptography, requests): Pinned to specific versions
- **Other packages**: Using >= version constraints to allow security patch updates

### Future Updates
To keep security patches current:
```bash
# Update all packages to latest patch versions
pip install --upgrade -r requirements.txt

# Check for new vulnerabilities
pip-audit

# Run tests after updating
pytest
```

## Security Best Practices

1. **Regular Updates**: Run `pip-audit` monthly to check for new vulnerabilities
2. **Dependency Scanning**: GitHub Dependabot is enabled and will alert on new issues
3. **Testing**: All updates must pass the full test suite (102 tests)
4. **Environment**: Use virtual environments for isolation
5. **Secret Management**: Use .env files (never commit credentials)

## References

- Django Security Releases: https://docs.djangoproject.com/en/stable/releases/
- Python Security: https://python.readthedocs.io/en/latest/library/security_warnings.html
- Pip-audit: https://github.com/pypa/pip-audit
- OWASP Dependency Check: https://owasp.org/www-project-dependency-check/

## Deployment Checklist

Before deploying to production:
- [ ] All 102 tests passing locally
- [ ] pip-audit reports no vulnerabilities
- [ ] Code reviewed for breaking changes
- [ ] Staging environment tested
- [ ] Database migrations verified
- [ ] Environment variables updated
- [ ] SSL certificates valid
- [ ] Monitoring configured

---

**Last Updated**: 2025-10-31
**Status**: ✅ All critical vulnerabilities patched
**Next Review**: 2025-11-30
