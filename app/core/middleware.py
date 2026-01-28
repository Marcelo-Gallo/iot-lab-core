from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlmodel import select
from app.core.database import get_session
from app.models.device_token import DeviceToken

class DeviceAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.endswith("/measurements/") or request.method != "POST":
            return await call_next(request)

        token_header = request.headers.get("x-device-token")
        
        if not token_header:
            return await call_next(request)

        async for session in get_session():
            query = select(DeviceToken).where(
                DeviceToken.token == token_header,
                DeviceToken.is_active == True
            )
            result = await session.exec(query)
            device_token = result.first()
            
            if device_token:
                request.state.device_id = device_token.device_id
                
            else:
                pass 
            
            break

        response = await call_next(request)
        return response