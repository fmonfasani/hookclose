# NAMING — Decisión de marcas y proyectos

> Documento canónico de nombres. Cualquier nombre nuevo (repo, carpeta, paquete,
> servicio, dominio) se valida contra este doc antes de crearse. Vive en el repo
> del **motor** (Hookclose), zona estable que no se toca en caliente.
>
> **Decisión tomada:** Opción A — **2 conceptos**, no 3.
> **Fecha:** 2026-06-12.

---

## 1. Los 2 conceptos (definitivos)

Antes había hasta 5 nombres para 2 cosas (AINE, HookClose, Waseller, HermesSell,
Wapsell). Se colapsan en **dos marcas por capa**: motor y producto.

| Concepto | Capa | Qué es | Responde a |
|---|---|---|---|
| **AINE** | Plataforma / motor / runtime | Motor genérico de ingeniería autónoma con IA (orquestador, workers, providers, routing, self-healing). El framework + el runtime + el SDK importable, todo bajo un nombre. | *"¿qué construye el software?"* |
| **Wapsell** | Producto / SaaS + marca | Agentes de venta por WhatsApp 24/7, determinísticos y auditables. Código, SDK del producto, dashboard, landing y marca comercial, todo bajo un nombre. | *"¿qué vendemos?"* |

**Regla de oro:** AINE es *cómo se construye*; Wapsell es *qué se vende*. Nunca se
mezcla código de AINE dentro de Wapsell ni al revés (AINE es dependencia externa
de Wapsell, no parte de él).

`HookClose` se **funde dentro de AINE** (era el nombre del repo; AINE era el nombre
de la plataforma — eran lo mismo). `Waseller` y `HermesSell` se **funden dentro de
Wapsell** (eran nombres legacy del mismo SaaS).

---

## 2. Mapa de renombrado (viejo → nuevo)

| Hoy | Tipo | Pasa a ser | Acción |
|---|---|---|---|
| `HookClose` / repo `fmonfasani/hookclose` | repo motor | **AINE** | renombrar repo a `aine` (o mantener `hookclose` como repo y "AINE" como nombre de producto — ver Fase 1) |
| `aine-platform` | paquete/dep | **AINE** | mantener nombre del paquete; reapuntar URL si se renombra el repo |
| carpeta `Porfolio/Hookclose` | carpeta local motor | **`Porfolio/aine`** | renombrar carpeta (Fase 3) |
| repo `fmonfasani/waseller` | repo SaaS | **Wapsell** | renombrar a `wapsell-saas` (o `wapsell-core`) + alias |
| paquete PyPI `waseller` | SDK producto | **Wapsell** | publicar `wapsell` + dejar `waseller` como alias deprecado |
| carpeta `Porfolio/HermesSell` | carpeta local SaaS | **`Porfolio/wapsell-saas`** | renombrar carpeta (Fase 3) |
| repo/carpeta `wapsell` (landing) | landing | **Wapsell** (landing) | ya correcto, se mantiene |
| dominios `*.wapsell.com` | prod | **Wapsell** | ya correcto, se mantiene |

Resultado: una marca de motor (**AINE**) + una marca de producto (**Wapsell**, con
sub-piezas: `wapsell-saas`/core, `wapsell` landing, SDK `wapsell`).

---

## 3. Riesgos (LEER antes de ejecutar el renombrado)

### 3.1 Riesgos del renombrado en sí

- **Breakage de imports.** La template T2 (`project-template-aine`) declara la dep
  `aine-platform` apuntando a `github.com/fmonfasani/hookclose`. Si se renombra el
  repo del motor, esa dependencia queda rota hasta reapuntar la URL. → *Mitigación:
  renombrar repo con redirect de GitHub activo + actualizar el `pyproject.toml` de T2
  en el mismo PR.*
- **Repo/paquete `waseller` ya público.** Está publicado con ese nombre (GitHub +
  PyPI). Renombrar deja instalaciones y URLs viejas muertas. → *Mitigación: GitHub
  redirige repos renombrados automáticamente; en PyPI NO se puede renombrar — hay que
  publicar `wapsell` nuevo y marcar `waseller` como deprecado apuntando al nuevo.*
- **Paths en CI/docs.** Carpetas `HermesSell`/`Hookclose` están referenciadas en
  workflows, READMEs y memoria. Renombrar carpeta sin actualizar refs rompe CI local.
  → *Mitigación: grep global de la cadena vieja antes de renombrar; Fase 3 al final.*
- **Memoria del agente desincronizada.** Los archivos de `memory/` referencian rutas
  y nombres viejos (`HermesSell`, `waseller`). → *Mitigación: actualizar `MEMORY.md`
  y los archivos afectados en la misma tanda del renombrado.*

### 3.2 Riesgos por el AGENTE CONCURRENTE en `wapsell` (crítico)

> Hay otro agente corriendo que está **mejorando `wapsell`** mientras escribimos esto.

- **Colisión de escritura / merge conflict.** Si tocamos archivos en `wapsell/`
  mientras el otro agente commitea, hay sobrescritura o conflicto. → *Mitigación: NO
  tocar `wapsell/` ni `HermesSell/` mientras el otro agente esté activo. El renombrado
  de esas carpetas/repos se difiere hasta que el otro agente termine y haga merge.*
