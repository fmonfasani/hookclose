Implementá ComplexityRoutingEngine.

Objetivo:
El runtime debe decidir automáticamente qué provider usar según complejidad y costo.

Implementar:

* Task complexity scoring
* Capability matching
* Cost-aware routing
* Priority-aware routing
* Retry-aware routing
* Context-window-aware routing

Ejemplos:

* architecture tasks → Claude
* simple implementation → OpenCode
* cheap extraction → Gemini
* fallback → local model

Agregar:

* routing policies
* dynamic scoring
* provider weighting
* observability
* metrics
* tracing

El routing debe ser:

* deterministic
* configurable
* auditable
