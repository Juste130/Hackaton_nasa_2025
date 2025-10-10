"""
Run the FastAPI app defined in `api_ai.py` with production-ready configuration.

This `main.py` provides a robust entrypoint with multiple workers support:

    # Development (single worker with auto-reload)
    python3 main.py

    # Production (multiple workers)
    python3 main.py --workers 4 --no-reload

Environment variables:
- HOST (default: 0.0.0.0)
- PORT (default: 8000)
- WORKERS (default: 1)
- RELOAD (default: true for dev, false for prod)
- LOG_LEVEL (default: info)
- ENVIRONMENT (default: development)
"""
import os
import argparse
import uvicorn
from multiprocessing import cpu_count


def get_workers_count() -> int:
    """
    Calculate optimal number of workers based on CPU cores
    Formula: (2 x CPU cores) + 1 for I/O bound applications
    """
    workers_env = os.environ.get("WORKERS")
    if workers_env:
        return int(workers_env)
    
    # For I/O bound applications like our AI services
    return min((2 * cpu_count()) + 1, 8)  # Cap at 8 workers


def is_production() -> bool:
    """Check if running in production environment"""
    env = os.environ.get("ENVIRONMENT", "development").lower()
    return env in ["production", "prod"]


def validate_app_import() -> str:
    """Validate that the app can be imported and return import string"""
    app_string = "api_ai:app"
    
    try:
        # Test import to make sure it works
        from api_ai import app  # type: ignore
        print(f" Successfully validated app import: {app_string}")
        return app_string
    except Exception as e:
        print(f" Failed to import FastAPI app from api_ai.py: {e}")
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="NASA AI Services API Server")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"),
                       help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")),
                       help="Port to bind to (default: 8000)")
    parser.add_argument("--workers", type=int, default=get_workers_count(),
                       help=f"Number of worker processes (default: {get_workers_count()})")
    parser.add_argument("--reload", action="store_true", 
                       default=not is_production() and os.environ.get("RELOAD", "true").lower() == "true",
                       help="Enable auto-reload for development")
    parser.add_argument("--no-reload", action="store_true",
                       help="Disable auto-reload (overrides --reload)")
    parser.add_argument("--log-level", default=os.environ.get("LOG_LEVEL", "info"),
                       choices=["critical", "error", "warning", "info", "debug", "trace"],
                       help="Log level (default: info)")
    parser.add_argument("--access-log", action="store_true", default=is_production(),
                       help="Enable access logs (default: enabled in production)")
    parser.add_argument("--no-access-log", action="store_true",
                       help="Disable access logs")
    parser.add_argument("--timeout-keep-alive", type=int, default=5,
                       help="Keep-alive timeout (default: 5)")
    parser.add_argument("--timeout-graceful-shutdown", type=int, default=30,
                       help="Graceful shutdown timeout (default: 30)")
    
    args = parser.parse_args()
    
    # Validate app import
    app_string = validate_app_import()
    
    # Handle reload logic
    if args.no_reload:
        reload = False
    else:
        reload = args.reload
    
    # Handle access log logic
    if args.no_access_log:
        access_log = False
    else:
        access_log = args.access_log
    
    # If reload is enabled, force workers to 1 (uvicorn limitation)
    if reload and args.workers > 1:
        print("  Auto-reload enabled, forcing workers to 1")
        workers = 1
    else:
        workers = args.workers
    
    # Base configuration
    config = {
        "app": app_string,  # Use import string for workers support
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "timeout_keep_alive": args.timeout_keep_alive,
        "timeout_graceful_shutdown": args.timeout_graceful_shutdown,
        "access_log": access_log,
    }
    
    # Production vs Development specific configuration
    if is_production():
        print(" Starting in PRODUCTION mode")
        config.update({
            "workers": workers,
            "reload": False,
            "loop": "auto",  # Use best available event loop
            "http": "auto",  # Use best available HTTP implementation
            "ws": "auto",    # Use best available WebSocket implementation
            "server_header": False,  # Don't send server header
            "date_header": False,    # Don't send date header for minimal overhead
        })
    else:
        print(" Starting in DEVELOPMENT mode")
        config.update({
            "workers": workers if not reload else 1,
            "reload": reload,
            "reload_dirs": ["./"] if reload else None,
            "reload_includes": ["*.py"] if reload else None,
            "reload_excludes": ["*.pyc", "__pycache__", ".git", ".venv"] if reload else None,
        })
    
    # Print startup information
    print(f" Host: {args.host}")
    print(f" Port: {args.port}")
    print(f" Workers: {workers}")
    print(f" Auto-reload: {'' if reload else ''}")
    print(f" Log level: {args.log_level}")
    print(f" Access logs: {'' if access_log else ''}")
    print(f" Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f" CPU cores: {cpu_count()}")
    print(f" App: {app_string}")
    print()
    print(" Available endpoints:")
    print(f"    API Docs: http://{args.host}:{args.port}/docs")
    print(f"    ReDoc: http://{args.host}:{args.port}/redoc")
    print(f"     Health: http://{args.host}:{args.port}/health")
    print(f"     Graph: http://{args.host}:{args.port}/api/graph/stats")
    print()
    
    # Performance recommendations
    if workers > 1:
        print(" Performance tips:")
        print(f"   - Using {workers} workers for better concurrency")
        print(f"   - Each worker will load models independently")
        print(f"   - Memory usage: ~{workers}x single worker")
        print(f"   - Consider Redis caching for better performance")
        print()
    
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n Shutting down gracefully...")
    except Exception as e:
        print(f" Server error: {e}")
        raise


if __name__ == "__main__":
    main()
