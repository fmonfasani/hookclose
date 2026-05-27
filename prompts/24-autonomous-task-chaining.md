Implementá AutonomousTaskChaining.

Objetivo:
El runtime debe generar automáticamente nuevas tasks según resultados previos.

Implementar:

* task dependency graph
* auto task generation
* workflow continuation
* repair task creation
* escalation tasks
* review tasks
* deployment tasks

Eventos:
TASK_COMPLETED
→ generate next task

TASK_FAILED
→ create repair task

Agregar:

* deterministic chaining
* retry-aware logic
* observability
* audit trail
* persistence

NO crear loops infinitos.
    