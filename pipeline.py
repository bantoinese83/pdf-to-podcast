import io
import logging
import os
import re
import threading
import time

import fitz
import google.generativeai as genai
import spacy
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment

voice_id_to_name = {
    "9BWtsMINqrJLrRacOk9x": "Aria",
    "CwhRBWXzGAHq8TQ4Fs17": "Roger",
    "EXAVITQu4vr4xnSDxMaL": "Sarah",
    "FGY2WhTYpPnrIDTdsKH5": "Laura",
    "IKne3meq5aSn9XLyUdCD": "Charlie",
    "JBFqnCBsd6RMkjVDRZzb": "George",
    "N2lVS1w4EtoT3dr4eOWO": "Callum",
    "SAz9YHcvj6GT2YYXdXww": "River",
    "TX3LPaxmHKxFdv7VOQHJ": "Liam",
    "XB0fDUnXU5powFXDhCwa": "Charlotte",
    "Xb7hH8MSUJpSbSDYk0k2": "Alice",
    "XrExE9yKIg1WjnnlVkGX": "Matilda",
    "bIHbv24MWmeRgasZH58o": "Will",
    "cgSgspJ2msm6clMCkdW9": "Jessica",
    "cjVigY5qzO86Huf0OWal": "Eric",
    "iP95p4xoKVk53GoZ742B": "Chris",
    "nPczCjzI2devNBz1zQrb": "Brian",
    "onwK4e9ZLuTAKqWW03F9": "Daniel",
    "pFZP5JQG7iQjIQuC4Bku": "Lily",
    "pqHfZKP75CvOlQylNhV4": "Bill",
}

name_to_voice_id = {v: k for k, v in voice_id_to_name.items()}

# Constants
GENAI_API_KEY = os.getenv('GEMINI_API_KEY', 'GEMINI_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVEN_LABS_KEY', 'ELEVEN_LABS_KEY')
TEMP_AUDIO_PATH = "temp_audio.mp3"
PDF_FILE_PATH = "AstrologyforBeginners.pdf"
OUTPUT_AUDIO_FILE_PATH = "podcast.mp3"
MAX_SCRIPT_CHARACTERS = 2000
MAX_AUDIO_DURATION_MS = 60000

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load SpaCy model
nlp = spacy.load('en_core_web_sm')

# Configure Google Gemini API
genai.configure(api_key=GENAI_API_KEY)

# Configure ElevenLabs API
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Generation configuration for Gemini model
generation_config = genai.GenerationConfig(
    temperature=1,
    top_p=0.95,
    top_k=64,
    max_output_tokens=8192,
    response_mime_type="text/plain"
)

# Define host and guest personalities
host_personalities = {
    "Kurt Cobain": {
        "description": "A legendary musician and lead singer of Nirvana, known for his deep and introspective lyrics",
        "catchphrase": "It's better to burn out than to fade away."
    }
}

guest_personalities = {
    "Tupac Shakur": {
        "description": "A highly influential rapper and actor, known for his powerful lyrics and social activism",
        "catchphrase": "Reality is wrong. Dreams are for real."
    }
}

requests_made = 0
lock = threading.Lock()


def rate_limiter(max_requests_per_minute=15):
    def decorator(func):
        def wrapper(*args, **kwargs):
            global requests_made
            with lock:
                requests_made += 1
                if requests_made > max_requests_per_minute:
                    logging.info(f"Rate limit reached. Waiting for {60 - (time.time() % 60)} seconds.")
                    time.sleep(60 - (time.time() % 60))
                    requests_made = 0
            return func(*args, **kwargs)

        return wrapper

    return decorator


def extract_text_from_pdf(pdf_path):
    try:
        logging.info("Extracting text from PDF...")
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        logging.info("Text extraction complete.")
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""


def clean_and_segment_text(text):
    try:
        logging.info("Cleaning and segmenting text...")
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        logging.info("Text cleaning and segmentation complete.")
        return "\n".join(sentences)
    except Exception as e:
        logging.error(f"Error cleaning and segmenting text: {e}")
        return ""


