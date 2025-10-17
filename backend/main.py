import logging
import sys
import socket
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from core.config import settings as config_settings
from api.endpoints import apps, system, auth, settings, backups, test
from api.middleware.auth import get_current_user
from services.proxmox_service import ProxmoxError
from services.app_service import AppServiceError


# Define Sentry event processor BEFORE initialization
def _sentry_before_send(event, hint):
    """
    Custom event processor to filter and enrich Sentry events.
    This runs before events are sent to Sentry.
    """
    # Filter out non-error events in production
    if config_settings.SENTRY_ENVIRONMENT == "production":
        if event.get("level") not in ["error", "fatal"]:
            return None
    
    # Add application context
    event.setdefault("contexts", {})
    event["contexts"]["app"] = {
        "name": config_settings.APP_NAME,
        "version": config_settings.APP_VERSION,
        "debug_mode": config_settings.DEBUG,
        "environment": config_settings.SENTRY_ENVIRONMENT or "auto-detected",
    }
    
    # Add Proxmox context (without sensitive data)
    event["contexts"]["proxmox"] = {
        "host": config_settings.PROXMOX_HOST,
        "port": config_settings.PROXMOX_PORT,
        "verify_ssl": config_settings.PROXMOX_VERIFY_SSL,
    }
    
    # Add database context
    event["contexts"]["database"] = {
        "url_scheme": config_settings.DATABASE_URL.split("://")[0] if config_settings.DATABASE_URL else "unknown",
    }
    
    # Extract exception information for better debugging
    if "exception" in hint:
        exc = hint["exception"]
        event.setdefault("extra", {})
        event["extra"]["exception_type"] = type(exc).__name__
        event["extra"]["exception_module"] = type(exc).__module__
        
        # Add custom exception attributes if available
        if hasattr(exc, "__dict__"):
            custom_attrs = {k: str(v) for k, v in exc.__dict__.items() 
                          if not k.startswith("_") and k not in ["args", "with_traceback"]}
            if custom_attrs:
                event["extra"]["exception_attributes"] = custom_attrs
    
    # Add request context if available
    if "request" in event.get("contexts", {}):
        request_ctx = event["contexts"]["request"]
        event.setdefault("extra", {})
        # Add useful request information
        if "url" in request_ctx:
            event["extra"]["request_path"] = request_ctx["url"]
        if "method" in request_ctx:
            event["extra"]["request_method"] = request_ctx["method"]
    
    return event


# Initialize Sentry BEFORE any application logic
if config_settings.SENTRY_DSN:
    # Detect environment automatically if not explicitly set
    environment = config_settings.SENTRY_ENVIRONMENT
    if not environment:
        hostname = socket.gethostname()
        # Default to development for local/test environments
        if hostname in ["localhost", "127.0.0.1"] or "local" in hostname.lower() or "test" in hostname.lower():
            environment = "development"
        else:
            environment = "production"
    
    # Use APP_VERSION as release if not explicitly set
    release = config_settings.SENTRY_RELEASE or config_settings.APP_VERSION
    
    # Determine sampling rates based on environment
    if environment == "development":
        traces_sample_rate = 1.0  # 100% of transactions in development
        error_sample_rate = 1.0   # 100% of errors in development
    elif environment == "production":
        traces_sample_rate = 0.1  # 10% of transactions in production
        error_sample_rate = 1.0   # 100% of errors in production
    else:
        traces_sample_rate = 0.5  # 50% for other environments
        error_sample_rate = 1.0   # 100% of errors
    
    sentry_sdk.init(
        dsn=config_settings.SENTRY_DSN,
        environment=environment,
        release=release,
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",  # Group transactions by route
                failed_request_status_codes={500, 502, 503, 504},
            ),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above
                event_level=logging.ERROR  # Send events for ERROR and above
            ),
        ],
        traces_sample_rate=traces_sample_rate,
        sample_rate=error_sample_rate,  # Error sampling rate
        profiles_sample_rate=0.0,  # Disable profiling for now
        send_default_pii=False,  # Don't send personally identifiable information
        before_send=_sentry_before_send,  # Custom event processor
        attach_stacktrace=True,  # Attach stack traces to all messages
        max_breadcrumbs=50,  # Keep more breadcrumbs for better debugging (default is 100)
        debug=environment == "development",  # Enable debug output in development
    )
    
    # Set user context for non-authenticated requests
    sentry_sdk.set_tag("app_name", config_settings.APP_NAME)
    sentry_sdk.set_tag("app_version", config_settings.APP_VERSION)
    
    print(f"✓ Sentry initialized (environment={environment}, release={release})")
    print(f"  - Traces sample rate: {traces_sample_rate * 100}%")
    print(f"  - Error sample rate: {error_sample_rate * 100}%")
