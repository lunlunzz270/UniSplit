FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY frontend/src frontend/src
COPY backend/docker-entrypoint.sh backend/docker-entrypoint.sh

RUN chmod +x backend/docker-entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["backend/docker-entrypoint.sh"]
