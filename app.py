import os
import whisper
import torch
import time
import shutil
import tiktoken
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from moviepy.video.io.VideoFileClip import VideoFileClip
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from fpdf import FPDF
from pydub import AudioSegment
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime
app = FastAPI()

# Custom Middleware to increase request size
class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            max_size = 1_000_000_000  # 1GB limit

            if content_length and int(content_length) > max_size:
                return Response("❌ File too large! Max 1GB allowed.", status_code=413)

        return await call_next(request)

# ✅ Add Middleware
app.add_middleware(LimitUploadSizeMiddleware)

# ✅ Load OpenAI API Key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ✅ Function to Send Progress Updates to UI
async def progress_generator(file_path, font="Arial", color="000000"):
    yield "⏳ Upload successful. Starting processing...\n"
    time.sleep(1)

    yield "🔄 Extracting audio...\n"
    audio_path = extract_audio(file_path)
    time.sleep(1)

    yield "📝 Transcribing audio...\n"
    transcription = transcribe_audio(audio_path)
    time.sleep(1)

    yield "📑 Summarizing transcript...\n"
    summary = summarize_text(transcription)
    time.sleep(1)

    yield "📄 Generating PDF...\n"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = export_to_pdf(summary, f"Meeting_Minutes_{timestamp}.pdf", font, color)
    time.sleep(1)

    yield f"✅ Processing complete! Download: /download/{filename}\n"
    yield f"FILENAME::{filename}\n"

### **🔹 Token Counting & Chunk Splitting (For Large Transcripts)**
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


### **🔹 Extract Audio from Video & Convert Audio Formats**
def extract_audio(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()
    audio_path = os.path.join(UPLOAD_DIR, "extracted_audio.wav")

    print(f"\nProcessing file: {file_path} (Type: {file_extension})")

    if file_extension in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
        print("🎥 Detected video file. Extracting audio...")
        video = VideoFileClip(file_path)

        if not video.audio:
            raise ValueError("❌ No audio found in the video file!")

        video.audio.write_audiofile(audio_path, codec="pcm_s16le")

    elif file_extension in [".wav", ".mp3", ".m4a", ".wma", ".aac", ".flac", ".ogg"]:
        print("🎵 Detected audio file. Converting to WAV...")
        audio = AudioSegment.from_file(file_path)
        audio.export(audio_path, format="wav")

    else:
        raise ValueError(f"❌ Unsupported file format: {file_extension}")

    print(f"✅ Audio saved to {audio_path}")
    return audio_path


### **🔹 Transcribe Audio with Whisper (Using GPU if Available)**
def transcribe_audio(audio_path):
    if not torch.cuda.is_available():
        print("⚠️ Warning: No GPU detected, running on CPU. This will be slower!")

    print("\nLoading Whisper model...")
    model = whisper.load_model("medium").to("cuda" if torch.cuda.is_available() else "cpu")

    print(f"✅ Model is running on: {'cuda' if torch.cuda.is_available() else 'cpu'}")

    result = model.transcribe(audio_path)
    return result["text"]


### **🔹 Summarize Transcription into MoM Format**
def summarize_text(transcription):
    print("\nGenerating Minutes of Meeting...")

    transcript_chunks = split_text_into_chunks(transcription)
    print(f"📌 Transcript split into {len(transcript_chunks)} chunks.")

    llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY)

    summarized_chunks = []

    for i, chunk in enumerate(transcript_chunks):
        print(f"\n📌 Summarizing Chunk {i + 1}/{len(transcript_chunks)}...")
        messages = [
            SystemMessage(
                content="You are an AI that converts meeting transcripts into structured Minutes of Meeting (MoM)."),
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


### **🔹 Export Summary to PDF in MoM Format**
def export_to_pdf(summary, filename="Meeting_Minutes.pdf", font="Arial", color="000000"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Meeting_Minutes_{timestamp}.pdf"

    print("\nExporting summary to PDF...")
    print("\n📜 Debug: Exporting summary to PDF...")
    print(f"🎨 Chosen font: {font}")
    print(f"🎨 Chosen color: {color}")

    # ✅ Convert color from HEX to RGB
    r, g, b = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
    print(f"🎨 Converted RGB Color: {r}, {g}, {b}")

    pdf_path = os.path.join(OUTPUT_DIR, filename)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ✅ Set Title Formatting (Always Bold and Colored)
    pdf.set_font(font, "B", 20)
    pdf.set_text_color(r, g, b)  # Apply user-selected color
    pdf.cell(200, 10, "MEETING MINUTES", ln=True, align='C')
    pdf.ln(10)

    # ✅ Replace **bold** markers from Markdown
    summary = summary.replace("**", "")

    # ✅ Define section headers that should be bold and colored
    bold_headers = [
        "Meeting Title:", "Date & Time:", "Attendees:", "Agenda:",
        "Discussion Points:", "Action Items:", "Next Meeting Date:"
    ]

    # ✅ Debug: Print Summary Before Processing
    print("\n📜 Processed Summary Content:\n", summary)

    lines = summary.split("\n")
    for line in lines:
        stripped_line = line.strip()

        # ✅ If the line is a bold header, apply bold font & selected color
        if any(stripped_line.startswith(header) for header in bold_headers):
            pdf.set_font(font, "B", 12)  # Apply Bold font
            pdf.set_text_color(r, g, b)  # Apply user-selected color
        else:
            pdf.set_font(font, "", 12)  # Regular font
            pdf.set_text_color(0, 0, 0)  # Reset to default black for normal text

        pdf.multi_cell(0, 10, line)
        pdf.ln(2)

    pdf.output(pdf_path)
    print(f"✅ Minutes of Meeting saved to {pdf_path}")

    return filename


### **🔹 FastAPI Endpoints**
@app.post("/upload/")
async def upload_file(
        file: UploadFile = File(...),
        font: str = Form("Arial"),
        color: str = Form("000000"),
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"✅ Received font: {font}")
    print(f"✅ Received color: {color}")

    async def event_stream():
        filename = None
        async for message in progress_generator(file_path, font=font, color=color):
            yield message
            if message.startswith("FILENAME::"):
                filename = message.replace("FILENAME::", "").strip()

        if filename:
            yield f"DOWNLOAD::{filename}"  # Send download filename as the final message

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/download/{filename}")
async def download_file(filename: str):
    filepath = os.path.abspath(os.path.join(OUTPUT_DIR, filename))
    print(f"Trying to serve file: {filepath}")

    if not os.path.exists(filepath):
        print("❌ File not found!")
        return {"error": "File not found"}

    # ✅ Force the browser to download the file instead of opening it
    return FileResponse(
        path=filepath,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )