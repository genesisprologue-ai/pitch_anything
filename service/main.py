import hashlib
import os
from io import StringIO
from pptx import Presentation
from fastapi import FastAPI, File

app = FastAPI()


@app.post("/upload")
async def upload_powerpoint(file: bytes = File(...)):
    print(file)
    source_stream = StringIO(file.decode())
    # Extract each slide as an image
    presentation = Presentation(source_stream)
    source_stream.close()
    for i, slide in enumerate(presentation.slides):
        # Create an MD5 hash from the file name
        file_name_hash = hashlib.md5(file.filename.encode()).hexdigest()
        image_path = os.path.join("uploads", file_name_hash, f"slide_{i}.jpg")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        slide.export(image_path)

    return {"message": "Slides extracted and saved successfully"}
