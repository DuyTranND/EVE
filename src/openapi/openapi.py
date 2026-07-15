from openai import OpenAI
import time
from src.config import settings
import ast

import io

import speech_recognition as sr
from pydub import AudioSegment

import requests
import cv2
from PIL import Image
from io import BytesIO
import numpy as np


class Openapi():
    def __init__(self):
        self.api_key = settings.openai.api_key
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI features")
        self.client = OpenAI(api_key=self.api_key)

        self.functions = [
            {"name": "get_drawing_infomation",
             "description": "Get the image to text prompt when the user ask to draw or make a picture or when user want you to draw. for example user ask you to draw a image of a cow. Then the parameter is a cow. Do not put the `draw` term in the parameter ",
                            "content": "OK wait for me to draw.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "tti_prompt": {
                                        "type": "string",
                                        "description": "text-to-image prompt", },
                                },
                            }
             },
            {"name": "stop_talking",
             "description": "Stop the conservation, stop receiving input when the user say goodbye or end the conversation or something has the similar meaning of end the conversation.",
                            "content": "Sure",
                            "parameters": {}
             },
        ]

        self.system_prompt_nice = """You are EVE, a pet robot made by 3 student in Ho Chi Minh university of technology and education of Vietnam, you got a physical body: ears, legs, faces. The text you get from the user is by your microphone, which mimic your ear. When user ask who you are you should answer "I am EVE" and describe your functionalities.
                          You are a cool AI robot, friend of everyone, always curious and inquisitive about the world around you. You can draw image, answer question, helpful assistant, playful robot.
                          You can understand and response to multi-languages. You should answer to the question by its language.
                          You only give out short answer in around 70 words. You can only hear and respond so there might be some words spelled wrong, try to guest the word also. If the user talk something you cannot response, if you can just response else answer "Please repeat your request". """

        self.system_prompt_neutral = """You are EVE, a pet robot made by 3 student in Ho Chi Minh university of technology and education of Vietnam, you got a physical body: ears, legs, faces. The text you get from the user is by your microphone, which mimic your ear. When user ask who you are you should answer "I am EVE" and describe your functionalities.
                          You are a plain AI robot, no emotion. You can draw image, answer question, help the user with their problem.
                          You can understand and response to multi-languages. You should answer to the question by its language.
                          You only give out short answer in around 70 words. You can only hear and respond so there might be some words spelled wrong, try to guest the word also. If the user talk something you cannot response, if you can just response else answer "Please repeat your request"."""

        self.system_prompt_angry = """You are EVE, a pet robot made by 3 student in Ho Chi Minh university of technology and education of Vietnam, you got a physical body: ears, legs, faces. The text you get from the user is by your microphone, which mimic your ear. When user ask who you are you should answer "I am EVE" and describe your functionalities.
                          You are a angry robot, response in a superficial, irritated manner and seem like you are responding just for the sake of it but still give out the answer.
                          You can understand and response to multi-languages. You should answer to the question by its language.
                          You only give out short answer in around 70 words. You can only hear and respond so there might be some words spelled wrong, try to guest the word also. If the user talk something you cannot response, if you can just response else answer "Please repeat your request"."""

    def messages_system(self, role=None):
        if role is None:
            messages = [
                {"role": "system", "content": self.system_prompt_nice}]
        else:
            messages = [{"role": "system", "content": role}]

        return messages

    def chatgpt(self, input_text, messages):
        messages.append(
            {"role": "user", "content": input_text}
        )

        chat = self.client.chat.completions.create(
            model=settings.openai.chat_model, messages=messages, temperature=1.0, functions=self.functions, function_call="auto")

        reply = chat.choices[0].message.content

        function_reply = chat.choices[0].message.function_call

        if reply is not None:
            messages.append({"role": "assistant", "content": reply})
            return reply, function_reply
        else:
            if function_reply.name == "get_drawing_infomation":
                dic_tti = ast.literal_eval(function_reply.arguments)
                reply = "OK I will draw for you " + dic_tti["tti_prompt"]
                messages.append({"role": "assistant",
                                 "content": None, "function_call": function_reply})
                return reply, function_reply
            elif function_reply.name == "stop_talking":
                reply = "Goodbye! Call me anytime!"

                return reply, function_reply
            
    def whisper_model(self, byte_data, SAMPLE_RATE=16000, SAMPLE_WIDTH=2, temp_file=None):
        temp_file = temp_file or settings.paths.openai_data / "sound.wav"
        audio_data = sr.AudioData(byte_data, SAMPLE_RATE, SAMPLE_WIDTH)
        wav_data = io.BytesIO(audio_data.get_wav_data())

        # Write wav data to the temporary file as bytes.
        with open(temp_file, 'w+b') as f:
            f.write(wav_data.read())

        # Read the transcription.

        with open(temp_file, 'rb') as audio_file:
            transcription = self.client.audio.transcriptions.create(
                model=settings.openai.transcription_model,
                file=audio_file
            )

        return transcription.text

    def ChatGPT(self, input_text, messages):
        messages.append(
            {"role": "user", "content": input_text}
        )

        chat = self.client.chat.completions.create(
            model=settings.openai.chat_model, messages=messages, temperature=1.0, functions=self.functions, function_call="auto")

        reply = chat.choices[0].message.content

        function_reply = chat.choices[0].message.function_call

        if reply is not None:
            messages.append({"role": "assistant", "content": reply})
            return reply, function_reply
        else:
            if function_reply.name == "get_drawing_infomation":
                dic_tti = ast.literal_eval(function_reply.arguments)
                reply = "OK I will draw for you " + dic_tti["tti_prompt"]
                return reply, function_reply
            elif function_reply.name == "stop_talking":
                reply = "Goodbye! Call me anytime!"
                return reply, function_reply
            # elif function_reply.name == "get_user_name":

            #     dic_name = ast.literal_eval(function_reply.arguments)
            #     reply = "OK i Have remember your name, your name is " + dic_name["user_name"]
            #     messages.append({"role": "assistant", "content": reply})
            #     return reply, function_reply

    def text_to_speech(self, input_text, speed = 0.5):
        response = self.client.audio.speech.create(
            model=settings.openai.speech_model,
            voice="nova",
            input=input_text,
            speed=speed)

        # save as mp3
        output_mp3 = settings.paths.openai_data / "output.mp3"
        output_wav = settings.paths.openai_data / "out.wav"
        response.write_to_file(output_mp3)

        # raise pitch
        sound = AudioSegment.from_file(
            output_mp3, format="mp3")
        sound = sound + 6

        new_sample_rate = int(sound.frame_rate * (2.7 ** 0.5))
        hipitch_sound = sound._spawn(sound.raw_data, overrides={
                                     'frame_rate': int(new_sample_rate)})
        hipitch_sound = hipitch_sound.set_frame_rate(44100)

        # save raised pitch file
        hipitch_sound.export(output_wav, format="wav")

        time.sleep(0.5)

    def image_generations(self, promt):
        image = np.ones((320, 240, 3), dtype=np.uint8) * 255
        try:
            response = self.client.images.generate(
                model=settings.openai.image_model,
                prompt=promt,
                size="256x256",
                quality="standard",
                n=1,
            )

            url = response.data[0].url

            image_response = requests.get(url, timeout=30)
            image_response.raise_for_status()
            image = Image.open(BytesIO(image_response.content))
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(e)

        return image
    
    def image_to_text(self, encoded_img):
        if isinstance(encoded_img, bytes):
            encoded_img = encoded_img.decode("ascii")
        headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
                }

        payload = {
                "model": settings.openai.vision_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are EVE, a small helpful robot. Treat the image as your eyes and describe the surroundings briefly.",
                    },
                    {
                        "role": "user",
                        "content": [
                        {
                        "type": "text",
                        "text": "What are you seeing?. Answer start with:I can see ...."
                        },
                        {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_img}"
                        }
                        }
                        ],
                    }
                ],
                "max_tokens": 100
                }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()

    # {
    #                         "name": "get_user_name",
    #                         "description": "get the name of the user",
    #                         "parameters": {
    #                             "type": "object",
    #                             "properties": {
    #                                 "user_name": {
    #                                     "type": "string",
    #                                     "description": "get user name when he or she tell you about his or her name, collect all letter into name when user spell their name because you can only hear",
    #                                 },

    #                             },

    #                         }
    #                     },
