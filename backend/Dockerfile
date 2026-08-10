FROM python:3.14-slim

RUN pip install --no-cache-dir uv

WORKDIR /src

COPY . .
RUN uv sync --frozen --no-dev

RUN mkdir -p /src/data

EXPOSE 9000

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/

CMD ["uv", "run", "app/main.py"]
