# Deployment — VPS production runtime (Hetzner / Ubuntu 24.04)

> **Gate:** deploy only once the runtime core is stable locally (queues, workers,
> provider routing, retry loops, task chaining — all green). That gate is met
> (see [`../ROADMAP.md`](../ROADMAP.md)).

This kit runs the full stack on a single VPS behind nginx+TLS, with restart
policies, healthchecks, backups, and one-command deploy/rollback.

## Topology

```
            ┌─────────── VPS (Ubuntu 24.04) ───────────┐
 internet ──▶ nginx :443 (TLS) ──▶ workflow-engine :8101 │
            │                       scheduler            │
            │                       opencode-worker      │
            │   postgres   redis  (internal only)        │
            └────────────────────────────────────────────┘
```

Only `nginx` (80/443) is exposed; Postgres/Redis stay on the internal compose network.

## One-time provisioning

```bash
# on the fresh box, as root
curl -fsSL https://raw.githubusercontent.com/fmonfasani/hookclose/main/deploy/scripts/bootstrap.sh | bash
#  └─ installs Docker, configures ufw (ssh/80/443), clones the repo to /opt/hookclose,
#     and creates deploy/.env.prod from the template
```

Then, on the server:

1. **Secrets** — edit `/opt/hookclose/deploy/.env.prod` (Postgres password, provider API keys).
2. **TLS certs** — put `fullchain.pem` + `privkey.pem` in `deploy/nginx/certs/`
   (e.g. `certbot certonly --standalone -d your.domain` then copy, or mount Let's Encrypt).
3. **DNS** — point your domain's A record at the VPS IP.

## Deploy

```bash
cd /opt/hookclose
deploy/scripts/deploy.sh          # build + up -d + wait for health
```

Run it under systemd so it survives reboots:

```bash
sudo cp deploy/systemd/hookclose.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now hookclose
```

## Day-2 operations

| Task | Command |
| --- | --- |
| Ship latest `main` | `deploy/scripts/update.sh` |
| Roll back to previous deploy | `deploy/scripts/rollback.sh` |
| Roll back to a specific ref | `deploy/scripts/rollback.sh <git-sha>` |
| Health/watchdog check | `deploy/scripts/healthcheck.sh` |
| Backup PG + Redis (cron daily) | `deploy/scripts/backup.sh` |
| Tail logs | `docker compose -f deploy/docker-compose.prod.yml logs -f --tail=200` |

## Resilience

- **Container crashes** → `restart: always` + healthchecks bring services back.
- **VPS reboot** → the systemd unit re-runs `compose up -d` on boot.
- **Bad release** → `rollback.sh` returns to the previously deployed commit (recorded
  in `/opt/hookclose/.deploy/previous`).
- **Provider outage / credit exhaustion** → handled in-runtime by the ProviderManager
  failover + SelfHealingRuntime (no redeploy needed).
- **Data loss** → nightly `backup.sh` (pg_dump + Redis AOF) with retention pruning.

## What is NOT included (deliberately)

- A managed observability stack (Grafana/Langfuse) — OTEL export is configured in
  [`../infra/otel/`](../infra/otel/); point `HOOKCLOSE_OTEL_*` at a collector when ready.
- Secrets management beyond a `.env.prod` file — graduate to a secret store
  (Vault / SOPS / Hetzner secrets) before scaling past one box.
