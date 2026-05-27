Implementá el Sandbox Runtime.

Objetivo:
Cada tarea AI debe ejecutarse en aislamiento seguro.

Implementar:

* Docker sandbox manager
* isolated workspaces
* git cloning
* ephemeral containers
* filesystem isolation
* command execution
* stdout/stderr capture
* timeout handling
* resource limits
* cleanup system

El runtime debe permitir:

* ejecutar tests
* correr linters
* instalar dependencias
* ejecutar builds
* destruir sandboxes automáticamente

Stack:

* Docker SDK Python
* async execution
* secure isolation

Agregar:

* logs
* tracing
* metrics
* retry support
* failure recovery

NO implementar agentes todavía.
