# NovoClip · frontend

Next.js (App Router) + TypeScript + Tailwind v4 + **HeroUI v3** (`@heroui/react`, `@heroui/styles`). Diseño inspirado en OpusClip y en los componentes de HeroUI. Datos simulados por defecto; se cambia a backend real con una variable.

## Cómo ejecutarlo

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

Producción: `npm run build && npm start`.

## Datos simulados o reales

`frontend/.env.local` (hay un `.env.example`):

| Variable | Valor | Efecto |
|---|---|---|
| `NEXT_PUBLIC_USE_MOCK` | `true` (por defecto) | Todo simulado; no necesita backend |
| `NEXT_PUBLIC_USE_MOCK` | `false` | Usa FastAPI; `next.config.ts` reenvía `/api/*` y `/files/*` a `BACKEND_URL` |
| `BACKEND_URL` | `http://127.0.0.1:8000` | Dónde corre el backend |

Con datos simulados, el selector **Datos de prueba** (abajo en la barra lateral; arriba en el celular) cambia entre: Normal, Vacío, Con errores, Carga lenta y Caso extremo.

## Estructura

```
app/                 rutas: / · /proyectos · /proyectos/[id] · /marca · /calendario · /cuentas
components/          ui/ (envoltorios de HeroUI: botón, chip, modal, aviso, switch…), shell/, home/, projects/, brand/, calendar/, accounts/
lib/api/             UNA capa de datos
  types.ts           formas del backend (parte 1) + lo que requiere backend nuevo (parte 2)
  mock.ts            simulador del pipeline (misma forma que app.py)
  real.ts            fetch al backend real
  extras.ts          kit de marca, calendario y cuentas (localStorage)  [REQUIERE BACKEND NUEVO]
lib/stages.ts        etapas reales del pipeline según el progreso
lib/time.ts          zona America/Santo_Domingo
capturas/            capturas de cada pantalla y estado (móvil y escritorio)
```

Ver `../PENDIENTES-BACKEND.md` para lo que falta en el backend.
