Implementá el sistema de Tasks AI-native.

Objetivo:
Todo trabajo del sistema debe ser una Task estructurada.

Implementar:

* Task model
* Task registry
* Task scheduler
* Task dependencies
* Task priorities
* Task retries
* Task ownership
* Task persistence
* Task events
* Task state machine

Cada Task debe tener:

* id
* goal
* inputs
* outputs
* dependencies
* constraints
* validations
* assigned_agent
* retry_policy
* workflow_state
* metadata

Agregar:

* PostgreSQL persistence
* Pydantic schemas
* async repository layer
* service layer
* event integration
* tracing
* metrics

NO implementar AI todavía.
NO usar agentes todavía.

Quiero infraestructura operacional sólida primero.
