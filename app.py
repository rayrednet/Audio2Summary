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
async def progress_generator(file_path, font="Arial", color="000000", language="en"):
    print(f"✅ [progress_generator] Received language: {language}")

    yield "⏳ Upload successful. Starting processing...\n"
    time.sleep(1)

    yield "🔄 Extracting audio...\n"
    audio_path = extract_audio(file_path)
    time.sleep(1)

    yield "📝 Transcribing audio...\n"
    transcription = transcribe_audio(audio_path)
    time.sleep(1)

    yield "📑 Summarizing transcript...\n"
    summary = summarize_text(transcription, language)
    time.sleep(1)

    yield "📄 Generating PDF...\n"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = export_to_pdf(summary, f"Meeting_Minutes_{timestamp}.pdf", font, color, language)
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
def summarize_text(transcription, language="en"):
    print("\nGenerating Minutes of Meeting...")

    transcript_chunks = split_text_into_chunks(transcription)
    print(f"📌 Transcript split into {len(transcript_chunks)} chunks.")

    llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY)

    summarized_chunks = []

    for i, chunk in enumerate(transcript_chunks):
        print(f"\n📌 Summarizing Chunk {i + 1}/{len(transcript_chunks)}...")
        messages = [
            SystemMessage(
                content=f"You are an AI that converts meeting transcripts into structured Minutes of Meeting (MoM). "
                        f"Generate the MoM **entirely in {language}**. Do not mix languages."
                        f"Do NOT add numbers before section headers."
                        f"Use only the exact section headers from the list below. Do NOT change them."
            ),
            HumanMessage(content=
                         f"""Summarize this part of a meeting transcript **in {language}**:

                                    1️⃣ **Agenda:** Extract the main topics discussed. **Format them as bullet points (`-`).**
                                    2️⃣ **Attendees:** List all attendees using bullet points (`-`). If roles are mentioned, include them in parentheses.
                                    3️⃣ **Discussion Points:** Summarize the key ideas, arguments, and perspectives shared.
                                    4️⃣ **Action Items:** List key tasks assigned in bullet points (`-`).
                                    5️⃣ **Conclusion:** Summarize the final thoughts and meeting takeaways.

                                     Transcript:  
                                     {chunk}
                                     """
                         )
        ]
        summary = llm.invoke(messages)
        summarized_chunks.append(summary.content)

        section_headers = {
            "en": [
                "**Meeting Title:**", "**Date & Time:**", "**Attendees:**",
                "**Agenda:**", "**Discussion Points:**", "**Action Items:**",
                "**Conclusion:**", "**Next Meeting Date:**"
            ],
            "id": [
                "**Judul Rapat:**", "**Tanggal & Waktu:**", "**Peserta:**",
                "**Agenda:**", "**Poin Diskusi:**", "**Tindakan:**",
                "**Kesimpulan:**", "**Tanggal Rapat Berikutnya:**"
            ],
            "ms": [
                "**Tajuk Mesyuarat:**", "**Tarikh & Masa:**", "**Peserta:**",
                "**Agenda:**", "**Perkara Dibincangkan:**", "**Tindakan:**",
                "**Kesimpulan:**", "**Tarikh Mesyuarat Seterusnya:**"
            ],
            "tl": [
                "**Pamagat ng Pulong:**", "**Petsa at Oras:**", "**Mga Dumalo:**",
                "**Adyenda:**", "**Mga Punto ng Talakayan:**", "**Mga Hakbang na Dapat Gawin:**",
                "**Konklusyon:**", "**Susunod na Petsa ng Pagpupulong:**"
            ]
        }

    date_not_mentioned = {
        "en": "Not mentioned",
        "id": "Tidak disebutkan",
        "ms": "Tidak dinyatakan",
        "tl": "Hindi nabanggit"
    }

    headers = section_headers.get(language, section_headers["en"])

    print("\n📌 Merging summarized chunks into final MoM...")
    messages = [
        SystemMessage(
            content=f"""You are an AI that converts meeting transcripts into structured Minutes of Meeting (MoM).
            - Generate the MoM **entirely in {language}**. Do not mix languages.
            - Do **NOT** add numbers or bullet points before section headers.
            - Use **only** the exact section headers from the list below. Do **NOT** modify them.
            - Ensure that **each section header appears on a new line, followed by its content**.
            - Leave **one empty line** between each section.
            """),
        HumanMessage(
            content="Combine these meeting summaries into a structured MoM:\n\n" + "\n\n".join(summarized_chunks) +
                    "\n\nFormat it with these section headers WITHOUT numbering:\n"
                    + "\n".join(headers) +
                    "\n\nRules:\n"
                    f"- If '{headers[1]}' (Date & Time) is missing, write **{date_not_mentioned[language]}**.\n"
                    f"- If '{headers[-1]}' (Next Meeting Date) is missing, write **{date_not_mentioned[language]}**.\n"
                    "- **Use bullet points (`-`) for Attendees, Agenda, and Action Items.**\n"
                    "- Ensure professional formatting and consistent spacing."
        )
    ]
    final_summary = llm.invoke(messages)

    return final_summary.content

