# Sentry Integration - Configuration Guide

## Overview

Proximity uses Sentry for comprehensive error tracking, performance monitoring, and debugging. The integration is configured to provide maximum visibility in development while being selective in production.

## Environment Configuration

### Development Environment
- **When**: Tests, local development, hostnames containing "local" or "test"
- **Traces Sample Rate**: 100% (all transactions tracked)
- **Error Sample Rate**: 100% (all errors captured)
- **Debug Mode**: Enabled (verbose Sentry logging)
- **Use Case**: Full visibility during development and testing

### Production Environment
- **When**: Production deployments, non-local hostnames
- **Traces Sample Rate**: 10% (performance sampling)
- **Error Sample Rate**: 100% (all errors captured)
- **Debug Mode**: Disabled
- **Event Filtering**: Only ERROR and FATAL level events sent
- **Use Case**: Optimized for production with focus on errors

## Configuration

### Environment Variables

```bash
# Required - Your Sentry DSN (leave empty to disable Sentry)
SENTRY_DSN=https://your-key@sentry.io/your-project

# Optional - Explicitly set environment (auto-detected if not set)
SENTRY_ENVIRONMENT=development  # or 'production'

# Optional - Release version (defaults to APP_VERSION)
SENTRY_RELEASE=0.1.0
```

### Auto-Detection

If `SENTRY_ENVIRONMENT` is not set, the environment is auto-detected:
- **development**: localhost, 127.0.0.1, or hostname contains "local" or "test"
- **production**: All other cases

## Context Information Captured

### 1. Application Context
Every event includes:
- Application name and version
- Debug mode status
- Environment (development/production)

### 2. Proxmox Context
Errors include (non-sensitive):
- Proxmox host (without credentials)
- Proxmox port
- SSL verification setting

### 3. Database Context
- Database URL scheme (e.g., "sqlite" or "postgresql")

### 4. User Context (when authenticated)
- User ID
- Username
- Email
- Role (admin/user)
- IP address

### 5. Request Context
- HTTP method
- URL path
- Query parameters
- Request headers (filtered for PII)

### 6. Exception Details
- Exception type and module
- Custom exception attributes
- Full stack trace
- Related breadcrumbs (last 50 actions)

## Error Handler Integration

### Proxmox Errors
```python
@app.exception_handler(ProxmoxError)
async def proxmox_exception_handler(request: Request, exc: ProxmoxError):
    # Automatically captured with:
    # - error_type: "proxmox" tag
    # - Full request context
    # - Proxmox-specific details
```

### App Service Errors
```python
@app.exception_handler(AppServiceError)
async def app_service_exception_handler(request: Request, exc: AppServiceError):
    # Automatically captured with:
    # - error_type: "app_service" tag
    # - Application operation context
```

### HTTP Exceptions
- **4xx errors**: Not captured (client errors)
- **5xx errors**: Captured with full context (server errors)

### Unhandled Exceptions
All unhandled exceptions are captured with:
- Full stack trace
- Request context
- Query parameters
- User information (if authenticated)

## Testing Configuration

During test execution:
- `SENTRY_ENVIRONMENT` is automatically set to "development"
- All test errors go to the development stream in Sentry
- Intentional test exceptions are captured for debugging
- Full context is preserved for test failure analysis

## Breadcrumbs

Sentry captures breadcrumbs (event trail) including:
- **HTTP Requests**: All API requests with method, path, status
- **Database Queries**: Important database operations
- **Background Tasks**: Backup operations, cleanups
- **User Actions**: Login, deployment, configuration changes
- **System Events**: Proxmox operations, container lifecycle

Maximum of 50 breadcrumbs kept (configurable).

## Tags for Filtering

Events are tagged for easy filtering in Sentry:

### Automatic Tags
- `app_name`: "Proximity"
- `app_version`: Current version
- `error_type`: proxmox | app_service | http_exception | unhandled
- `user_role`: admin | user
- `authenticated`: true | false
- `status_code`: HTTP status code (for HTTP errors)

### Custom Tags
You can add custom tags in your code:

```python
import sentry_sdk

sentry_sdk.set_tag("operation", "deploy_app")
sentry_sdk.set_tag("catalog_id", catalog_id)
```

## Performance Monitoring

### Transaction Naming
Transactions are grouped by API endpoint:
- `GET /api/v1/apps`
- `POST /api/v1/apps/deploy`
- `DELETE /api/v1/apps/{app_id}`

### Sampling
- **Development**: 100% of transactions
- **Production**: 10% of transactions
- Errors always include performance data regardless of sampling

## Best Practices

### 1. Development
- Use development environment for all testing and local work
- Check Sentry after running tests to see captured exceptions
- Review breadcrumbs to understand event flow

### 2. Production
- Monitor ERROR and FATAL events closely
- Use tags to filter by error type
- Check performance data for slow endpoints
- Set up alerts for critical errors

### 3. Adding Context
When you need more context in specific areas:

```python
import sentry_sdk

# Add custom context
with sentry_sdk.push_scope() as scope:
    scope.set_context("deployment", {
        "app_id": app_id,
        "catalog_id": catalog_id,
        "lxc_id": lxc_id,
    })
    # Your code here
```

### 4. Filtering Sensitive Data
The configuration already filters PII, but if you need more:

```python
# In before_send function
def _sentry_before_send(event, hint):
    # Remove sensitive data
    if "request" in event.get("contexts", {}):
        request = event["contexts"]["request"]
        # Filter headers, query params, etc.
    return event
```

## Troubleshooting

### Sentry Not Capturing Events
1. Check `SENTRY_DSN` is set
2. Verify environment is correct (`development` or `production`)
3. In production, ensure error level is ERROR or FATAL
4. Check network connectivity to Sentry

### Too Many Events
1. Increase sampling rate thresholds
2. Add more filters in `before_send`
3. Use error grouping to consolidate similar errors

### Missing Context
1. Check that middleware is running
2. Verify authentication is working
3. Add custom context as needed
4. Review breadcrumb configuration

## Monitoring Checklist

- [ ] Sentry DSN configured
- [ ] Development environment receiving test errors
- [ ] Production environment receiving real errors
- [ ] User context populating correctly
- [ ] Performance data showing up
- [ ] Breadcrumbs capturing important actions
- [ ] Alerts configured for critical errors
- [ ] Team members have Sentry access

## Example Queries

### In Sentry Dashboard

**All Proxmox Errors:**
```
error_type:proxmox
```

**Errors from Admin Users:**
```
user_role:admin
```

**Unhandled Exceptions:**
```
error_type:unhandled
```

**Production 5xx Errors:**
```
environment:production status_code:5*
```

## Support

For more information on Sentry:
- [Sentry Python SDK Documentation](https://docs.sentry.io/platforms/python/)
- [FastAPI Integration](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [Error Monitoring Best Practices](https://docs.sentry.io/product/error-monitoring/)
