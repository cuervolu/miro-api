import os
import time

import httpx
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.controllers import user_controller
from app.api.v1.controllers.auth import auth_controller
from app.core.config import settings
from app.core.logger import logger
from .redis_manager import redis_instance


class MiroAPI(FastAPI):
    def __init__(self):
        self.__server_timezone = None
        kwargs = {
            "title": "Miro API [latest]",
            "description": "0Ataos website REST API",
            "version": settings.CURRENT_VERSION,
            "open_api_tags": settings.TAGS_METADATA,
            "docs_url": "/docs",
            "redoc_url": "/redocs",
        }
        self.api_log = logger.get_context_logger("api")
        super().__init__(**kwargs)

    @property
    def server_timezone(self):
        return self.__server_timezone

    def configure(self):
        # Config app
        self.setup_server_timezone()
        self.setup_middlewares()
        self.setup_base_routes()
        self.setup_routes()
        self.setup_events()

    def setup_server_timezone(self):
        tz = settings.TIMEZONE
        os.environ["TZ"] = tz
        time.tzset()
        self.__server_timezone = tz
        self.api_log.info(f"SERVER TIME ZONE SETTER {tz}")

    def setup_middlewares(self):
        self.add_middleware(
            CORSMiddleware,
            allow_origins=settings.ALLOW_ORIGINS,
            allow_credentials=settings.ALLOW_CREDENTIALS,
            allow_methods=settings.ALLOW_METHODS,
            allow_headers=settings.ALLOW_HEADERS,
            expose_headers=settings.EXPOSE_HEADERS,
            max_age=settings.MAX_AGE,
        )
        self.api_log.info("Middlewares Set")

    def setup_base_routes(self):
        """MAIN PATH"""

        @self.get("/", include_in_schema=False)
        async def root():
            return {"response": "Ping!"}

    def setup_routes(self):
        """api ROUTER"""

        # V1 ROUTER
        v1_router = APIRouter()

        # Controllers
        v1_router.include_router(auth_controller.router, prefix=settings.VERSION.get(1))
        v1_router.include_router(user_controller.router, prefix=settings.VERSION.get(1))

        # api ROUTER
        api_router = APIRouter()
        api_router.include_router(v1_router, prefix="/api")

        # GLOBAL ROUTER
        self.include_router(api_router)

        self.api_log.info("API Routes Set")

    def setup_events(self):
        """GLOBAL EVENTS"""

        @self.on_event("startup")
        async def startup_event():
            self.api_log.info("Server starting")
            self.state.redis = redis_instance
            self.state.client = httpx.AsyncClient()
            self.api_log.info("Redis connected")
            self.api_log.info("Server started")

        @self.on_event("shutdown")
        async def shutdown():
            self.api_log.info("Server stopping")
            self.state.redis.close()
            self.api_log.info("Server stopped")
