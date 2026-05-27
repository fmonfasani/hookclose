Implementá exclusivamente el EventBus interno del sistema.

Objetivo:
El runtime debe ser request-driven operativamente pero event-capable internamente.

Implementar:

* Event base class
* Typed events
* EventBus
* Async subscribers
* Event registry
* Event persistence hooks
* Replay support
* Dead-letter support
* Retry support
* Event metadata
* Correlation IDs
* Tenant IDs
* Trace IDs

Eventos iniciales:
TASK_CREATED
TASK_ASSIGNED
SPEC_GENERATED
CODE_GENERATED
TEST_FAILED
TEST_PASSED
REVIEW_REJECTED
REVIEW_APPROVED
DEPLOY_STARTED
DEPLOY_FAILED
DEPLOY_SUCCEEDED

Requisitos:

* async-first
* Redis Streams compatible
* in-memory fallback
* deterministic behavior
* idempotency
* replayable
* observable

Agregar:

* pytest suite
* tracing
* structured logging
* architecture documentation

NO usar Kafka.
NO usar microservices todavía.
NO usar distributed systems complejos.
