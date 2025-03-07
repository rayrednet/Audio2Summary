import streamlit as st
import streamlit.components.v1 as components
import requests
import time
import os
from ui_components.introduction import show_introduction

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

# ✅ Display the introduction from `introduction.py`
show_introduction()

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
        "Times": "Times New Roman, serif",
        "Helvetica": "Helvetica, sans-serif",
        "Poppins": "Poppins"
    }

    # ✅ Render the dropdown using Streamlit
    selected_font = st.selectbox(
        "Choose a font for the PDF",
        options=list(font_options.keys()),  # Show available fonts
        index=0,  # Default to
        key="font_selector",
    )

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Times+New+Roman&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Arial&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Helvetica&display=swap');

        /* Ensure ALL labels remain unchanged */
        label {{
            font-family: Arial, sans-serif !important;
        }}

        /* Target ONLY the first dropdown (Font Selector) */
        div[data-testid="stSelectbox"]:first-of-type div[data-baseweb="select"] > div {{
            font-family: {font_options[selected_font]} !important;
        }}

        /* Target ONLY the first dropdown menu items (Font Options) */
        div[data-testid="stSelectbox"]:first-of-type div[data-baseweb="popover"] ul li {{
            font-family: {font_options[selected_font]} !important;
        }}

        </style>
        """, unsafe_allow_html=True)

    # ✅ Allow the user to pick a color for bold text
    selected_color = st.color_picker("Pick a color for bold text", "#000000")

    # ✅ Add a language selection dropdown
    st.markdown("## 🌎 Select Notes Language")

    language_options = {
        "English": "en",
        "Bahasa Indonesia": "id",
        "Malay":"ms",
        "Tagalog":"tl"
    }

    selected_language = st.selectbox(
        "Choose the language for the Meeting Minutes",
        list(language_options.keys()),
        index=0,
        key="language_selector",
    )

    # ✅ Upload File Section
    st.markdown("## 📂 Upload Your File")

    uploaded_file = st.file_uploader(
        "Upload an audio or video file",
        type=["mp3", "wav", "mp4", "m4a", "wma", "avi", "mkv"],
        help="Limit: 1GB per file"
    )


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
                status_class = "completed"  # ✅ Steps that are done become pink
            elif i == step:
                status_class = "active"  # ✅ The current step being processed is highlighted

            # ✅ Apply `final-step` only when progress reaches the last step
            if i == len(step_titles) - 1 and step == len(step_titles) - 1:
                status_class = "final-step"

            stepper_html += f'''
            <div class="step {status_class}">
                <div class="circle">{i + 1}</div>
                <div>{title}</div>
            </div>
            '''

        stepper_html += '</div>'
        return stepper_html, len(step_titles)


    # ✅ Ensure session state for progress exists before usage
    if "progress" not in st.session_state:
        st.session_state.progress = 0  # Initialize progress

    # ✅ Load CSS and prepare the stepper BEFORE processing
    css = load_css()  # Load the external CSS file
    stepper_html, step_count = render_stepper(st.session_state.progress)  # Now safe to use

    # ✅ Compute required height dynamically
    height_needed = step_count * 70 + 100  # Adjusted for padding

    # ✅ Create placeholders to maintain correct UI order
    button_placeholder = st.empty()  # Button placeholder (at the top)
    notification_placeholder = st.empty()  # Notification placeholder (below button)
    stepper_container = st.empty()  # Stepper placeholder (below notification)

    # ✅ Move "Process File" Button ABOVE the stepper
    if uploaded_file:
        # ✅ Render the button inside its placeholder
        process_button = button_placeholder.button("🚀 Process File Now")  # Button first

        # ✅ If button is clicked, show notification & process file
        if process_button:
            notification_placeholder.info("📂 File uploaded successfully. Click 'Process File' to generate MoM.")
            time.sleep(1)  # Small delay for user feedback
            notification_placeholder.info("⏳ Uploading and processing... please wait.")

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

            # ✅ Stream real-time updates from FastAPI
            response = requests.post(f"{API_URL}/upload/", files=files, data=payload, stream=True)

            if response.status_code == 200:
                for line in response.iter_lines():
                    decoded_line = line.decode("utf-8").strip()

                    # ✅ Detect Filename
                    if "FILENAME::" in decoded_line:
                        filename = decoded_line.replace("FILENAME::", "").strip()
                        print(f"🔎 Extracted filename: {filename}")
                        continue

                    # ✅ Update stepper dynamically based on progress messages
                    if "⏳" in decoded_line or "🔄" in decoded_line:
                        st.session_state.progress = 1
                    elif "📝" in decoded_line:
                        st.session_state.progress = 2
                    elif "📑" in decoded_line:
                        st.session_state.progress = 3
                    elif "📄" in decoded_line:
                        st.session_state.progress = 4
                    elif "✅" in decoded_line:
                        st.session_state.progress = 5

                    # ✅ Re-render the stepper
                    stepper_html, _ = render_stepper(st.session_state.progress)
                    with stepper_container:
                        components.html(f"""
                            <style>{css}</style>
                            {stepper_html}
                        """, height=height_needed)

                    time.sleep(1)  # Simulating stepper progression delay

                # ✅ Final step update
                st.session_state.progress = step_count - 1
                stepper_html, _ = render_stepper(st.session_state.progress)

                with stepper_container:
                    components.html(f"""
                        <style>{css}</style>
                        {stepper_html}
                    """, height=height_needed)

                notification_placeholder.success("🎉 Processing complete! Your Meeting Minutes are ready.")

                if filename:
                    filename = filename.strip()
                    print(f"🔎 Filename received in UI: {filename}")
                    download_url = f"{API_URL}/download/{filename}"

                    # ✅ Use HTML anchor with 'download' attribute to force direct download
                    st.markdown(f'<a href="{download_url}" download="{filename}" target="_blank">'
                                f'📥 **Download PDF**</a>', unsafe_allow_html=True)
                else:
                    notification_placeholder.error("❌ Error retrieving the file!")

            else:
                notification_placeholder.error("❌ Something went wrong!")

    # ✅ Render Stepper Placeholder BELOW the notification
    with stepper_container:
        components.html(f"""
            <style>{css}</style>
            {stepper_html}
        """, height=height_needed)
