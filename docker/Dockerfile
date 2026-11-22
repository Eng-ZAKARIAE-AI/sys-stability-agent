FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml .
COPY config/ config/
COPY src/ src/

RUN pip install --no-cache-dir -e .

CMD ["sys-agent"]
