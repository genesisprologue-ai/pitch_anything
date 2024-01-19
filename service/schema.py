from pydantic import BaseModel


class PageDraft(BaseModel):
    page: int
    cornerstone: str
    draft: str
    draft_from_images: str
    links: list


class PageTranscript(BaseModel):
    page: int
    transcript: str
    links: list
    medias: list
    references: list
