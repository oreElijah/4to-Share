import sentry_sdk
from fastapi import FastAPI
from contextlib import asynccontextmanager
from settings.config import GlobalConfig as Config
from app.auth.router import auth_router
from app.user.router import user_router
from app.post.router import post_router
from app.database.main import init_db

@asynccontextmanager
async def life_span(app: FastAPI):
    print("starting server")
    await init_db() # type: ignore
    yield
    print("Stopping server")

version = "v1"

def activate_sentry(app: FastAPI):
    sentry_sdk.init(
        dsn=Config.SENTRY_DSN,
        send_default_pii=True,
    )

def register_routers(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(post_router)


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=life_span,
        title="4to Share API", 
        description="A REST API for sharing Photos and videos",
        version=version,
        docs_url=f"/{version}/docs",
        redoc_url=f"/{version}/redoc",
        contact={
            "name": "random_guyy",
            "email": "oreelijah33@gmail.com"
        }
    )

    register_routers(app)
    activate_sentry(app)
    return app