class PDFWithFooter(FPDF):
    def footer(self):
        self.set_y(-15)  # Position footer 15mm from the bottom
        self.set_font("Arial", "I", 10)
        self.set_text_color(150, 150, 150)  # Light gray text

        # Format timestamp in a human-readable format
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        footer_text = f"Generated by MoMify | {timestamp}"

        # Logo settings
        logo_path = "assets/logo.png"
        logo_width = 6  # Adjust for better alignment
        logo_height = 6  # Adjust for better alignment

        try:
            # Get page width for centering
            page_width = self.w
            text_width = self.get_string_width(footer_text)
            total_width = text_width + logo_width + 5  # Space between logo and text

            # Calculate X position for centering
            x_position = (page_width - total_width) / 2
            y_position = self.get_y() + 1  # Adjust text baseline

            # Print debug info
            print(f"📌 Footer Debug Info:")
            print(f"   - Page Width: {page_width}")
            print(f"   - Text Width: {text_width}")
            print(f"   - Logo Width: {logo_width}")
            print(f"   - Total Width: {total_width}")
            print(f"   - X Position: {x_position}")
            print(f"   - Y Position (before): {self.get_y()}")
            print(f"   - Y Position (after adj.): {y_position}")

            # Place logo
            self.image(logo_path, x=x_position, y=y_position - 1, w=logo_width, h=logo_height)

            # Place text
            self.set_xy(x_position + logo_width + 3, y_position)  # Fine-tune text positioning
            self.cell(0, 6, footer_text, align="L")

        except Exception as e:
            print(f"⚠️ Error in footer rendering: {e}")
            print("⚠️ Warning: MoMify logo not found at 'assets/logo.png'!")

### **🔹 Export Summary to PDF in MoM Format**
def export_to_pdf(summary, filename="Meeting_Minutes.pdf", font="Arial", color="000000", language="en"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Format timestamp
    formatted_date = datetime.now().strftime("%B-%d-%Y_%H-%M-%S")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Meeting_Minutes_{formatted_date.upper()}_{language.upper()}.pdf"

    print("\nExporting summary to PDF...")
    print("\n📜 Debug: Exporting summary to PDF...")
    print(f"🎨 Chosen font: {font}")
    print(f"🎨 Chosen color: {color}")
    print(f" 🌎 Language selected: {language}")
    print(f"📜 File name: {filename}")

    # ✅ Convert color from HEX to RGB
    r, g, b = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
    print(f"🎨 Converted RGB Color: {r}, {g}, {b}")

    pdf_path = os.path.join(OUTPUT_DIR, filename)
    pdf = PDFWithFooter()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ✅ Register Poppins font (if not already registered)
    pdf.add_font("Poppins", "", "assets/fonts/Poppins-Regular.ttf", uni=True)
    pdf.add_font("Poppins", "B", "assets/fonts/Poppins-Bold.ttf", uni=True)

    pdf.set_font("Poppins", "", 12)  # Normal text
    pdf.set_font("Poppins", "B", 14)  # Bold text

    # ✅ Set Title Formatting (Always Bold and Colored)
    pdf.set_font(font, "B", 20)
    pdf.set_text_color(r, g, b)  # Apply user-selected color
    pdf.cell(200, 10, "MEETING MINUTES", ln=True, align='C')

    # ✅ Draw a colored line below the title
    pdf.ln(2)  # Small space before the line
    pdf.set_draw_color(r, g, b)  # Use the user-selected color
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())  # Draw a horizontal line across the page

    pdf.ln(8)  # Space after the line before the content

    # ✅ Replace **bold** markers from Markdown
    summary = summary.replace("**", "")

    # ✅ Define section headers that should be bold and colored
    bold_headers_dict = {
        "en": ["Meeting Title:", "Date & Time:", "Attendees:", "Agenda:",
               "Discussion Points:", "Action Items:", "Conclusion:", "Next Meeting Date:"],

        "id": ["Judul Rapat:", "Tanggal & Waktu:", "Peserta:", "Agenda:",
               "Poin Diskusi:", "Tindakan:", "Kesimpulan:", "Tanggal Rapat Berikutnya:"],

        "ms": ["Tajuk Mesyuarat:", "Tarikh & Masa:", "Peserta:", "Agenda:",
               "Perkara Dibincangkan:", "Tindakan:", "Kesimpulan:", "Tarikh Mesyuarat Seterusnya:"],

        "tl": ["Pamagat ng Pulong:", "Petsa at Oras:", "Mga Dumalo:", "Adyenda:",
               "Mga Punto ng Talakayan:", "Mga Hakbang na Dapat Gawin:", "Konklusyon:",
               "Susunod na Petsa ng Pagpupulong:"]
    }

    # ✅ Debugging: Print what language was actually used
    if language not in bold_headers_dict:
        print(f"⚠️ Warning: Language '{language}' not found, defaulting to 'en'.")
        language = "en"

    bold_headers = bold_headers_dict[language]
    print(f"📌 Using bold headers for language: {language}")
    print(f"🔎 Expected bold headers: {bold_headers}")

    # ✅ Debug: Print Summary Before Processing
    print("\n📜 Processed Summary Content:\n", summary)

    lines = summary.split("\n")
    for line in lines:
        stripped_line = line.strip()

        # ✅ If the line is a bold header, apply bold font & selected color
        if any(stripped_line.startswith(header) for header in bold_headers):
            print(f"✅ Applying bold color to: {stripped_line}")
            pdf.set_font(font, "B", 14)  # Apply Bold font
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
        language: str = Form("en")
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"✅ Received font: {font}")
    print(f"✅ Received color: {color}")
    print(f"✅ Received language: {language}")

    async def event_stream():
        filename = None
        async for message in progress_generator(file_path, font=font, color=color, language=language):
            yield message
            if message.startswith("FILENAME::"):
                filename = message.replace("FILENAME::", "").strip()

        if filename:
            yield f"DOWNLOAD::{filename}"

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