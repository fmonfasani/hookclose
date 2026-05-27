Quiero que actúes como Principal AI Systems Architect y Staff Software Engineer.

Objetivo:
Construir desde cero un ecosistema AI-native para desarrollo autónomo de software.

El sistema debe evolucionar progresivamente hacia:

* generación autónoma de código
* revisión automática
* testing automático
* reparación automática
* coordinación multiagente
* workflows determinísticos
* ejecución 24/7
* observabilidad
* runtime operacional reusable

IMPORTANTE:
NO quiero un chatbot.
NO quiero un “AI agent” simple.
Quiero una infraestructura operacional para agentes especializados.

Arquitectura objetivo:

* deterministic-first
* event-capable
* operational-memory-first
* multi-agent orchestration
* vendor-agnostic
* Docker local primero
* VPS después
* shared runtime
* state-machine driven

Stack obligatorio:

* Python 3.11+
* FastAPI
* PostgreSQL
* Redis
* Docker Compose
* Celery
* AsyncIO
* Pydantic v2
* SQLAlchemy 2.0
* pgvector
* OpenTelemetry
* Ruff
* Pytest
* mypy

Quiero que generes SOLAMENTE:

1. estructura completa del repositorio
2. bounded contexts
3. arquitectura por capas
4. contracts/interfaces
5. event schema inicial
6. workflow states
7. docker-compose base
8. bootstrap scripts
9. pyproject.toml
10. README arquitectónico

NO implementes lógica todavía.
NO generes business logic.
NO generes agentes todavía.

Reglas:

* fully typed
* async-first
* clean architecture
* SOLID
* no circular imports
* deterministic runtime
* event-capable desde diseño
* cada módulo con responsabilidad única
* adapters desacoplados
* contracts primero

La estructura debe incluir:

runtime/
agents/
contracts/
events/
workflows/
memory/
sandbox/
observability/
scheduler/
tasks/
adapters/
infra/
docker/
specs/
reviews/

Quiero una arquitectura seria enterprise-grade.
