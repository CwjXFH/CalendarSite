FROM python:3.14-slim

RUN pip install uv -i https://pypi.mirrors.ustc.edu.cn/simple/

WORKDIR /src

COPY . .
RUN uv sync --frozen --no-dev
RUN mkdir -p /src/data

EXPOSE 9000

ENV TZ=Asia/Shanghai
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/src

CMD ["uv", "run", "app/main.py"]
