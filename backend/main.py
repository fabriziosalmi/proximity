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

from core.config import settings
from api.endpoints import apps, system
from services.proxmox_service import ProxmoxError
from services.app_service import AppServiceError

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
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
        # Step 1: Initialize Network Infrastructure
        logger.info("=" * 60)
        logger.info("STEP 1: Initializing Network Infrastructure")
        logger.info("=" * 60)
        
        from services.network_manager import NetworkManager
        
        network_manager = NetworkManager()
        network_init_success = await network_manager.initialize()
        
        if not network_init_success:
            logger.warning("⚠️  Network infrastructure not available (development mode or initialization failed)")
            logger.info("ℹ️  Containers will use default Proxmox networking (vmbr0)")
            network_manager = None  # Clear reference so ProxmoxService knows to use fallback
        else:
            logger.info("✅ Network infrastructure ready")
        
        # Step 2: Test Proxmox connection and inject NetworkManager
        logger.info("=" * 60)
        logger.info("STEP 2: Connecting to Proxmox")
        logger.info("=" * 60)
        
        from services.proxmox_service import proxmox_service
        
        # Inject NetworkManager into ProxmoxService (None if not available)
        proxmox_service.network_manager = network_manager
        
        is_connected = await proxmox_service.test_connection()
        if is_connected:
            logger.info("✓ Proxmox connection successful")
        else:
            logger.warning("⚠ Proxmox connection failed - some features may not work")
        
        # Step 3: Initialize app service (loads catalog)
        logger.info("=" * 60)
        logger.info("STEP 3: Loading Application Catalog")
        logger.info("=" * 60)
        
        from services.app_service import get_app_service
        app_service = get_app_service()
        catalog = await app_service.get_catalog()
        logger.info(f"✓ Loaded catalog with {catalog.total} applications")
        
        # Step 4: Deploy Caddy proxy in background (non-blocking)
        logger.info("=" * 60)
        logger.info("STEP 4: Deploying Caddy Reverse Proxy")
        logger.info("=" * 60)
        
        try:
            from services.caddy_service import get_caddy_service
            import asyncio
            
            async def deploy_caddy_background():
                """Deploy Caddy proxy in background"""
                try:
                    logger.info("🌐 Deploying Caddy reverse proxy...")
                    caddy_service = get_caddy_service(proxmox_service)
                    
                    # Get best node for deployment
                    nodes = await proxmox_service.get_nodes()
                    if nodes:
                        target_node = nodes[0].node
                        success = await caddy_service.ensure_caddy_deployed(target_node)
                        if success:
                            logger.info("✓ Caddy reverse proxy deployed successfully")
                        else:
                            logger.warning("⚠ Caddy proxy deployment failed - apps will work but without unified proxy")
                    else:
                        logger.warning("⚠ No Proxmox nodes available for Caddy deployment")
                except Exception as e:
                    logger.error(f"Failed to deploy Caddy proxy: {e}")
                    logger.warning("⚠ Continuing without reverse proxy - apps will still work")
            
            # Start Caddy deployment in background
            asyncio.create_task(deploy_caddy_background())
            
        except Exception as e:
            logger.error(f"Failed to initialize Caddy service: {e}")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Don't fail startup, but log the error
    
    logger.info(f"🚀 Proximity API started on {settings.API_HOST}:{settings.API_PORT}")
    
    yield
    
    # Shutdown tasks
    logger.info("Shutting down Proximity API...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="Self-hosted application delivery platform for Proxmox VE",
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
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
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[settings.PROXMOX_HOST, "localhost", "127.0.0.1"]
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
    app.include_router(
        apps.router, 
        prefix=f"/api/{settings.API_VERSION}/apps", 
        tags=["Applications"]
    )
    
    app.include_router(
        system.router, 
        prefix=f"/api/{settings.API_VERSION}/system", 
        tags=["System"]
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
            "project": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs_url": f"/docs" if settings.DEBUG else "Disabled in production",
            "api_version": settings.API_VERSION
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Simple health check"""
        return {"status": "healthy", "version": settings.APP_VERSION}
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )