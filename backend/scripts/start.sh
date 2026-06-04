#!/usr/bin/env sh
set -e

bash /app/scripts/prestart.sh

WORKERS=${BACKEND_WORKERS:-$(nproc)}

exec granian \
  --interface asgi \
  --host 0.0.0.0 \
  --port 8000 \
  --workers "$WORKERS" \
  --loop asyncio \
  --runtime-threads 1 \
  --http 1 \
  --http1-pipeline-flush \
  --backpressure 30 \
  --no-ws \
  --backlog 1024 \
  --workers-lifetime 3600 \
  --workers-max-rss 768 \
  --respawn-failed-workers \
  --respawn-interval 3.5 \
  --workers-kill-timeout 20 \
  --log-level warning \
  app.main:app
