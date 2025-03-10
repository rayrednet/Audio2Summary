import streamlit as st

def upload_file():
    """Displays the file upload section and returns the uploaded file."""
    # ✅ Upload File Section
    st.markdown("## 📂 Upload Your File")

    uploaded_file = st.file_uploader(
        "Upload an audio or video file",
        type=["mp3", "wav", "mp4", "m4a", "wma", "avi", "mkv"],
        help="Limit: 1GB per file"
    )

    return uploaded_file