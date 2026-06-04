#!/usr/bin/env bash
set -e
set -x

python scripts/wait_for_db.py

alembic upgrade head

python -m scripts.seed_catalog --source all

python scripts/initial_data.py

if [ "${ENVIRONMENT:-local}" = "local" ]; then
  python -m scripts.seed_dev_listings
fi
