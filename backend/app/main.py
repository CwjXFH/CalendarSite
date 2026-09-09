from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.ops import router as ops_router
from app.api.v1 import limiter
from app.api.v1 import router as v1_router
from app.db.database import require_db
from app.web import router as web_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    require_db()
    yield


app = FastAPI(
    title="Calendar Site API",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(v1_router)
app.include_router(ops_router)
app.include_router(web_router)


def _html_error(status_code: int, message: str) -> HTMLResponse:
    body = (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
        f"<title>{message}</title></head><body>"
        f"<p>{message}</p><p><a href='/'>返回首页</a></p></body></html>"
    )
    return HTMLResponse(status_code=status_code, content=body)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse | HTMLResponse:
    if request.url.path.startswith("/api/") is False:
        message = "页面不存在" if exc.status_code == 404 else str(exc.detail)
        return _html_error(exc.status_code, message)
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": "HTTP_ERROR", "message": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"code": "VALIDATION_ERROR", "message": "invalid request parameters"},
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"code": "RATE_LIMITED", "message": "too many requests"},
        headers={"Retry-After": "60"},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
