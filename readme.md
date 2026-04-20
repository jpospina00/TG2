# Entrenador Virtual de Habilidades Blandas

Entrenador virtual basado en inteligencia artificial para el desarrollo de escritura empática y networking profesional en estudiantes universitarios de Ingeniería de Sistemas.
Construido con FastAPI, SQLModel, Groq (LLaMA 3.3 70B), ChromaDB y React 18.

---

## Stack Tecnológico

| Capa | Tecnología | Detalle |
|---|---|---|
| Frontend | React 18 | localhost:3000 |
| Backend | FastAPI (Python) | localhost:8000 |
| BD Relacional | SQLite (dev) / PostgreSQL (prod) | SQLModel ORM |
| BD Vectorial | ChromaDB (local, solo lectura) | 40+ documentos curados |
| LLM | Groq API — llama-3.3-70b-versatile | Capa gratuita con fallback de keys |
| Autenticación | Auth0 — OAuth 2.0 | cacheLocation=localstorage + useRefreshTokens |
| Contenedores | Docker + Docker Compose | Backend + Frontend + PostgreSQL |
| CI | GitHub Actions | Lint + tests + build en cada push a main |

---

## Estructura del Proyecto

```
TG2/
├── docker-compose.yml
├── .github/workflows/ci.yml
├── Back/
│   ├── model/                   # Entidades SQLModel (9 tablas)
│   ├── service/                 # Lógica de negocio y servicio de IA
│   │   ├── ai.py                # Evaluación, generación de retos, diagnóstico, empatía lab
│   │   └── rag.py               # Consultas ChromaDB con filtros por módulo, nivel y tipo
│   ├── web/                     # Routers REST
│   │   ├── ai.py                # Endpoints IA — simple, conversacional, empatía lab
│   │   ├── diagnostic.py        # Diagnóstico adaptativo
│   │   └── student_profile.py   # Perfil del estudiante
│   ├── tests/                   # Tests unitarios (58+ tests)
│   ├── chromadb_data/
│   │   ├── empathy.json         # 25+ documentos de empatía (español)
│   │   ├── networking.json      # 16 documentos de networking (español)
│   │   └── load_chroma.py       # Script de carga con fallback modulo/tipo/nivel
│   ├── main.py
│   ├── config.py
│   ├── database.py              # Soporta SQLite y PostgreSQL
│   ├── seed.py                  # Crea los 2 módulos base
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── pytest.ini
└── Front/soft-skills-front/
    └── src/components/
        ├── login/               # Login con Auth0
        ├── onboarding/          # Perfil inicial del estudiante
        ├── dashboard/           # Dashboard con stats e historial
        ├── module/              # Módulo networking con personajes
        ├── empathy/             # Módulo empatía — Laboratorio
        │   ├── EmpathyModule.js # Lista de situaciones sin personajes
        │   ├── EmpathyLab.js    # Reto — análisis o selección múltiple
        │   └── EmpathyFeedback.js # Retroalimentación con puntajes
        ├── diagnostic/          # Test diagnóstico inicial
        ├── challenge/           # Reto simple y conversacional (networking)
        ├── feedback/            # Retroalimentación networking
        ├── guide/               # Guía de aprendizaje
        └── shared/              # LevelUp, NotFound, ErrorMessage
```

---

## Configuración sin Docker (desarrollo local)

### Backend

```bash
cd Back
python -m venv venv
source venv/Scripts/activate   # Git Bash
pip install -r requirements.txt
```

Crea `Back/.env`:
```
GROQ_API_KEYS=tu_key_aqui
```

```bash
python seed.py
python chromadb_data/load_chroma.py
uvicorn main:app --reload
```

Servidor: **http://localhost:8000** | Swagger: **http://localhost:8000/docs**

### Frontend

```bash
cd Front/soft-skills-front
npm install
npm start
```

Crea `Front/soft-skills-front/.env`:
```
REACT_APP_AUTH0_DOMAIN=dev-dc5eye6w4usbnja8.us.auth0.com
REACT_APP_AUTH0_CLIENT_ID=qQnU7ml9b9EPhJ2J8Tc6dPHzyxQcn32t
REACT_APP_API_URL=http://localhost:8000
```

---

## Configuración con Docker

