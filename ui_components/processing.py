import streamlit as st
import requests
import time
import streamlit.components.v1 as components
from ui_components.stepper import render_stepper
from logger import logger, log_messages

API_URL = "http://localhost:8000"

def process_file(uploaded_file, selected_font, selected_color, selected_language, css):
    """Handles file processing and UI updates in Streamlit with logging."""

    # ✅ Process File Button
    process_button = st.button("🚀 Process File Now", key="process_file_now", help="Click to start processing")

    # ✅ Summary Section
    with st.expander("📄 Summary of MoM Configuration"):
        st.markdown(f"""
        - **Font:** {selected_font}  
        - **Bold Text Color:** {selected_color}  
        - **Language:** {selected_language}  
        - **Uploaded File Type:** {uploaded_file.type if uploaded_file else "No file uploaded"}  
        """)

    # ✅ Placeholders for Notifications and Stepper
    notification_placeholder = st.empty()
    stepper_container = st.empty()

    # ✅ Ensure session state for progress exists before usage
    if "progress" not in st.session_state:
        st.session_state.progress = 0  # Initialize progress

    stepper_html, step_count = render_stepper(st.session_state.progress)
    height_needed = step_count * 70 + 100

    if process_button:
        logger.info("📂 File upload started.")
        notification_placeholder.info("📂 File uploaded successfully. Processing... please wait.")
        time.sleep(1)

        # ✅ Prepare API request
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        payload = {
            "font": selected_font,
            "color": selected_color.lstrip("#"),
            "language": selected_language,
        }

        response = requests.post(f"{API_URL}/upload/", files=files, data=payload, stream=True)

        filename = None
        if response.status_code == 200:
            for line in response.iter_lines():
                decoded_line = line.decode("utf-8").strip()

                if "FILENAME::" in decoded_line:
                    filename = decoded_line.replace("FILENAME::", "").strip()
                    logger.info(f"📄 Processed file available: {filename}")
                    continue

                # ✅ Update Stepper Progress
                if "⏳" in decoded_line or "🔄" in decoded_line:
                    logger.info("🔄 Extracting audio...")
                    st.session_state.progress = 1
                elif "📝" in decoded_line:
                    logger.info("📝 Transcribing audio using Whisper AI...")
                    st.session_state.progress = 2
                elif "📑" in decoded_line:
                    logger.info("📑 Summarizing transcript using GPT-4...")
                    st.session_state.progress = 3
                elif "📄" in decoded_line:
                    logger.info("📄 Generating PDF output...")
                    st.session_state.progress = 4
                elif "✅" in decoded_line:
                    logger.info("✅ Processing complete!")
                    st.session_state.progress = 5

                # ✅ Update Stepper UI
                stepper_html, _ = render_stepper(st.session_state.progress)
                with stepper_container:
                    components.html(f"<style>{css}</style>{stepper_html}", height=height_needed)

                time.sleep(1)


            # ✅ Final Step Update
            st.session_state.progress = step_count - 1
            stepper_html, _ = render_stepper(st.session_state.progress)

            with stepper_container:
                components.html(f"<style>{css}</style>{stepper_html}", height=height_needed)

            notification_placeholder.success("🎉 Processing complete! Your Meeting Minutes are ready.")
            logger.info("🎉 MoM successfully generated.")

            # ✅ Show Download Button
            if filename:
                filename = filename.strip()
                download_url = f"{API_URL}/download/{filename}"

                st.markdown("""
                <style>
                .styled-button {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background-color: #1E1E1E; /* Match Process File Now button */
                    color: white;
                    font-size: 16px;
                    padding: 12px 24px;
                    border: 1px solid #ffffff40;
                    border-radius: 8px;
                    cursor: pointer;
                    text-decoration: none;
                    transition: background 0.3s ease-in-out, transform 0.1s ease-in-out, color 0.3s ease-in-out;
                }
                .styled-button:hover {
                    background-color: #FF957F; /* Same hover effect */
                    color: white !important; /* Ensure text stays white */
                    transform: scale(1.05);
                }
                .styled-button:active {
                    transform: scale(0.98); /* Small press effect */
                }
                </style>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="display: flex; justify-content: center; margin-top: 20px;">
                    <a href="{download_url}" download="{filename}" target="_blank" class="styled-button">
                        📥 Download PDF
                    </a>
                </div>
                """, unsafe_allow_html=True)
                logger.info(f"📥 Download link generated: {download_url}")
            else:
                notification_placeholder.error("❌ Error retrieving the file!")
                logger.error("❌ File retrieval failed!")
        else:
            notification_placeholder.error("❌ Something went wrong!")
            logger.error(f"❌ API Error! Status Code: {response.status_code}")

    # ✅ Render Stepper UI Below
    with stepper_container:
        components.html(f"<style>{css}</style>{stepper_html}", height=height_needed)
