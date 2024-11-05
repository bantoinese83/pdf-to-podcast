# 🎙️ PDF to Podcast Converter

This project converts a PDF document into a podcast by extracting text from the PDF, generating a conversational script, and converting the script to speech using ElevenLabs API.

## ✨ Features

- 📄 Extracts text from a PDF document
- 🧹 Cleans and segments the text
- 🗣️ Generates a conversational script using Google Gemini API
- 🎧 Convert the script to speech using ElevenLabs API
- 🎶 Combines audio segments into a final podcast

## 📋 Requirements

- 🐍 Python 3.7+
- `fitz` (PyMuPDF)
- `google-generativeai`
- `spacy`
- `elevenlabs`
- `pydub`

## 🛠️ Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/bantoinese83/pdf-to-podcast.git
    cd pdf-to-podcast
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Download the SpaCy model:
    ```sh
    python -m spacy download en_core_web_sm
    ```

## ⚙️ Configuration

Set the following environment variables:

- `GEMINI_API_KEY`: Your Google Gemini API key
- `ELEVEN_LABS_KEY`: Your ElevenLabs API key

You can set these variables in your shell or create a `.env` file in the project root:

```sh
GEMINI_API_KEY=your_gemini_api_key
ELEVEN_LABS_KEY=your_eleven_labs_api_key

```


## EXAMPLE PDF TO PODCAST AUDIO
<audio controls="controls">
  <source type="audio/mp3" src="podcast.mp3"></source>
  <p>Your browser does not support the audio element.</p>
</audio>