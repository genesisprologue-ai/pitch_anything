import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import openai

client = None


def llm_client():
    global client
    load_dotenv()
    if not client:
        print(os.getenv("AZURE_OPENAI_API_KEY"))
        print(os.getenv("AZURE_OPENAI_ENDPOINT"))
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2023-07-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )

    return client


def get_remote_chat_response(messages):
    """
    Returns a streamed OpenAI chat response.

    Parameters:
    messages (List[dict]): List of messages to be included in the prompt.
    model (str): The model to be used for encoding, default is "gpt-4-1106-preview".

    Returns:
    str: The streamed OpenAI chat response.
    """
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2023-07-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=messages,
            temperature=0.2,
            # stream=True,
        )

        # for chunk in response:
        #     current_context = chunk.choices[0].delta.content
        #     yield current_context
        print(response)
        content = response.choices[0].message.content
        return content

    except openai.AuthenticationError as error:
        print("401 Authentication Error:", error)
        raise Exception("Invalid OPENAI_API_KEY. Please re-run with a valid key.")

    except Exception as error:
        print("Streaming Error:", error)
        raise Exception("Internal Server Error")
