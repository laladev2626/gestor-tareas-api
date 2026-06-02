# API de Gestión de Tareas

API REST para gestionar tareas construida con **FastAPI** y **SQLAlchemy**. Permite crear, consultar, actualizar y eliminar tareas. Cada tarea tiene un identificador, título, descripción opcional, estado (`pending`, `in_progress`, `done`), prioridad (`low`, `medium`, `high`), categoría (`trabajo`, `personal`, `estudio`, `hogar`, `otro`) y fecha de creación automática.

---

## Requisitos previos

| Requisito | Versión mínima |
|---|---|
| Python | 3.12+ |

### Dependencias principales

| Paquete | Versión |
|---|---|
| FastAPI | 0.136.1 |
| SQLAlchemy | 2.0.49 |
| Pydantic | 2.13.4 |
| Uvicorn | 0.46.0 |

### Dependencias de desarrollo

| Paquete | Versión |
|---|---|
| pytest | 9.0.3 |
| httpx | 0.28.1 |
| anyio | 4.13.0 |

---

## Instalación

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/laladev2626/gestor-tareas-api.git
   cd gestor-tareas-api
   ```

2. Crear y activar el entorno virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS / Linux
   venv\Scripts\activate           # Windows
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

---

## Arrancar la aplicación

```bash
uvicorn aplicacion.principal:app --reload
```

La API quedará disponible en `http://127.0.0.1:8000`.
La documentación interactiva (Swagger UI) estará en `http://127.0.0.1:8000/docs`.

---

## Endpoints

Todos los endpoints se encuentran bajo el prefijo `/tasks`.

### 1. Listar todas las tareas

| | |
|---|---|
| **Método** | `GET` |
| **Ruta** | `/tasks/` |
| **Parámetros** | Ninguno |

**Ejemplo de petición:**

```bash
curl http://127.0.0.1:8000/tasks/
```

**Ejemplo de respuesta** (`200 OK`):

```json
[
  {
    "id": 1,
    "title": "Revisar documentación",
    "description": "Revisar la documentación del proyecto",
    "status": "pending",
    "priority": "medium",
    "category": "otro",
    "created_at": "2025-05-28T10:00:00"
  }
]
```

---

### 2. Obtener una tarea por ID

| | |
|---|---|
| **Método** | `GET` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |

**Ejemplo de petición:**

```bash
curl http://127.0.0.1:8000/tasks/1
```

**Ejemplo de respuesta** (`200 OK`):

```json
{
  "id": 1,
  "title": "Revisar documentación",
  "description": "Revisar la documentación del proyecto",
  "status": "pending",
  "priority": "medium",
  "category": "otro",
  "created_at": "2025-05-28T10:00:00"
}
```

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 3. Crear una tarea

| | |
|---|---|
| **Método** | `POST` |
| **Ruta** | `/tasks/` |
| **Cuerpo (JSON)** | `title` (str, obligatorio), `description` (str, opcional), `status` (str, opcional — por defecto `"pending"`), `priority` (str, opcional — por defecto `"medium"`), `category` (str, opcional — por defecto `"otro"`) |

Valores válidos para `status`: `"pending"`, `"in_progress"`, `"done"`.
Valores válidos para `priority`: `"low"`, `"medium"`, `"high"`.
Valores válidos para `category`: `"trabajo"`, `"personal"`, `"estudio"`, `"hogar"`, `"otro"`.

**Ejemplo de petición:**

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Escribir tests", "description": "Cubrir los endpoints principales", "priority": "high"}'
```

**Ejemplo de respuesta** (`201 Created`):

```json
{
  "id": 2,
  "title": "Escribir tests",
  "description": "Cubrir los endpoints principales",
  "status": "pending",
  "priority": "high",
  "category": "otro",
  "created_at": "2025-05-28T10:05:00"
}
```

---

### 4. Actualizar parcialmente una tarea

| | |
|---|---|
| **Método** | `PATCH` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |
| **Cuerpo (JSON)** | `title` (str, opcional), `description` (str, opcional), `status` (str, opcional), `priority` (str, opcional), `category` (str, opcional) |

Solo se modifican los campos incluidos en el cuerpo de la petición.

**Ejemplo de petición:**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/2 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

**Ejemplo de respuesta** (`200 OK`):

```json
{
  "id": 2,
  "title": "Escribir tests",
  "description": "Cubrir los endpoints principales",
  "status": "in_progress",
  "priority": "high",
  "category": "otro",
  "created_at": "2025-05-28T10:05:00"
}
```

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 5. Eliminar una tarea

| | |
|---|---|
| **Método** | `DELETE` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |

**Ejemplo de petición:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

**Respuesta exitosa:** `204 No Content` (sin cuerpo).

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

## Tests

Los tests utilizan una base de datos SQLite en memoria con `StaticPool` para garantizar aislamiento entre casos. No tocan el archivo `tareas.db` de producción.

```bash
pytest tests/ -v
```

---

## Estructura del proyecto

```
gestor-tareas-api/
├── aplicacion/                # Paquete principal de la aplicación
│   ├── principal.py           # Punto de entrada: instancia de FastAPI y registro de routers
│   ├── base_de_datos.py       # Configuración del engine y sesión de SQLAlchemy
│   ├── modelos.py             # Modelos ORM (tabla tasks, enum TaskStatus)
│   ├── esquemas.py            # Esquemas Pydantic de entrada y respuesta
│   └── rutas/                 # Definición de endpoints REST
│       └── tareas.py          # Endpoints CRUD de tareas
├── tests/                     # Suite de tests automatizados con pytest
│   └── test_tasks.py          # Tests de los endpoints de tareas
├── requirements.txt           # Dependencias del proyecto
├── AGENTS.md                  # Documentación técnica y guía arquitectónica
└── README.md                  # Este archivo
```
