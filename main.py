from fastapi import FastAPI, File, UploadFile
from google.cloud import speech
import google.generativeai as genai
from fastapi import FastAPI
from dotenv import load_dotenv
import os

app = FastAPI()

# Allow all origins, all methods, and all headers (for simplicity)
# Function to process audio transcription
# Load the .env file
load_dotenv()

# Access the API key from the environment
google_api_key = os.getenv("GOOGLE_API_KEY")
def process_audio_and_transcribe(file_location):
    # Google Cloud Speech API setup
    client = speech.SpeechClient.from_service_account_file('keys.json')
    with open(file_location, "rb") as f:
        mp3_data = f.read()

    audio_file_obj = speech.RecognitionAudio(content=mp3_data)
    config = speech.RecognitionConfig(
        sample_rate_hertz=44100,
        enable_automatic_punctuation=True,
        language_code="en-US"
    )

    # Transcribe audio
    response = client.recognize(config=config, audio=audio_file_obj)
    if response.results:
        transcript = ' '.join([result.alternatives[0].transcript for result in response.results])
        return transcript
    else:
        return ""


# Route to handle audio upload and transcription
@app.post("/upload-audio/")
async def upload_audio_and_transcribe(file: UploadFile = File(...)):
    file_location = f"received_{file.filename}"
    with open(file_location, "wb") as audio_file:
        audio_file.write(await file.read())

    # Process audio and get transcript
    transcript = process_audio_and_transcribe(file_location)

    # Generate content based on transcript using Generative AI
    if transcript:
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-pro')
        question = "Rate this content 1 to 10 for kids: " + transcript
        response = model.generate_content(question)
        generated_text = response.text
    else:
        generated_text = "No transcript available."

    return {
        "message": f"Audio '{file.filename}' received and transcribed successfully",
        "transcript": transcript,
        "generated_text": generated_text
    }
