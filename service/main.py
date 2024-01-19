import os
from io import StringIO
from uuid import uuid4
from pdf2image import convert_from_bytes
from fastapi import FastAPI, File, UploadFile

app = FastAPI()


@app.post("/upload")
async def upload_powerpoint(file: UploadFile):
    print(file)
    source_stream = await file.read()
    # Extract each slide as an image
    images = convert_from_bytes(source_stream)

    file_name_hash = str(uuid4())
    for i in range(len(images)):
        image_path = os.path.join("uploads", file_name_hash, f"slide_{i}.jpg")
        # Save pages as images in the pdf
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        images[i].save(image_path, "JPEG")

    # kick off pdf transcribe and tts service

    return {"filename": file.filename}
