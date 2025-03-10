import streamlit as st

def show_customization():
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
        options=list(font_options.keys()),
        index=0,
        key="font_selector",
    )

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Times+New+Roman&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Arial&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Helvetica&display=swap');

        label {{
            font-family: Arial, sans-serif !important;
        }}

        div[data-testid="stSelectbox"]:first-of-type div[data-baseweb="select"] > div {{
            font-family: {font_options[selected_font]} !important;
        }}

        div[data-testid="stSelectbox"]:first-of-type div[data-baseweb="popover"] ul li {{
            font-family: {font_options[selected_font]} !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    # ✅ Allow the user to pick a color for bold text
    selected_color = st.color_picker("Pick a color for bold text", "#000000")

    # ✅ Language selection dropdown
    st.markdown("## 🌎 Select Notes Language")

    language_options = {
        "English": "en",
        "Bahasa Indonesia": "id",
        "Malay": "ms",
        "Tagalog": "tl"
    }

    selected_language_label = st.selectbox(
        "Choose the language for the Meeting Minutes",
        list(language_options.keys()),  # Show language names
        index=0,
        key="language_selector",
    )

    # ✅ Return the **correct language code** instead of the label
    selected_language = language_options[selected_language_label]

    return selected_font, selected_color, selected_language
