from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import logging
import os
from typing import List, Optional
from prometheus_client import make_asgi_app, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration base de données
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dev_user:dev_password@localhost:5432/taskmanager_dev")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modèle SQLAlchemy
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    completed = Column(Boolean, default=False)
    priority = Column(String(50), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # dnouvelle_colonne = Column(String(255), default="nouvelle_valeur")

# Modèles Pydantic
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    completed: Optional[bool] = None

class TaskResponse(TaskBase):
    id: int
    completed: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Créer les tables (pour le développement uniquement)
if os.getenv("ENVIRONMENT") == "development":
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created for development environment")

# FastAPI app
app = FastAPI(
    title="TaskManager API - Alembic Bug Demo",
    description="API pour démontrer le problème de désynchronisation Alembic",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency pour la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint de health check
@app.get("/health")
async def health_check():
    try:
        # Test de connexion à la base de données
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Health check: OK")
        return {
            "status": "healthy", 
            "database": "connected",
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Database connection failed: {str(e)}"
        )

# Endpoints CRUD
@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    try:
        db_task = Task(**task.dict())
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        logger.info(f"Task created: {db_task.id}")
        return db_task
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error creating task: {str(e)}"
        )

@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0, 
    limit: int = 100, 
    completed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Task)
        if completed is not None:
            query = query.filter(Task.completed == completed)
        
        tasks = query.offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(tasks)} tasks")
        return tasks
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error retrieving tasks: {str(e)}"
        )

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Task not found"
            )
        logger.info(f"Retrieved task: {task_id}")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error retrieving task: {str(e)}"
        )

@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    try:
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Task not found"
            )
        
        update_data = task.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task, key, value)
        
        db.commit()
        db.refresh(db_task)
        logger.info(f"Task updated: {task_id}")
        return db_task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error updating task: {str(e)}"
        )

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    try:
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Task not found"
            )
        
        db.delete(db_task)
        db.commit()
        logger.info(f"Task deleted: {task_id}")
        return {"message": "Task deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error deleting task: {str(e)}"
        )

@app.get("/")
async def root():
    return {
        "message": "TaskManager API - Alembic Bug Demo",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "docs": "/docs",
        "health": "/health"
    }

# Après la création de l'app FastAPI
app.mount("/metrics", make_asgi_app())

# Instrumentation Prometheus FastAPI pour les métriques HTTP
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Crée une métrique de statut de migration Alembic
alembic_migration_status = Gauge('alembic_migration_status', 'Statut de la migration Alembic (1=OK, 0=Erreur)')

# Applique la migration Alembic au démarrage (prod uniquement)
if os.getenv("ENVIRONMENT") == "production":
    import subprocess
    try:
        result = subprocess.run(["alembic", "upgrade", "head"], check=True, capture_output=True, text=True)
        alembic_migration_status.set(1)
        logger.info("Migration Alembic appliquée avec succès")
    except subprocess.CalledProcessError as e:
        alembic_migration_status.set(0)
        logger.error(f"Erreur lors de la migration Alembic : {e.stderr}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 