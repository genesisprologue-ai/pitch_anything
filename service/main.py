import json
import os
from typing import List
from fastapi import FastAPI, UploadFile
import orm
from schema import PageTranscript
from tasks import transcribe, resume, ssml_audio_sync
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orm.init_db()


# --------------web api routes----------------
@app.post("/upload_master")
async def upload_powerpoint(file: UploadFile):
    source_stream = await file.read()
    # upload file to uploads folder
    upload_path = os.path.join("uploads", file.filename)
    with open(upload_path, "wb") as f:
        f.write(source_stream)

    # create pitch session
    pitch = orm.Pitch(published=False)
    pitch.save()

    master_doc = orm.Document(
        pitch_id=pitch.id,
        master_doc=True,
        file_name=file.filename,
        storage_path=upload_path,
    )
    master_doc.save()
    try:
        # send task
        task_resp = transcribe.delay(
            {
                "pitch_id": pitch.id,
                "doc_id": master_doc.id,
                "file_name": file.filename,
                "storage_path": upload_path,
            }
        )

        if not task_resp.id:
            return {"pitch_id": pitch.id, "task_id": task_resp.id, "message": "failed"}

        master_doc.processed = 1
        master_doc.save()

        return {"pitch_id": pitch.id, "task_id": task_resp.id, "message": None}
    except Exception as e:
        return {
            "pitch_id": None,
            "task_id": None,
            "message": f"create task failed: {e}",
        }


@app.post("/resume_transcribe/{pitch_id}")
async def resume_transcribe(pitch_id: int):
    task = orm.Task.get_by_pitch_id(pitch_id=pitch_id)
    if not task:
        return {"message": "task not found"}

    # send task
    _ = resume.delay(
        {
            "pitch_id": pitch_id,
        }
    )
    return {"task_id": task.task_id, "message": None}


@app.post("/{pitch_id}/upload_embedding")
async def upload_embedding(pitch_id: int, file: UploadFile):
    source_stream = await file.read()
    # upload file to uploads folder
    upload_path = os.path.join("uploads", f"{pitch_id}_embedding", file.filename)
    with open(upload_path, "wb") as f:
        f.write(source_stream)

    # create document
    document = orm.Document(
        pitch_id=pitch_id,
        master_doc=False,
        file_name=file.filename,
        storage_path=upload_path,
    )
    document.save()

    # run embedding task
    # todo:

    return {"doc_id": document.id, "message": None}


@app.post("/{pitch_id}/tts")
def transcript_tts(pitch_id: int):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        return {"message": "pitch not found"}
    task_resp = ssml_audio_sync.delay(
        {"speeches": json.loads(pitch.transcript), "pitch_id": pitch_id}
    )
    if not task_resp.id:
        return {"message": "failed to create task"}

    return {"task_id": task_resp.id, "message": None}


@app.post("/{pitch_id}/video_generation")
def video_generation(pitch_id: int):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        return {"message": "pitch not found"}


@app.get("/tasks/{task_id}")
def task_status(task_id):
    task = orm.Task.get_by_task_id(task_id)
    if task.document_id:
        document = orm.Document.get_by_doc_id(task.document_id)
        return {
            "status": task.process_stage,
            "progress": document.progress,
            "message": None,
        }
    else:
        return {
            "status": task.process_stage,
            "progress": "0:0",
            "message": None,
        }


@app.get("/{pitch_id}/transcript")
def get_transcript(pitch_id: int):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        return {"message": "pitch not found"}
    return {"transcripts": json.loads(pitch.transcript), "message": None}


@app.put("/{pitch_id}/transcript")
def update_transcript(pitch_id: int, transcripts: List[PageTranscript]):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        return {"message": "pitch not found"}
    pitch.transcript = json.dumps(transcripts)
    pitch.save()
    return {"message": None}


@app.get("/{pitch_id}/master_doc")
def serving_master_doc(pitch_id: int):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        return {"message": "pitch not found"}
    master_doc = orm.Document.get_master_by_pitch_id(pitch_id=pitch_id)
    if not master_doc:
        return {"message": "master doc not found"}
    return FileResponse(master_doc.storage_path, media_type="application/pdf")
