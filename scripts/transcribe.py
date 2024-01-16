import os
from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)
import vertexai
from vertexai.preview.generative_models import (
    GenerativeModel,
    Image as VertextImg,
)

PROJECT_ID = "moonbox-auth-dev"
LOC = "asia-southeast1"


def transcribe(img_path):
    vertexai.init(project=PROJECT_ID, location=LOC)
    multimodal_model = GenerativeModel("gemini-pro-vision")
    # Query the model

    # Get the directory of the current file
    descri_img = VertextImg.load_from_file("images/slide_4.jpg")
    response = multimodal_model.generate_content(
        [
            descri_img,
            # ref_img,
            "Descirbe this image.",
            # descri_img,
        ]
    )
    print(response)
    return response.text


def convert_and_transcript():
    # images = convert_from_bytes(
    #     open("./Netflix Culture_Freedom & Responsibility.pdf", "rb").read()
    # )

    # for i in range(len(images)):
    #     img_path = os.path.join("images", "slide_" + str(i) + ".jpg")
    #     # Save pages as images in the pdf
    #     images[i].save(img_path, "JPEG")

    # transcribe images
    transcribe("")


if __name__ == "__main__":
    convert_and_transcript()
