import streamlit as st
import streamlit.components.v1 as components
import requests
import time

API_URL = "http://localhost:8000"

# ✅ Load external CSS
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
    st.image("assets/logo.png", width=50)
with col2:
    st.markdown(
        "<h1 style='color: white; font-family: sans-serif;'>MoMify: Audio to Minutes of Meeting Generator</h1>",
        unsafe_allow_html=True
    )

# ✅ Introduction Section
st.markdown("""
    **MoMify** is a powerful tool designed to help you effortlessly generate **Minutes of Meeting (MoM)** from your audio or video recordings.
""")

with st.expander("What are Minutes of Meeting (MoM)?"):
    st.markdown("""
    Minutes of Meeting (MoM) are official written records of discussions, decisions, and action items made during a meeting. They help keep track of key points and ensure accountability among participants.
    """)

with st.expander("How Does MoMify Work?"):
    st.markdown("""
    1️⃣ **Upload an Audio or Video File** (Max: **1GB**) 📤  
    2️⃣ **Automatic Transcription** – We process the file and convert speech into text 📝  
    3️⃣ **Summarization** – Key discussion points and action items are extracted 📑  
    4️⃣ **Download the MoM PDF** – Get your professionally formatted meeting notes 📄  

    ✅ **Customization** (Optional): You can **choose a font and text color** for bold sections.  
    - **Default Settings:** Font - Arial, Color - Black.
    """)

# ✅ Initialize session state to control visibility
if "show_options" not in st.session_state:
    st.session_state.show_options = False  # Initially hidden

# ✅ "Let's Get Started" Button (Reveals the Next Section)
if st.button("🚀 Let's Get Started"):
    st.session_state.show_options = True

# ✅ Only show customization and upload sections when button is clicked
if st.session_state.show_options:
    st.markdown("## 🎨 Customize Your MoM (Optional)")

    # ✅ Font options with actual styles
    font_options = {
        "Arial": "Arial, sans-serif",
        "Courier": "Courier, monospace",
        "Times": "Times New Roman, serif"
    }

    # ✅ Render the dropdown using Streamlit
    selected_font = st.selectbox(
        "Choose a font for the PDF",
        options=list(font_options.keys()),  # Show available fonts
        index=0,  # Default to Arial
    )

    # ✅ Apply custom CSS for a **dark-themed dropdown**
    st.markdown(
        f"""
        <style>
            /* Make the dropdown dark */
            div[data-baseweb="select"] > div {{
                background-color: #1E1E1E !important; /* Dark background */
                color: white !important; /* White text */
                font-family: {font_options[selected_font]} !important; /* Apply font style */
            }}

            /* Ensure dropdown list matches dark theme */
            ul[role="listbox"] {{
                background-color: #1E1E1E !important; /* Darker dropdown */
                color: white !important;
            }}

            /* Ensure selected item is also styled */
            div[data-baseweb="select"] span {{
                font-family: {font_options[selected_font]} !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ✅ Allow the user to pick a color for bold text
    selected_color = st.color_picker("Pick a color for bold text", "#000000")

    # ✅ Add a language selection dropdown
    st.markdown("## 🌎 Select Notes Language")

    language_options = {
        "English": "en",
        "Bahasa Indonesia": "id",
        "Spanish": "es",
        "French": "fr",
        "German": "de"
    }

    selected_language = st.selectbox("Choose the language for the Meeting Minutes", list(language_options.keys()),
                                     index=0)

    # ✅ Upload File Section
    st.markdown("## 📂 Upload Your File")

    uploaded_file = st.file_uploader(
        "Upload an audio or video file",
        type=["mp3", "wav", "mp4", "m4a", "wma", "avi", "mkv"],
        help="Limit: 1GB per file"
    )

    # ✅ Progress Stepper
    def render_stepper(step):
        """Dynamically renders the stepper UI based on the current step using proper HTML rendering"""
        step_titles = [
            "📩 Uploading file...",
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
    stepper_container = st.empty()
    with stepper_container:
        components.html(f"""
            <style>{css}</style>
            {stepper_html}
        """, height=height_needed)

    # ✅ Process File Button
    if uploaded_file:
        st.info("File uploaded successfully. Click 'Process File' to generate MoM.")

        if st.button("Process File 🚀"):
            st.info("Uploading and processing... please wait.")

            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            payload = {
                "font": selected_font,
                "color": selected_color.lstrip("#"),
                "language": language_options[selected_language]
            }

            print(f"Sending font: {payload['font']}")
            print(f"Sending color: {payload['color']}")
            print(f"Sending language: {payload['language']}")

            filename = None

            with requests.post(f"{API_URL}/upload/", files=files, data=payload, stream=True) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        decoded_line = line.decode("utf-8")

                        if "FILENAME::" in decoded_line:
                            filename = decoded_line.replace("FILENAME::", "").strip()
                            print(f"🔎 Extracted filename: {filename}")
                            continue

                        st.write(decoded_line)  # Show processing steps in UI

                        for step in range(step_count - 1):
                            st.session_state.progress = step
                            stepper_html, _ = render_stepper(st.session_state.progress)

                            with stepper_container:
                                components.html(f"""
                                    <style>{css}</style>
                                    {stepper_html}
                                """, height=height_needed)

                            time.sleep(2)

                    # ✅ Final step update
                    st.session_state.progress = step_count - 1
                    stepper_html, _ = render_stepper(st.session_state.progress)

                    with stepper_container:
                        components.html(f"""
                            <style>{css}</style>
                            {stepper_html}
                        """, height=height_needed)

                    st.success("🎉 Your Meeting Minutes are ready!")

                    if filename:
                        filename = filename.strip()
                        print(f"🔎 Filename received in UI: {filename}")
                        download_url = f"{API_URL}/download/{filename}"

                        # ✅ Use HTML anchor with 'download' attribute to force direct download
                        st.markdown(f'<a href="{download_url}" download="{filename}" target="_blank">'
                                    f'📥 **Download PDF**</a>', unsafe_allow_html=True)
                    else:
                        st.error("❌ Error retrieving the file!")

                else:
                    st.error("❌ Something went wrong!")
