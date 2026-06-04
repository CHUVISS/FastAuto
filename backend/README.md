# backend/

The application code. All `task` commands are run from here.

For the full guide (setup, configuration, API surface, CI, troubleshooting),
see the root [`README.md`](../README.md).

Quick reference:

```bash
task setup     # create .venv and install deps
task up        # start db + redis + minio + backend (hot-reload)
task migrate   # alembic upgrade head
task seed      # create the first superuser
task down      # stop everything
```

Useful directories:

- `app/` - FastAPI application
- `alembic/` - migrations (`PRODUCTION_ROLLOUT.md` covers manual rollouts)
- `tests/` - `unit/`, `integration/`, `e2e/`, `property/`
- `scripts/` - container entrypoints and seeds
- `Taskfile.dev.yml` - the Taskfile used by default in dev
- `Taskfile.yml` - production ops
