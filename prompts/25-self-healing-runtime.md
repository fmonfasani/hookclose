Implementá SelfHealingRuntime.

Objetivo:
El runtime debe detectar, analizar y reparar errores automáticamente.

Implementar:

* failure analysis engine
* stacktrace parsing
* repair workflows
* retry loops
* rollback support
* repair limits
* escalation policies

Agregar:

* failure memory
* repair history
* metrics
* tracing
* observability

Los repair loops deben:

* tener límites
* ser deterministic-first
* ser auditables
