import base64
import io
import os
import re

import cv2
import openai
import pytesseract
import requests
import whisper
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from google.cloud import vision
from wolframclient.evaluation import (SecuredAuthenticationKey,
                                      WolframCloudSession,
                                      WolframLanguageSession)
from wolframclient.language import wl, wlexpr

app = Flask(__name__)
CORS(app)

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
maxCompletionTokens = int(os.getenv("MAX_COMPLETION_TOKENS"))


def allButLast(array):
    return array[:len(array)-1]


def transcribe(file):
    model = whisper.load_model("base")
    return (model.transcribe(file.read()))["text"]


def splitSteps(steps):
    lefts = []
    rights = []

    for step in steps:
        split = step.split("=")
        lefts.append(split[0])
        rights.append(split[1])

    assert len(lefts) == len(rights)
    return lefts, rights


def image_to_text(blob):
    # img = cv2.imread(fileName)
    # print(pytesseract.get_languages(config=''))
    # text = pytesseract.image_to_string(img, lang="equ")

    ocr = OCR(blob)
    info = ocr.get_info()
    return info


def toWolfram(eqn):
    return eqn.replace("=", "==")


def completion(prompt):
    R = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0,
        max_tokens=maxCompletionTokens,
    )
    return (R["choices"])[0].text


class OCR:
    def __init__(self, file):
        self.client = vision.ImageAnnotatorClient()
        self.file = file

    def get_img(self):
        # binary = self.blob.download_as_string()
        # with io.open(self.blob, 'rb') as image_file:
        content = self.file.read()
        image = vision.Image(content=content)
        return image

    def get_info(self):
        img = self.get_img()
        response = self.client.document_text_detection(image=img)
        return response


@app.route('/', methods=['POST'])
def root():
    # question: str, imgBlobURL, studentWork

    print(request.form)
    question = request.form["question"]
    imgFile = request.files["imgFile"]
    # audioBlobURL = request.form["audioBlobURL"]

    info = image_to_text(imgFile)

    wolframKey = SecuredAuthenticationKey(
        'NAh6jwqC/QsPX9xli7BldYZuKzo8hXklH2qkDUCrtQc=', 'P/AHQIyKf4Tnrcj4NbOaQYUVvlKFpYZ+vkHPjdvJm6Q=')
    session = WolframCloudSession(credentials=wolframKey)
    session.start()

    if not session.authorized():
        print("not authorized!")

    # print(info)
    # print(dir(info))
    # print(info.full_text_annotation.text)
    # print(info.text)
    steps = info.full_text_annotation.text.split(
        "\n")  # split each eqn by new line
    errors = []

    for idx, step in enumerate(steps):
        wolframStep = toWolfram(step)
        # if the step doesn't line up w correct soln
        if session.evaluate(f"{wolframStep} /. Solve[{question}]") != (True,):
            errors.append(steps[idx-1])
            errors.append(step)
            break

    print("made it past here")
    # wolfram code: session.evaluate('x /. Solve[2x+3==5,x]')
    # other code: session.evaluate('2x+3==5 /. Solve[2x+3==5]')

    # url = "http://169.233.206.193:3001/api/assignments/problems/63dea28786448290b9292ce5"
    # res = requests.post(url, json={
    #     "transcription": transcribe("test.mp3"),
    #     "steps": steps
    # })

    # wolframUrl = "https://www.wolframcloud.com/obj/1ecaee59-6bcd-4f80-95ac-3be2a0c49499"
    # wolframRes = requests.get(wolframUrl, params={"steps": steps})

    # if success:

    # for idx, step in enumerate(steps[:len(steps)-1]):  # up until the last step
    # "identify the portion relevant to this step?"

    # relevantTranscript = completion(find_transcript_portion(
    #     errors[0], errors[1], transcribe("test.mp3")))
    # print(relevantTranscript)

    # transcribe("test.mp3")
    pt = find_error_prompt(errors[0], errors[1], steps, question)

    print(steps)
    print(errors)

    print(completion(pt).strip())
    tokens = completion(pt).strip().split("Keywords: ")
    print({
        "explanation": tokens[0],
        "keywords": [x.replace('.', '') for x in tokens[1].split(";")]
    })

    return {
        "erroneousStep": errors,
        "res": completion(pt),
        "explanation": tokens[0],
        "keywords": [x.replace('.', '') for x in tokens[1].split(";")],
        "prompt": pt,
        # "info": info
    }


# def find_transcript_portion(eq1: str, eq2: str, transcript: str) -> str:
#     return "The first erroneous step of a student's algebraic work occurs when the equation " + f"'{eq1}'" + " becomes the equation " + f"'{eq2}' in the next step." + " Here's a transcript of the student's verbal explanation of their work: '" + transcript + "'. Find the portion of the transcript mentioning the erroneous step."


def find_error_prompt(eq1: str, eq2: str, steps, question) -> str:
    # return "Here are the steps a student took to solve 2x+3=1 for x, with each equation separated by a semicolon: " + ';'.join(steps) + ". The first erroneous step of a student's algebraic work is equation " + f"'{eq2}'." + " Here's a transcript of the student's verbal explanation of their work: '" + transcript + "'. Explain the student's mistake, and generate key word(s) about the mistake."
    # " Here's a transcript of the student's verbal explanation of their work: '" + transcript +
    formattedQ = question.replace("==", "=")
    return f"Here are the steps a student took to solve {formattedQ} for x, with each equation separated by a semicolon: " + ';'.join(steps) + ". The first erroneous step of a student's algebraic work is when equation " + f"'{eq1}'" + " is rewritten as " + f"'{eq2}'." + ". Explain the student's mistake, then, generate key word(s) about the mistake starting with 'keywords: '."
    # return " Here's a transcript of the student's verbal explanation of their work: '" + transcript + "'. Identify the sections of the explanation that are incorrect, and generate keywords relevant to the mistake."
    # return "A student's work goes from the equation " + f"'{eq1}'" + " to the equation " + f"'{eq2}'." + " Here is a transcript of the student's verbal explanation of their work: '" + transcript + "'. If the student didn't make a mistake, include 'no error' in your response. Otherwise, explain the student's mistake, and generate key word(s) about the mistake."
    # return "Explain the cause of the error in the following step of algebraic work; each equation is separated by a semicolon:" + mathematicalWork
    # return "Here's the solution to an algebra problem, delimited with semicolons: ;" + soln + "; First, write a step-by-step solution. Then, determine whether this step of a student's work differs from this solution, and if so, explain the difference. If there are no errors, explain why. Each equation is separated by a newline: " + mathematicalWork


if __name__ == '__main__':
    app.run(port=7000)
