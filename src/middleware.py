from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging
from datetime import datetime

logger = logging.getLogger('uvicorn.access')
logger.disabled = True 


def register_middleware(app:FastAPI):
    
    @app.middleware('http')
    async def custom_logging(request:Request, call_next):
        start_time = time.time()
        print("before", datetime.now())
        response = await call_next(request)
        processing_time = time.time() - start_time
        message = f"{request.client.host}:{request.client.port} - {request.method} - {request.url.path} - {response.status_code} completed after {processing_time:6.4f}s"
        print(message)
        return response
    
    app.add_middleware(
        CORSMiddleware, 
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True
    )
        
    app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=["localhost", "127.0.0.1"],
    )
    
        

