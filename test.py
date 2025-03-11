import torch
import whisper
import tiktoken
from fastapi import FastAPI
from fpdf import FPDF
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment

def check_gpu():
    print("🔍 Checking GPU availability...")
    if torch.cuda.is_available():
        print("✅ GPU is available!")
        print(f"🔹 Number of GPUs: {torch.cuda.device_count()}")
        print(f"🔹 GPU Name: {torch.cuda.get_device_name(0)}")
    else:
        print("❌ No GPU detected. Running on CPU.")

def check_dependencies():
    print("\n🔍 Verifying installed dependencies...")

    try:
        model = whisper.load_model("tiny")
        print("✅ Whisper model loaded successfully.")
    except Exception as e:
        print(f"❌ Whisper model loading failed: {e}")

    try:
        enc = tiktoken.encoding_for_model("gpt-4")
        print("✅ Tiktoken is working correctly.")
    except Exception as e:
        print(f"❌ Tiktoken issue: {e}")

    try:
        app = FastAPI()
        print("✅ FastAPI is successfully imported.")
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, "Test PDF Generation", ln=True)
        print("✅ FPDF is working properly.")
    except Exception as e:
        print(f"❌ FPDF error: {e}")

    try:
        clip = VideoFileClip
        print("✅ MoviePy is successfully imported.")
    except Exception as e:
        print(f"❌ MoviePy error: {e}")

    try:
        audio = AudioSegment
        print("✅ Pydub is successfully imported.")
    except Exception as e:
        print(f"❌ Pydub error: {e}")

if __name__ == "__main__":
    check_gpu()
    check_dependencies()
