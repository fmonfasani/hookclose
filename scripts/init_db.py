"""Initialize the HookClose database schema."""

import asyncio
import os

import asyncpg

DSN = (
    f"postgresql://{os.getenv('HOOKCLOSE_POSTGRES_USER', 'hookclose')}"
    f":{os.getenv('HOOKCLOSE_POSTGRES_PASSWORD', 'hookclose')}"
    f"@{os.getenv('HOOKCLOSE_POSTGRES_HOST', 'localhost')}"
    f":{os.getenv('HOOKCLOSE_POSTGRES_PORT', '5432')}"
    f"/{os.getenv('HOOKCLOSE_POSTGRES_DB', 'hookclose')}"
)

SQL = """
CREATE TABLE IF NOT EXISTS workflows (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status          TEXT NOT NULL DEFAULT 'pending',
    provider        TEXT,
    definition      JSONB NOT NULL DEFAULT '{}',
    state           JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id     UUID REFERENCES workflows(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'pending',
    task_type       TEXT NOT NULL,
    payload         JSONB NOT NULL DEFAULT '{}',
    result          JSONB,
    provider        TEXT,
    attempts        INT NOT NULL DEFAULT 0,
    max_attempts    INT NOT NULL DEFAULT 3,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id     UUID,
    event_type      TEXT NOT NULL,
    payload         JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def main() -> None:
    conn = await asyncpg.connect(DSN)
    await conn.execute(SQL)
    await conn.close()
    print("database initialized")


if __name__ == "__main__":
    asyncio.run(main())
