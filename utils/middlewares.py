from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

class VerifyClientIPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract the client's IP address from the request
        client_ip = request.client.host
        print("Client IP:", client_ip)  # For debugging purposes
        
        # Check if the client IP is the one allowed
        if client_ip != "127.0.0.1":
            # Raise an exception or return a custom response if the IP is not allowed
            raise HTTPException(status_code=403, detail="Access denied")

        # If IP is allowed, just proceed to handle the request
        response = await call_next(request)
        return response