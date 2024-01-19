import os
from dotenv import load_dotenv
from openai import AzureOpenAI

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
