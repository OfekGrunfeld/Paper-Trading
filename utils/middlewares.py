from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import ipaddress

from os import getenv
from dotenv import load_dotenv

ALLOWED_NETWORK = getenv("ALLOWED_NETWORK")

class VerifyClientIPMiddleware(BaseHTTPMiddleware):
    # Allowed networks
    allowed_networks = [ipaddress.ip_network(str(ALLOWED_NETWORK))] 

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip_str = self.get_client_ip(request)

        try:
            client_ip = ipaddress.ip_address(client_ip_str)
        except ValueError:
            return Response("Invalid IP address", status_code=403)

        if not any(client_ip in network for network in self.allowed_networks):
            return Response(f"Access denied\nCannot Access from {client_ip_str}", status_code=403)

        response = await call_next(request)
        return response

    def get_client_ip(self, request: Request) -> str:
        # Get the IP address from the X-Forwarded-For header
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            # Get the IP address from the X-Real-IP header
            x_real_ip = request.headers.get("X-Real-IP")
            if x_real_ip:
                ip = x_real_ip.strip()
            else:
                ip = request.client.host

        return ip