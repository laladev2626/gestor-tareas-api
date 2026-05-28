# ADR-001: Elección de SQLite como base de datos

## Estado

**Aceptado**

## Contexto

La API de Gestión de Tareas necesita una base de datos para almacenar tareas con sus atributos (título, descripción, estado y fecha de creación). El proyecto está orientado a servir como plantilla backend estandarizada para aplicaciones basadas en tareas, por lo que la solución de persistencia debe cumplir los siguientes requisitos:

- Despliegue sencillo sin dependencias externas de infraestructura.
- Mínima configuración para que un desarrollador pueda arrancar el proyecto en local de forma inmediata.
- Compatibilidad con SQLAlchemy 2.0 y el patrón de sesión inyectada por dependencia que usa FastAPI.
- Volumen de datos esperado reducido: una sola tabla (`tasks`) con operaciones CRUD básicas.

## Decisión

Se ha elegido **SQLite** como motor de base de datos, almacenando los datos en el archivo local `tareas.db`. La conexión se configura con el parámetro `check_same_thread=False` para permitir el acceso concurrente desde los hilos del servidor ASGI (Uvicorn). Los tests utilizan SQLite en memoria con `StaticPool` para garantizar aislamiento entre casos sin tocar la base de datos de producción.

## Razones

1. **Cero infraestructura**: SQLite es una librería embebida; no requiere instalar, configurar ni mantener un servidor de base de datos independiente.
2. **Portabilidad**: el archivo `tareas.db` se puede copiar, versionar o eliminar directamente desde el sistema de ficheros.
3. **Integración nativa con Python**: el módulo `sqlite3` viene incluido en la biblioteca estándar, eliminando dependencias adicionales del sistema operativo.
4. **Coherencia con el alcance del proyecto**: para una API de plantilla con una sola tabla y volumen bajo, un motor embebido es la solución más proporcional.
5. **Compatibilidad total con SQLAlchemy**: SQLite está soportado como dialecto de primera clase en SQLAlchemy, incluyendo soporte para `StaticPool` en tests.

## Alternativas consideradas

### PostgreSQL

| Aspecto | Detalle |
|---|---|
| **Ventajas** | Soporte completo de transacciones ACID concurrentes, tipos de datos avanzados (JSONB, arrays), escalabilidad horizontal con réplicas de lectura, amplio ecosistema de extensiones (PostGIS, pg_trgm). |
| **Inconvenientes** | Requiere instalar y mantener un servidor independiente (o un contenedor Docker), configurar credenciales, red y permisos. Añade complejidad al onboarding de nuevos desarrolladores y a los pipelines de CI. Sobredimensionado para el volumen y la complejidad actuales del proyecto. |

### MySQL

| Aspecto | Detalle |
|---|---|
| **Ventajas** | Rendimiento sólido en operaciones de lectura, amplia adopción en la industria, buena documentación, replicación nativa maestro-esclavo. |
| **Inconvenientes** | Al igual que PostgreSQL, necesita un servidor dedicado con configuración de red y usuarios. Dialectos y modos SQL que pueden generar inconsistencias si no se configuran correctamente (`STRICT_TRANS_TABLES`, juego de caracteres). No aporta ventajas significativas sobre PostgreSQL para este caso de uso y añade la misma sobrecarga operativa. |

## Consecuencias

### Positivas

- **Arranque inmediato**: cualquier desarrollador puede clonar el repositorio, instalar dependencias con `pip install -r requirements.txt` y ejecutar la API sin configurar ningún servicio externo.
- **Tests rápidos y aislados**: la base de datos en memoria con `StaticPool` permite ejecutar la suite de tests en milisegundos sin efectos secundarios.
- **Mantenimiento mínimo**: no hay que gestionar backups de servidor, actualizaciones de versiones del motor ni monitorización de procesos.

### Negativas y riesgos a largo plazo

- **Concurrencia limitada**: SQLite permite un solo escritor a la vez. Si la API escala a múltiples instancias o recibe carga alta de escrituras concurrentes, se producirán bloqueos (`database is locked`).
- **Falta de funcionalidades avanzadas**: no hay soporte nativo para tipos complejos (JSONB), búsqueda de texto completo robusta, ni mecanismos de replicación.
- **Migración futura necesaria**: si el proyecto crece más allá de una plantilla o prototipo, será necesario migrar a PostgreSQL u otro motor cliente-servidor. Gracias a SQLAlchemy, el cambio de dialecto solo requiere modificar la URL de conexión y ajustar configuraciones específicas del motor, pero será necesario validar las migraciones de esquema y adaptar los tests.
- **Archivo local como único almacén**: el archivo `tareas.db` no debe incluirse en control de versiones y depende del sistema de ficheros local, lo que impide despliegues en entornos efímeros (contenedores sin volúmenes persistentes) sin configuración adicional.
