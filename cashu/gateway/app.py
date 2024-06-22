import sys
from traceback import print_exception

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.requests import Request

from ..core.errors import CashuError
from ..core.logging import configure_logger
from ..core.settings import settings
from .router import router
from .startup import start_gateway_init

if settings.debug_profiling:
    pass

if settings.mint_rate_limit:
    pass

# this errors with the tests but is the appropriate way to handle startup and shutdown
# until then, we use @app.on_event("startup")
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # startup routines here
#     await start_mint_init()
#     yield
#     # shutdown routines here


def create_app(config_object="core.settings") -> FastAPI:
    configure_logger()

    app = FastAPI(
        title="Nutshell Cashu Mint",
        description="Ecash wallet and mint based on the Cashu protocol.",
        version=settings.version,
        license_info={
            "name": "MIT License",
            "url": "https://raw.githubusercontent.com/cashubtc/cashu/main/LICENSE",
        },
    )

    return app


app = create_app()


@app.middleware("http")
async def catch_exceptions(request: Request, call_next):
    CORS_HEADERS = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true",
    }
    try:
        return await call_next(request)
    except Exception as e:
        try:
            err_message = str(e)
        except Exception:
            err_message = e.args[0] if e.args else "Unknown error"

        if isinstance(e, CashuError) or isinstance(e.args[0], CashuError):
            logger.error(f"CashuError: {err_message}")
            code = e.code if isinstance(e, CashuError) else e.args[0].code
            # return with cors headers
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": err_message, "code": code},
                headers=CORS_HEADERS,
            )
        logger.error(f"Exception: {err_message}")
        if settings.debug:
            print_exception(*sys.exc_info())
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": err_message, "code": 0},
            headers=CORS_HEADERS,
        )


# Add exception handlers
app.include_router(router=router, tags=["Gateway"])


@app.on_event("startup")
async def startup_gateway():
    await start_gateway_init()