- **Divergencia de criterio.** El otro agente no conoce esta decisión → sigue usando
  `waseller`/`HermesSell` y deshace el renombrado. → *Mitigación: este doc vive en
  Hookclose (no en wapsell); comunicar la decisión antes de que el otro agente toque
  naming; el renombrado lo hace UN solo actor, coordinado.*
- **Inventario movedizo.** Cualquier listado del estado de `wapsell` que hagamos ahora
  queda obsoleto en minutos. → *Mitigación: no basar el plan en un snapshot; basar las
  fases en pasos idempotentes que se puedan correr cuando el repo esté quieto.*
- **Doble fuente de verdad de la landing.** Existe `Porfolio/wapsell` (real, con git
  propio) y una copia suelta `Hookclose/wapsell/` (untracked). El otro agente podría
  estar en cualquiera de las dos. → ✅ **Resuelto 2026-06-12:** `Porfolio/wapsell` es la
  canónica (al día con origin/main); `Hookclose/wapsell/` era un clon olvidado 2 commits
  atrás, working tree limpio, sin nada sin pushear → **borrado**.

### 3.3 Riesgo de elegir Opción A (2 nombres) vs B (3 nombres)

- **Pérdida de granularidad de marca.** Al fundir HookClose en AINE, perdés la
  distinción "SDK público vs runtime interno". Si en el futuro querés vender el motor
  como producto aparte del SDK, habrá que volver a separar. → *Aceptado: hoy no hay
  caso de negocio para 3 marcas; la simplicidad gana. Revisar si AINE se comercializa.*

---

## 4. Plan de renombrado por fases (coordinado, seguro)

Orden pensado para **no chocar con el agente concurrente** y para que cada fase sea
reversible.

**Fase 0 — Congelar la decisión (ahora).**
Este doc. No se toca código todavía.

**Fase 1 — Motor (AINE), zona segura.**
El otro agente NO toca Hookclose. Se puede hacer ya:
- Unificar el nombre en docs del motor: README/ARCHITECTURE pasan de "HookClose / AINE"
  a solo **AINE**. HookClose queda mencionado solo como "nombre histórico del repo".
- Decidir si se renombra el repo `hookclose → aine` (con redirect) o se deja el repo
  y solo el *producto* se llama AINE. Recomendado: renombrar repo + redirect.
- Si se renombra el repo: actualizar la URL de `aine-platform` en T2 en el mismo PR.

**Fase 2 — Producto (Wapsell), SOLO cuando el agente concurrente termine.**
- 🟡 **En curso (2026-06-12):** rename del paquete SDK `waseller → wapsell` hecho en
  rama `feat/rebrand-wapsell` → **PR #48** (gate verde: ruff+mypy strict+pytest 427).
  Incluye shim de env bidireccional para no romper prod.
- [ ] Mergear PR #48.
- [ ] Renombrar repo `waseller → wapsell-saas` (GitHub redirige) + actualizar URLs
  `fmonfasani/waseller` y el bloque `git clone`/`cd` en README. **Tras merge.**
- [ ] Publicar SDK `wapsell` en PyPI; marcar `waseller` deprecado. **BLOQUEADO: falta
  token PyPI.**
- [ ] Unificar nombre en docs operativos del SaaS: queda lo de `docs/DEPLOY*`,
  `PRODUCTION-LOG`, `prompts/` (histórico) — gran parte va con Fase 3.

**Fase 3 — Carpetas locales (al final, con todo quieto).**
- `Porfolio/Hookclose → Porfolio/aine`
- `Porfolio/HermesSell → Porfolio/wapsell-saas`
- Actualizar `memory/MEMORY.md` + archivos afectados + working dirs del harness.
- ~~Resolver la copia duplicada `Hookclose/wapsell/`~~ ✅ hecho 2026-06-12 (borrada).

**Verificación al cierre de cada fase:**
- `grep` global del nombre viejo → 0 resultados en código (los menciones históricas
  en docs están OK si están etiquetadas como "legacy").
- CI verde en cada repo afectado.
- `aine-platform` instala y la template T2 levanta con la dep reapuntada.

---

## 5. Estado

- [x] Fase 0 — Decisión congelada (Opción A).
- [~] Fase 1 — Motor → AINE.
  - [x] Docs del motor unificados a "AINE" (README, ARCHITECTURE, CONTRIBUTING,
    ROADMAP, prompts/INDEX). Nota histórica de HookClose añadida en README.
  - [ ] Renombrar repo `hookclose → aine` + redirect + reapuntar URL de `aine-platform`
    en T2. **Pendiente de OK** (acción outward-facing, no reversible sin fricción).
  - [ ] Renombrar namespaces de métricas `hookclose_<...>` (cambio de código, no doc;
    rompe dashboards — se hace junto al rename del repo, no ahora).
- [ ] Fase 2 — Producto → Wapsell (bloqueada por agente concurrente en `wapsell`).
- [ ] Fase 3 — Carpetas locales.
