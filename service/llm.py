import os
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AzureOpenAI
import openai

llm_cli = None

async_llm_cli = None


def async_llm_client() -> AsyncAzureOpenAI:
    global async_llm_cli
    load_dotenv()
    openai.api_type = "azure"
    openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    openai.api_version = "2023-07-01-preview"

    if not async_llm_cli:
        async_llm_cli = AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version="2023-07-01-preview",
            api_key=os.getenv("AZURE_OPENAI_KEY"),
        )

    return async_llm_cli


def llm_client() -> AsyncAzureOpenAI:
    global llm_cli
    load_dotenv()
    openai.api_type = "azure"
    openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    openai.api_version = "2023-07-01-preview"

    if not llm_cli:
        llm_cli = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version="2023-07-01-preview",
            api_key=os.getenv("AZURE_OPENAI_KEY"),
        )

    return llm_cli


async def get_remote_chat_response(messages):
    """
    Returns a streamed OpenAI chat response.

    Parameters:
    messages (List[dict]): List of messages to be included in the prompt.
    model (str): The model to be used for encoding, default is "gpt-4-1106-preview".

    Returns:
    str: The streamed OpenAI chat response.
    """
    llm_cli = async_llm_client()
    try:
        response = await llm_cli.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=messages,
            temperature=0.2,
            stream=True,
        )

        async for chunk in response:
            if len(chunk.choices) > 0:
                current_context = chunk.choices[0].delta.content
                yield current_context

    except openai.AuthenticationError as error:
        print("401 Authentication Error:", error)
        raise Exception("Invalid OPENAI_API_KEY. Please re-run with a valid key.")

    except Exception as error:
        print("Streaming Error:", error)
        raise Exception("Internal Server Error")


if __name__ == "__main__":
    load_dotenv()

    async def main():
        async for number in get_remote_chat_response(
            [{"role": "user", "content": "Hello"}]
        ):
            print(number)

    # To run the async main function, you typically use an event loop
    import asyncio

    asyncio.run(main())
