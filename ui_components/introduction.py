import streamlit as st
import os

def show_introduction():
    """Displays the introduction section and explanation of MoM."""

    # ✅ Define the correct logo path
    logo_path = "assets/logo.png"

    # ✅ Create a layout with columns
    col1, col2 = st.columns([1, 10])  # Adjusts spacing

    # ✅ Place logo in col1 (left)
    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=60)
        else:
            st.warning("⚠️ Logo file not found! Please check 'assets/logo.png'.")

    # ✅ Place title in col2 (left-aligned)
    with col2:
        st.markdown("""
                <h1 style="color: white; font-family: sans-serif; text-align: left;">
                    MoMify: Audio to Minutes of Meeting Generator
                </h1>
            """, unsafe_allow_html=True)

    # ✅ Add an underline spanning the full width
    st.markdown("""
            <hr style="border: 3px solid #FF957F; border-radius: 3px; margin-top: -10px; width: 100%; text-align: left;">
        """, unsafe_allow_html=True)

    # ✅ Left-aligned introduction text
    st.markdown("""
            <p style="font-size: 18px; text-align: left;">
                <strong>MoMify</strong> is a powerful tool designed to help you effortlessly generate 
                <strong style="color: #FF957F;">Minutes of Meeting (MoM)</strong> from your audio or video recordings.
            </p>
        """, unsafe_allow_html=True)

    with st.expander("What are Minutes of Meeting (MoM)?"):
        st.markdown("""
        **Minutes of Meeting (MoM)** are structured records that capture **key discussions, decisions, and action items** from a meeting. These notes serve as an official reference, ensuring that all participants are aligned and accountable for their tasks.  

        #### **Why are MoM Important?**
        - 📝 **Accurate Record Keeping:** Provides a clear summary of what was discussed.  
        - ✅ **Accountability:** Assigns responsibility for action items and follow-ups.  
        - 📅 **Future Reference:** Helps participants recall details of previous meetings.  
        - ⏳ **Saves Time:** Eliminates confusion by documenting agreements and decisions.  

        **MoM can include details like:**  
        - **Meeting Title & Date**  
        - **List of Attendees**  
        - **Agenda & Discussion Points**  
        - **Decisions Made & Next Steps**  
        - **Next Meeting Schedule (if applicable)**  

        Below is an example of a professionally formatted MoM:  
        """)

        # ✅ Define file paths
        img1_path = "assets/mom_example1.jpg"
        img2_path = "assets/mom_example2.jpg"

        # ✅ Display images side by side if both exist
        if os.path.exists(img1_path) and os.path.exists(img2_path):
            col1, col2 = st.columns(2)
            with col1:
                st.image(img1_path, caption="MoM Example - Part 1", use_container_width=True)
            with col2:
                st.image(img2_path, caption="MoM Example - Part 2", use_container_width=True)
        else:
            # ✅ Display images in a stacked layout if one is missing
            if os.path.exists(img1_path):
                st.image(img1_path, caption="MoM Example - Part 1", use_container_width=True)
            if os.path.exists(img2_path):
                st.image(img2_path, caption="MoM Example - Part 2", use_container_width=True)

            if not os.path.exists(img1_path) and not os.path.exists(img2_path):
                st.warning(
                    "⚠️ Example images not found. Please ensure `mom_example1.jpg` and `mom_example2.jpg` are inside the `assets/` folder.")

    with st.expander("How Does MoMify Work?"):
        st.markdown("""
        **MoMify** transforms your meeting recordings into professional **Minutes of Meeting (MoM)** using cutting-edge AI technology.  

        #### The Process:

        1️⃣ **Upload an Audio or Video File** (Max: **1GB**) 📤  
            - Supports formats like **MP3, WAV, MP4, M4A, WMA, AVI, MKV**  

        2️⃣ **Speech-to-Text Conversion** 📝  
            - We use **OpenAI's Whisper model** for **high-accuracy transcription**  
            - Supports multiple languages with near **human-level accuracy**  

        3️⃣ **AI-Powered Summarization** 📑  
            - The transcript is analyzed using **GPT-4**  
            - Extracts **key discussion points, action items, and decisions**  

        4️⃣ **Professional MoM Generation** 📄  
            - The summarized text is formatted into a structured **Minutes of Meeting (MoM)**  
            - Includes **Meeting Title, Date & Time, Attendees, Agenda, Action Items, and Next Steps**  

        5️⃣ **Customization & PDF Export** 🎨  
            - You can **customize the font, text color, and language**  
            - Supports **English, Bahasa Indonesia, Malay, and Tagalog**  
            - Download your **MoM as a PDF** in a **clean and readable format**  

        **💡 Under the Hood:**  
        - 🗣️ **Whisper AI** (for high-quality audio transcription)  
        - 🧠 **GPT-4** (for structured summarization)  
        - 📄 **PDF Generation** (for a professional and shareable MoM format)  

        🎯 **Default Settings:**  
        - **Font:** Arial  
        - **Color:** Black  
        - **Language:** English  
        """)

