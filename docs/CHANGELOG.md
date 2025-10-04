# Proximity Changelog

## [Unreleased]

### Security
- **CRITICAL**: Eliminated command injection vulnerability by replacing arbitrary command execution with predefined safe commands
- Implemented SafeCommandService with 10 read-only commands (logs, status, disk, processes, memory, network, images, volumes, config, system)
- Removed dangerous `/api/v1/apps/{app_id}/exec` endpoint
- Added comprehensive audit logging for all command executions
- See [Security Refactoring Documentation](SECURITY_REFACTORING_SAFE_COMMANDS.md) for details

### Changed
- **UI**: Replaced free-form command input with dropdown selector for safe commands
- **UI**: Added dynamic parameter forms for commands requiring input (logs tail, service name filtering)
- **UI**: Removed Deploy and Info buttons from app store cards (entire card is now clickable)
- **UI**: Enhanced app store card hover effects with primary color border and glow
- **API**: Changed from `localhost:8765` to relative URLs to fix CORS issues

### Added
- Enhanced error handling in app deletion with granular error tracking
- Added `openssh-wrapper` dependency for Proxmox SSH backend
- Improved ProxmoxService connection error messages
- New documentation:
  - `docs/SECURITY_REFACTORING_SAFE_COMMANDS.md` - Comprehensive security guide
  - `docs/SAFE_COMMANDS_REFERENCE.md` - Quick reference for safe commands
  - Safe Commands section in `docs/troubleshooting.md`

### Fixed
- Fixed CORS errors when accessing from localhost vs 127.0.0.1
- Fixed app deletion HTTP 500 errors with better error handling
- Fixed Proxmox startup errors related to missing openssh-wrapper
- Fixed spacing issues in Settings and Infrastructure pages

---

## [1.0.0] - October 4, 2025

### Major Refactoring
- **Database Migration**: Fully migrated from JSON file-based storage (`data/apps.json`) to SQLite database
- Eliminated all file I/O operations from `app_service.py`
- Implemented proper dependency injection with SQLAlchemy sessions
- Added database constraints for data integrity (unique hostnames, lxc_ids)

### Testing
- Comprehensive test suite with 250+ tests
- Added `test_database_models.py` (60+ tests)
- Added `test_database_transactions.py` (25+ tests)
- Added `test_error_handling.py` (40+ tests)
- Enhanced integration and API endpoint tests
- 80%+ code coverage achieved

### Database Schema
- **Users Table**: Authentication and authorization
  - Username and email uniqueness constraints
  - Password hashing with bcrypt
  - Role-based access control (admin/user)
- **Apps Table**: Application state management
  - Hostname and LXC ID uniqueness
  - Foreign key to users (ownership)
  - Status tracking and metadata
- **Audit Logs Table**: Comprehensive activity tracking
  - User actions logging
  - Timestamp and IP tracking
  - Metadata storage in JSON format

### Migration Tools
- `scripts/migrate_json_to_sqlite.py` - Automated migration from JSON to SQLite
- Automatic backup of original JSON data
- Owner assignment to first admin user

### Documentation
- Comprehensive documentation structure in `/docs`
- `docs/architecture.md` - System architecture overview
- `docs/deployment.md` - Deployment and operations guide
- `docs/development.md` - Development and contribution guide
- `docs/troubleshooting.md` - Common issues and solutions

---

## [0.9.0] - Initial Release

### Features
- Proxmox LXC container management
- Application catalog system
- Network appliance orchestration (Caddy reverse proxy)
- User authentication with JWT
- RESTful API with FastAPI
- Modern single-page application UI
- Real-time container monitoring
- Safe command execution console

### Supported Applications
- Nginx
- WordPress
- Nextcloud
- Jellyfin
- Gitea
- Portainer
- Uptime Kuma
- n8n
- Grafana
- Ghost
- Code Server

---

## Version History Notes

### Version Numbering
- **Major.Minor.Patch** (Semantic Versioning)
- **Major**: Breaking changes, major refactors
- **Minor**: New features, non-breaking changes
- **Patch**: Bug fixes, security patches

### Security Releases
Security updates are marked with **SECURITY** label and include:
- Vulnerability descriptions
- Impact assessment
- Remediation steps
- Credit to reporters (if external)

### Breaking Changes
Breaking changes are marked with **BREAKING** label and include:
- Description of the change
- Migration guide
- Deprecation timeline (if applicable)
