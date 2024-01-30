import os
from dotenv import load_dotenv
import openai


def llm_client():
    load_dotenv()
    openai.api_type = "azure"
    openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    openai.api_version = "2023-07-01-preview"

    return


async def get_remote_chat_response(messages):
    """
    Returns a streamed OpenAI chat response.

    Parameters:
    messages (List[dict]): List of messages to be included in the prompt.
    model (str): The model to be used for encoding, default is "gpt-4-1106-preview".

    Returns:
    str: The streamed OpenAI chat response.
    """

    try:
        response = openai.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=messages,
            temperature=0.2,
            # stream=True,
        )

        for chunk in response:
            print(chunk)
            # current_context = chunk.choices[0].delta.content
            # yield current_context
            yield chunk
        # print(response)
        # content = response.choices[0].message.content

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
