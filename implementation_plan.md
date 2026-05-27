# Implementación de HermesSell - Master Plan

Plan detallado de ejecución end-to-end del SaaS HermesSell (WhatsApp Sales AI) basado en las especificaciones maestras del documento de diseño.

> [!NOTE]
> Este plan abarca desde la inicialización del repositorio hasta el despliegue en producción con seguridad y multi-tenancy. La duración estimada total es de **23 días hábiles**.

## User Review Required

> [!IMPORTANT]
> **Dominio y VPS:** Para la fase 1 se necesita un VPS Ubuntu 24.04 LTS y un dominio apuntado al servidor (requerido para TLS y webhooks de Meta).
> **Credenciales:** Se requiere acceso de administrador al Meta Business Manager, OpenRouter API y Kapso.

## Open Questions

> [!WARNING]
> 1. ¿Disponemos ya del VPS y el dominio configurado o debemos planificar su adquisición?
> 2. ¿El equipo de infraestructura será el mismo que el de desarrollo o habrá separación de roles para las fases de VPS (Fase 1 y 13)?
> 3. Las fases 5, 6, 8, 10 y 11 aparecen en el índice del docx original, pero los pasos a nivel de código no están tan desarrollados como otras. ¿Se deben ejecutar basándonos en mejores prácticas estándar o proveerás más adelante las especificaciones técnicas para ellas?

## Proposed Changes

La implementación se dividirá en 4 Hitos Principales (Milestones).

---

### Hito 1: Infraestructura y Core Agent (Días 1-4)
**Entregable:** Repositorio estructurado, servidor productivo asegurado, agente Hermes base corriendo y webhook de Meta Gateway en funcionamiento.

#### Fase 0: Repositorio y estructura (1 día)
- [ ] Inicializar Git y agregar submódulos de Kapso (inbox, api-js, skills, broadcasts, voice-agent).
- [ ] Crear estructura de directorios (`sdk/`, `services/`, `dashboard/`, `infra/`, `skills/`).
- [ ] Configurar `pyproject.toml` base con dependencias (FastAPI, Celery, SQLAlchemy, openai, etc.).
- [ ] Inicializar CI/CD básico en GitHub Actions.

#### Fase 1: VPS y sistema base (1 día)
- [ ] Ejecutar script de provisioning (`provision_vps.sh`) en Ubuntu 24.04.
- [ ] Instalar Docker, Node.js 20, Python 3.11, Redis y PostgreSQL 16.
- [ ] Configurar UFW (Firewall) permitiendo puertos 22, 80 y 443.
- [ ] Crear el usuario restringido `hermesell` y los directorios de tenants (`/opt/hermesell`).

#### Fase 2: Hermes Agent (1 día)
- [ ] Instalar Hermes v0.13.13 bajo el usuario `hermesell`.
- [ ] Configurar el template base `config.yaml` apuntando a Claude 3.5 Sonnet y OpenRouter.
- [ ] Configurar variables de entorno iniciales en `.env`.
- [ ] Instalar y habilitar el servicio systemd del Gateway Hermes.

#### Fase 3: Gateway WhatsApp (1 día)
- [ ] Levantar gateway local Kapso en puerto 4000.
- [ ] Construir Webhook Handler en FastAPI (`routers/webhook.py`).
- [ ] Implementar verificación de firmas HMAC-SHA256 y parseo de payloads de Meta.

---

### Hito 2: RAG, Memoria y Lógica de Negocio (Días 5-10)
**Entregable:** Motor de Ingesta Asíncrona, Base de Conocimiento (Hindsight) funcionando con múltiples formatos y Skills de Venta operativos.

#### Fase 4: Preprocesador multimodal (2 días)
- [ ] Crear aplicación Celery + Redis (`worker.py`).
- [ ] Implementar extractores: CSV (Pandas), PDF/DOCX, Audio (Whisper), Video/Imágenes (Gemini 2.5 Flash).
- [ ] Implementar `HindsightIngestor` y su schema de BD PostgreSQL (tabla `facts`).

#### Fase 5 y 6: RAG, Ingesta y Memoria (2 días)
- [ ] Configurar Hindsight en modo local para el RAG de productos.
- [ ] Configurar Honcho para la memoria de compradores y dialecticDepth (perfiles de usuarios).

#### Fase 7: Lógica de Ventas (2 días)
- [ ] Definir `sales-closer` skill: protocolo de identificación, stock, precio, objeciones y confirmación de pago.
- [ ] Definir `catalog-lookup` y `lead-qualifier` skills.
- [ ] Implementar template `SOUL.md` dinámico para cada Tenant.
- [ ] Implementar inyección automática del prompt de comportamiento (`/goal`) en cada mensaje.

---

### Hito 3: Arquitectura Multi-tenant y SDK (Días 11-17)
**Entregable:** SDK Python empaquetado para distribución y motor de orquestación levantando contenedores Docker aislados por cliente.

#### Fase 8: Orquestador Multi-tenant (2 días)
- [ ] Implementar Router y Supervisor de Tenants.
- [ ] Habilitar tableros Kanban del agente.

#### Fase 9: SDK Python (`hermesell`) (3 días)
- [ ] Desarrollar `HermesSellClient` como punto de entrada de alto nivel.
- [ ] Implementar lógica de `TenantManager` para levantar contenedores Docker dinámicos y base de datos propia al crear un cliente.
- [ ] Desarrollar CLI en Typer para control de operaciones desde terminal.
- [ ] Publicar paquete en PyPI.

#### Fase 12: Onboarding Flow (2 días)
- [ ] Integrar Meta Embedded Signup para conexión 1-clic.
- [ ] Exponer endpoint `/tenants/connect-whatsapp` y manejar el callback.
- [ ] Automatizar: crear registro, generar SOUL.md, inicializar Hindsight, levantar contenedor del tenant en background.

---

### Hito 4: Dashboards y Producción (Días 18-23)
**Entregable:** Interfaces gráficas de usuario operativas y sistema expuesto a internet de forma segura bajo protocolo HTTPS.

#### Fase 10: Dashboard Implementador (3 días)
- [ ] Desarrollar Next.js Admin app para administrar Tenants, Skills globales y visualización de métricas del servidor.

#### Fase 11: Dashboard Cliente Final (2 días)
- [ ] Desarrollar Next.js Client app: bandeja de entrada, vista Kanban, analítica simplificada y control de catálogo (drag & drop al preprocesador).

#### Fase 13: Seguridad y Producción (1 día)
- [ ] Configurar proxy inverso Nginx (`nginx.conf`).
- [ ] Emitir y configurar certificados TLS vía Let's Encrypt / certbot.
- [ ] Validar encriptado de tokens (AES-256) y validación de webhooks.
- [ ] Habilitar Rate Limiting (SlowAPI) y revisión de logs ocultando secrets.

## Verification Plan

### Automated Tests
- Validar pipeline CI/CD en `.github/workflows`.
- Probar localmente subida de archivos multimodal y verificar inserción en Hindsight BD.
- Unit testing de las abstracciones del SDK (TenantManager y HermesSellClient).

### Manual Verification
- Levantar un tenant de prueba utilizando el CLI (`hermesell tenant_create`).
- Probar el flujo completo interactuando con el bot de WhatsApp vía Meta Webhooks (asegurando el correcto enrutamiento del webhook a Meta).
- Registrar una venta ficticia y corroborar la notificación al home channel.
