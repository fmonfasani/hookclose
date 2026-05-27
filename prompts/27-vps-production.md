# PROMPT 27 — VPS Production Runtime (fase final, GATEADA)

> Fusión de los antiguos Prompt 11 y Prompt 18 (eran duplicados).
>
> ⚠️ **GATE:** No ejecutar este prompt hasta que el runtime core esté estable
> localmente: queues, workers, provider routing, retry loops y task chaining
> funcionando y verificados (es decir, prompts 20–26 completos y en verde).

## Objetivo

Migrar el AI Factory Runtime desde Docker local a operación persistente 24/7 en VPS.

## Target

- Hetzner
- Ubuntu 24.04

## Implementar

- production docker-compose (perfil prod)
- nginx reverse proxy
- HTTPS (TLS / certbot)
- systemd services
- persistent workers
- Redis persistence (AOF/RDB)
- PostgreSQL backups
- observability stack (Grafana, OpenTelemetry, Langfuse)
- deployment scripts
- update scripts
- rollback scripts
- restart policies / auto-restart
- monitoring + alerting
- health endpoints

## Resiliencia — el sistema debe sobrevivir a

- reinicios del VPS
- crashes de Docker
- provider failures
- worker failures (recovery + watchdogs)
- scheduler failures (recovery)
- network interruptions
- caídas parciales / workers muertos

## Agregar

- bootstrap scripts
- deploy / update / rollback scripts
- watchdogs + heartbeats
- worker recovery + scheduler recovery
- provider failover
