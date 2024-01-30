import json
import os
import uuid
from typing import Any, List, Annotated
from fastapi import FastAPI, HTTPException, UploadFile, Form, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from llm import get_remote_chat_response

import orm
import rag
import cache
from common import all_pitch_folders_path
from tasks import transcribe, resume, ssml_audio_sync

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
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# --------------web api routes----------------
@app.get("/")
async def ping():
    return {"message": "pong"}


@app.post("/upload_master")
async def upload_master(request: Request, file: UploadFile):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())

    pitch = orm.Pitch(published=False, pitch_uid=session_id)
    pitch.save()

    pitch_folder, references_folder = all_pitch_folders_path(pitch.id)

    os.makedirs(pitch_folder, exist_ok=True)
    source_stream = await file.read()
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
        task_resp = transcribe.delay(
            {
                "pitch_uid": session_id,
                "doc_id": master_doc.id,
                "file_name": file.filename,
                "storage_path": upload_path,
            }
        )

        if not task_resp.id:
            raise HTTPException(
                status_code=500, detail="Failed to start transcription task"
            )

        master_doc.processed = 1
        master_doc.save()

        response = JSONResponse(
            {"pitch_uid": session_id, "task_id": task_resp.id, "message": None}
        )
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resume_transcribe/{pitch_uid}")
async def resume_transcribe(pitch_uid: str):
    task = orm.Task.get_by_pitch_uid(pitch_id=pitch_uid)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # send task
    _ = resume.delay(
        {
            "pitch_uid": pitch_uid,
        }
    )
    return {"task_id": task.task_id, "message": None}


@app.post("/{pitch_id}/reference_doc")
async def upload_embedding(
    pitch_id: int, file: Annotated[UploadFile, Form()], keywords: Annotated[str, Form()]
):
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
        rag.load_and_embed(pitch_id, upload_path, keywords.split(","))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": None}


@app.post("/{pitch_uid}/tts")
def transcript_tts(pitch_uid: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    task_resp = ssml_audio_sync.delay(
        {"speeches": json.loads(pitch.transcript), "pitch_uid": pitch_uid}
    )
    if not task_resp.id:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"task_id": task_resp.id, "message": None}


@app.get("/tasks/{task_id}")
def task_status(task_id):
    task = orm.Task.get_by_task_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

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
            return {
                "status": task.process_stage,
                "progress": progress,
                "message": "failed",
            }
    else:
        return {
            "status": task.process_stage,
            "progress": "0:0",
            "message": None,
        }


@app.get("/{pitch_uid}/transcript")
def get_transcript(pitch_uid: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    return {"transcripts": json.loads(pitch.transcript), "message": None}


@app.put("/{pitch_uid}/transcript")
def update_transcript(pitch_uid: str, transcripts: List[Any]):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
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


@app.get("/{pitch_uid}/master_doc")
def serving_master_doc(pitch_uid: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    master_doc = orm.Document.get_master_by_pitch_id(pitch_id=pitch.id)
    if not master_doc:
        raise HTTPException(status_code=404, detail="Master doc not found")
    return FileResponse(master_doc.storage_path, media_type="application/pdf")


@app.get("/pitch_video/{pitch_uid}/{file_name}")
def deliver_hls(pitch_uid: str, file_name: str):
    hls_path = os.path.join("media", pitch_uid, file_name)
    if not os.path.exists(hls_path):
        raise HTTPException(status_code=404, detail="Pitch video not found")
    else:
        return FileResponse(hls_path, media_type="application/x-mpegURL")


@app.get("/{pitch_uid}/clear_context")
async def clear_context(pitch_uid: str):
    new_session_id = str(uuid.uuid4())
    response = JSONResponse({"message": None})
    response.set_cookie("user_session_id", new_session_id, httponly=True)
    return response


@app.get("/{pitch_uid}/streaming")
async def conversation(pitch_uid: str, request: Request):
    user_session_id = request.cookies.get("user_session_id")
    if not user_session_id:
        user_session_id = request.headers.get("user_session_id")
        if not user_session_id:
            # this happens when user clears current session to remove all current context
            user_session_id = str(uuid.uuid4())

    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")

    query = request.query_params.get("query")
    print(query)
    # read from cache first
    history = cache.get_cache(user_session_id)
    messages = []
    if history:
        messages = json.loads(history)
    messages.append({"role": "user", "content": query})
    # send message to GPT3
    # request vector db and llm
    # repose should have context bound result with reference url
    context_message = rag.retrieve_context(query, k=10, filters={"pitch_id": pitch.id})
    if not context_message:
        context_message = {"role": "user", "content": "No context found"}
    prompt = rag.construct_prompt(messages, context_message, context_window=3000)

    # cache messages
    cache.set_cache(user_session_id, json.dumps(prompt[1:], ensure_ascii=False))

    async def event_generator():
        try:
            async for message in get_remote_chat_response(prompt):
                if await request.is_disconnected():
                    break
                if message:
                    yield f"data: {message} \n\n"  # required by SSE format
            return
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # content = get_remote_chat_response(prompt)

    response = StreamingResponse(event_generator(), media_type="text/event-stream")
    response.set_cookie("user_session_id", user_session_id, httponly=True)
    # response = JSONResponse({"content": content})
    # response.set_cookie("user_session_id", user_session_id, httponly=True)

    return response
