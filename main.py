from contextlib import asynccontextmanager

from fastapi import FastAPI, status, HTTPException, Depends
from pydantic import BaseModel
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped,mapped_column, Session

DATABASE_URL = "postgresql+psycopg://postgres:admin@127.0.0.1:5433/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind = engine)

class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(primary_key=True, default= lambda: str(uuid4()))

class TaskORM(Base):
    __tablename__ = "tasks"
    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False)



@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind = engine)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials = True,
)
class Task(BaseModel):
    id: str
    title: str
    completed: bool = False

class TaskCreate(BaseModel):
    title: str

tasks: list[Task] = []

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def task_orm_to_orm(task_orm: TaskORM) -> Task :
    return Task(id = task_orm.id, title=task_orm.title, completed=task_orm.completed)


@app.get("/tasks", response_model=list[Task], status_code=status.HTTP_200_OK)
def get_task(db: Session = Depends(get_db)) -> Task:
    tasks_from_db = db.scalars(select(TaskORM)).all()
    return [task_orm_to_orm(task) for task in tasks_from_db]

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    new_task = TaskORM(title=payload.title, completed=False)
    db.add(new_task)
    db.commit()
    return task_orm_to_orm(new_task)

class TaskUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None

@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    task_for_update = db.get(TaskORM, task_id)
    if task_for_update is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.title is not None:
        task_for_update.title = payload.title
    if payload.completed is not None:
        task_for_update.completed = payload.completed
    db.commit()
    return task_for_update


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db)) -> None:
    task_to_delete = db.get(TaskORM, task_id)

    if task_to_delete is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task_to_delete)
    db.commit()


class CategoryORM(Base):
    __tablename__ = "categories"
    title: Mapped[str]

def cat_orm_to_orm(cat_orm: CategoryORM) -> Category:
    return Category(id = cat_orm.id, name = cat_orm.title)

class Category(BaseModel):
    id: str
    name: str



class CategoryCreate(BaseModel):
    name: str

class CategoryUpdate(BaseModel):
    name: str

@app.get("/categories", response_model=list[Category])
def get_categories(db: Session = Depends(get_db)) -> Category:
    cats_from_db = db.scalars(select(CategoryORM)).all()
    return [cat_orm_to_orm(cat) for cat in cats_from_db]


@app.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED)
def post_categories(payload: CategoryCreate, db: Session = Depends(get_db)):
    new_cat = CategoryORM(title=payload.name)
    db.add(new_cat)
    db.commit()
    return cat_orm_to_orm(new_cat)


@app.patch("/categories/{category_id}", response_model=Category)
def patch_categories(category_id: str, payload: CategoryUpdate, db: Session = Depends(get_db)):
    cat_for_update = db.get(CategoryORM, category_id)
    if cat_for_update is None:
        raise HTTPException(status_code=404, detail="Category not found")
    if payload.name is not None:
        cat_for_update.title = payload.name
    db.commit()
    return cat_orm_to_orm(cat_for_update)

"""@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db)) -> None:
    task_to_delete = db.get(TaskORM, task_id)

    if task_to_delete is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task_to_delete)
    db.commit()"""

@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, db: Session = Depends(get_db)) ->  None:
    cat_to_delete = db.get(CategoryORM, category_id)
    if cat_to_delete is None:
        raise HTTPException(status_code= 404, detail="Category not found")
    db.delete(cat_to_delete)
    db.commit()
