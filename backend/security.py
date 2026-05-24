import os
from collections import defaultdict, deque
from time import monotonic

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.requests = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else "unknown"
        now = monotonic()
        timestamps = self.requests[client_host]

        while timestamps and now - timestamps[0] > self.window_seconds:
            timestamps.popleft()

        if len(timestamps) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded. Please try again shortly."},
            )

        timestamps.append(now)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


def get_allowed_origins():
    raw_origins = os.getenv(
        "STOCK_API_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,https://stonks.vercel.app",
    )
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def get_rate_limit():
    raw_limit = os.getenv("STOCK_API_RATE_LIMIT_PER_MINUTE", "120")
    try:
        return max(1, int(raw_limit))
    except ValueError:
        return 120
