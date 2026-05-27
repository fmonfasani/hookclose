Ahora implementá exclusivamente el WorkflowEngine.

Objetivo:
El WorkflowEngine será el verdadero core del sistema.

NO usar LLMs para orquestación.

Responsabilidades:

* state transitions
* task lifecycle
* workflow orchestration
* retries
* escalation
* deterministic execution
* event emission

Implementar:

* WorkflowEngine
* WorkflowState enum
* Transition system
* WorkflowContext
* Event emission hooks
* Persistence interfaces
* Retry policies
* Failure handling
* Workflow registry

Estados:
NEW
PLANNING
CODING
TESTING
REVIEWING
FIXING
READY
DEPLOYING
DEPLOYED
FAILED
ESCALATED

Reglas:

* async-only
* fully typed
* production-ready
* sin dependencias AI todavía
* no mocks
* no placeholders vacíos
* clean architecture
* extensible
* sin lógica hardcodeada

NO implementar agentes todavía.

Agregar:

* tests
* typing
* logging
* tracing hooks
* architecture comments
