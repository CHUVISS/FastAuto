# Production Rollout — New Indexes

Regular Alembic migrations cannot use `CREATE INDEX CONCURRENTLY` because they
run inside a transaction. On a live production database with significant data, a
regular index build takes an `AccessShareLock` for its duration and blocks
concurrent DDL. The safe approach is to build the indexes manually with
`CONCURRENTLY` (no lock) and then tell Alembic the migration is done.

## Affected migrations

| Revision | Index / Object |
|---|---|
| `a1b2c3d4e5f6` | 10 B-tree indexes on cars, deals, viewings, car_images |
| `b7e9f21a3d8c` | `uniq_viewing_active_slot` partial UNIQUE index |
| `d4e8f91b2c7a` | `user_id` column + FK + `ix_messages_user_id` + `uniq_active_purchase_inquiry` |
| `e3a7b52f9d1c` | `pg_trgm` extension + 2 GIN indexes on cars |
| `f5c9d83e2b4a` | 2 partial indexes on car_images / car_offer_images |

## Step-by-step

### 1. Apply non-index DDL while app is running

```sql
-- d4e8f91b2c7a — column + FK only (non-blocking in PG 11+)
ALTER TABLE messages ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE messages ADD CONSTRAINT fk_messages_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    NOT VALID;  -- skips full table scan; validate separately
ALTER TABLE messages VALIDATE CONSTRAINT fk_messages_user_id;

-- c5c3d57d5ca0
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at
    TIMESTAMPTZ NOT NULL DEFAULT NOW();
```

### 2. Build indexes CONCURRENTLY (no locks, run outside transaction)

Run each statement in a separate `psql` session — CONCURRENTLY cannot be used
inside a transaction block.

```sql
-- a1b2c3d4e5f6
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_car_images_car_id ON car_images (car_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cars_created_at_desc ON cars (created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cars_status_created_at ON cars (status, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_deals_car_id ON deals (car_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_deals_client_id ON deals (client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_deals_manager_id ON deals (manager_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_deals_deal_date ON deals (deal_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_viewings_car_id ON viewings (car_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_viewings_client_id ON viewings (client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_viewings_car_date_result ON viewings (car_id, viewing_date, result);

-- b7e9f21a3d8c
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uniq_viewing_active_slot
    ON viewings(car_id, viewing_date, viewing_time)
    WHERE result IN ('scheduled', 'confirmed') AND viewing_time IS NOT NULL;

-- d4e8f91b2c7a
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_messages_user_id ON messages (user_id);
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uniq_active_purchase_inquiry
    ON messages(user_id, car_id)
    WHERE message_type = 'inquiry' AND status IN ('new', 'in_progress')
    AND user_id IS NOT NULL AND car_id IS NOT NULL;

-- e3a7b52f9d1c
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cars_brand_trgm
    ON cars USING GIN (lower(brand) gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cars_model_trgm
    ON cars USING GIN (lower(model) gin_trgm_ops);

-- f5c9d83e2b4a
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_car_images_primary
    ON car_images (car_id) WHERE is_primary = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_car_offer_images_primary
    ON car_offer_images (offer_id) WHERE is_primary = true;
```

### 3. Stamp Alembic to skip migration execution

After all objects exist, tell Alembic these migrations are already applied:

```bash
alembic stamp f5c9d83e2b4a  # latest of the 5 new migrations
```

Verify:

```bash
alembic current  # should show f5c9d83e2b4a (head)
alembic history --verbose  # all revisions applied
```

### 4. Rollback plan

If any index needs to be dropped:

```sql
DROP INDEX CONCURRENTLY IF EXISTS <index_name>;
```

Then run `alembic downgrade <previous_revision>` — the idempotent `IF EXISTS`
downgrade statements handle the case where the index is already gone.