else:
    print("ℹ️  Sentry disabled (no SENTRY_DSN configured)")


# Configure logging
logging.basicConfig(
    level=getattr(logging, config_settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    logger.info("Starting Proximity API...")
    
    # Startup tasks
    try:
        # Step 0: Initialize Database
        logger.info("=" * 60)
        logger.info("STEP 0: Initializing Database")
        logger.info("=" * 60)

        from models.database import init_db
        init_db()
        logger.info("✓ Database initialized successfully")

        # Step 1: Initialize Proxmox Connection
        logger.info("=" * 60)
        logger.info("STEP 1: Connecting to Proxmox")
        logger.info("=" * 60)
        
        from services.proxmox_service import proxmox_service
        
        is_connected = await proxmox_service.test_connection()
        if is_connected:
            logger.info("✓ Proxmox connection successful")
        else:
            logger.warning("⚠ Proxmox connection failed - some features may not work")
        
        # Step 2: Simple networking with vmbr0 + DHCP
        logger.info("=" * 60)
        logger.info("STEP 2: Network Configuration")
        logger.info("=" * 60)
        logger.info("✓ Using vmbr0 with DHCP (simple and reliable)")
        
        # Step 2.5: Ensure optimized template exists
        logger.info("=" * 60)
        logger.info("STEP 2.5: Checking LXC Template")
        logger.info("=" * 60)
        
        try:
            from services.template_service import TemplateService
            
            template_service = TemplateService(proxmox_service)
            template_ready = await template_service.ensure_template_exists()
            
            if template_ready:
                logger.info("✓ Optimized Alpine+Docker template ready")
                logger.info("   • Deployments will be 50% faster!")
            else:
                logger.warning("⚠ Template creation failed - using fallback template")
                logger.warning("   • Deployments will take longer (Docker installation required)")
        
        except Exception as e:
            logger.error(f"Template check failed: {e}")
            logger.warning("⚠ Continuing with fallback template")
        
        # Step 3: Initialize app service (loads catalog)
        logger.info("=" * 60)
        logger.info("STEP 3: Loading Application Catalog")
        logger.info("=" * 60)
        
        from services.app_service import get_app_service
        from models.database import get_db
        
        # Get a database session for startup initialization
        db = next(get_db())
        try:
            app_service = get_app_service(db)
            catalog = await app_service.get_catalog()
            logger.info(f"✓ Loaded catalog with {catalog.total} applications")
        finally:
            db.close()
        
        # Step 4: Initialize Scheduler Service for AUTO mode
        logger.info("=" * 60)
        logger.info("STEP 4: Initializing Scheduler Service (AUTO Mode)")
        logger.info("=" * 60)

        try:
            from services.scheduler_service import SchedulerService
            from services.backup_service import get_backup_service

            # Get services with fresh db session
            db = next(get_db())
            try:
                app_service = get_app_service(db)
                backup_service = get_backup_service(db)

                # Create scheduler instance
                scheduler = SchedulerService(
                    backup_service=backup_service,
                    app_service=app_service
                )

                # Start the scheduler
                scheduler.start()

                # Store in app state
                app.state.scheduler = scheduler

                logger.info("✓ Scheduler Service initialized")
                logger.info("   • Daily backups scheduled for 2:00 AM")
                logger.info("   • Weekly update checks scheduled for Sunday 3:00 AM")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to initialize Scheduler Service: {e}")
            logger.warning("⚠ Continuing without scheduler")
            app.state.scheduler = None
        
        # Step 5: Initialize Cleanup Service
        logger.info("=" * 60)
        logger.info("STEP 5: Initializing Cleanup Service")
        logger.info("=" * 60)

        try:
            from services.cleanup_service import get_cleanup_service

            # Get cleanup service with fresh db session
            db = next(get_db())
            try:
                cleanup_service = get_cleanup_service(proxmox_service, db)
                
                # Run initial cleanup if enabled
                if cleanup_service and cleanup_service.config.enabled:
                    logger.info("Running initial cleanup check...")
                    stats = await cleanup_service.run_cleanup()
                    
                    if stats.total_removed > 0:
                        logger.info(f"✓ Initial cleanup: removed {stats.total_removed} stale records")
                    else:
                        logger.info("✓ No stale records found")
                    
                    # Start background cleanup
                    await cleanup_service.start_background_cleanup()
                    logger.info(f"✓ Cleanup service started (interval: {cleanup_service.config.cleanup_interval_minutes}m)")
                else:
                    logger.info("ℹ️  Cleanup service disabled")
                
                # Store in app state
                app.state.cleanup_service = cleanup_service

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to initialize Cleanup Service: {e}")
            logger.warning("⚠ Continuing without cleanup service")
            app.state.cleanup_service = None

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Don't fail startup, but log the error

    logger.info(f"🚀 Proximity API started on {config_settings.API_HOST}:{config_settings.API_PORT}")

    yield

    # Shutdown tasks
    logger.info("Shutting down Proximity API...")

    # Stop cleanup service if running
    if hasattr(app.state, 'cleanup_service') and app.state.cleanup_service:
        try:
            logger.info("Stopping cleanup service...")
            await app.state.cleanup_service.stop_background_cleanup()
            logger.info("✓ Cleanup service stopped")
        except Exception as e:
            logger.error(f"Error stopping cleanup service: {e}")

    # Stop scheduler if running
    if hasattr(app.state, 'scheduler') and app.state.scheduler:
        try:
            logger.info("Stopping scheduler...")
            app.state.scheduler.stop()
            logger.info("✓ Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=config_settings.APP_NAME,
        description="Self-hosted application delivery platform for Proxmox VE",
        version=config_settings.APP_VERSION,
        debug=config_settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if config_settings.DEBUG else None,
        redoc_url="/redoc" if config_settings.DEBUG else None,
        redirect_slashes=False,  # Disable automatic trailing slash redirects
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicit methods for CORS compliance
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],  # Explicit headers for CORS compliance
    )
    
    # Trusted host middleware (security)
    if not config_settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[config_settings.PROXMOX_HOST, "localhost", "127.0.0.1"]
        )
    
    # Exception handlers
    @app.exception_handler(ProxmoxError)
    async def proxmox_exception_handler(request: Request, exc: ProxmoxError):
        logger.error(f"Proxmox error: {exc}")
        
        # Add Sentry context for Proxmox errors
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("error_type", "proxmox")
            scope.set_context("proxmox_error", {
                "error_message": str(exc),
                "request_path": request.url.path,
                "request_method": request.method,
            })
            sentry_sdk.capture_exception(exc)
        
        return JSONResponse(
            status_code=502,
            content={"success": False, "error": "Proxmox API error", "details": str(exc)}
        )
    
    @app.exception_handler(AppServiceError)
    async def app_service_exception_handler(request: Request, exc: AppServiceError):
        logger.error(f"App service error: {exc}")
        
        # Add Sentry context for App Service errors
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("error_type", "app_service")
            scope.set_context("app_service_error", {
                "error_message": str(exc),
                "request_path": request.url.path,
                "request_method": request.method,
            })
            sentry_sdk.capture_exception(exc)
        
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Application service error", "details": str(exc)}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # Only capture 5xx errors to Sentry, not 4xx client errors
        if exc.status_code >= 500:
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("error_type", "http_exception")
                scope.set_tag("status_code", exc.status_code)
                scope.set_context("http_error", {
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                    "request_path": request.url.path,
                    "request_method": request.method,
                })
                sentry_sdk.capture_exception(exc)
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None)
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        # Capture unhandled exceptions with full context
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("error_type", "unhandled")
            scope.set_context("unhandled_exception", {
                "exception_type": type(exc).__name__,
                "exception_module": type(exc).__module__,
                "error_message": str(exc),
                "request_path": request.url.path,
                "request_method": request.method,
                "request_url": str(request.url),
            })
            # Add query parameters if present
            if request.query_params:
                scope.set_context("query_params", dict(request.query_params))
            
            sentry_sdk.capture_exception(exc)
        
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )
    
    # Middleware for request logging and Sentry context
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        # Handle OPTIONS requests for CORS preflight
        if request.method == "OPTIONS":
            return JSONResponse(
                content={},
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin, X-Requested-With",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Clear Sentry user context at the start of each request
        # Will be set later by auth middleware if user is authenticated
        sentry_sdk.set_user(None)
        
        # Add request breadcrumb for Sentry error tracking
        sentry_sdk.add_breadcrumb(
            category="request",
            message=f"{request.method} {request.url.path}",
            level="info",
            data={
                "url": str(request.url),
                "method": request.method,
                "client_host": request.client.host if request.client else None,
            }
        )
        
        start_time = request.state.start_time = logger.time() if hasattr(logger, 'time') else 0
        
        # Log request
        logger.info(f"{request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Log response
        if hasattr(logger, 'time'):
            process_time = logger.time() - start_time
            logger.info(f"{request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
        
        return response
    
    # Include routers
    # Auth router (UNPROTECTED - allows login/register)
    app.include_router(
        auth.router,
        prefix=f"/api/{config_settings.API_VERSION}/auth",
        tags=["Authentication"]
    )

    # System router - Public endpoints (UNPROTECTED)
    # Only /health and /status/initial are public - the rest need auth
    from api.endpoints.system import check_first_run, health_check
    public_system = APIRouter()
    public_system.add_api_route("/health", health_check, methods=["GET"])
    public_system.add_api_route("/status/initial", check_first_run, methods=["GET"])
    
    app.include_router(
        public_system,
        prefix=f"/api/{config_settings.API_VERSION}/system",
        tags=["System - Public"]
    )

    # Test router (PUBLIC - for debugging and monitoring)
    # Includes Sentry test endpoints and health checks
    app.include_router(
        test.router,
        prefix=f"/api/{config_settings.API_VERSION}",
        tags=["Test & Debugging"]
    )

    # Apps router (PROTECTED - requires authentication)
    app.include_router(
        apps.router,
        prefix=f"/api/{config_settings.API_VERSION}/apps",
        tags=["Applications"],
        dependencies=[Depends(get_current_user)]  # ← PROTECTED
    )

    # System router (PROTECTED - requires authentication)
    app.include_router(
        system.router,
        prefix=f"/api/{config_settings.API_VERSION}/system",
        tags=["System"],
        dependencies=[Depends(get_current_user)]  # ← PROTECTED
    )

    # Settings router (PROTECTED - admin only for most endpoints)
    app.include_router(
        settings.router,
        prefix=f"/api/{config_settings.API_VERSION}/settings",
        tags=["Settings"],
        dependencies=[Depends(get_current_user)]  # ← PROTECTED
    )

    # Backups router (PROTECTED - requires authentication)
    # Note: Backup routes are nested under apps (e.g., /api/v1/apps/{app_id}/backups)
    app.include_router(
        backups.router,
        prefix=f"/api/{config_settings.API_VERSION}",
        tags=["Backups"],
        dependencies=[Depends(get_current_user)]  # ← PROTECTED
    )

    # Serve static files (UI)
    static_dir = Path(__file__).parent / "frontend"

    @app.get("/")
    async def read_root():
        """Serve the main UI"""
        return FileResponse(static_dir / "index.html")

    @app.get("/favicon.ico")
    async def serve_favicon():
        """Serve the favicon"""
        return FileResponse(static_dir / "favicon.ico", media_type="image/x-icon")

    @app.get("/logo.png")
    async def serve_logo():
        """Serve the Proximity logo"""
        return FileResponse(static_dir / "logo.png", media_type="image/png")

    # Mount static file directory for all frontend assets
    app.mount("/js", StaticFiles(directory=static_dir / "js"), name="js")
    app.mount("/css", StaticFiles(directory=static_dir / "css"), name="css")
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/app.js")
    async def serve_app_js():
        """Serve the legacy JavaScript application"""
        response = FileResponse(static_dir / "app.js", media_type="application/javascript")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.get("/styles.css")
    async def serve_styles_css():
        """Serve the CSS stylesheet (legacy path)"""
        response = FileResponse(static_dir / "css" / "styles.css", media_type="text/css")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    @app.get("/api")
    async def api_root():
        """API root endpoint with basic information"""
        return {
            "project": config_settings.APP_NAME,
            "version": config_settings.APP_VERSION,
            "status": "running",
            "docs_url": f"/docs" if config_settings.DEBUG else "Disabled in production",
            "api_version": config_settings.API_VERSION
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Simple health check"""
        return {"status": "healthy", "version": config_settings.APP_VERSION}
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config_settings.API_HOST,
        port=config_settings.API_PORT,
        reload=config_settings.DEBUG,
        log_level=config_settings.LOG_LEVEL.lower(),
        access_log=True
    )