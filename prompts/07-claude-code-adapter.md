Implementá ClaudeCodeAdapter.

Objetivo:
Claude será el CodingAgent principal.

Implementar:

* Claude adapter
* prompt pipeline
* context builder
* task-to-prompt conversion
* code generation pipeline
* file generation
* patch generation
* retry handling
* validation hooks

IMPORTANTE:
Claude NO decide arquitectura.
Claude NO controla workflows.
Claude solo implementa tasks específicas.

El adapter debe:

* recibir Tasks estructuradas
* generar prompts determinísticos
* validar outputs
* emitir eventos
* persistir resultados

Agregar:

* token accounting
* tracing
* replay
* structured logs
* retries
* timeout handling

NO usar prompts gigantes.
Usar:

* contracts
* bounded context
* deterministic generation
