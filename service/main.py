import json
import os
from typing import List
from pdf2image import convert_from_path
from fastapi import FastAPI, UploadFile
from celery import Celery, states
import orm
from schema import PageDraft, PageTranscript
from tts import text_to_ssml, speech_synthesize
from transcribe import draft_transcribe, gen_transcript

app = FastAPI()

# Celery app
# Configure Celery
celery = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

orm.init_db()


# --------------celery tasks----------------
@celery.task(bind=True)
def transcribe(self, param):
    # create task entry
    task_id = self.request.id
    print(f"task id: {task_id}")
    task = orm.Task(
        task_id=task_id,
        pitch_id=param.get("pitch_id"),
        document_id=param.get("doc_id"),
        process_stage=orm.TranscribeStage.KICKOFF.value,
        version=1,
    )
    task.save()
    # Extract each slide as an image
    task.process_stage = orm.TranscribeStage.SEGMENT.value
    task.save()
    images = convert_from_path(param.get("storage_path"), 300)
    image_folder = os.path.join("uploads", f"{param.get('pitch_id')}")
    image_paths = []
    # update document:
    document = orm.Document.get_by_doc_id(param.get("doc_id"))
    try:
        for i in range(len(images)):
            image_path = os.path.join(image_folder, f"slide_{i}.jpg")
            # Save pages as images in the pdf
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            images[i].save(image_path, "JPEG")
            image_paths.append(image_path)
        document.progress = f"0:{len(images)}"
        document.save()
    except Exception as e:
        print(e)
        self.update_state(state=states.FAILURE, meta=f"failed to segment pdf: {e}")

    # kick off transcribe
    task.process_stage = orm.TranscribeStage.DRAFT.value
    task.save()
    page_drafts = draft_transcribe(image_paths, document)

    # write transcripts
    task.process_stage = orm.TranscribeStage.GEN_TRANSCRIPT.value
    task.save()
    speech_content = gen_transcript(page_drafts)

    # save speech for audio dialog generation
    pitch = orm.Pitch(id=param.get("pitch_id")).get()
    pitch.transcript = speech_content
    pitch.save()

    # call azure to create audio content
    # call whisper to create srt format subtitle
    return


@celery.task(bind=True)
def resume(self, param):
    # lookup task associated with pitch
    task = orm.Task.get_by_pitch_id(pitch_id=param.get("pitch_id"))
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=param.get("pitch_id"))
    print(f"task stage {task.process_stage}")
    stage = orm.TranscribeStage(task.process_stage)
    if stage == orm.TranscribeStage.SEGMENT:  # send to drafting
        # kick off transcribe
        task.process_stage = orm.TranscribeStage.DRAFT.value
        task.save()
        stage = orm.TranscribeStage(task.process_stage)
        # lookup image paths
        image_dir = os.path.join("uploads", f"{param.get('pitch_id')}")
        image_paths = []
        for file in os.listdir(image_dir):
            if file.endswith(".jpg"):
                image_paths.append(os.path.join(image_dir, file))
        page_drafts = draft_transcribe(image_paths)
        pitch.drafts = json.dumps(page_drafts)
        pitch.save()

    # continue
    if stage == orm.TranscribeStage.DRAFT:  # send to trascribe
        # write transcripts
        page_drafts = json.loads(pitch.drafts)
        task.process_stage = orm.TranscribeStage.GEN_TRANSCRIPT.value
        task.save()
        stage = orm.TranscribeStage(task.process_stage)
        speech_content = gen_transcript(page_drafts)
        # save speech for audio dialog generation
        pitch = orm.Pitch(id=param.get("pitch_id")).get()
        pitch.transcript = speech_content
        pitch.save()

    if stage == orm.TranscribeStage.FINISH:  # send to finish
        # create audio file
        return {"message": "transcribe completed"}


@celery.task(bind=True)
async def ssml_audio_sync(self, param):
    # convert to ssml
    speeches = param.get("speeches")
    pitch_id = param.get("pitch_id")

    task_id = self.request.id
    print(f"task id: {task_id}")
    task = orm.Task(
        task_id=task_id,
        pitch_id=param.get("pitch_id"),
        task_type=1,
        process_stage=orm.AudioStage.PROCESSING.value,
        version=1,
    )
    task.save()

    for i, speech in enumerate(speeches):
        ssml = text_to_ssml(speech)
        retries = 0
        while retries < 3:
            try:
                audio_success = await speech_synthesize(ssml, pitch_id)
                if audio_success:
                    break
            except Exception as e:
                print(e)
                retries += 1

    return {"message": "ssml audio sync completed", "task_id": task_id}


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


@app.post("/{pitch_id}/resume_transcribe")
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
    task_resp = ssml_audio_sync.delay({
        "speeches": json.loads(pitch.transcript),
        "pitch_id": pitch_id})
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
    return {"task": task}


@app.get("/{pitch_id}/transcript")
def get_transcript(pitch_id: int):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        return {"message": "pitch not found"}
    return {"transcripts": json.loads(pitch.transcript), "message": None}


@app.put("/{pitch_id}/trasncript")
def update_transcript(pitch_id: int, transcripts: List[PageTranscript]):
    pitch = orm.Pitch.get_by_pitch_id(pitch_id=pitch_id)
    if not pitch:
        return {"message": "pitch not found"}
    pitch.transcript = json.dumps(transcripts)
    pitch.save()
    return {"message": None}
