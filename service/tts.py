import json
import os

import azure.cognitiveservices.speech as speechsdk
import torch
from dotenv import load_dotenv
from transformers import pipeline
from transformers.utils import is_flash_attn_2_available

import prompts.prompts as prompts
from llm import llm_client


def text_to_ssml(text):
    # gen transcript based backward/foward ref and cornerstone
    sys_prompt, _ = prompts.load_prompt(
        {"speech": text, "voice": "en-US-GuyNeural"},
        "synth_audio.txt",
    )
    print("----------------")
    print(sys_prompt)
    print("----------------")
    llm_cli = llm_client()
    response = llm_cli.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[{"role": "system", "content": sys_prompt}],
    )

    print(response)
    return response.choices[0].message.content


def speech_synthesize(ssml, pitch_id, sequence, voice_name="en-US-GuyNeural"):
    load_dotenv()
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    print(os.environ.get("AZURE_SPEECH_REGION"))
    print(os.environ.get("AZURE_SPEECH_KEY"))
    speech_config = speechsdk.SpeechConfig(
        subscription=os.environ.get("AZURE_SPEECH_KEY"),
        region=os.environ.get("AZURE_SPEECH_REGION"),
    )

    # Required for WordBoundary event sentences.
    speech_config.set_property(
        property_id=speechsdk.PropertyId.SpeechServiceResponse_RequestSentenceBoundary,
        value="true",
    )
    speech_config.speech_synthesis_voice_name = voice_name

    # audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None
    )
    # speech_synthesis_result = speech_synthesizer.speak_ssml(ssml)
    speech_synthesis_result = speech_synthesizer.speak_text(ssml)

    if (
        speech_synthesis_result.reason
        == speechsdk.ResultReason.SynthesizingAudioCompleted
    ):
        print("SynthesizingAudioCompleted result")
        stream = speechsdk.AudioDataStream(speech_synthesis_result)
        # creat a tmp file to store the audio
        os.makedirs(
            os.path.abspath(os.path.join("media", str(pitch_id))), exist_ok=True
        )
        output_audio = os.path.abspath(
            os.path.join("media", str(pitch_id), str(sequence) + ".wav")
        )
        print(f"output audio: {output_audio}")
        stream.save_to_wav_file(output_audio)
        return True
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")
        return False


# insanely fast whisper


def convert_to_srt(data):
    # Parse the JSON data
    transcript = json.loads(data)

    # Open the SRT file for writing


def format_srt_time(seconds):
    """Converts time in seconds to the SRT time format."""
    if seconds:
        milliseconds = int((seconds % 1) * 1000)
        seconds = int(seconds)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
    else:
        return "00:00:00,000"


def srt_from_whisper(pitch_id):
    pitch_id = str(pitch_id)
    audio_files = os.listdir(os.path.abspath(os.path.join("media", pitch_id)))
    device = "cuda:0" if torch.cuda.is_available() else os.getenv("DEVICE", "mps")
    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-large-v3",
        # select checkpoint from https://huggingface.co/openai/whisper-large-v3#model-details
        torch_dtype=torch.float16,
        device=device,  # or mps for Mac devices
        model_kwargs={"attn_implementation": "flash_attention_2"}
        if is_flash_attn_2_available()
        else {"attn_implementation": "sdpa"},
    )
    for audio_file in audio_files:
        if audio_file.endswith(".wav"):
            srt_file_path = os.path.abspath(
                os.path.join("media", pitch_id, audio_file.replace(".wav", ".srt"))
            )
            with open(srt_file_path, "w") as srt_file:
                audio_file_path = os.path.abspath(
                    os.path.join("media", pitch_id, audio_file)
                )
                outputs = pipe(
                    audio_file_path,
                    chunk_length_s=30,
                    batch_size=24,
                    return_timestamps=True,
                )
                print(f"whisper outputs: {outputs}")
                # Iterate over each chunk in the transcript
                for index, chunk in enumerate(outputs["chunks"], start=1):
                    start_time = format_srt_time(chunk["timestamp"][0])
                    end_time = format_srt_time(chunk["timestamp"][1])
                    text = chunk["text"].replace("\n", " ")

                    # Write the SRT format to the file
                    srt_file.write(f"{index}\n")
                    srt_file.write(f"{start_time} --> {end_time}\n")
                    srt_file.write(f"{text}\n\n")


if __name__ == "__main__":
    # ssml = text_to_ssml("hello world")
    # speech_synthesize(ssml, 1)
    srt_from_whisper(1)
