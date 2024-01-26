import json
import os
from typing import Any, List, Annotated
from fastapi import FastAPI, HTTPException, UploadFile, Form
import orm
from common import all_pitch_folders_path
from service import rag

from tasks import transcribe, resume, ssml_audio_sync
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
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
@app.get("/")
async def ping():
    return {"message": "pong"}


@app.post("/upload_master")
async def upload_master(file: UploadFile):
    # create pitch session
    pitch = orm.Pitch(published=False)
    pitch.save()

    # create pitch folder
    pitch_folder, references_folder = all_pitch_folders_path(pitch.id)

    os.makedirs(pitch_folder, exist_ok=True)
    source_stream = await file.read()
    # upload file to uploads folder
    upload_path = os.path.join(pitch_folder, file.filename)
    with open(upload_path, "wb") as f:
        f.write(source_stream)

    os.makedirs(references_folder, exist_ok=True)
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
        raise HTTPException(status_code=404, detail="Task not found")
    # send task
    _ = resume.delay(
        {
            "pitch_id": pitch_id,
        }
    )
    return {"task_id": task.task_id, "message": None}


@app.post("/{pitch_id}/upload_embedding")
async def upload_embedding(pitch_id: int, file: Annotated[UploadFile, Form()],
                           keywords: Annotated[str, Form()]):
    source_stream = await file.read()
    # upload file to uploads folder
    _, ref_folder = all_pitch_folders_path(pitch_id)
    upload_path = os.path.join(ref_folder, file.filename)
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

    try:
        rag.load_and_embed(pitch_id, upload_path, keywords.split(','))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": None}


@app.post("/{pitch_id}/tts")
def transcript_tts(pitch_id: int):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    task_resp = ssml_audio_sync.delay(
        {"speeches": json.loads(pitch.transcript), "pitch_id": pitch_id}
    )
    if not task_resp.id:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"task_id": task_resp.id, "message": None}


@app.get("/tasks/{task_id}")
def task_status(task_id):
    task = orm.Task.get_by_task_id(task_id)
    if task.document_id > 0:
        document = orm.Document.get_by_doc_id(task.document_id)
        return {
            "status": task.process_stage,
            "progress": document.progress,
            "message": None,
        }
    elif task.task_type == 1:  # video task
        progress = "0:0"
        if task.process_stage != orm.AudioStage.FAILED.value:
            if task.process_stage == orm.AudioStage.PROCESSING.value:
                progress = "1:4"
            elif task.process_stage == orm.AudioStage.AUDIO.value:
                progress = "2:4"
            elif task.process_stage == orm.AudioStage.VIDEO.value:
                progress = "3:4"
            elif task.process_stage == orm.AudioStage.FINISH.value:
                progress = "4:4"

            return {"status": task.process_stage, "progress": progress, "message": None}
        else:
            return {"status": task.process_stage, "progress": progress, "message": "failed"}
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
        raise HTTPException(status_code=404, detail="Pitch not found")
    return {"transcripts": json.loads(pitch.transcript), "message": None}


@app.put("/{pitch_id}/transcript")
def update_transcript(pitch_id: int, transcripts: List[Any]):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    try:
        pitch.transcript = json.dumps(
            transcripts, default=str, ensure_ascii=False
        )  # default=str helps avoid serialization errors
        pitch.save()
    except Exception as e:  # Catch any unexpected errors
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Transcript updated successfully"}  # More informative message


@app.get("/{pitch_id}/master_doc")
def serving_master_doc(pitch_id: int):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    master_doc = orm.Document.get_master_by_pitch_id(pitch_id=pitch_id)
    if not master_doc:
        raise HTTPException(status_code=404, detail="Master doc not found")
    return FileResponse(master_doc.storage_path, media_type="application/pdf")


@app.get("/{pitch_id}/pitch_video")
def deliver_hls(pitch_id: int):
    hls_path = os.path.join("media", str(pitch_id), "index.m3u8")
    if not os.path.exists(hls_path):
        raise HTTPException(status_code=404, detail="Pitch video not found")
    else:
        return FileResponse(hls_path, media_type="application/x-mpegURL")


@app.post("/{pitch_id}/conversation")
def conversation(pitch_id: int, query: str):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    #
    messages = [{"role": "user", "content": query}]
    # send message to GPT3
    # request vector db and llm
    # repose should have context bound result with reference url
    context_window = 500
    context_message = rag.retrieve_context(query, k=10, filters={'pitch_id': pitch_id})
    prompt = rag.construct_prompt(messages, context_message, context_window)
    return {"message": "response from GPT3", "references": "www.example.com"}
