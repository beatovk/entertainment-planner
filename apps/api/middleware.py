import time
import json
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware for timing requests and logging structured data"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extract operation name from path
        op = request.url.path
        if op.startswith('/api/'):
            op = op[5:]  # Remove /api/ prefix
        
        # Initialize timing data
        timing_data = {
            'op': op,
            'method': request.method,
            'start_time': start_time
        }
        
        # Process request
        response = await call_next(request)
        
        # Calculate timing
        end_time = time.time()
        duration_ms = round((end_time - start_time) * 1000, 2)
        
        # Extract additional data from response headers if available
        db_status = response.headers.get('X-Debug', '').split('db=')[1].split(';')[0] if 'db=' in response.headers.get('X-Debug', '') else 'unknown'
        cache_status = response.headers.get('X-Cache-Status', 'unknown')
        cache_store = response.headers.get('X-Cache-Store', 'unknown')
        
        # Build timing log
        timing_log = {
            'op': op,
            'ms': duration_ms,
            'status': response.status_code,
            'db': db_status,
            'cache': f"{cache_status}:{cache_store}",
            'method': request.method,
            'path': str(request.url.path),
            'query': str(request.query_params) if request.query_params else None
        }
        
        # Log as JSON for structured logging
        logger.info(json.dumps(timing_log))
        
        # Update response headers with timing info
        existing_debug = response.headers.get('X-Debug', '')
        if existing_debug:
            new_debug = f"{existing_debug};time_ms={duration_ms}"
        else:
            new_debug = f"time_ms={duration_ms};db={db_status};cache={cache_status}:{cache_store}"
        
        response.headers['X-Debug'] = new_debug
        
        return response

def log_operation(operation: str, **kwargs):
    """Helper function to log operations with structured data"""
    log_data = {
        'op': operation,
        'timestamp': time.time(),
        **kwargs
    }
    logger.info(json.dumps(log_data))
