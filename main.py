import os
import shutil
import uuid
from datetime import datetime
from fastapi import FastAPI, UploadFile, File as FastAPIFile, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models
from .database import engine, SessionLocal
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
origins = ["http://localhost:8080", "http://127.0.0.1:8080", "http://4.224.89.237:8000"]
app.add_middleware(
    CORSMiddleware,
    
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


models.Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


FileModel = models.File
FileStatus = models.FileStatus

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parse_file_simulation(file_id: str):
    from .database import SessionLocal
    from .models import File as FileModel, FileStatus
    import time

    db = SessionLocal()
    try:
        db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
        if not db_file:
            return

        db_file.status = FileStatus.processing
        db.commit()

        for progress in range(10, 101, 10):
            time.sleep(1)
            db_file.progress = progress
            db.commit()
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(manager.send_progress(file_id, {
                "file_id": file_id,
                "status": "processing",
                "progress": progress
            }))

        db_file.status = FileStatus.ready
        db_file.progress = 100
        db_file.parsed_content = {"message": "Parsed content placeholder"}
        db.commit()

        loop.run_until_complete(manager.send_progress(file_id, {
            "file_id": file_id,
            "status": "ready",
            "progress": 100
        }))
    finally:
        db.close()

        
        
        
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, file_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(file_id, []).append(websocket)

    def disconnect(self, file_id: str, websocket: WebSocket):
        self.active_connections[file_id].remove(websocket)
        if not self.active_connections[file_id]:
            del self.active_connections[file_id]

    async def send_progress(self, file_id: str, message: dict):
        connections = self.active_connections.get(file_id, [])
        for connection in connections:
            await connection.send_json(message)


manager = ConnectionManager()




# POST /files 
@app.post("/files")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
):
    file_id = str(uuid.uuid4())
    saved_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_file = FileModel(
        file_id=file_id,
        filename=file.filename,
        file_path=saved_path,
        status=FileStatus.uploading,
        progress=0,
        created_at=datetime.utcnow(),
    )
    db.add(db_file)
    db.commit()

    background_tasks.add_task(parse_file_simulation, file_id)

    return {"file_id": file_id, "status": "uploading", "progress": 0}

# GET /files/{file_id}/progress 
@app.get("/files/{file_id}/progress")
def get_progress(file_id: str, db: Session = Depends(get_db)):
    db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    # status may be Enum or string depending on DB backend, so be safe
    status = db_file.status.value if hasattr(db_file.status, "value") else str(db_file.status)
    return {
        "file_id": db_file.file_id,
        "status": status,
        "progress": db_file.progress,
    }

# GET /files/{file_id} 
@app.get("/files/{file_id}")
def get_file_content(file_id: str, db: Session = Depends(get_db)):
    db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    status = db_file.status.value if hasattr(db_file.status, "value") else str(db_file.status)
    if status == "ready":
        return db_file.parsed_content or {"message": "No parsed content available"}
    else:
        return {"message": "File upload or processing in progress. Please try again later."}

#  GET /files 
@app.get("/files")
def list_files(db: Session = Depends(get_db)):
    files = db.query(FileModel).all()
    result = []
    for f in files:
        status_value = f.status.value if hasattr(f.status, 'value') else str(f.status)
        created_at = f.created_at.isoformat() if f.created_at else None
        result.append({
            "file_id": f.file_id,
            "filename": f.filename,
            "status": status_value,
            "progress": f.progress,
            "created_at": created_at,
        })
    return result

# DELETE /files/{file_id} 
@app.delete("/files/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db)):
    db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    if os.path.exists(db_file.file_path):
        os.remove(db_file.file_path)

    db.delete(db_file)
    db.commit()

    return {"message": f"File {file_id} deleted successfully."}




@app.websocket("/ws/progress/{file_id}")
async def websocket_progress_endpoint(websocket: WebSocket, file_id: str):
    await manager.connect(file_id, websocket)
    try:
        while True:
            # Keep connection alive by receiving pings or waiting
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(file_id, websocket)
