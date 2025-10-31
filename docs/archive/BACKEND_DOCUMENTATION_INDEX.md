# Proximity Backend - Documentation Index

## Overview

This folder contains comprehensive documentation of the Proximity backend codebase, automatically generated through systematic exploration of the Django project structure, API endpoints, database models, and service implementations.

## Documentation Files

### 1. BACKEND_ARCHITECTURE.md (30 KB, 1066 lines)
**Comprehensive Technical Reference**

The definitive guide to the entire backend architecture. Use this for:
- Complete API endpoint reference with request/response examples
- Full database schema documentation
- Error handling patterns and exception hierarchy
- Authentication & authorization flow details
- Service layer architecture and patterns
- Celery task configuration and background processing
- Monitoring & observability (Sentry, logging)
- Design patterns used throughout the codebase
- Quick reference workflows for common operations

**Sections:**
- Executive Summary
- Backend Directory Structure
- Django Apps & Purposes (6 apps detailed)
- Complete API Endpoint Map (42+ endpoints)
- API Request/Response Schemas
- Database Models (8 models with all fields)
- Error Handling Patterns
- Authentication & Authorization
- Async/Background Tasks (Celery)
- Service Layer Architecture
- Monitoring & Observability
- Configuration & Deployment
- Key Design Patterns
- Testing & Validation
- Common Workflows
- Dependencies
- Future Improvements

### 2. BACKEND_QUICK_REFERENCE.md (8 KB)
**Fast Lookup Guide**

Quick reference for developers needing rapid answers. Use this for:
- API endpoints at a glance (organized by domain)
- HTTP response codes
- Common curl/API examples
- Database models quick map
- Deployment and backup flows
- Configuration checklist for production
- File location quick reference
- Security notes
- Common tasks (deploy, backup, adopt)

**Sections:**
- Core Fact Sheet
- Django Apps Overview
- API Endpoints at a Glance (by domain)
- Database Models Quick Map
- Response Codes
- Deployment Flow
- Backup Flow
- Important Patterns with code snippets
- Error Handling Summary
- Celery Periodic Tasks
- Configuration Checklist
- Common Tasks
- File Locations
- Security Notes
- Monitoring
- Testing Mode

### 3. BACKEND_SUMMARY.txt (22 KB)
**High-Level Exploration Report**

Executive summary of the exploration and systematic findings. Use this for:
- Understanding key architectural decisions
- Getting statistics and metrics
- Seeing complete breakdown of each component
- Understanding design patterns used
- Configuration requirements
- Overview of async tasks
- API endpoints summary

**Sections:**
- Key Findings (8 major findings)
- Documentation Files Overview
- Django Apps Breakdown (6 apps detailed)
- API Endpoints Summary (42 endpoints categorized)
- Database Models (8 models with structure)
- Async Task Processing
- Error Handling Patterns
- Key Design Patterns (10 patterns identified)
- File Organization Summary
- Configuration Notes
- Statistics and Metrics
- Exploration Completion Checklist

## Quick Start Navigation

### I want to...

**Understand the overall architecture**
→ Start with BACKEND_SUMMARY.txt (high-level overview)
→ Then read BACKEND_ARCHITECTURE.md (detailed documentation)

**Call an API endpoint**
→ BACKEND_QUICK_REFERENCE.md (endpoints at a glance)
→ BACKEND_ARCHITECTURE.md Section 4 (detailed request/response examples)

**Fix an API bug**
→ BACKEND_QUICK_REFERENCE.md (find endpoint)
→ BACKEND_ARCHITECTURE.md (find request/response schemas)
→ Check `/Users/fab/GitHub/proximity/backend/apps/*/api.py`

**Understand the deployment process**
→ BACKEND_QUICK_REFERENCE.md (Deployment Flow section)
→ BACKEND_ARCHITECTURE.md Section 14 (detailed workflow)
→ Check `/Users/fab/GitHub/proximity/backend/apps/applications/tasks.py`

**Deploy to production**
→ BACKEND_QUICK_REFERENCE.md (Configuration Checklist)
→ BACKEND_ARCHITECTURE.md Section 11 (Configuration & Deployment)

**Add a new API endpoint**
→ BACKEND_ARCHITECTURE.md Section 4 (API schemas)
→ Look at existing endpoint in `backend/apps/*/api.py`
→ Define Pydantic schema in `backend/apps/*/schemas.py`
→ Implement endpoint handler

**Debug an error**
→ BACKEND_QUICK_REFERENCE.md (Error Handling Summary)
→ BACKEND_ARCHITECTURE.md Section 6 (Error Handling Patterns)
→ Check Sentry integration details

