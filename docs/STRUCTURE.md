# Documentation Structure

This guide explains the organization of Proximity documentation.

## Root Level - Master Documents Only

These files provide project-wide visibility and should be kept minimal:

### Essential Files
- **`README.md`** - Project overview, quick links, and getting started
- **`STATUS.md`** - Current project status, progress tracking, and timeline
- **`SECURITY_SUMMARY.md`** - Comprehensive security audit results and remediation status
- **`CONTRIBUTING.md`** - Contribution guidelines and development setup

### Removed from Root
- Session-specific summaries → `/docs/archive/`
- Implementation checklists → `/docs/archive/`
- Temporary notes → `/docs/archive/`

## `/docs/` Folder Organization

### `/docs/security/`
Security-specific documentation
- `FRONTEND_SECURITY_AUDIT_REPORT.md` - Detailed frontend security analysis
- `BACKEND_SECURITY_AUDIT_REPORT.md` - Detailed backend security analysis
- `FRONTEND_FIXES_ROADMAP.md` - Frontend security fix implementation guide
- `BACKEND_FIXES_ROADMAP.md` - Backend security fix roadmap

### `/docs/guides/`
User and developer guides
- `QUICK_START.md` - Quick start guide
- `FRONTEND_QUICK_START.md` - Frontend development setup
- `BACKEND_QUICK_START.md` - Backend development setup
- `DEPLOYMENT.md` - Deployment instructions

### `/docs/architecture/`
System design and architecture documentation
- `FRONTEND_ARCHITECTURE.md` - Frontend architecture overview
- `BACKEND_ARCHITECTURE.md` - Backend architecture overview
- `DATABASE_SCHEMA.md` - Database design
- `API_DESIGN.md` - API design patterns

### `/docs/api/`
API documentation
- `ENDPOINTS.md` - REST API endpoints reference
- `AUTHENTICATION.md` - Auth flow and JWT handling
- `ERRORS.md` - Error codes and handling
- `EXAMPLES.md` - API usage examples

### `/docs/archive/`
Outdated or session-specific documents
- Historical session notes
- Superseded implementation plans
- Temporary working documents
- Reference materials no longer in use

## Test Organization

### Backend Tests
Location: `/backend/tests/` and `/backend/apps/*/tests/`

```
backend/
├── tests/                    # Root-level tests
│   ├── conftest.py          # Pytest fixtures
│   ├── test_auth.py         # Authentication tests
│   ├── test_models.py       # Model tests
│   ├── test_schemas.py      # Schema validation tests
│   ├── test_services.py     # Service layer tests
│   ├── test_utils.py        # Utility tests
│   ├── test_catalog_quick.py
│   ├── test_ssh_pct.py
│   └── test_sentry_integration.py
│
└── apps/
    ├── applications/
    │   ├── tests.py         # Application-specific tests
    │   └── test_node_selection.py
    ├── backups/
    │   ├── conftest.py      # Backup fixtures
    │   ├── test_api.py
    │   └── test_tasks.py
    └── catalog/
        ├── test_api.py
        └── tests.py
```

### Frontend Tests
Location: `/e2e_tests/`

```
e2e_tests/
├── conftest.py              # E2E test fixtures
├── test_*.py                # Individual test files
└── README.md                # E2E test documentation
```

### Running Tests
```bash
# All backend tests
cd backend && python manage.py test

# Specific app tests
cd backend && python manage.py test apps.applications

# E2E tests
npm run test:e2e

# With coverage
pytest --cov=backend/apps backend/tests
```

## File Structure Diagram

```
proximity/
├── STATUS.md                    ← PROJECT STATUS (MASTER)
├── SECURITY_SUMMARY.md          ← SECURITY STATUS (MASTER)
├── README.md                    ← PROJECT OVERVIEW
├── CONTRIBUTING.md              ← CONTRIBUTION GUIDE
│
├── docs/
│   ├── STRUCTURE.md             ← THIS FILE
│   ├── security/                ← Security documentation
│   │   ├── FRONTEND_SECURITY_AUDIT_REPORT.md
│   │   ├── BACKEND_SECURITY_AUDIT_REPORT.md
│   │   ├── FRONTEND_FIXES_ROADMAP.md
│   │   └── BACKEND_FIXES_ROADMAP.md
│   ├── guides/                  ← User & developer guides
│   │   ├── QUICK_START.md
│   │   ├── DEPLOYMENT.md
│   │   └── DEVELOPMENT.md
│   ├── architecture/            ← System design docs
│   │   ├── FRONTEND_ARCHITECTURE.md
│   │   ├── BACKEND_ARCHITECTURE.md
│   │   └── DATABASE_SCHEMA.md
│   ├── api/                     ← API documentation
│   │   ├── ENDPOINTS.md
│   │   ├── AUTHENTICATION.md
│   │   └── ERRORS.md
│   └── archive/                 ← Historical/superseded docs
│       ├── ATOMIC_AUTHSTORE_COMPLETE.md
│       ├── SESSION_SUMMARY_*.md
│       └── [other outdated docs]
│
├── backend/
│   ├── tests/                   ← Unit/integration tests
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_models.py
│   │   └── test_*.py
│   ├── apps/
│   │   ├── applications/
│   │   │   └── tests/
│   │   ├── backups/
│   │   │   └── tests/
│   │   └── [other apps]/
│   ├── proximity/               ← Django settings
│   ├── scripts/                 ← Dev scripts
│   └── manage.py
│
├── frontend/
│   ├── src/
│   │   ├── lib/                 ← Utilities & helpers
│   │   │   ├── logger.ts
│   │   │   ├── types/
│   │   │   └── errors.ts
│   │   └── routes/              ← Pages
│   ├── QUICK_START.md
│   └── FRONTEND_IMPLEMENTATION.md
│
└── e2e_tests/
    ├── conftest.py              ← E2E fixtures
    ├── test_*.py                ← E2E test suites
    └── README.md
```

## Documentation Best Practices

### When to Create New Documentation
1. **Major architectural changes** → `/docs/architecture/`
2. **API changes** → `/docs/api/`
3. **Security findings** → `/docs/security/`
4. **Setup/deployment changes** → `/docs/guides/`
5. **Historical notes/session summaries** → `/docs/archive/`

### When to Update Existing Documentation
1. Keep root-level files (`STATUS.md`, `SECURITY_SUMMARY.md`) updated with current progress
2. Update `/docs/security/` after security fixes
3. Update `/docs/guides/` when processes change
4. Archive documents when they become outdated (don't delete)

### Document Naming Conventions
- Use UPPERCASE for major documents: `SECURITY_AUDIT_REPORT.md`
- Use lowercase for guides: `quick_start.md`, `deployment.md`
- Use descriptive names: `FRONTEND_SECURITY_AUDIT_REPORT.md` not `AUDIT.md`
- Version important docs: `API_REFERENCE_v1.md` if multiple versions exist

## Maintenance

### Regular Updates (After Each Work Session)
- [ ] Update `STATUS.md` with current progress
- [ ] Update `SECURITY_SUMMARY.md` if security changes made
- [ ] Archive session-specific files to `/docs/archive/`
- [ ] Move completed roadmaps to archive

### Weekly Cleanup
- [ ] Review root-level .md files - keep only 4-6 active
- [ ] Check `/docs/` for orphaned or duplicate files
- [ ] Update cross-references between documents
- [ ] Archive any superseded documents

### Before Release
- [ ] Verify all documentation is current
- [ ] Check all links are valid
- [ ] Update version numbers
- [ ] Create release notes in `/docs/archive/RELEASES/`

---

Last Updated: 2025-10-30
