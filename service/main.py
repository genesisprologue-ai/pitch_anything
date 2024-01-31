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
    # session id used to track user created pitch sessions
    uid = str(uuid.uuid4())
    pitch = orm.Pitch(published=False, pitch_uid=uid)
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

    task_id = str(uuid.uuid4())
    orm.Task.create_task(
        pitch_id=pitch.id,
        task_id=task_id,
        task_type=0,
        process_stage=0,
        version=0,
        doc_id=master_doc.id,
    )
    try:
        task_resp = transcribe.delay(
            {
                "task_id": task_id,
                "pitch_id": pitch.id,
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
            {"pitch_uid": uid, "task_id": task_resp.id, "message": None}
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/{pitch_uid}/master_doc")
def serving_master_doc(pitch_uid: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    master_doc = orm.Document.get_master_by_pitch_id(pitch_id=pitch.id)
    if not master_doc:
        raise HTTPException(status_code=404, detail="Master doc not found")
    return FileResponse(master_doc.storage_path, media_type="application/pdf")


@app.post("/resume_transcribe/{pitch_uid}")
async def resume_transcribe(pitch_uid: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    task = orm.Task.get_master_by_pitch_id(pitch_id=pitch.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # send task
    _ = resume.delay(
        {
            "pitch_uid": pitch_uid,
        }
    )
    return {"task_id": task.task_id, "message": None}


@app.post("/{pitch_uid}/reference_doc")
async def upload_embedding(
    pitch_uid: str,
    file: Annotated[UploadFile, Form()],
    keywords: Annotated[str, Form()],
):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")

    source_stream = await file.read()
    # upload file to uploads folder
    _, ref_folder = all_pitch_folders_path(pitch_uid)
    upload_path = os.path.join(ref_folder, file.filename)
    with open(upload_path, "wb") as f:
        f.write(source_stream)

    # create document
    document = orm.Document(
        pitch_id=pitch.id,
        master_doc=False,
        file_name=file.filename,
        storage_path=upload_path,
        keywords=keywords,
    )
    document.save()

    task_id = str(uuid.uuid4())
    orm.Task.create_task(
        pitch_id=pitch.id,
        task_id=task_id,
        task_type=2,
        process_stage=0,
        version=0,
        doc_id=document.id,
    )
    try:
        rag.load_and_embed(pitch.id, upload_path, keywords.split(","))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": None}


@app.get("/{pitch_uid}/reference_doc")
async def list_reference_docs(pitch_uid: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    docs = orm.Document.get_ref_docs_by_pitch_id(pitch_id=pitch.id)
    return {
        "docs": [
            {
                "id": doc.id,
                "filename": doc.file_name,
                "type": "PDF",
                "keywords": doc.keywords,
            }
            for doc in docs
        ],
        "message": None,
    }


@app.get("/{pitch_uid}/reference_doc/download/{doc_id}")
async def downloand_reference_docs(pitch_uid: str, doc_id: int):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    doc = orm.Document.get_by_doc_id(doc_id=doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doc not found")
    return FileResponse(doc.storage_path, media_type="application/pdf")


@app.delete("/{pitch_uid}/reference_doc/{doc_id}")
async def remove_reference_doc(pitch_uid: str, doc_id: int):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    if orm.Document.remove_by_doc_id(pitch_id=pitch.id):
        return {"message": None}

    raise HTTPException(status_code=500, detail="Failed to remove reference doc")


@app.post("/{pitch_uid}/tts")
def transcript_tts(pitch_uid: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    # check if there is a tts task running
    running_tsk = orm.Task.get_running_tts_by_pitch_id(pitch_id=pitch.id)
    if running_tsk:
        return {
            "task_id": running_tsk.task_id,
            "status": running_tsk.process_stage,
            "message": "TTS task already running",
        }

    task_id = str(uuid.uuid4())
    orm.Task.create_task(
        pitch_id=pitch.id,
        task_id=task_id,
        task_type=1,
        process_stage=101,
        version=0,
    )

    task_resp = ssml_audio_sync.delay(
        {
            "speeches": json.loads(pitch.transcript),
            "pitch_id": pitch.id,
            "task_id": task_id,
        }
    )
    if not task_resp.id:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"task_id": task_id, "status": 101, "message": None}


@app.get("/{pitch_uid}/transcibe_status")
def transcribe_task_status(pitch_uid: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")

    transcribe_task = orm.Task.get_master_by_pitch_id(pitch_id=pitch.id)
    if not transcribe_task_status:
        raise HTTPException(status_code=404, detail="Transcribe task not found")

    document = orm.Document.get_by_doc_id(transcribe_task.document_id)
    return {
        "status": transcribe_task.process_stage,
        "progress": document.progress,
        "message": None,
    }


@app.get("/{pitch_uid}/tts_status/{task_id}")
def tts_task_status(pitch_uid: str, task_id: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")

    tts_task = orm.Task.get_by_task_id(task_id=task_id)
    if not tts_task:
        raise HTTPException(status_code=404, detail="TTS task not found")

    return {"status": tts_task.process_stage, "message": None}


@app.get("/{pitch_uid}/pitch")
def get_pitch_info(pitch_uid: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")

    master_task = orm.Task.get_master_by_pitch_id(pitch_id=pitch.id)
    if not master_task:
        raise HTTPException(status_code=404, detail="Transcribe task not found")

    response = JSONResponse(
        {"pitch_uid": pitch.pitch_uid, "task_id": master_task.task_id, "message": None}
    )
    return response


@app.get("/{pitch_uid}/transcript")
def get_transcript(pitch_uid: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    print(pitch.id)
    print(pitch.transcript)
    if pitch.transcript:
        return {"transcripts": json.loads(pitch.transcript), "message": None}
    else:
        return {"transcripts": [], "message": None}


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


@app.get("/pitch_video/{pitch_uid}/{file_name}")
def deliver_hls(pitch_uid: str, file_name: str):
    pitch = orm.Pitch.get_by_pitch_uid(pitch_uid=pitch_uid)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    hls_path = os.path.join("media", str(pitch.id), file_name)
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
                    yield f"data: {message}\n\n"  # required by SSE format
            return
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # content = get_remote_chat_response(prompt)

    response = StreamingResponse(event_generator(), media_type="text/event-stream")
    response.set_cookie("user_session_id", user_session_id, httponly=True)

    return response
