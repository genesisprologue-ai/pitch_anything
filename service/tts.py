import os
from uuid import uuid4
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import prompts.prompts as prompts
from llm import llm_client


async def text_to_ssml(text):
    # gen transcript based backward/foward ref and cornerstone
    sys_prompt, _ = prompts.load_prompt(
        {
            "speech": text,
            "voice": "en-US-GuyNeural"

        },
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


async def speech_synthesize(ssml, pitch_id, voice_name="en-US-GuyNeural"):
    load_dotenv()
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(
        subscription=os.environ.get("AZURE_SPEECH_KEY"),
        region=os.environ.get("AZURE_SPEECH_REGION"),
    )

    # Required for WordBoundary event sentences.
    speech_config.set_property(
        property_id=speechsdk.PropertyId.SpeechServiceResponse_RequestSentenceBoundary,
        value="true",
    )

    # audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None
    )
    speech_synthesis_result = await speech_synthesizer.speak_ssml_async(ssml).get()

    if (
            speech_synthesis_result.reason
            == speechsdk.ResultReason.SynthesizingAudioCompleted
    ):
        print("SynthesizingAudioCompleted result")
        stream = speechsdk.AudioDataStream(speech_synthesis_result)
        # creat a tmp file to store the audio
        output_audio = os.path.join("./media/output", str(pitch_id), uuid4() + ".wav")
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
