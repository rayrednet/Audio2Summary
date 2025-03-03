import os
import whisper
from moviepy.video.io.VideoFileClip import VideoFileClip
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from fpdf import FPDF
from pydub import AudioSegment

import time
from tqdm import tqdm
import torch
import tiktoken
from dotenv import load_dotenv

# ✅ Load API key from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Hardcoded file path
FILE_PATH = "inputs/meeting-short.mp4"

def count_tokens(text, model="gpt-4"):
    """Returns the number of tokens in a string using OpenAI's tokenizer."""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def split_text_into_chunks(text, max_tokens=7500):
    """Splits long text into smaller chunks while preserving sentence structure."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_token_count = 0

    for word in words:
        word_token_count = count_tokens(word)
        if current_token_count + word_token_count > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_token_count = 0
        current_chunk.append(word)
        current_token_count += word_token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# ✅ Extract audio from video
def extract_audio(file_path):
    audio_path = "inputs/extracted_audio.wav"  # Output file in WAV format

    file_extension = os.path.splitext(file_path)[1].lower()  # Get file extension

    print(f"\nProcessing file: {file_path} (Type: {file_extension})")

    # ✅ If it's a video file, extract audio using MoviePy
    if file_extension in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
        print("🎥 Detected video file. Extracting audio...")
        video = VideoFileClip(file_path)

        if not video.audio:
            raise ValueError("❌ No audio found in the video file!")

        video.audio.write_audiofile(audio_path, codec="pcm_s16le")

    # ✅ If it's an audio file, convert it to WAV using Pydub
    elif file_extension in [".wav", ".mp3", ".m4a", ".wma", ".aac", ".flac", ".ogg"]:
        print("🎵 Detected audio file. Converting to WAV...")
        audio = AudioSegment.from_file(file_path)
        audio.export(audio_path, format="wav")

    else:
        raise ValueError(f"❌ Unsupported file format: {file_extension}")

    print(f"✅ Audio saved to {audio_path}")
    return audio_path

# ✅ Transcribe audio using OpenAI Whisper
def transcribe_audio(audio_path):
    if not torch.cuda.is_available():
        print("⚠️ Warning: No GPU detected, running on CPU. This will be slower!")

    print("\nLoading Whisper model...")
    model = whisper.load_model("medium")

    # Move model to GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    print(f"✅ Model is running on: {device}")  # Debugging print

    result = model.transcribe(audio_path)
    return result["text"]

# ✅ Summarize transcription using GPT-4 in MoM Format
def summarize_text(transcription):
    """Handles long transcripts by splitting them into smaller chunks and summarizing each separately."""
    print("\nGenerating Minutes of Meeting...")

    transcript_chunks = split_text_into_chunks(transcription)
    print(f"📌 Transcript split into {len(transcript_chunks)} chunks.")

    llm = ChatOpenAI(
        model_name="gpt-4",
        temperature=0,
        openai_api_key=OPENAI_API_KEY
    )

    summarized_chunks = []

    for i, chunk in enumerate(transcript_chunks):
        print(f"\n📌 Summarizing Chunk {i+1}/{len(transcript_chunks)}...")
        messages = [
            SystemMessage(content="You are an AI that converts meeting transcripts into structured Minutes of Meeting (MoM)."),
            HumanMessage(content=f"Summarize this part of a meeting transcript:\n\n{chunk}")
        ]
        summary = llm.invoke(messages)
        summarized_chunks.append(summary.content)

    print("\n📌 Merging summarized chunks into final MoM...")
    messages = [
        SystemMessage(content="You are an AI that creates professional Minutes of Meeting."),
        HumanMessage(
            content="Combine these meeting summaries into a structured MoM:\n\n" + "\n\n".join(summarized_chunks) +
                    "\n\nFormat it with:\n"
                    "1. **Meeting Title**\n"
                    "2. **Date & Time**\n"
                    "3. **Attendees** (List of Participants)\n"
                    "4. **Agenda**\n"
                    "5. **Discussion Points**\n"
                    "6. **Action Items**\n"
                    "7. **Next Meeting Date (if applicable)**\n\n"
                    "Ensure it's concise, clear, and professional.")
    ]
    final_summary = llm.invoke(messages)

    return final_summary.content

# ✅ Export summary to PDF in MoM format
def export_to_pdf(summary, output_filename="outputs/Meeting_Minutes.pdf"):
    os.makedirs("outputs", exist_ok=True)  # Ensure output folder exists

    print("\nExporting summary to PDF...")
    for _ in tqdm(range(100), desc="Saving PDF", unit="%"):
        time.sleep(0.01)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ✅ Meeting Title
    pdf.set_font("Arial", "B", 20)
    pdf.cell(200, 10, "MEETING MINUTES", ln=True, align='C')
    pdf.ln(5)

    # ✅ Subtitle (Meeting Type)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 8, "ADMIN MEETING", ln=True, align='C')
    pdf.ln(5)

    # ✅ Horizontal Line
    pdf.set_draw_color(0, 128, 0)  # Green color
    pdf.set_line_width(1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # ✅ Process Summary Sections
    sections = summary.split("\n\n")  # Split sections

    for section in sections:
        if "**" in section:  # If section has a heading
            section = section.replace("**", "").strip()  # Remove Markdown bold
            pdf.set_font("Arial", "B", 12)  # ✅ Bold for headings
            pdf.multi_cell(0, 8, section)  # Print heading
            pdf.ln(2)  # Small space after heading
        else:
            pdf.set_font("Arial", "", 12)  # ✅ Normal font for body text
            pdf.multi_cell(0, 8, section)  # Print body text
            pdf.ln(4)  # Space between paragraphs

    # ✅ Attempt to Save the PDF Safely
    max_attempts = 5  # Retry up to 5 times
    for attempt in range(max_attempts):
        try:
            pdf.output(output_filename)
            print(f"✅ Minutes of Meeting saved to {output_filename}")
            return
        except PermissionError:
            print(f"⚠️ File '{output_filename}' is open. Close it and retrying ({attempt + 1}/{max_attempts})...")
            time.sleep(2)  # Wait before retrying

    print(f"❌ Failed to save PDF. Make sure '{output_filename}' is closed and try again.")

# ✅ Run the script
if __name__ == "__main__":
    if not os.path.exists(FILE_PATH):
        print(f"❌ Error: File '{FILE_PATH}' not found!")
    else:
        print("\n🚀 Starting the process...")

        audio_path = extract_audio(FILE_PATH)
        transcription = transcribe_audio(audio_path)
        summary = summarize_text(transcription)
        export_to_pdf(summary)

        print("\n✅ Process complete!")
