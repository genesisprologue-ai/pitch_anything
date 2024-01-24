import json
import os
from typing import List
import vertexai
from vertexai.preview.generative_models import (
    GenerativeModel,
    Image as VertextImg,
)
from schema import PageDraft, PageTranscript
from config import PROJECT_ID, LOC
from llm import llm_client
import pickle
import prompts.prompts as prompts


def cornerstone_from_cover(file_path, multimodal_model):
    if file_path is None or file_path == "":
        return

    cover_img = VertextImg.load_from_file(file_path)
    ref_img = VertextImg.load_from_file("./prompts/examples/cornerstone.jpg")

    cornerstone = multimodal_model.generate_content(
        [
            prompts.CORNERSTONE_PROMPT,
            cover_img,
        ]
    )

    print("cornerstone: ", cornerstone.text)

    return cornerstone.text


def draft_transcribe(file_paths, document):
    """transcribe the images in the file_paths with gemini-pro-vision
    The first image is the cover of pdf, the title/main idea of the pdf will be generated
    based on the first image.
    The following images are the content of the pdf, the content of the pdf will be generated

    The result from this function will be used as a draft to determin:
    1. The idea of pdf.
    2. If anything else, image, links in pdf is needed to be added to the draft.

    output is a list of page draft.
    {
        "page": 1,
        "main_idea": "The title of the pdf",
        "draft": "The content of the pdf as a draft",
        "draft_from_images": "a description of the image in combination with draft content",
        "links": [], # list of links in the pdf
    }

    Args:
        file_paths (str): list of file paths of the images
    Return:
        list: list of page draft
    """
    if file_paths is None or len(file_paths) == 0:
        return []

    vertexai.init(project=PROJECT_ID, location=LOC)
    multimodal_model = GenerativeModel("gemini-pro-vision")

    retries = 0
    cornerstone = None
    while retries < 3:
        # fetch cornerstone
        try:
            cornerstone = cornerstone_from_cover(file_paths[0], multimodal_model)
            break
        except Exception as e:
            print(e)
            retries += 1

    if not cornerstone:
        raise Exception("Failed to generate cornerstone")

    page_transcribe_prompt = prompts.PAGE_TRANSCRIBE_PROMPT.format(
        cornerstone_idea=cornerstone
    )
    page_drafts = []
    for i, fpath in enumerate(file_paths):
        # Get the directory of the current file
        retries = 0
        descri_img = VertextImg.load_from_file(fpath)
        while retries < 3:
            try:
                response = multimodal_model.generate_content(
                    [
                        page_transcribe_prompt,
                        descri_img,
                    ]
                )
                print(f"\npage {i + 1}: ", response.text)
                draft = PageDraft(
                    page=i + 1,
                    cornerstone=cornerstone,
                    draft=response.text,
                    draft_from_images="",  # extract images and links
                    links=[],
                )
                page_drafts.append(draft)
                if document:
                    document.progress = f"{i + 1}:{len(file_paths)}"
                    document.save()
                break
            except Exception as e:
                print(e)
                retries += 1

    return page_drafts


def gen_transcript(drafts: List[PageDraft]) -> str:
    """Gather cornerstone and draft. Create a readable transcript based on the content
    without timestamp.

    Args:
        drafts (list[PageDraft]): A list of draft content
    """
    speeches = []
    llm_cli = llm_client()
    for i, draft in enumerate(drafts):
        backward_ref = []
        forward_ref = ""
        if i > 0:
            backward_ref.append(drafts[i - 1].draft)
        backward_ref.append(draft.draft)
        if i < len(drafts) - 1:
            forward_ref += drafts[i + 1].draft

        # gen transcript based backward/foward ref and cornerstone
        sys_prompt, _ = prompts.load_prompt(
            {
                "backward_ref": backward_ref,
                "forward_ref": forward_ref,
                "cornerstone": draft.cornerstone,
                "current_page": draft.draft,
                "current_speech": "".join(speeches),
            },
            "gen_speech.txt",
        )
        print("----------------")
        print(sys_prompt)
        print("----------------")
        response = llm_cli.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[{"role": "system", "content": sys_prompt}],
        )
        print(response)
        speeches.append(response.choices[0].message.content)

    return json.dumps(speeches)

# if __name__ == "__main__":
#     page_drafts = None
#     if not os.path.exists("page_drafts.pickle"):
#         page_drafts = draft_transcribe(
#             [
#                 "./images/slide_0.jpg",
#                 "./images/slide_1.jpg",
#                 "./images/slide_2.jpg",
#                 "./images/slide_3.jpg",
#                 "./images/slide_4.jpg",
#                 "./images/slide_5.jpg",
#             ]
#         )

#         # Pickle the page_drafts variable
#         with open("page_drafts.pickle", "wb") as f:
#             pickle.dump(page_drafts, f)
#     else:
#         # Load the pickled page_drafts variable
#         with open("page_drafts.pickle", "rb") as f:
#             page_drafts = pickle.load(f)

#     final_speech = gen_transcript(page_drafts)

#     print("final speech: ", final_speech)
