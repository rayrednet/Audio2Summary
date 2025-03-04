import streamlit as st
import streamlit.components.v1 as components
import requests
import time

API_URL = "http://localhost:8000"


# ✅ Load external CSS from a file
def load_css():
    with open("assets/styles.css", "r") as f:
        return f.read()


# ✅ Set Page Config
st.set_page_config(
    page_title="MoMify",
    page_icon="assets/favicon.ico",
    layout="centered",
)

# ✅ Custom Header with Logo
col1, col2 = st.columns([1, 10])
with col1:
    st.image("assets/logo.png", width=50)  # Load and display the logo
with col2:
    st.markdown(
        "<h1 style='color: white; font-family: sans-serif;'>MoMify: Audio to Minutes of Meeting Generator</h1>",
        unsafe_allow_html=True
    )

uploaded_file = st.file_uploader(
    "Upload an audio or video file",
    type=["mp3", "wav", "mp4", "m4a", "wma", "avi", "mkv"],
    help="Limit: 1GB per file"
)


def render_stepper(step):
    """Dynamically renders the stepper UI based on the current step using proper HTML rendering"""
    step_titles = [
        "1️⃣ Uploading file...",
        "🔄 Extracting audio...",
        "📝 Transcribing audio...",
        "📑 Summarizing transcript...",
        "📄 Generating PDF...",
        "✅ Processing Complete!"
    ]

    stepper_html = '<div class="stepper">'

    for i, title in enumerate(step_titles):
        status_class = "inactive"
        if i < step:
            status_class = "completed"
        elif i == step:
            status_class = "active"

        stepper_html += f'''
        <div class="step {status_class}">
            <div class="circle">{i + 1}</div>
            <div>{title}</div>
        </div>
        '''

    stepper_html += '</div>'
    return stepper_html, len(step_titles)


# ✅ Initialize session state for tracking progress
if "progress" not in st.session_state:
    st.session_state.progress = 0

css = load_css()  # Load the external CSS file
stepper_html, step_count = render_stepper(st.session_state.progress)

# ✅ Compute required height dynamically
height_needed = step_count * 70 + 100  # Adjusted for padding

# ✅ Use `components.html()` instead of `st.empty().html()`
stepper_container = components.html(f"""
    <style>{css}</style>
    {stepper_html}
""", height=height_needed)

if uploaded_file:
    st.info("Uploading and processing... please wait.")

    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    filename = None  # To store the correct filename

    with requests.post(f"{API_URL}/upload/", files=files, stream=True) as response:
        if response.status_code == 200:
            for line in response.iter_lines():
                decoded_line = line.decode("utf-8")

                if decoded_line.startswith("FILENAME::"):
                    filename = decoded_line.replace("FILENAME::", "").strip()  # Extract filename
                    continue

                st.write(decoded_line)  # Show processing steps in UI

                for step in range(step_count - 1):
                    st.session_state.progress = step
                    stepper_html, _ = render_stepper(st.session_state.progress)
                    stepper_container = components.html(f"""
                        <style>{css}</style>
                        {stepper_html}
                    """, height=height_needed)
                    time.sleep(2)

            # ✅ Final step
            st.session_state.progress = step_count - 1
            stepper_html, _ = render_stepper(st.session_state.progress)
            stepper_container = components.html(f"""
                <style>{css}</style>
                {stepper_html}
            """, height=height_needed)

            st.success("🎉 Your Meeting Minutes are ready!")

            if filename:
                download_url = f"{API_URL}/download/{filename}"
                st.markdown(f"[📥 Download PDF]({download_url})")
            else:
                st.error("❌ Error retrieving the file!")

        else:
            st.error("❌ Something went wrong!")
