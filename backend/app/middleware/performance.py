"""
Performance monitoring middleware for tracking request timing.

Logs response times and identifies slow endpoints.
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request/response timing.
    
    Logs:
    - Total request duration
    - Endpoint path
    - Status code
    - Slow requests (>5s)
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and measure timing."""
        # Start timer
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        duration_ms = duration * 1000
        
        # Log performance metrics
        log_data = {
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "duration_s": round(duration, 2)
        }
        
        # Log slow requests as warnings
        if duration > 5.0:
            logger.warning(f"⚠️  SLOW REQUEST: {log_data}")
        elif duration > 2.0:
            logger.info(f"⏱️  {log_data}")
        else:
            logger.debug(f"✓ {log_data}")
        
        # Add timing header to response
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        return response


class DetailedPerformanceMiddleware(BaseHTTPMiddleware):
    """
    Enhanced performance middleware with breakdown timing.
    
    Use request.state to track specific operations:
    - request.state.perf_db_time
    - request.state.perf_llm_time
    - request.state.perf_vector_time
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request with detailed timing."""
        start_time = time.time()
        
        # Initialize timing trackers on request state
        request.state.perf_start = start_time
        request.state.perf_db_time = 0.0
        request.state.perf_llm_time = 0.0
        request.state.perf_vector_time = 0.0
        request.state.perf_embedding_time = 0.0
        
        # Process request
        response = await call_next(request)
        
        # Calculate total duration
        total_duration = time.time() - start_time
        
        # Get breakdown (if tracked)
        breakdown = {
            "total_ms": round(total_duration * 1000, 2),
            "db_ms": round(request.state.perf_db_time * 1000, 2),
            "llm_ms": round(request.state.perf_llm_time * 1000, 2),
            "vector_ms": round(request.state.perf_vector_time * 1000, 2),
            "embedding_ms": round(request.state.perf_embedding_time * 1000, 2),
        }
        
        # Calculate overhead (unaccounted time)
        accounted = (request.state.perf_db_time + 
                    request.state.perf_llm_time + 
                    request.state.perf_vector_time +
                    request.state.perf_embedding_time)
        overhead = total_duration - accounted
        breakdown["overhead_ms"] = round(overhead * 1000, 2)
        
        # Log detailed breakdown for chat endpoints
        if "/chat/" in request.url.path or "/messages" in request.url.path:
            logger.info(f"📊 CHAT PERFORMANCE: {breakdown}")
        
        # Add headers
        response.headers["X-Response-Time"] = f"{breakdown['total_ms']}ms"
        response.headers["X-LLM-Time"] = f"{breakdown['llm_ms']}ms"
        response.headers["X-Vector-Time"] = f"{breakdown['vector_ms']}ms"
        
        return response
