import streamlit as st
import os
from logger import logger

def upload_file():
    """Displays the file upload section and returns the uploaded file."""

    # ✅ Upload File Section
    st.markdown("## 📂 Upload Your File")

    uploaded_file = st.file_uploader(
        "Upload an audio or video file",
        type=["mp3", "wav", "mp4", "m4a", "wma", "avi", "mkv"],
        help="Limit: 1GB per file"
    )

    # ✅ Log file upload attempt
    if uploaded_file:
        file_size = len(uploaded_file.getvalue()) / (1024 * 1024)  # Convert to MB
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()

        logger.info(f"📂 File Uploaded: {uploaded_file.name} | Type: {file_extension} | Size: {file_size:.2f}MB")

        # ✅ Validate file size
        if file_size > 1000:  # 1GB Limit
            logger.warning(f"❌ File too large: {uploaded_file.name} ({file_size:.2f}MB)")
            st.error("❌ File size exceeds limit (1GB). Please upload a smaller file.")
            return None

        # ✅ Return the valid file
        return uploaded_file

    return None
