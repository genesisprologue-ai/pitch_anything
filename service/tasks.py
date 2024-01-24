import json
import os

import cv2
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
from pdf2image import convert_from_path
from celery import Celery, states

import orm
from tts import text_to_ssml, speech_synthesize
from transcribe import draft_transcribe, gen_transcript

# Celery app
# Configure Celery
celery = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)


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
            image_path = os.path.join(image_folder, f"slide_{i + 1}.jpg")
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
def ssml_audio_sync(self, param):
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
        # ssml = text_to_ssml(speech)
        ssml = speech
        retries = 0
        while retries < 3:
            try:
                audio_success = speech_synthesize(ssml, pitch_id, i + 1)
                if audio_success:
                    break
            except Exception as e:
                print(e)
                retries += 1

    task.process_stage = orm.AudioStage.AUDIO.value
    task.save()

    # create video
    image_dir = os.path.join("uploads", f"{param.get('pitch_id')}")
    image_paths = []
    for file in os.listdir(image_dir):
        if file.endswith(".jpg"):
            image_paths.append(os.path.join(image_dir, file))
    image_paths.sort()

    # Initialize an empty list to hold individual video clips
    video_clips = []
    video_name = os.path.join("media", str(pitch_id), "video.mp4")
    tmp_path = os.path.join('media', str(pitch_id), 'temp.avi')

    for i, img in enumerate(image_paths):
        # Assuming audio files have same name as images but with .wav extension
        audio_file = os.path.abspath(os.path.join("media", str(pitch_id), str(i + 1) + ".wav"))

        # Get the duration of the audio file
        audio_clip = AudioFileClip(audio_file)
        audio_duration = audio_clip.duration

        # Load the image
        frame = cv2.imread(img)
        height, width, layers = frame.shape

        # Create a video clip from the image
        video_clip = cv2.VideoWriter(tmp_path, 0, 1, (width, height))

        # Display the image for the duration of the corresponding audio file
        num_frames = int(audio_duration * 1)  # 1 fps

        for _ in range(num_frames):
            video_clip.write(frame)

        # Release the video writer
        video_clip.release()

        # Load the video clip with moviepy to attach audio
        video_clip = VideoFileClip(tmp_path)
        video_clip = video_clip.set_audio(audio_clip)
        video_clips.append(video_clip)

    # Concatenate all the video clips
    final_clip = concatenate_videoclips(video_clips, method="compose")

    # Write the result to a file
    final_clip.write_videofile(video_name, codec='libx264', fps=1, audio_codec='aac')

    # Clean up temporary files
    for clip in video_clips:
        clip.close()
    os.remove(tmp_path)

    # Release resources
    cv2.destroyAllWindows()

    task.process_stage = orm.AudioStage.FINISH.value
    task.save()

    return {"message": "ssml audio sync completed", "task_id": task_id}
