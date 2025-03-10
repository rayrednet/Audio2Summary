import streamlit as st
from ui_components.introduction import show_introduction
from ui_components.customization import show_customization
from ui_components.file_upload import upload_file
from ui_components.processing import process_file

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

# ✅ Show Introduction
show_introduction()

# ✅ Initialize session state to control visibility
if "show_options" not in st.session_state:
    st.session_state.show_options = False

# ✅ "Let's Get Started" Button
if st.button("🚀 Let's Get Started"):
    st.session_state.show_options = True

# ✅ If customization is enabled, show options
if st.session_state.show_options:
    selected_font, selected_color, selected_language = show_customization()
    uploaded_file = upload_file()

    # ✅ Load CSS **before calling process_file()**
    css = load_css()

    # ✅ Call process_file only if a file is uploaded
    if uploaded_file:
        process_file(uploaded_file, selected_font, selected_color, selected_language, css)