**Understand async tasks**
→ BACKEND_QUICK_REFERENCE.md (Important Patterns)
→ BACKEND_ARCHITECTURE.md Section 8 (Async/Background Tasks)
→ Check `backend/apps/applications/tasks.py`

**Set up monitoring**
→ BACKEND_ARCHITECTURE.md Section 10 (Monitoring & Observability)
→ BACKEND_QUICK_REFERENCE.md (Monitoring section)

## File Structure for Easy Navigation

```
/Users/fab/GitHub/proximity/
├── BACKEND_ARCHITECTURE.md          ← COMPREHENSIVE REFERENCE
├── BACKEND_QUICK_REFERENCE.md       ← QUICK LOOKUP
├── BACKEND_SUMMARY.txt              ← EXECUTIVE SUMMARY
├── BACKEND_DOCUMENTATION_INDEX.md   ← THIS FILE
│
└── backend/                         ← ACTUAL SOURCE CODE
    ├── proximity/
    │   ├── settings.py              ← All config
    │   ├── urls.py                  ← API routes
    │   ├── auth.py                  ← JWT auth
    │   └── celery.py                ← Celery config
    │
    └── apps/
        ├── core/                    ← Users, settings
        ├── proxmox/                 ← Host management
        ├── applications/            ← Main app logic
        ├── backups/                 ← Backup logic
        ├── catalog/                 ← Catalog service
        └── monitoring/              ← (placeholder)
```

## Key Statistics

- **Django Apps**: 6 (core, proxmox, applications, backups, catalog, monitoring)
- **API Endpoints**: 42+ (organized by domain)
- **Database Models**: 8 (with relationships)
- **Celery Tasks**: 9+ (lifecycle + periodic)
- **Service Classes**: 3 (ProxmoxService, PortManagerService, CatalogService)
- **Documentation Lines**: 2000+ (across 3 files)

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Framework | Django 5.0 |
| API | Django Ninja (async-first) |
| Authentication | dj-rest-auth + simple-jwt (JWT) |
| Task Queue | Celery + Redis |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Validation | Pydantic |
| Monitoring | Sentry |
| Proxmox | proxmoxer + paramiko (SSH) |

## Key Concepts

### Authentication
- JWT tokens in HttpOnly cookies
- Global auth required (exceptions: /health, /auth/*)
- Admin checks for sensitive operations
- User ownership isolation

### Async Processing
- Celery tasks for long-running operations
- 202 Accepted responses (client polls for completion)
- Exponential backoff retries
- Deployment logging for audit trail

### Database
- 8 models with foreign key relationships
- Singleton pattern for system settings
- Deployment logs track multi-step processes

### Error Handling
- ProxmoxError for Proxmox API failures
- HttpError for API responses (400, 403, 404, 409, 500, 503)
- Sentry integration with event filtering

### Design Patterns
- Service layer (ProxmoxService, etc.)
- Singleton (SystemSettings)
- Transaction safety (create DB first, queue task after)
- Connection pooling (ProxmoxAPI client cached 5 min)
- Smart node selection (auto-select best available)

## How to Update Documentation

When making backend changes:

1. **If adding/modifying API endpoint:**
   - Update BACKEND_ARCHITECTURE.md Section 3
   - Update BACKEND_QUICK_REFERENCE.md API section

2. **If adding/modifying database model:**
   - Update BACKEND_ARCHITECTURE.md Section 5
   - Update BACKEND_QUICK_REFERENCE.md models section

3. **If adding new Celery task:**
   - Update BACKEND_ARCHITECTURE.md Section 8
   - Update BACKEND_SUMMARY.txt task list

4. **If changing configuration:**
   - Update BACKEND_ARCHITECTURE.md Section 11
   - Update BACKEND_QUICK_REFERENCE.md Configuration Checklist

## Contact & Support

For questions about:
- **Architecture**: See BACKEND_ARCHITECTURE.md
- **Quick answers**: See BACKEND_QUICK_REFERENCE.md
- **High-level overview**: See BACKEND_SUMMARY.txt

## Document History

- **Generated**: 2024-10-29
- **Explorer**: Claude Code (File Search Specialist)
- **Thoroughness**: Comprehensive (all apps, APIs, models explored)
- **Source**: Systematic exploration of backend codebase
- **Coverage**: 100% of main apps, APIs, models, error handling

---

**Total Documentation**: 38 KB across 3 files covering 2000+ lines
**Last Updated**: 2024-10-29
**Status**: Complete and comprehensive
