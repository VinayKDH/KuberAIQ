#!/usr/bin/env python3
"""Copy data from legacy vyaparai Postgres to prod kuberaiq Postgres (schema must exist)."""
from __future__ import annotations

import asyncio
import os
import sys

import asyncpg

LEGACY_URL = os.environ.get(
    "LEGACY_DATABASE_URL",
    "postgresql://vyaparaiadmin@vyaparai-pg-tqjbqun57vvae.postgres.database.azure.com:5432/vyaparai?sslmode=require",
)
PROD_URL = os.environ.get("PROD_DATABASE_URL", "")

# Tables in FK-safe order (parents before children).
TABLES = [
    "alembic_version",
    "companies",
    "users",
    "customers",
    "products",
    "invoices",
    "invoice_line_items",
    "payments",
    "reminders",
    "reminder_triggers",
    "audit_logs",
    "quotations",
    "quotation_line_items",
    "credit_notes",
    "credit_note_line_items",
    "subscriptions",
]


async def copy_table(src: asyncpg.Connection, dst: asyncpg.Connection, table: str) -> int:
    exists = await src.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = $1)",
        table,
    )
    if not exists:
        return 0
    rows = await src.fetch(f'SELECT * FROM "{table}"')
    if not rows:
        return 0
    cols = list(rows[0].keys())
    col_list = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(f"${i + 1}" for i in range(len(cols)))
    await dst.execute(f'TRUNCATE "{table}" CASCADE')
    await dst.executemany(
        f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})',
        [tuple(r[c] for c in cols) for r in rows],
    )
    return len(rows)


async def main() -> int:
    if not PROD_URL:
        print("Set PROD_DATABASE_URL (postgresql://user:pass@host:5432/kuberaiq?sslmode=require)", file=sys.stderr)
        return 1
    legacy_pw = os.environ.get("LEGACY_POSTGRES_PASSWORD", "")
    prod_pw = os.environ.get("PROD_POSTGRES_PASSWORD", "")
    if not legacy_pw or not prod_pw:
        print("Set LEGACY_POSTGRES_PASSWORD and PROD_POSTGRES_PASSWORD", file=sys.stderr)
        return 1

    legacy_dsn = LEGACY_URL.replace("vyaparaiadmin@", f"vyaparaiadmin:{legacy_pw}@")
    prod_dsn = PROD_URL
    if "kuberaiqadmin@" in prod_dsn and prod_pw:
        prod_dsn = prod_dsn.replace("kuberaiqadmin@", f"kuberaiqadmin:{prod_pw}@")

    src = await asyncpg.connect(legacy_dsn)
    dst = await asyncpg.connect(prod_dsn)
    try:
        total = 0
        for table in TABLES:
            n = await copy_table(src, dst, table)
            if n:
                print(f"  {table}: {n} rows")
                total += n
        print(f"Done — {total} rows copied.")
    finally:
        await src.close()
        await dst.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
