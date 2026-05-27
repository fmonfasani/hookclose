Implementá OpenClawWorker REAL.

Objetivo:
OpenClaw debe funcionar como execution runtime persistente.

Implementar:

* task consumer
* sandbox execution
* git branch-per-task
* file patching
* test execution
* lint execution
* retry loops
* artifact persistence
* event emission
* report generation

Agregar:

* Docker sandbox support
* local execution fallback
* structured logs
* tracing
* metrics
* watchdogs

IMPORTANTE:
OpenClaw NO controla workflows.
Solo ejecuta tasks.
