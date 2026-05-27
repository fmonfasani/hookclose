Implementá ProviderManager REAL para HookClose Runtime.

Objetivo:
Desacoplar completamente providers AI del runtime.

Implementar:

* BaseProvider
* ProviderRegistry
* ProviderManager
* ClaudeProvider
* OpenCodeProvider
* GeminiProvider
* LocalProvider

Agregar:

* capability routing
* health checks
* token budgeting
* cooldown handling
* retry policies
* automatic failover
* provider metrics
* structured tracing

El runtime debe:

* sobrevivir credit exhaustion
* cambiar provider automáticamente
* pausar workflows correctamente
* reanudar workflows automáticamente

Agregar:

* provider state persistence
* Redis integration
* PostgreSQL integration
* event integration

NO usar lógica hardcodeada.
NO acoplar providers al WorkflowEngine.
