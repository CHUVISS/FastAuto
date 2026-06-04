#!/usr/bin/env sh
set -e

bash /app/scripts/prestart.sh

exec granian \
  --interface asgi \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  --loop asyncio \
  --http auto \
  --log-level info \
  app.main:app
