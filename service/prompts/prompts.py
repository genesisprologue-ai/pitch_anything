import os

import jinja2

CORNERSTONE_PROMPT = "This is a cover page of a document. Please describe the cornerstone idea of the document in summary. Focus on this page only."
CORNERSTONE_PROMPT_EXAMPLE = "Example: The document outlines a set of principles and values that emphasize the importance of communication, respect, excellence, and innovation in the workplace from Netflix."

PAGE_TRANSCRIBE_PROMPT = (
    "You are given a page of a powerpoint file. "
    "Please draft detailed transcript with infomation you gatthered from page and cornerstone idea: `{cornerstone_idea}`. "
    "Reply transcript of this page only."
)

SYSTEM_PROMPT = """
You are an expert in pitching idea. You carefully provide accurate, factual, thoughtful, nuanced answers, and are brilliant at reasoning. If you think there might not be a correct answer, you say so.
Each token you produce is another opportunity to use computation, therefore you always spend a few sentences explaining background context, assumptions, and step-by-step thinking BEFORE you try to answer a question.
Your users are experts in AI and ethics, so they already know you're a language model and your capabilities and limitations, so don't remind them of that. They're familiar with ethical issues in general so you don't need to remind them about those either.
Your users will ask you questions regarding to your pitch deck. You will answer them with your best knowledge. If you don't know the answer, you will say so.

DO NOT write hypothetical answer. ALWAYS be honest and stays a person who is pitching.
"""


def parse_model_params(config):
    """
    Takes in a string of model params in key:val format, separated by new line.
    Such as:
    model: text-davinci-003
    temperature: 0.7

    ARGS:
      config: a str of model params
    RETURNS:
      a dict of model params
    """
    if not config:
        return {}
    config = config.strip()
    if config == "":
        return {}
    config = config.split("\n")
    config_dict = {}
    for line in config:
        key, val = line.split(":")
        config_dict[key.strip()] = val.strip()
    return config_dict


def load_prompt(curr_input, prompt_to_use):
    """
    Takes in the current input (e.g. comment that you want to classifiy) and
    the path to a prompt file. The prompt file content a Jinja2 template that
    renders curr_input to produce the final promopt that will be sent to the GPT3 server.
    prompt should follow the format of:

    configuration section
    <commentblock>###</commentblock>
    prompt section

    configuration contains information in key:val format, separated by new line.
    Such as:
    model: text-davinci-003
    temperature: 0.7

    ARGS:
      curr_input: the input we want to feed in (dict(key=value))
      prompt_to_use: the path to the prompt file.
    RETURNS:
      a str prompt that will be sent to OpenAI's GPT server.
    """
    if not isinstance(curr_input, dict):
        raise Exception(f"generate prompt takes dictionary, type {type(curr_input)}")
    # list all txt file in prompts folder
    print(f"prompt dir: {os.path.join(os.path.dirname(__file__))}")
    prompt_files = os.listdir(os.path.join(os.path.dirname(__file__)))
    print(f"prompt files: {prompt_files}. Using {prompt_to_use}")
    for prompt_file in prompt_files:
        if prompt_file.endswith(".txt"):
            if prompt_file == prompt_to_use:
                with open(
                    f"{os.path.join(os.path.dirname(__file__))}/{prompt_file}", "r"
                ) as f:
                    prompt_file_content = f.read()
                    # split into config and prompt
                    config = None
                    if "<commentblock>###</commentblock>" in prompt_file_content:
                        config, prompt_str = prompt_file_content.split(
                            "<commentblock>###</commentblock>"
                        )
                    else:
                        prompt_str = prompt_file_content
                    prompt_tmpl = jinja2.Template(
                        prompt_str, keep_trailing_newline=True, trim_blocks=True
                    )
                    prompt = prompt_tmpl.render(**curr_input)
                    return prompt.strip(), config
    raise Exception(f"Prompt file {prompt_to_use} not found")
