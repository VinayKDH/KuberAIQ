# Backup Strategy — VyaparAI

This document defines backup and recovery for PostgreSQL and blob storage. See also
[docs/11-azure-architecture.md](../docs/11-azure-architecture.md) §11.7.

## Recovery objectives

| Environment | RPO (max data loss) | RTO (max downtime) |
| --- | --- | --- |
| Production | ≤ 15 minutes | ≤ 1 hour |
| Staging | ≤ 1 hour | ≤ 4 hours |
| Dev | Best effort | Best effort |

## PostgreSQL (Azure Database for PostgreSQL Flexible Server)

### Automated backups (platform-managed)

Configured in `infra/bicep/main.bicep`:

- **Backup retention**: 35 days (prod), 7 days (non-prod).
- **Geo-redundant backup**: enabled in prod for cross-region restore capability.
- **Point-in-time restore (PITR)**: restore to any second within the retention window.

### Operational procedures

1. **Daily verification** — confirm backup status in Azure Portal → PostgreSQL → Backups.
2. **Quarterly restore drill** — restore to a temporary server, run smoke queries, delete temp server.
3. **Before major migrations** — take a manual snapshot note (timestamp) for fast PITR rollback.

### Restore runbook (PITR)

```bash
# Example: restore to a new server (replace placeholders)
az postgres flexible-server restore \
  --resource-group rg-vyaparai-prod \
  --name vyaparai-pg-restored \
  --source-server vyaparai-pg-prod \
  --restore-time "2026-06-01T10:00:00Z"
```

After restore:

1. Update Key Vault secret `database-url` with the new connection string.
2. Restart the API App Service.
3. Run Alembic migration status check and application health probes.

### High availability (prod)

Zone-redundant HA is enabled in prod Bicep. Failover is automatic for zone outages;
application connection strings remain unchanged.

## Blob storage (invoice PDFs and exports)

### Platform features

Configured on the Storage Account in Bicep:

| Feature | Setting | Purpose |
| --- | --- | --- |
| **GRS replication** | Prod SKU | Secondary region copy for geo-disaster recovery |
| **Blob soft delete** | 30 days | Recover accidentally deleted PDFs |
| **Container soft delete** | 30 days | Recover deleted containers |
| **Versioning** | Enable post-deploy | Previous blob versions retained on overwrite |

> Enable blob versioning after first deploy:
> `az storage account blob-service-properties update --enable-versioning true`

### Lifecycle management

Apply a lifecycle policy (post-deploy) to move blobs to **Cool** tier after 90 days and
**Archive** after 1 year for compliance archives.

### Restore runbook (deleted blob)

1. Azure Portal → Storage Account → Containers → `invoices`.
2. Show deleted blobs → select version → **Undelete**.
3. If overwritten, restore a previous **version** instead of the current blob.

### Geo-redundant failover (DR)

In a regional outage:

```bash
az storage account failover --name <storage-account-name> --yes
```

Failover is **last resort** — it makes the secondary region primary and is irreversible
without re-enabling GRS afterward.

## Key Vault

- Soft delete: 90 days (Bicep).
- Purge protection: enabled.
- Secrets are not "backed up" separately; they are recreated from secure offline records
  or rotated. Document secret rotation in [docs/12-security-design.md](../docs/12-security-design.md).

## Local development (Docker Compose)

| Asset | Mechanism |
| --- | --- |
| PostgreSQL | Named volume `postgres_data` persists data across restarts |
| Blob (mock) | Named volume `blob_storage` maps to `/app/local_blob_storage` |

To reset local data:

```bash
docker compose down -v
```

## Infrastructure as Code

- Bicep templates are version-controlled in `infra/bicep/`.
- Redeploy from git is the recovery path for misconfigured Azure resources.
- Tag production releases (`v*`) so container images in ACR can be rolled back.

## Compliance & audit

- Audit logs in Postgres (`audit_logs`) are included in PostgreSQL PITR backups.
- Mirror critical audit events to Log Analytics for tamper-evident retention (see
  [infra/monitoring.md](./monitoring.md)).

## Drill schedule

| Drill | Frequency | Owner |
| --- | --- | --- |
| PostgreSQL PITR restore to temp server | Quarterly | Platform / DBA |
| Blob undelete / version restore | Quarterly | Platform |
| Full DR simulation (secondary region) | Annually | Platform + App team |

Document results and action items after each drill.
