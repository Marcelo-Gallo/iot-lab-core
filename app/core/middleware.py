from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlmodel import select
from app.core.database import get_session
from app.models.device_token import DeviceToken

class DeviceAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if "/api/v1/measurements" not in request.url.path or request.method != "POST":
            return await call_next(request)

        token_header = request.headers.get("x-device-token")
        
        if not token_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token de dispositivo ausente (Header: x-device-token)"}
            )

        device_id = None
        async for session in get_session():
            query = select(DeviceToken).where(
                DeviceToken.token == token_header,
                DeviceToken.is_active == True
            )
            result = await session.exec(query)
            token_obj = result.first()
            
            if token_obj:
                device_id = token_obj.device_id
            
            break
        
        if not device_id:
             return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Token de dispositivo inválido ou revogado"}
            )

        request.state.device_id = device_id
        response = await call_next(request)
        return response