```bash
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432

---

## Tests

```bash
cd Back
pytest tests/ -v
```

| Archivo | Tests | Cobertura |
|---|---|---|
| test_user.py | 8 | CRUD + duplicado + auth0 |
| test_module.py | 3 | Listar + obtener + 404 |
| test_challenge.py | 8 | CRUD + filtro módulo/nivel/usuario |
| test_progress.py | 5 | Crear + duplicado + actualizar nivel |
| test_conversation.py | 5 | Crear + cerrar + listar |
| test_message.py | 3 | Crear + orden |
| test_feedback.py | 4 | Crear + obtener + completado/no |
| test_ai.py | 6 | Simple + conversacional con mocks Groq |
| test_diagnostic.py | 5 | Preguntas + submit + reset |
| test_student_profile.py | 4 | CRUD perfil |
| test_empathy.py | 7 | Opciones + análisis + selección múltiple |

---

## Módulos del Sistema

### Módulo de Empatía — Laboratorio de Empatía

Flujo completamente diferente al networking. Sin personajes ni chat.

**Rutas:**
- `/empathy/:moduleId` — lista de situaciones (EmpathyModule.js)
- `/empathy/challenge/:challengeId` — reto activo (EmpathyLab.js)
- `/empathy/feedback/:conversationId` — retroalimentación (EmpathyFeedback.js)

**Tipos de reto:**
- `analysis` — el estudiante identifica emociones Y escribe un mensaje. La IA evalúa 4 dimensiones con puntaje numérico.
- `multiple_choice` — el estudiante elige la respuesta más empática entre 4 opciones generadas por IA. La IA explica por qué cada opción funciona o no.

**Distribución por nivel:**
| Nivel | multiple_choice | analysis |
|---|---|---|
| Inicial | 3 | 2 |
| Intermedio | 2 | 3 |
| Avanzado | 1 | 4 |

**Dimensiones evaluadas en análisis:**
- Precisión emocional (1-10)
- Calidad del mensaje (1-10)
- Tono empático (1-10)
- Coherencia contextual (1-10)
- Aprobado si promedio ≥ 6.0 (inicial), ≥ 6.5 (intermedio), ≥ 7.0 (avanzado)

**Endpoints nuevos:**
- `GET /ai/empathy/options/:challengeId` — genera 4 opciones para selección múltiple
- `POST /ai/empathy/evaluate` — evalúa las dos respuestas del análisis
- `POST /ai/empathy/multiple-choice` — registra resultado de selección múltiple

### Módulo de Networking — Personajes virtuales

Flujo con personajes, panel de detalle y retos tipo chat.

**Rutas:**
- `/module/:moduleId` — módulo con grid de personajes (Module.js)
- `/challenge/simple/:id` — reto de respuesta única
- `/challenge/conversational/:id` — reto con hasta 3 turnos

**Tipos de reto:** `simple` y `conversational`

---

## Flujo Completo del Usuario

1. Login con Auth0
2. Onboarding — semestre, especialización, nivel autopercibido
3. Dashboard — ver módulos y progreso
4. Diagnóstico inicial — 3 preguntas múltiple + 1 escritura
5. IA determina nivel y genera retos personalizados contextualizados por especialización
6. Retos del módulo según tipo (empatía o networking)
7. Retroalimentación automática por IA + RAG
8. Al completar 4/5 retos → sube de nivel → IA genera 5 retos nuevos
9. Pantalla de celebración al subir de nivel

---

## Endpoints Principales

| Método | Endpoint | Descripción |
|---|---|---|
| POST | /users | Registrar usuario |
| GET | /users/auth0/{auth0_id} | Obtener usuario por auth0_id |
| GET | /modules | Listar módulos |
| GET | /challenges/module/{id}/level/{level} | Retos por módulo, nivel y usuario |
| POST | /progress | Inicializar progreso |
| GET | /progress/user/{user_id} | Progreso del usuario |
| POST | /conversations | Iniciar conversación |
| POST | /ai/simple/evaluate | Evaluar reto simple |
| POST | /ai/conversational/turn | Turno conversacional |
| POST | /ai/conversational/close | Cerrar conversación |
| GET | /ai/empathy/options/{challenge_id} | Opciones selección múltiple empatía |
| POST | /ai/empathy/evaluate | Evaluar análisis de empatía |
| POST | /ai/empathy/multiple-choice | Registrar selección múltiple empatía |
| GET | /diagnostic/questions/{module_name} | Generar preguntas diagnóstico |
| POST | /diagnostic/submit | Evaluar y generar retos personalizados |
| GET | /diagnostic/user/{user_id}/module/{module_id} | Último diagnóstico |
| DELETE | /diagnostic/user/{user_id}/module/{module_id}/reset | Reiniciar diagnóstico |
| POST | /students/profile | Crear/actualizar perfil |
| GET | /students/profile/user/{user_id} | Obtener perfil |

---

## ChromaDB

- Colección: `system_context` | Modelo: all-MiniLM-L6-v2
- Filtros: módulo + nivel + tipo (usando operador `$and`)
- Tipos de documentos: `agent_profile`, `evaluation_criteria`, `example_response`, `challenge_pattern`, `personalization_guide`
- empathy.json: 25+ documentos en español
- networking.json: 16 documentos en español

---

## Decisiones de Diseño

- **Módulo empatía y networking completamente independientes** en flujo y visual
- **Sin retos quemados** — 100% generados por IA según diagnóstico y perfil
- **La escritura pesa más que el puntaje múltiple** en el diagnóstico
- **ChromaDB solo lectura en ejecución** — se puebla una sola vez
- **Historial de conversación en estado del frontend** durante la sesión
- **Límite 300/400 caracteres** en análisis de empatía, 500 en networking
- **Docker usa PostgreSQL** — desarrollo local usa SQLite sin cambios al código
- **Feedback de empatía guardado como JSON** en tabla feedback.content