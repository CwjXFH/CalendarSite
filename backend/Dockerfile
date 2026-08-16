# 多阶段构建，build装依赖，runtime只带venv+应用代码
# 合理设计layer尽可能复用构建缓存(Docker build cache)
# 整体复制虚拟环境、运行时不依赖uv/编译工具
# 依赖层、代码层分离
# 非root用户运行
# https://hynek.me/articles/docker-uv/
# https://mp.weixin.qq.com/s/znDhEj8KRDLCGafxAEWxgg

FROM python:3.14-slim AS build

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install uv -i https://pypi.mirrors.ustc.edu.cn/simple/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LOCKED=1 \
    UV_NO_DEV=1 \
    UV_PROJECT_ENVIRONMENT=/venv

WORKDIR /src
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.toml,target=uv.toml \
    uv sync

FROM python:3.14-slim

ENV PATH=/venv/bin:$PATH \
    PYTHONPATH=/ \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

COPY --from=build /venv /venv
COPY app /app

WORKDIR /app
RUN mkdir -p /app/data

CMD ["python", "-m", "main"]
