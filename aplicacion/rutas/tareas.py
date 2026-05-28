# Definición de los endpoints REST para la gestión de tareas

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db
from aplicacion.esquemas import TaskCreate, TaskResponse, TaskUpdate
from aplicacion.modelos import Task

# Router con prefijo /tasks; agrupa todos los endpoints de tareas
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """Devuelve la lista completa de tareas almacenadas.

    Args:
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        List[TaskResponse]: Lista con todas las tareas registradas.
    """
    return db.query(Task).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Devuelve una tarea por su identificador.

    Args:
        task_id (int): Identificador único de la tarea.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        TaskResponse: La tarea correspondiente al identificador proporcionado.

    Raises:
        HTTPException: Error 404 si no existe una tarea con el identificador
            indicado.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Crea una nueva tarea y devuelve el recurso creado.

    Args:
        payload (TaskCreate): Datos de la tarea a crear. Incluye título
            obligatorio, descripción opcional y estado (por defecto
            ``pending``).
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        TaskResponse: La tarea recién creada con su identificador y fecha
            de creación asignados por la base de datos.
    """
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Actualiza parcialmente una tarea existente.

    Solo se modifican los campos incluidos en el cuerpo de la petición;
    los campos omitidos conservan su valor actual.

    Args:
        task_id (int): Identificador único de la tarea a actualizar.
        payload (TaskUpdate): Campos a modificar. Todos son opcionales:
            título, descripción y estado.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Returns:
        TaskResponse: La tarea actualizada con los nuevos valores.

    Raises:
        HTTPException: Error 404 si no existe una tarea con el identificador
            indicado.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Elimina una tarea de la base de datos.

    Args:
        task_id (int): Identificador único de la tarea a eliminar.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Raises:
        HTTPException: Error 404 si no existe una tarea con el identificador
            indicado.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
