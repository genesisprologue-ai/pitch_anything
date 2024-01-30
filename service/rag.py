import uuid
from typing import List

import tiktoken
from langchain_community.document_loaders import PyPDFLoader
import chromadb
from chromadb.utils import embedding_functions
from prompts.prompts import SYSTEM_PROMPT, CITE_PROMPT

chroma_cli = None
default_ef = None


def get_vec_collection(pitch_id):
    global chroma_cli
    if chroma_cli is None:
        chroma_cli = chromadb.PersistentClient(path="vec_db")
        if not chroma_cli.heartbeat():
            raise Exception("Could not connect to ChromaDB")

    collection = chroma_cli.get_or_create_collection(
        f"pitch_collection_{pitch_id}", embedding_function=get_embedding_func()
    )
    return collection


def get_embedding_func():
    global default_ef
    if not default_ef:
        default_ef = embedding_functions.DefaultEmbeddingFunction()
    return default_ef


def load_and_embed(pitch_id, file_path, keywords: List[str]):
    collection = get_vec_collection(pitch_id)
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()

    documents = []
    metadatas = []
    ids = []
    for page in pages:
        documents.append(
            page.page_content
            + "\n"
            + " ".join(["KEYWORD:{}".format(keyword) for keyword in keywords])
        )
        metadatas.append({"pitch_id": pitch_id, "doc_type": "pdf"})
        ids.append(str(uuid.uuid4()))

    try:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
    except Exception as e:
        print(e)
        raise e

    return pages


def retrieve_context(query, k=10, filters={}):
    """Gets the context from our libraries vector db for a given query.

    Args:
        filters: filters, must include pitch to return results
        query (str): User input query
        k (int, optional): number of retrieved results. Defaults to 10.
    """

    # First, we query the API
    pitch_id = filters.get("pitch_id", None)
    if not pitch_id:
        return None

    collection = get_vec_collection(pitch_id)
    responses = collection.query(query_texts=[query], n_results=k, where=filters)

    # Then, we build the prompt_with_context string
    prompt_with_context = ""
    # chroma thing, it's wierd, map query to documents, documents is a list of list, each list contain ACTUAL result tied to the query in query_texts list in order
    if len(responses["documents"]) > 0:
        for response in responses["documents"][0]:
            prompt_with_context += f"\n\n### Context ###\n{response}"
    return {"role": "user", "content": prompt_with_context}


def construct_prompt(
    messages,
    context_message,
    context_window=3000,
):
    """
    Constructs a RAG (Retrieval-Augmented Generation) prompt by balancing the token count of messages and context_message.
    If the total token count exceeds the maximum limit, it adjusts the token count of each to maintain a 1:1 proportion.
    It then combines both lists and returns the result.

    Parameters:
    messages (List[dict]): List of messages to be included in the prompt.
    context_message (dict): Context message to be included in the prompt.
    model (str): The model to be used for encoding, default is "gpt-4-1106-preview".

    Returns:
    List[dict]: The constructed RAG prompt.
    """
    encoding = tiktoken.get_encoding("cl100k_base")

    # 1) calculate tokens
    reserved_space = 1000
    max_messages_count = int((context_window - reserved_space) / 2)
    max_context_count = int((context_window - reserved_space) / 2)

    # 2) construct prompt
    prompts = messages.copy()
    prompts.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    prompts.insert(-1, {"role": "user", "content": CITE_PROMPT})

    # 3) find how many tokens each list has
    messages_token_count = len(
        encoding.encode(
            "\n".join(
                [
                    f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>"
                    for message in prompts
                ]
            )
        )
    )
    context_token_count = len(
        encoding.encode(
            f"<|im_start|>{context_message['role']}\n{context_message['content']}<|im_end|>"
        )
    )

    # 4) Balance the token count for each
    if (messages_token_count + context_token_count) > (context_window - reserved_space):
        # context has more than limit, messages has less than limit
        if (messages_token_count < max_messages_count) and (
            context_token_count > max_context_count
        ):
            max_context_count += max_messages_count - messages_token_count
        # messages has more than limit, context has less than limit
        elif (messages_token_count > max_messages_count) and (
            context_token_count < max_context_count
        ):
            max_messages_count += max_context_count - context_token_count

    # 5) Cut each list to the max count
    # Cut down messages
    while messages_token_count > max_messages_count:
        removed_encoding = encoding.encode(
            f"<|im_start|>{prompts[1]['role']}\n{prompts[1]['content']}<|im_end|>"
        )
        messages_token_count -= len(removed_encoding)
        if messages_token_count < max_messages_count:
            prompts = (
                [prompts[0]]
                + [
                    {
                        "role": prompts[1]["role"],
                        "content": encoding.decode(
                            removed_encoding[
                                : min(
                                    int(max_messages_count - messages_token_count),
                                    len(removed_encoding),
                                )
                            ]
                        )
                        .replace("<|im_start|>", "")
                        .replace("<|im_end|>", ""),
                    }
                ]
                + prompts[2:]
            )
        else:
            prompts = [prompts[0]] + prompts[2:]

    # Cut down context
    if context_token_count > max_context_count:
        # Taking a proportion of the content chars length
        reduced_chars_length = int(
            len(context_message["content"]) * (max_context_count / context_token_count)
        )
        context_message["content"] = context_message["content"][:reduced_chars_length]

    # 6) Combine both lists
    prompts.insert(-1, context_message)

    return prompts


if __name__ == "__main__":
    pages = load_and_embed(
        1,
        "/Volumes/station/src/pitch_anything/service/uploads/airbnb.pdf",
        ["airbnb", "rental"],
    )
    for page in pages:
        print(page)