@rate_limiter()
def generate_conversational_script(cleaned_text, host_name, guest_name):
    try:
        logging.info("Generating conversational script...")
        prompt = f"""
        Generate a conversational script based on the following text:
        {cleaned_text}

        The script should be engaging, informative, and suitable for a podcast format.
        Use two speakers: a host named {host_name} and a guest named {guest_name}. The host should guide the 
        conversation with insightful questions, while the guest provides detailed responses. Include interruptions, 
        interjections, and natural pauses to make the conversation feel spontaneous and engaging. Clearly label the 
        speakers with "Host:" and "Guest:". The script should not exceed 1 minute in length and should be free of 
        special characters. Example interjections: "Wow!", "That's fascinating!", "I see what you mean.", 
        etc. The host can interrupt or interject abruptly while the guest is speaking, and the guest can do so 
        politely while the host is speaking.

        Focus on a friendly, informal tone. Include humor and fun facts about the topic.
        Emphasize key points from the PDF. Follow this dialogue structure:

        Host: (Introduction/Topic)
        Guest: (Response/Explanation)
        Host: (Follow-up Question/Clarification)
        Guest: (Additional Information/Example)
        """

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config
        )

        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(prompt)
        script = response.text[:MAX_SCRIPT_CHARACTERS]
        logging.info("Conversational script generation complete.")
        logging.info(f"Generated script: {script}")
        return script
    except Exception as e:
        logging.error(f"Error generating conversational script: {e}")
        return ""


def clean_script(script):
    return re.sub(r'[*]', '', script)


def text_to_speech(script, output_path, host_voice_id, guest_voice_id):
    try:
        logging.info("Converting text to speech...")
        script = clean_script(script)
        speaker_parts = script.split("\n")

        audio_segments = []
        for part in speaker_parts:
            if "Host:" in part:
                voice_id = host_voice_id
            elif "Guest:" in part:
                voice_id = guest_voice_id
            else:
                continue

            text = part.replace("Host:", "").replace("Guest:", "").strip()
            audio = client.generate(text=text, voice=voice_id, model="eleven_monolingual_v1")
            audio_data = b"".join(audio)
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            audio_segments.append(audio_segment)

        combined = AudioSegment.empty()
        for segment in audio_segments:
            combined += segment
            if len(combined) > MAX_AUDIO_DURATION_MS:
                combined = combined[:MAX_AUDIO_DURATION_MS]
                break
        combined.export(output_path, format="mp3")
        logging.info("Text to speech conversion complete.")
    except Exception as e:
        logging.error(f"Error converting text to speech: {e}")


def combine_audio_segments(audio_files, output_path):
    try:
        logging.info("Combining audio segments...")
        combined = AudioSegment.empty()
        for file in audio_files:
            segment = AudioSegment.from_file(file)
            combined += segment
            if len(combined) > MAX_AUDIO_DURATION_MS:
                combined = combined[:MAX_AUDIO_DURATION_MS]
                break
        combined.export(output_path, format="mp3")
        logging.info("Audio segments combined.")
    except Exception as e:
        logging.error(f"Error combining audio segments: {e}")


def choose_host_and_guest():
    host_name = "Kurt Cobain"
    guest_name = "Tupac Shakur"
    host_voice_name = "Eric"
    guest_voice_name = "Brian"
    host_voice_id = name_to_voice_id[host_voice_name]
    guest_voice_id = name_to_voice_id[guest_voice_name]
    return host_name, guest_name, host_voice_id, guest_voice_id


def map_voice_ids_to_names(host_voice_id, guest_voice_id):
    host_name = voice_id_to_name.get(host_voice_id, "Unknown")
    guest_name = voice_id_to_name.get(guest_voice_id, "Unknown")
    return host_name, guest_name


def pdf_to_podcast(pdf_path, output_audio_path):
    try:
        logging.info("Starting PDF to podcast conversion...")
        raw_text = extract_text_from_pdf(pdf_path)
        cleaned_text = clean_and_segment_text(raw_text)
        host_name, guest_name, host_voice_id, guest_voice_id = choose_host_and_guest()
        script = generate_conversational_script(cleaned_text, host_name, guest_name)
        text_to_speech(script, TEMP_AUDIO_PATH, host_voice_id, guest_voice_id)
        combine_audio_segments([TEMP_AUDIO_PATH], output_audio_path)
        os.remove(TEMP_AUDIO_PATH)
        logging.info(f"Podcast generated: {output_audio_path}")
        host_voice_name, guest_voice_name = map_voice_ids_to_names(host_voice_id, guest_voice_id)
        logging.info(f"Host voice: {host_voice_name}, Guest voice: {guest_voice_name}")
    except Exception as e:
        logging.error(f"Error in pdf_to_podcast: {e}")


if __name__ == "__main__":
    pdf_to_podcast(PDF_FILE_PATH, OUTPUT_AUDIO_FILE_PATH)
