import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from core.config import settings as config_settings
from api.endpoints import apps, system, auth, settings
from api.middleware.auth import get_current_user
from services.proxmox_service import ProxmoxError
from services.app_service import AppServiceError

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
        
        # Step 2: Initialize Network Appliance (Platinum Edition with proximity-lan)
        logger.info("=" * 60)
        logger.info("STEP 2: Initializing Network Appliance (Platinum Edition)")
        logger.info("=" * 60)
        logger.info("🌐 Deploying proximity-lan bridge and network appliance...")
        
        from services.network_appliance_orchestrator import NetworkApplianceOrchestrator
        
        orchestrator = NetworkApplianceOrchestrator(proxmox_service)
        network_init_success = await orchestrator.initialize()
        
        if not network_init_success:
            logger.warning("⚠️  Network appliance initialization failed")
            logger.info("ℹ️  Containers will use default Proxmox networking (vmbr0)")
            orchestrator = None
        else:
            logger.info("✅ Network Appliance ready:")
            if orchestrator.appliance_info:
                logger.info(f"   • Bridge: proximity-lan (10.20.0.0/24)")
                logger.info(f"   • Appliance: {orchestrator.appliance_info.hostname} (VMID {orchestrator.appliance_info.vmid})")
                logger.info(f"   • Gateway: 10.20.0.1")
                logger.info(f"   • DHCP Range: 10.20.0.100-250")
                logger.info(f"   • DNS Domain: .prox.local")
                logger.info(f"   • Management UI: http://{orchestrator.appliance_info.wan_ip}:9090")
        
        # Inject orchestrator into ProxmoxService for network config
        # Note: orchestrator may be None if initialization failed (will use vmbr0 fallback)
        proxmox_service.network_manager = orchestrator
        
        if orchestrator:
            logger.info("✓ Network orchestrator injected into ProxmoxService")
            logger.info("  → New containers will use proximity-lan network")
        else:
            logger.warning("⚠ No network orchestrator available")
            logger.info("  → New containers will use default vmbr0 network")
        
        # Store orchestrator in app state for API endpoints
        app.state.orchestrator = orchestrator
        
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
        
        # Step 4: Initialize Reverse Proxy Manager (integrated with Network Appliance)
        logger.info("=" * 60)
        logger.info("STEP 4: Initializing Reverse Proxy Manager")
        logger.info("=" * 60)
        
        if orchestrator and orchestrator.appliance_info:
            try:
                from services.reverse_proxy_manager import ReverseProxyManager
                
                proxy_manager = ReverseProxyManager(
                    appliance_vmid=orchestrator.appliance_info.vmid
                )
                
                # Store in app state (app_service instances will get their own db sessions via dependency injection)
                app.state.proxy_manager = proxy_manager
                
                # Store in app state
                app.state.proxy_manager = proxy_manager
                
                logger.info("✓ Reverse Proxy Manager initialized")
                logger.info(f"   • Using Caddy on appliance VMID {orchestrator.appliance_info.vmid}")
                logger.info(f"   • Vhosts will be created automatically for deployed apps")
                
            except Exception as e:
                logger.error(f"Failed to initialize Reverse Proxy Manager: {e}")
                logger.warning("⚠ Continuing without reverse proxy manager")
                app.state.proxy_manager = None
        else:
            logger.warning("⚠ Network appliance not available - reverse proxy disabled")
            app.state.proxy_manager = None
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Don't fail startup, but log the error
    
    logger.info(f"🚀 Proximity API started on {config_settings.API_HOST}:{config_settings.API_PORT}")
    
    yield
    
    # Shutdown tasks
    logger.info("Shutting down Proximity API...")


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
        allow_methods=["*"],
        allow_headers=["*"],
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
        return JSONResponse(
            status_code=502,
            content={"success": False, "error": "Proxmox API error", "details": str(exc)}
        )
    
    @app.exception_handler(AppServiceError)
    async def app_service_exception_handler(request: Request, exc: AppServiceError):
        logger.error(f"App service error: {exc}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Application service error", "details": str(exc)}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.detail}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )
    
    # Middleware for request logging
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
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

    # Apps router (PROTECTED - requires authentication)
    from fastapi import Depends
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

    # Serve static files (UI)
    static_dir = Path(__file__).parent
    
    @app.get("/")
    async def read_root():
        """Serve the main UI"""
        return FileResponse(static_dir / "index.html")
    
    @app.get("/app.js")
    async def serve_app_js():
        """Serve the JavaScript application"""
        return FileResponse(static_dir / "app.js", media_type="application/javascript")
    
    @app.get("/styles.css")
    async def serve_styles_css():
        """Serve the CSS stylesheet"""
        return FileResponse(static_dir / "styles.css", media_type="text/css")
    
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